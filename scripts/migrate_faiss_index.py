"""
FAISS 인덱스 마이그레이션 스크립트 (Issue #19)

IndexFlatL2 → IndexIVFFlat + Inner Product 변환

사용법:
    cd /Users/young/ai-work/craveny
    .venv/bin/python scripts/migrate_faiss_index.py
"""
import os
import sys
import pickle
import shutil
from datetime import datetime

import faiss
import numpy as np

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """L2 정규화 (Inner Product = Cosine Similarity)"""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # 0으로 나누기 방지
    return vectors / norms


def migrate_index():
    """기존 IndexFlatL2를 IndexIVFFlat + Inner Product로 마이그레이션"""

    index_path = settings.FAISS_INDEX_PATH
    metadata_path = settings.FAISS_METADATA_PATH

    print(f"📂 인덱스 경로: {index_path}")
    print(f"📂 메타데이터 경로: {metadata_path}")

    # 1. 기존 인덱스 로드
    if not os.path.exists(index_path):
        print("❌ 기존 인덱스 파일이 없습니다.")
        return False

    old_index = faiss.read_index(index_path)
    ntotal = old_index.ntotal
    dim = settings.EMBEDDING_DIM

    print(f"\n📊 기존 인덱스 정보:")
    print(f"   - 벡터 수: {ntotal:,}개")
    print(f"   - 차원: {dim}")

    # IVF 인덱스인지 확인
    try:
        _ = old_index.nprobe
        print("   - 타입: IVFFlat (이미 마이그레이션됨)")
        print("\n⚠️  이미 IVF 인덱스입니다. 마이그레이션 필요 없음.")
        return True
    except AttributeError:
        print("   - 타입: FlatL2 (마이그레이션 필요)")

    # 2. 백업 생성
    backup_dir = os.path.dirname(index_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_index = os.path.join(backup_dir, f"backup_{timestamp}.index")
    backup_metadata = os.path.join(backup_dir, f"backup_{timestamp}.pkl")

    print(f"\n💾 백업 생성 중...")
    shutil.copy2(index_path, backup_index)
    shutil.copy2(metadata_path, backup_metadata)
    print(f"   - {backup_index}")
    print(f"   - {backup_metadata}")

    # 3. 기존 벡터 추출
    print(f"\n📤 벡터 추출 중...")
    vectors = np.zeros((ntotal, dim), dtype=np.float32)
    for i in range(ntotal):
        vectors[i] = old_index.reconstruct(i)
    print(f"   - {ntotal:,}개 벡터 추출 완료")

    # 4. 벡터 정규화
    print(f"\n🔄 벡터 정규화 중...")
    vectors_normalized = normalize_vectors(vectors)
    print(f"   - L2 정규화 완료")

    # 5. IVF 인덱스 생성
    nlist = min(100, int(np.sqrt(ntotal)))  # 클러스터 수 (sqrt(N) 권장)
    print(f"\n🏗️  IVF 인덱스 생성 중...")
    print(f"   - 클러스터 수: {nlist}")

    quantizer = faiss.IndexFlatIP(dim)  # Inner Product
    new_index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)

    # 6. 인덱스 학습
    print(f"\n📚 인덱스 학습 중...")
    new_index.train(vectors_normalized)
    print(f"   - 학습 완료 (is_trained={new_index.is_trained})")

    # 7. 벡터 추가
    print(f"\n📥 벡터 추가 중...")
    new_index.add(vectors_normalized)
    print(f"   - {new_index.ntotal:,}개 벡터 추가 완료")

    # 8. 저장
    print(f"\n💾 새 인덱스 저장 중...")
    faiss.write_index(new_index, index_path)
    print(f"   - 저장 완료: {index_path}")

    # 9. 검증
    print(f"\n✅ 검증:")
    verify_index = faiss.read_index(index_path)
    print(f"   - 벡터 수: {verify_index.ntotal:,}개")
    print(f"   - IVF 인덱스: {hasattr(verify_index, 'nprobe')}")

    # 10. 간단한 검색 테스트
    print(f"\n🔍 검색 테스트:")
    verify_index.nprobe = 10
    query = vectors_normalized[:1]
    distances, indices = verify_index.search(query, 5)
    print(f"   - 상위 5개 결과: indices={indices[0].tolist()}")
    print(f"   - 유사도: {[round(d, 4) for d in distances[0].tolist()]}")

    print(f"\n🎉 마이그레이션 완료!")
    print(f"   - 백업 위치: {backup_dir}")
    print(f"   - 롤백: cp {backup_index} {index_path}")

    return True


if __name__ == "__main__":
    try:
        success = migrate_index()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
