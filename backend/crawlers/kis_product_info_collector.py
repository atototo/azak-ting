import asyncio
import logging
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models.stock import Stock
from backend.crawlers.kis_client import get_kis_client
from backend.services.kis_data_service import save_product_info
import os

logger = logging.getLogger(__name__)


async def collect_product_info_for_all_stocks():
    """
    모든 활성 종목의 상품정보 수집

    매주 일요일 새벽 1시 실행
    """
    logger.info("🔄 Starting weekly product info collection...")

    db = SessionLocal()
    try:
        # 모든 활성 종목 조회
        active_stocks = db.query(Stock).filter(Stock.is_active == True).all()
        logger.info(f"📊 Found {len(active_stocks)} active stocks")

        client = await get_kis_client()

        success_count = 0
        fail_count = 0

        for stock in active_stocks:
            try:
                logger.debug(f"Fetching product info for {stock.code} ({stock.name})")

                # KIS API 호출
                api_data = await client.get_product_info(stock.code, priority="low")

                # DB 저장 (UPSERT)
                save_product_info(db, stock.code, api_data)

                success_count += 1

                # Rate Limiting (초당 20 요청)
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"❌ Error for {stock.code}: {e}")
                fail_count += 1
                continue

        logger.info(f"✅ Product info collection completed: {success_count} success, {fail_count} failed")

    except Exception as e:
        logger.error(f"❌ Product info collection failed: {e}")
        raise

    finally:
        db.close()


def run_product_info_collection():
    """
    Sync wrapper for APScheduler
    """
    asyncio.run(collect_product_info_for_all_stocks())
