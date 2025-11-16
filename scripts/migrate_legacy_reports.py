"""
레거시 리포트를 모델별 리포트로 마이그레이션하는 스크립트

실행 전 반드시:
1. DB 백업 완료 확인
2. 스케줄러 중지 확인
3. 프로덕션이 아닌 환경에서 먼저 테스트

실행 방법:
    python scripts/migrate_legacy_reports.py [--dry-run] [--verbose]
"""
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.config import settings
from backend.db.models.stock_analysis import StockAnalysisSummary
from backend.db.models.ab_test_config import ABTestConfig

import argparse
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportMigrator:
    """레거시 리포트 마이그레이션 클래스"""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose

        # DB 연결
        database_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.stats = {
            'total_legacy': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0,
            'created_reports': {}  # model_id별 생성 개수
        }

    def get_ab_test_config(self) -> Optional[ABTestConfig]:
        """현재 활성화된 A/B 테스트 설정 조회"""
        try:
            ab_config = (
                self.session.query(ABTestConfig)
                .filter(ABTestConfig.is_active == True)
                .first()
            )

            if ab_config:
                logger.info(f"활성 A/B 테스트 설정 발견: Model A ID={ab_config.model_a_id}, Model B ID={ab_config.model_b_id}")
            else:
                logger.warning("활성화된 A/B 테스트 설정이 없습니다.")

            return ab_config
        except Exception as e:
            logger.error(f"A/B 테스트 설정 조회 실패: {e}")
            return None

    def get_legacy_reports(self):
        """마이그레이션 대상 레거시 리포트 조회"""
        try:
            legacy_reports = (
                self.session.query(StockAnalysisSummary)
                .filter(StockAnalysisSummary.model_id == None)
                .order_by(StockAnalysisSummary.last_updated.desc())
                .all()
            )

            self.stats['total_legacy'] = len(legacy_reports)
            logger.info(f"레거시 리포트 {len(legacy_reports)}개 발견")

            return legacy_reports
        except Exception as e:
            logger.error(f"레거시 리포트 조회 실패: {e}")
            raise

    def extract_model_report(
        self,
        custom_data: Dict[str, Any],
        model_key: str
    ) -> Optional[Dict[str, Any]]:
        """custom_data에서 특정 모델의 리포트 추출"""
        try:
            if not custom_data:
                return None

            # A/B 테스트 활성화된 경우
            if custom_data.get('ab_test_enabled'):
                model_data = custom_data.get(model_key)
                if model_data:
                    return model_data

            return None
        except Exception as e:
            logger.error(f"모델 리포트 추출 실패 ({model_key}): {e}")
            return None

    def create_model_report(
        self,
        legacy_report: StockAnalysisSummary,
        model_id: int,
        model_data: Dict[str, Any]
    ) -> StockAnalysisSummary:
        """모델별 새 리포트 생성"""
        new_report = StockAnalysisSummary(
            stock_code=legacy_report.stock_code,
            model_id=model_id,

            # LLM 생성 콘텐츠
            overall_summary=model_data.get('overall_summary'),
            short_term_scenario=model_data.get('short_term_scenario'),
            medium_term_scenario=model_data.get('medium_term_scenario'),
            long_term_scenario=model_data.get('long_term_scenario'),
            risk_factors=model_data.get('risk_factors'),
            opportunity_factors=model_data.get('opportunity_factors'),
            recommendation=model_data.get('recommendation'),

            # 통계 데이터 (legacy에서 복사)
            total_predictions=legacy_report.total_predictions,
            up_count=legacy_report.up_count,
            down_count=legacy_report.down_count,
            hold_count=legacy_report.hold_count,
            avg_confidence=legacy_report.avg_confidence,

            # A/B 테스트용 전체 데이터 (새 형식에서는 사용 안 함)
            custom_data=None,

            # 투자 전략 데이터
            short_term_target_price=model_data.get('short_term_target_price'),
            short_term_support_price=model_data.get('short_term_support_price'),
            medium_term_target_price=model_data.get('medium_term_target_price'),
            medium_term_support_price=model_data.get('medium_term_support_price'),
            long_term_target_price=model_data.get('long_term_target_price'),
            base_price=model_data.get('base_price'),

            # 메타 정보 (legacy 타임스탬프 유지)
            last_updated=legacy_report.last_updated,
            based_on_prediction_count=legacy_report.based_on_prediction_count
        )

        return new_report

    def migrate_report(
        self,
        legacy_report: StockAnalysisSummary,
        ab_config: ABTestConfig
    ) -> int:
        """단일 레거시 리포트를 마이그레이션"""
        created_count = 0

        try:
            custom_data = legacy_report.custom_data

            # custom_data가 없거나 ab_test_enabled가 아닌 경우
            if not custom_data or not custom_data.get('ab_test_enabled'):
                logger.warning(
                    f"종목 {legacy_report.stock_code}: "
                    f"A/B 테스트 데이터 없음 (스킵)"
                )
                self.stats['skipped'] += 1
                return 0

            # Model A 리포트 생성
            model_a_data = self.extract_model_report(custom_data, 'model_a')
            if model_a_data and ab_config:
                if not self.dry_run:
                    new_report_a = self.create_model_report(
                        legacy_report,
                        ab_config.model_a_id,
                        model_a_data
                    )
                    self.session.add(new_report_a)
                    created_count += 1
                    self.stats['created_reports'][ab_config.model_a_id] = \
                        self.stats['created_reports'].get(ab_config.model_a_id, 0) + 1

                if self.verbose:
                    logger.info(
                        f"  → Model A (ID={ab_config.model_a_id}) 리포트 생성"
                    )

            # Model B 리포트 생성
            model_b_data = self.extract_model_report(custom_data, 'model_b')
            if model_b_data and ab_config:
                if not self.dry_run:
                    new_report_b = self.create_model_report(
                        legacy_report,
                        ab_config.model_b_id,
                        model_b_data
                    )
                    self.session.add(new_report_b)
                    created_count += 1
                    self.stats['created_reports'][ab_config.model_b_id] = \
                        self.stats['created_reports'].get(ab_config.model_b_id, 0) + 1

                if self.verbose:
                    logger.info(
                        f"  → Model B (ID={ab_config.model_b_id}) 리포트 생성"
                    )

            if created_count > 0:
                logger.info(
                    f"종목 {legacy_report.stock_code}: {created_count}개 리포트 생성 "
                    f"(업데이트: {legacy_report.last_updated.strftime('%Y-%m-%d %H:%M')})"
                )
                self.stats['migrated'] += 1

            return created_count

        except Exception as e:
            logger.error(f"종목 {legacy_report.stock_code} 마이그레이션 실패: {e}", exc_info=True)
            self.stats['errors'] += 1
            return 0

    def run(self):
        """마이그레이션 실행"""
        logger.info("=" * 80)
        logger.info("레거시 리포트 마이그레이션 시작")
        logger.info(f"모드: {'DRY RUN (실제 변경 없음)' if self.dry_run else '실제 마이그레이션'}")
        logger.info("=" * 80)

        try:
            # 1. A/B 테스트 설정 조회
            ab_config = self.get_ab_test_config()
            if not ab_config:
                logger.error("A/B 테스트 설정이 없어 마이그레이션을 중단합니다.")
                return False

            # 2. 레거시 리포트 조회
            legacy_reports = self.get_legacy_reports()
            if not legacy_reports:
                logger.info("마이그레이션할 레거시 리포트가 없습니다.")
                return True

            # 3. 각 리포트 마이그레이션
            logger.info(f"\n{len(legacy_reports)}개 리포트 마이그레이션 시작...\n")

            for idx, legacy_report in enumerate(legacy_reports, 1):
                if self.verbose or idx % 10 == 0:
                    logger.info(f"진행 중: {idx}/{len(legacy_reports)}")

                self.migrate_report(legacy_report, ab_config)

            # 4. 커밋 (dry_run이 아닌 경우만)
            if not self.dry_run:
                logger.info("\nDB 커밋 중...")
                self.session.commit()
                logger.info("✅ 커밋 완료")
            else:
                logger.info("\n⚠️ DRY RUN 모드: 변경사항 롤백")
                self.session.rollback()

            # 5. 결과 출력
            self.print_summary()

            return True

        except Exception as e:
            logger.error(f"마이그레이션 중 오류 발생: {e}", exc_info=True)
            self.session.rollback()
            return False
        finally:
            self.session.close()

    def print_summary(self):
        """마이그레이션 결과 요약 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("마이그레이션 완료")
        logger.info("=" * 80)
        logger.info(f"총 레거시 리포트:    {self.stats['total_legacy']:>5}개")
        logger.info(f"마이그레이션 완료:   {self.stats['migrated']:>5}개")
        logger.info(f"스킵:                {self.stats['skipped']:>5}개")
        logger.info(f"에러:                {self.stats['errors']:>5}개")
        logger.info("-" * 80)
        logger.info("모델별 생성된 리포트:")
        for model_id, count in sorted(self.stats['created_reports'].items()):
            logger.info(f"  Model ID {model_id}:    {count:>5}개")
        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="레거시 리포트를 모델별 리포트로 마이그레이션"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 변경 없이 테스트만 수행'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='상세 로그 출력'
    )

    args = parser.parse_args()

    # 경고 메시지
    if not args.dry_run:
        logger.warning("\n" + "!" * 80)
        logger.warning("⚠️  실제 마이그레이션을 수행합니다!")
        logger.warning("⚠️  반드시 DB 백업을 완료했는지 확인하세요!")
        logger.warning("⚠️  스케줄러가 중지되었는지 확인하세요!")
        logger.warning("!" * 80)

        response = input("\n계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("마이그레이션이 취소되었습니다.")
            return

    # 마이그레이션 실행
    migrator = ReportMigrator(dry_run=args.dry_run, verbose=args.verbose)
    success = migrator.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
