"""
PostgreSQL → FAISS 마이그레이션 스크립트

PostgreSQL에 있는 모든 뉴스를 새 임베딩 모델(KoSimCSE)로 임베딩하고 FAISS에 저장합니다.
"""
import os
import sys
import logging
from typing import List

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models.news import NewsArticle
from backend.llm.embedder import NewsEmbedder
from backend.llm.vector_search import get_vector_search


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_news(db: Session) -> List[NewsArticle]:
    """PostgreSQL에서 모든 뉴스를 조회합니다."""
    try:
        logger.info("PostgreSQL에서 뉴스 조회 중...")

        # 모든 뉴스 조회 (발행일 역순)
        all_news = (
            db.query(NewsArticle)
            .order_by(NewsArticle.published_at.desc())
            .all()
        )

        logger.info(f"✅ PostgreSQL에서 {len(all_news)}건 조회 완료")
        return all_news

    except Exception as e:
        logger.error(f"❌ PostgreSQL 조회 실패: {e}")
        raise


def migrate_news_to_faiss(
    news_list: List[NewsArticle],
    embedder: NewsEmbedder,
    batch_size: int = 100
) -> int:
    """
    뉴스를 배치로 임베딩하고 FAISS에 저장합니다.

    Args:
        news_list: 뉴스 리스트
        embedder: 임베더 인스턴스
        batch_size: 배치 크기

    Returns:
        성공적으로 마이그레이션된 뉴스 개수
    """
    total = len(news_list)
    migrated_count = 0
    failed_count = 0

    vector_search = get_vector_search()

    logger.info(f"총 {total}건 마이그레이션 시작 (배치 크기: {batch_size})")

    # 배치로 처리
    for i in range(0, total, batch_size):
        end = min(i + batch_size, total)
        batch_news = news_list[i:end]

        logger.info(f"\n배치 {i//batch_size + 1}: {i+1}~{end}/{total}")

        # 1. 텍스트 준비 (제목 + 본문)
        texts = [f"{news.title}\n{news.content}" for news in batch_news]

        # 2. 임베딩 생성
        logger.info(f"   임베딩 생성 중... ({len(texts)}개)")
        embeddings = embedder.embed_batch(texts)

        # 3. 성공/실패 분류
        success_news = []
        success_embeddings = []

        for news, embedding in zip(batch_news, embeddings):
            if embedding is not None:
                success_news.append(news)
                success_embeddings.append(embedding)
            else:
                failed_count += 1
                logger.warning(f"   뉴스 ID {news.id} 임베딩 실패")

        # 4. FAISS에 저장
        if success_embeddings:
            news_ids = [news.id for news in success_news]
            stock_codes = [news.stock_code or "" for news in success_news]
            published_timestamps = [
                int(news.published_at.timestamp()) for news in success_news
            ]

            saved_count = vector_search.add_embeddings(
                news_ids=news_ids,
                embeddings=success_embeddings,
                stock_codes=stock_codes,
                published_timestamps=published_timestamps,
            )

            migrated_count += saved_count
            logger.info(f"   ✅ {saved_count}건 저장 완료 (누적: {migrated_count}/{total})")

        # 진행률 표시
        progress = (end / total) * 100
        logger.info(f"   진행률: {progress:.1f}%")

    logger.info(f"\n최종 결과: 성공 {migrated_count}건, 실패 {failed_count}건")
    return migrated_count


def verify_migration():
    """마이그레이션 결과 검증"""
    try:
        logger.info("\n마이그레이션 결과 검증 중...")

        vector_search = get_vector_search()
        indexed_news_ids = vector_search.get_indexed_news_ids()

        logger.info(f"✅ FAISS에 {len(indexed_news_ids)}개 벡터 인덱싱됨")

        # 샘플 검색 테스트
        logger.info("\n샘플 검색 테스트:")

        test_queries = [
            "반도체 투자",
            "전기차 판매",
            "주가 상승"
        ]

        for query in test_queries:
            logger.info(f"\n  쿼리: '{query}'")
            results = vector_search.search_similar_news(
                news_text=query,
                top_k=3,
                similarity_threshold=0.0,
            )

            for i, result in enumerate(results[:3], 1):
                logger.info(f"    {i}. 뉴스 ID: {result['news_id']}, 유사도: {result['similarity']}")

        return True

    except Exception as e:
        logger.error(f"❌ 검증 실패: {e}")
        return False


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("PostgreSQL → FAISS 마이그레이션 시작")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # 1. PostgreSQL에서 모든 뉴스 조회
        all_news = get_all_news(db)

        if not all_news:
            logger.info("마이그레이션할 뉴스가 없습니다")
            return

        # 2. 임베더 초기화
        logger.info("\n임베딩 모델 초기화 중...")
        embedder = NewsEmbedder()

        # 3. 마이그레이션 실행
        logger.info("\n" + "=" * 60)
        migrated_count = migrate_news_to_faiss(
            news_list=all_news,
            embedder=embedder,
            batch_size=50  # 메모리 고려하여 배치 크기 조정
        )

        # 4. 검증
        verify_migration()

        # 5. 완료 메시지
        logger.info("\n" + "=" * 60)
        logger.info("✅ 마이그레이션 완료!")
        logger.info("=" * 60)
        logger.info(f"총 마이그레이션 건수: {migrated_count}/{len(all_news)}")
        logger.info(f"성공률: {(migrated_count/len(all_news)*100):.1f}%")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"마이그레이션 실패: {e}", exc_info=True)
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
