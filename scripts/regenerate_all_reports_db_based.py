"""
전체 활성 종목에 대한 DB 기반 리포트 재생성

US-004: 통합 리포트 생성 시스템 적용
- 모든 활성 모델에 대해 리포트 생성
- DB 데이터만 사용 (예측 불필요)
- 뉴스 독립적
"""
import asyncio
import logging
from backend.db.session import SessionLocal
from backend.db.models.stock import Stock
from backend.db.models.stock_analysis import StockAnalysisSummary
from backend.services.stock_analysis_service import generate_stock_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """전체 활성 종목 리포트 재생성"""
    db = SessionLocal()

    try:
        # 활성 종목 조회
        active_stocks = db.query(Stock).filter(Stock.is_active == True).all()

        logger.info(f"=" * 80)
        logger.info(f"🚀 전체 활성 종목 리포트 재생성 시작")
        logger.info(f"대상 종목: {len(active_stocks)}개")
        logger.info(f"=" * 80)

        success_stocks = []
        failed_stocks = []

        for idx, stock in enumerate(active_stocks, 1):
            logger.info(f"\n[{idx}/{len(active_stocks)}] {stock.name} ({stock.code})")

            try:
                # 기존 리포트 삭제
                deleted_count = db.query(StockAnalysisSummary).filter(
                    StockAnalysisSummary.stock_code == stock.code
                ).delete()
                db.commit()
                logger.info(f"  🗑️  기존 리포트 {deleted_count}개 삭제")

                # 새 리포트 생성 (전체 모델)
                reports = await generate_stock_report(stock.code, db)

                if reports:
                    success_stocks.append(stock.name)
                    logger.info(f"  ✅ {len(reports)}개 모델 리포트 생성 완료")
                    for r in reports:
                        logger.info(f"    - Model {r.model_id}: {r.confidence_level} ({r.data_completeness_score:.2f})")
                else:
                    failed_stocks.append(f"{stock.name} (데이터 부족)")
                    logger.warning(f"  ⚠️  리포트 생성 실패 (데이터 부족)")

                # Rate limit
                await asyncio.sleep(1)

            except Exception as e:
                failed_stocks.append(f"{stock.name} (오류: {str(e)[:50]})")
                logger.error(f"  ❌ 오류 발생: {e}")
                db.rollback()
                continue

        # 최종 통계
        logger.info(f"\n" + "=" * 80)
        logger.info(f"✅ 리포트 재생성 완료")
        logger.info(f"성공: {len(success_stocks)}개")
        logger.info(f"실패: {len(failed_stocks)}개")

        if failed_stocks:
            logger.warning(f"\n실패 종목:")
            for stock_name in failed_stocks:
                logger.warning(f"  - {stock_name}")

        logger.info(f"=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
