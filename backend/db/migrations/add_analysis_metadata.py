"""
stock_analysis_summaries 테이블에 데이터 가용성 메타데이터 컬럼 추가

Migration: US-004 - 분석 로직 재설계
"""
import logging
from sqlalchemy import text
from backend.db.session import SessionLocal

logger = logging.getLogger(__name__)


def upgrade():
    """
    stock_analysis_summaries 테이블에 메타데이터 컬럼 추가
    - data_sources_used: 사용된 데이터 소스 (JSON)
    - limitations: 분석 한계점 (JSON)
    - confidence_level: 신뢰도 수준 (String)
    - data_completeness_score: 데이터 완전도 점수 (Float)
    """
    db = SessionLocal()

    try:
        logger.info("=== Migration 시작: 분석 메타데이터 컬럼 추가 ===")

        # 1. data_sources_used 컬럼 추가 (JSON)
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            ADD COLUMN IF NOT EXISTS data_sources_used JSON DEFAULT '{}';
        """))
        logger.info("✅ data_sources_used 컬럼 추가 완료")

        # 2. limitations 컬럼 추가 (JSON)
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            ADD COLUMN IF NOT EXISTS limitations JSON DEFAULT '[]';
        """))
        logger.info("✅ limitations 컬럼 추가 완료")

        # 3. confidence_level 컬럼 추가 (String)
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(10) DEFAULT 'medium';
        """))
        logger.info("✅ confidence_level 컬럼 추가 완료")

        # 4. data_completeness_score 컬럼 추가 (Float)
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            ADD COLUMN IF NOT EXISTS data_completeness_score FLOAT DEFAULT 0.5;
        """))
        logger.info("✅ data_completeness_score 컬럼 추가 완료")

        # 5. 기존 레코드의 기본값 설정
        result = db.execute(text("""
            UPDATE stock_analysis_summaries
            SET
                data_sources_used = '{}',
                limitations = '[]',
                confidence_level = 'medium',
                data_completeness_score = 0.5
            WHERE data_sources_used IS NULL;
        """))
        logger.info(f"✅ 기존 데이터 업데이트 완료: {result.rowcount}건")

        db.commit()
        logger.info("=== Migration 완료 ===")

    except Exception as e:
        logger.error(f"❌ Migration 실패: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def downgrade():
    """
    메타데이터 컬럼 제거 (롤백)
    """
    db = SessionLocal()

    try:
        logger.info("=== Rollback 시작: 분석 메타데이터 컬럼 제거 ===")

        # 1. data_completeness_score 컬럼 제거
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            DROP COLUMN IF EXISTS data_completeness_score;
        """))
        logger.info("✅ data_completeness_score 컬럼 제거 완료")

        # 2. confidence_level 컬럼 제거
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            DROP COLUMN IF EXISTS confidence_level;
        """))
        logger.info("✅ confidence_level 컬럼 제거 완료")

        # 3. limitations 컬럼 제거
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            DROP COLUMN IF EXISTS limitations;
        """))
        logger.info("✅ limitations 컬럼 제거 완료")

        # 4. data_sources_used 컬럼 제거
        db.execute(text("""
            ALTER TABLE stock_analysis_summaries
            DROP COLUMN IF EXISTS data_sources_used;
        """))
        logger.info("✅ data_sources_used 컬럼 제거 완료")

        db.commit()
        logger.info("=== Rollback 완료 ===")

    except Exception as e:
        logger.error(f"❌ Rollback 실패: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Migration 실행
    upgrade()

    print("\n✅ Migration 완료!")
    print("stock_analysis_summaries 테이블에 메타데이터 컬럼이 추가되었습니다.")
