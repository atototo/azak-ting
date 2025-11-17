"""
재무비율 테이블 추가 Migration

financial_ratios 테이블: KIS API에서 수집한 재무 지표
- 성장성 지표: 매출액/영업이익/순이익 증가율
- 수익성 지표: ROE
- 주당 지표: EPS, BPS
- 안정성 지표: 부채비율, 유보율

NOTE: Foreign Key 제약조건을 사용하지 않습니다.
      데이터 무결성은 애플리케이션 레벨에서 관리합니다.
      stock_code는 반드시 stocks 테이블에 존재하는 값이어야 합니다.

Usage:
    uv run python backend/db/migrations/add_financial_ratios_table.py
"""
import logging
from sqlalchemy import text

from backend.db.session import SessionLocal


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def upgrade():
    """Migration 실행"""
    logger.info("=" * 80)
    logger.info("🚀 Migration: financial_ratios 테이블 생성")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        # 테이블 생성
        logger.info("\n1. 테이블 생성 중...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS financial_ratios (
                id SERIAL PRIMARY KEY,
                stock_code VARCHAR(10) NOT NULL,
                stac_yymm VARCHAR(6) NOT NULL,
                div_cls_code VARCHAR(1) DEFAULT '0' NOT NULL,

                -- 성장성 지표
                grs FLOAT,
                bsop_prfi_inrt FLOAT,
                ntin_inrt FLOAT,

                -- 수익성 지표
                roe_val FLOAT,

                -- 주당 지표
                eps FLOAT,
                bps FLOAT,

                -- 안정성 지표
                lblt_rate FLOAT,
                rsrv_rate FLOAT,

                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

                CONSTRAINT uq_financial_ratios UNIQUE (stock_code, stac_yymm, div_cls_code)
            );

            COMMENT ON TABLE financial_ratios IS '재무비율 데이터 (년도/분기별 재무 지표)';
            COMMENT ON COLUMN financial_ratios.stock_code IS '종목 코드 (stocks.code 참조, 애플리케이션 레벨 관리)';
            COMMENT ON COLUMN financial_ratios.stac_yymm IS '결산년월 (YYYYMM)';
            COMMENT ON COLUMN financial_ratios.div_cls_code IS '구분코드 (0:년도, 1:분기)';
            COMMENT ON COLUMN financial_ratios.grs IS '매출액증가율 (%)';
            COMMENT ON COLUMN financial_ratios.bsop_prfi_inrt IS '영업이익증가율 (%)';
            COMMENT ON COLUMN financial_ratios.ntin_inrt IS '순이익증가율 (%)';
            COMMENT ON COLUMN financial_ratios.roe_val IS 'ROE 자기자본이익률 (%)';
            COMMENT ON COLUMN financial_ratios.eps IS 'EPS 주당순이익 (원)';
            COMMENT ON COLUMN financial_ratios.bps IS 'BPS 주당순자산 (원)';
            COMMENT ON COLUMN financial_ratios.lblt_rate IS '부채비율 (%)';
            COMMENT ON COLUMN financial_ratios.rsrv_rate IS '유보율 (%)';
        """))
        logger.info("   ✅ financial_ratios 테이블 생성 완료")

        # 인덱스 생성
        logger.info("\n2. 인덱스 생성 중...")

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_financial_ratios_stock_code
            ON financial_ratios(stock_code);
        """))
        logger.info("   ✅ idx_financial_ratios_stock_code 인덱스 생성")

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_financial_ratios_stock_stac
            ON financial_ratios(stock_code, stac_yymm DESC);
        """))
        logger.info("   ✅ idx_financial_ratios_stock_stac 인덱스 생성 (최신 데이터 조회 최적화)")

        # updated_at 자동 업데이트 트리거 생성
        logger.info("\n3. updated_at 트리거 생성 중...")
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_financial_ratios_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))

        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_financial_ratios_updated_at ON financial_ratios;
        """))

        db.execute(text("""
            CREATE TRIGGER trigger_financial_ratios_updated_at
            BEFORE UPDATE ON financial_ratios
            FOR EACH ROW
            EXECUTE FUNCTION update_financial_ratios_updated_at();
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
            WHERE table_name = 'financial_ratios'
            ORDER BY ordinal_position;
        """))

        for row in result:
            logger.info(f"   {row[0]}: {row[1]} (NULL: {row[2]})")

        # 인덱스 정보 출력
        logger.info("\n📊 인덱스 정보:")
        result = db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'financial_ratios';
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
    logger.info("🔙 Rollback: financial_ratios 테이블 삭제")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        # 트리거 및 함수 삭제
        db.execute(text("DROP TRIGGER IF EXISTS trigger_financial_ratios_updated_at ON financial_ratios;"))
        db.execute(text("DROP FUNCTION IF EXISTS update_financial_ratios_updated_at();"))

        # 테이블 삭제
        db.execute(text("DROP TABLE IF EXISTS financial_ratios CASCADE;"))
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
