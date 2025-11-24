"""
Verification script for Issue #13: predicted_at field and auto-notification logic.

This script:
1. Creates a test news article with predicted_at=None.
2. Runs process_new_news_notifications.
3. Verifies that predicted_at is updated.
"""
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.db.session import SessionLocal
from backend.db.models.news import NewsArticle
from backend.notifications.auto_notify import process_new_news_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    db = SessionLocal()
    try:
        logger.info("🧪 Starting verification for Issue #13...")

        # 1. Create test news
        test_news = NewsArticle(
            title="[TEST] Issue #13 Verification News",
            content="This is a test news article to verify predicted_at field update logic.",
            source="test",
            stock_code="005930",  # Samsung Electronics
            published_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            predicted_at=None,  # Explicitly None
            notified_at=None
        )
        db.add(test_news)
        db.commit()
        db.refresh(test_news)
        logger.info(f"✅ Created test news (ID: {test_news.id})")

        # 2. Run process
        logger.info("🔄 Running process_new_news_notifications...")
        stats = await process_new_news_notifications(db)
        logger.info(f"📊 Stats: {stats}")

        # 3. Verify
        db.refresh(test_news)
        logger.info(f"🧐 Checking news ID {test_news.id}...")
        logger.info(f"   - predicted_at: {test_news.predicted_at}")
        logger.info(f"   - notified_at: {test_news.notified_at}")

        if test_news.predicted_at is not None:
            logger.info("🎉 Verification SUCCESS: predicted_at was updated!")
        else:
            logger.error("❌ Verification FAILED: predicted_at is still None")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Verification failed with error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'test_news' in locals():
            db.delete(test_news)
            db.commit()
            logger.info("🧹 Cleaned up test data")
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify())
