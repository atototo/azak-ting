"""
priority 컬럼 Deprecated Migration
모든 priority 값을 1로 설정하여 사실상 사용하지 않도록 함
(하위 호환성을 위해 컬럼은 유지)

Usage:
    uv run python backend/db/migrations/deprecate_priority_column.py
"""
import logging
from sqlalchemy import text

from backend.db.session import SessionLocal


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def upgrade():
    """Migration 실행"""
    logger.info("=" * 80)
    logger.info("🚀 Migration: priority 컬럼 Deprecated")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        # 기존 priority 값 확인
        logger.info("\n1. 기존 priority 값 확인 중...")
        result = db.execute(text("""
            SELECT priority, COUNT(*) as count
            FROM stocks
            GROUP BY priority
            ORDER BY priority;
        """))

        logger.info("   현재 priority 분포:")
        for row in result:
            logger.info(f"   - priority {row[0]}: {row[1]}개")

        # 모든 priority를 1로 설정
        logger.info("\n2. 모든 priority를 1로 설정 중...")
        result = db.execute(text("""
            UPDATE stocks SET priority = 1 WHERE priority != 1;
        """))
        affected_rows = result.rowcount
        logger.info(f"   ✅ {affected_rows}개 행 업데이트 완료")

        # 컬럼에 주석 추가 (deprecated 표시)
        logger.info("\n3. 컬럼 주석 추가 중...")
        db.execute(text("""
            COMMENT ON COLUMN stocks.priority IS
            'DEPRECATED: 이 컬럼은 더 이상 사용하지 않습니다. is_active를 사용하세요.';
        """))
        logger.info("   ✅ priority 컬럼에 DEPRECATED 주석 추가")

        db.commit()

        logger.info("\n" + "=" * 80)
        logger.info("✅ Migration 완료!")
        logger.info("=" * 80)

        # 최종 상태 확인
        logger.info("\n📊 최종 상태:")
        result = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN priority = 1 THEN 1 END) as priority_1,
                COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active
            FROM stocks;
        """))

        row = result.fetchone()
        logger.info(f"   전체 종목: {row[0]}개")
        logger.info(f"   priority = 1: {row[1]}개 (100%)")
        logger.info(f"   is_active = TRUE: {row[2]}개")

    except Exception as e:
        db.rollback()
        logger.error(f"\n❌ Migration 실패: {e}", exc_info=True)
        raise

    finally:
        db.close()


def downgrade():
    """
    Migration 롤백
    주의: priority 값을 원래대로 복원할 수 없습니다.
    백업에서 복원해야 합니다.
    """
    logger.info("=" * 80)
    logger.info("🔙 Rollback: priority 컬럼 주석 제거")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        # 주석 제거
        db.execute(text("""
            COMMENT ON COLUMN stocks.priority IS NULL;
        """))
        db.commit()
        logger.info("\n✅ Rollback 완료!")
        logger.warning("\n⚠️  주의: priority 값은 복원되지 않았습니다. 백업에서 복원이 필요합니다.")

    except Exception as e:
        db.rollback()
        logger.error(f"\n❌ Rollback 실패: {e}", exc_info=True)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    upgrade()
