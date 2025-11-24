"""
Migration script for Issue #13: Add predicted_at field to news_articles table.

This script:
1. Adds 'predicted_at' column to 'news_articles' table if it doesn't exist.
2. Creates an index on 'predicted_at'.
3. Backfills 'predicted_at' with 'notified_at' for existing records where 'notified_at' is not null.
"""
import sys
from pathlib import Path
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.db.session import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db = SessionLocal()
    try:
        logger.info("Starting migration for Issue #13...")

        # 1. Add column
        try:
            db.execute(text("ALTER TABLE news_articles ADD COLUMN predicted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL"))
            logger.info("✅ Added column 'predicted_at'")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Column 'predicted_at' already exists")
                db.rollback()
            else:
                logger.error(f"❌ Failed to add column: {e}")
                raise e

        # 2. Add index
        try:
            db.execute(text("CREATE INDEX idx_news_articles_predicted_at ON news_articles(predicted_at)"))
            logger.info("✅ Created index 'idx_news_articles_predicted_at'")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("ℹ️ Index 'idx_news_articles_predicted_at' already exists")
                db.rollback()
            else:
                logger.error(f"❌ Failed to create index: {e}")
                # Index creation failure shouldn't stop migration
                pass

        # 3. Backfill data using predictions table
        try:
            # Update predicted_at from existing predictions
            # Use the earliest prediction time if multiple predictions exist for the same news
            result = db.execute(text("""
                UPDATE news_articles n
                SET predicted_at = p.min_created_at
                FROM (
                    SELECT news_id, MIN(created_at) as min_created_at
                    FROM predictions
                    GROUP BY news_id
                ) p
                WHERE n.id = p.news_id AND n.predicted_at IS NULL
            """))
            db.commit()
            logger.info(f"✅ Backfilled {result.rowcount} records from predictions table")

            # Fallback: Use notified_at for records that have notification but no prediction record (legacy data)
            result_fallback = db.execute(text("""
                UPDATE news_articles 
                SET predicted_at = notified_at 
                WHERE notified_at IS NOT NULL AND predicted_at IS NULL
            """))
            db.commit()
            logger.info(f"✅ Backfilled {result_fallback.rowcount} records from notified_at (fallback)")

        except Exception as e:
            logger.error(f"❌ Failed to backfill data: {e}")
            db.rollback()
            raise e

        logger.info("🎉 Migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
