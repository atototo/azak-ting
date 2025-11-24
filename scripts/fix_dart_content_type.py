"""
Fix content_type for DART news articles.

Updates all news articles with source containing 'DART' to have content_type='dart'.
"""
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file (before importing backend modules)
load_dotenv(project_root / ".env")

from backend.db.session import SessionLocal
from backend.db.models.news import NewsArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_dart_content_type():
    db = SessionLocal()
    try:
        logger.info("🔧 DART 뉴스 content_type 수정 시작...")

        # Find all news with 'DART' in source but content_type != 'dart'
        dart_news = (
            db.query(NewsArticle)
            .filter(
                NewsArticle.source.like('%DART%'),
                NewsArticle.content_type != 'dart'
            )
            .all()
        )

        logger.info(f"📊 수정 대상: {len(dart_news)}건")

        if not dart_news:
            logger.info("✅ 수정할 데이터가 없습니다")
            return

        # Update content_type to 'dart'
        count = 0
        for news in dart_news:
            logger.debug(f"수정 중: ID={news.id}, source={news.source}")
            news.content_type = 'dart'
            count += 1

        db.commit()
        logger.info(f"✅ {count}건의 DART 뉴스 content_type을 'dart'로 수정 완료")

        # Verify
        remaining = (
            db.query(NewsArticle)
            .filter(
                NewsArticle.source.like('%DART%'),
                NewsArticle.content_type != 'dart'
            )
            .count()
        )

        if remaining == 0:
            logger.info("🎉 검증 완료: 모든 DART 뉴스가 올바르게 수정되었습니다")
        else:
            logger.warning(f"⚠️  아직 수정되지 않은 DART 뉴스가 {remaining}건 남아있습니다")

    except Exception as e:
        logger.error(f"❌ 수정 실패: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    fix_dart_content_type()
