"""
Migration script: Add 'dart' to ContentType enum and update existing DART news.

This script:
1. Adds 'dart' value to content_type ENUM in PostgreSQL
2. Updates existing DART news articles to have content_type='dart'
"""
import sys
from pathlib import Path
from sqlalchemy import text
import logging
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
load_dotenv(project_root / ".env")

from backend.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db = SessionLocal()
    try:
        logger.info("Starting DART content_type migration...")

        # 1. Add 'dart' to ENUM type
        try:
            db.execute(text("ALTER TYPE contenttype ADD VALUE 'dart'"))
            db.commit()
            logger.info("✅ Added 'dart' to contenttype ENUM")
        except Exception as e:
            if "already exists" in str(e) or "duplicate key value" in str(e):
                logger.info("ℹ️ 'dart' already exists in contenttype ENUM")
                db.rollback()
            else:
                logger.error(f"❌ Failed to add 'dart' to ENUM: {e}")
                raise e

        # 2. Update existing DART news to content_type='dart'
        try:
            result = db.execute(text("""
                UPDATE news_articles
                SET content_type = 'dart'
                WHERE source LIKE '%DART%' AND content_type != 'dart'
            """))
            db.commit()
            logger.info(f"✅ Updated {result.rowcount} DART news articles to content_type='dart'")
        except Exception as e:
            logger.error(f"❌ Failed to update content_type: {e}")
            db.rollback()
            raise e

        # 3. Verify
        result = db.execute(text("""
            SELECT COUNT(*)
            FROM news_articles
            WHERE source LIKE '%DART%' AND content_type = 'dart'
        """))
        dart_count = result.scalar()

        result = db.execute(text("""
            SELECT COUNT(*)
            FROM news_articles
            WHERE source LIKE '%DART%' AND content_type != 'dart'
        """))
        non_dart_count = result.scalar()

        logger.info(f"📊 Verification:")
        logger.info(f"   - DART news with content_type='dart': {dart_count}건")
        logger.info(f"   - DART news with other content_type: {non_dart_count}건")

        if non_dart_count == 0:
            logger.info("🎉 Migration completed successfully!")
        else:
            logger.warning(f"⚠️  There are still {non_dart_count} DART news with incorrect content_type")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
