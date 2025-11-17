"""
상품 정보 테이블 추가 Migration

product_info 테이블: KIS API에서 수집한 상품 메타데이터
- stock_info와 차이: 업종/시가총액 등 숫자 데이터가 아닌 상품명/분류/위험등급 등 메타정보

NOTE: Foreign Key 제약조건을 사용하지 않습니다.
      데이터 무결성은 애플리케이션 레벨에서 관리합니다.
      stock_code는 반드시 stocks 테이블에 존재하는 값이어야 합니다.

Usage:
    uv run python backend/db/migrations/add_product_info_table.py
"""
import logging
from sqlalchemy import text

from backend.db.session import SessionLocal


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def upgrade():
    """Migration 실행"""
    logger.info("=" * 80)
    logger.info("🚀 Migration: product_info 테이블 생성")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        # 테이블 생성
        logger.info("\n1. 테이블 생성 중...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS product_info (
                id SERIAL PRIMARY KEY,
                stock_code VARCHAR(10) NOT NULL UNIQUE,
                prdt_name VARCHAR(120),
                prdt_clsf_name VARCHAR(100),
                ivst_prdt_type_cd_name VARCHAR(100),
                prdt_risk_grad_cd VARCHAR(10),
                frst_erlm_dt VARCHAR(8),
                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

                CONSTRAINT uk_product_info_stock_code UNIQUE (stock_code)
            );

            COMMENT ON TABLE product_info IS '상품 메타데이터 (상품명, 분류, 위험등급 등)';
            COMMENT ON COLUMN product_info.stock_code IS '종목 코드 (stocks.code 참조, 애플리케이션 레벨 관리)';
            COMMENT ON COLUMN product_info.prdt_name IS '상품명';
            COMMENT ON COLUMN product_info.prdt_clsf_name IS '상품분류명 (예: 주권)';
            COMMENT ON COLUMN product_info.ivst_prdt_type_cd_name IS '투자상품유형명 (예: 보통주)';
            COMMENT ON COLUMN product_info.prdt_risk_grad_cd IS '위험등급코드';
            COMMENT ON COLUMN product_info.frst_erlm_dt IS '최초등록일 (YYYYMMDD)';
        """))
        logger.info("   ✅ product_info 테이블 생성 완료")

        # 인덱스 생성
        logger.info("\n2. 인덱스 생성 중...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_info_stock_code
            ON product_info(stock_code);
        """))
        logger.info("   ✅ idx_product_info_stock_code 인덱스 생성")

        # updated_at 자동 업데이트 트리거 생성
        logger.info("\n3. updated_at 트리거 생성 중...")
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_product_info_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_product_info_updated_at ON product_info;
        """))

        db.execute(text("""
            CREATE TRIGGER trigger_product_info_updated_at
            BEFORE UPDATE ON product_info
            FOR EACH ROW
            EXECUTE FUNCTION update_product_info_updated_at();
        """))
        logger.info("   ✅ updated_at 자동 업데이트 트리거 생성")

        db.commit()

        logger.info("\n" + "=" * 80)
        logger.info("✅ Migration 완료!")
        logger.info("=" * 80)

        # 테이블 정보 출력
        logger.info("\n📊 테이블 정보:")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'product_info'
            ORDER BY ordinal_position;
        """))

        for row in result:
            logger.info(f"   {row[0]}: {row[1]} (NULL: {row[2]})")

        # 인덱스 정보 출력
        logger.info("\n📊 인덱스 정보:")
        result = db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'product_info';
        """))

        for row in result:
            logger.info(f"   {row[0]}")

    except Exception as e:
        db.rollback()
        logger.error(f"\n❌ Migration 실패: {e}", exc_info=True)
        raise

    finally:
        db.close()


def downgrade():
    """Migration 롤백"""
    logger.info("=" * 80)
    logger.info("🔙 Rollback: product_info 테이블 삭제")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        # 트리거 및 함수 삭제
        db.execute(text("DROP TRIGGER IF EXISTS trigger_product_info_updated_at ON product_info;"))
        db.execute(text("DROP FUNCTION IF EXISTS update_product_info_updated_at();"))

        # 테이블 삭제
        db.execute(text("DROP TABLE IF EXISTS product_info CASCADE;"))
        db.commit()
        logger.info("\n✅ Rollback 완료!")

    except Exception as e:
        db.rollback()
        logger.error(f"\n❌ Rollback 실패: {e}", exc_info=True)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    upgrade()
