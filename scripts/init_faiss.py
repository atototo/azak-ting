"""
FAISS 인덱스 초기화 스크립트

빈 FAISS 인덱스를 생성하거나 기존 인덱스를 초기화합니다.
"""
import os
import sys
import logging
import pickle

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import faiss
from backend.config import settings


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_faiss_index(force: bool = False):
    """
    FAISS 인덱스를 초기화합니다.

    Args:
        force: True이면 기존 인덱스를 덮어씁니다.
    """
    logger.info("=" * 60)
    logger.info("FAISS 인덱스 초기화 시작")
    logger.info("=" * 60)

    index_path = settings.FAISS_INDEX_PATH
    metadata_path = settings.FAISS_METADATA_PATH

    # 디렉토리 생성
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

    # 기존 인덱스 확인
    if os.path.exists(index_path) and not force:
        logger.warning(f"FAISS 인덱스가 이미 존재합니다: {index_path}")
        logger.warning("기존 인덱스를 덮어쓰려면 --force 옵션을 사용하세요")

        # 기존 인덱스 정보 출력
        try:
            index = faiss.read_index(index_path)
            logger.info(f"기존 인덱스 정보: {index.ntotal}개 벡터")
        except Exception as e:
            logger.error(f"기존 인덱스 로드 실패: {e}")

        return

    try:
        # 빈 FAISS 인덱스 생성 (L2 거리)
        logger.info(f"FAISS 인덱스 생성 중 (차원: {settings.EMBEDDING_DIM})")
        index = faiss.IndexFlatL2(settings.EMBEDDING_DIM)

        # 인덱스 저장
        faiss.write_index(index, index_path)
        logger.info(f"✅ FAISS 인덱스 생성 완료: {index_path}")

        # 빈 메타데이터 생성
        metadata = []
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        logger.info(f"✅ 메타데이터 파일 생성 완료: {metadata_path}")

        logger.info("=" * 60)
        logger.info("FAISS 인덱스 초기화 성공!")
        logger.info("=" * 60)
        logger.info(f"인덱스 경로: {index_path}")
        logger.info(f"메타데이터 경로: {metadata_path}")
        logger.info(f"임베딩 차원: {settings.EMBEDDING_DIM}")
        logger.info(f"현재 벡터 개수: 0")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"FAISS 인덱스 초기화 실패: {e}", exc_info=True)
        sys.exit(1)


def check_faiss_status():
    """FAISS 인덱스 상태를 확인합니다."""
    logger.info("=" * 60)
    logger.info("FAISS 인덱스 상태 확인")
    logger.info("=" * 60)

    index_path = settings.FAISS_INDEX_PATH
    metadata_path = settings.FAISS_METADATA_PATH

    # 인덱스 파일 확인
    if os.path.exists(index_path):
        try:
            index = faiss.read_index(index_path)
            logger.info(f"✅ 인덱스 파일: {index_path}")
            logger.info(f"   - 벡터 개수: {index.ntotal}")
            logger.info(f"   - 차원: {index.d}")
        except Exception as e:
            logger.error(f"❌ 인덱스 로드 실패: {e}")
    else:
        logger.warning(f"❌ 인덱스 파일 없음: {index_path}")

    # 메타데이터 파일 확인
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            logger.info(f"✅ 메타데이터 파일: {metadata_path}")
            logger.info(f"   - 메타데이터 개수: {len(metadata)}")

            if metadata:
                # 샘플 메타데이터 출력
                sample = metadata[0]
                logger.info(f"   - 샘플: {sample}")
        except Exception as e:
            logger.error(f"❌ 메타데이터 로드 실패: {e}")
    else:
        logger.warning(f"❌ 메타데이터 파일 없음: {metadata_path}")

    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FAISS 인덱스 초기화")
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 인덱스를 덮어쓰기"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="현재 인덱스 상태 확인"
    )

    args = parser.parse_args()

    if args.status:
        check_faiss_status()
    else:
        init_faiss_index(force=args.force)
