"""
사용자 리포트 업데이트 권한 및 횟수 제한 필드 추가

실행 방법:
    python -m backend.db.migrations.add_report_update_quota
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.db.session import SessionLocal, engine


def migrate():
    """사용자 테이블에 리포트 업데이트 관련 필드 추가"""
    print("🔄 리포트 업데이트 권한 및 횟수 제한 필드 추가 시작...")

    with engine.connect() as conn:
        try:
            # 1. report_update_enabled 필드 추가
            print("  📝 report_update_enabled 필드 추가 중...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS report_update_enabled BOOLEAN DEFAULT FALSE NOT NULL
            """))
            conn.commit()
            print("    ✅ report_update_enabled 필드 추가 완료")

            # 2. report_update_quota 필드 추가
            print("  📝 report_update_quota 필드 추가 중...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS report_update_quota INTEGER DEFAULT 0 NOT NULL
            """))
            conn.commit()
            print("    ✅ report_update_quota 필드 추가 완료")

            # 3. report_update_used 필드 추가
            print("  📝 report_update_used 필드 추가 중...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS report_update_used INTEGER DEFAULT 0 NOT NULL
            """))
            conn.commit()
            print("    ✅ report_update_used 필드 추가 완료")

            # 4. 관리자 계정에 무제한 권한 부여
            print("  📝 관리자 계정 권한 설정 중...")
            conn.execute(text("""
                UPDATE users
                SET report_update_enabled = TRUE,
                    report_update_quota = 999999
                WHERE role = 'admin'
            """))
            conn.commit()
            print("    ✅ 관리자 계정 권한 설정 완료")

            print("✅ 마이그레이션 완료!")

        except Exception as e:
            conn.rollback()
            print(f"❌ 마이그레이션 실패: {e}")
            raise


if __name__ == "__main__":
    migrate()
