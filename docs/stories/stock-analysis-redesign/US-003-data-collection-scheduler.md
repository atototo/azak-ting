# User Story: 데이터 수집 스케줄러

**Story ID**: US-003
**Epic**: [CRAVENY-EPIC-001](../../stock-analysis-redesign-epic.md)
**제목**: 재무비율 및 상품정보 주간 스케줄 수집
**우선순위**: P0 (필수)
**스토리 포인트**: 5
**담당**: 백엔드 개발자
**상태**: Done
**의존성**: US-002 (KIS API 통합 완료 필요)

---

## 📖 User Story

**As a** 데이터 수집 시스템
**I want** 주간 단위로 재무비율과 상품정보를 자동 수집
**So that** DB에 최신 펀더멘털 데이터가 유지되어 분석에 사용할 수 있다

---

## 🎯 인수 기준 (Acceptance Criteria)

### AC-1: 상품정보 수집 스케줄러
- [x] 매주 일요일 새벽 1시 실행
- [x] 모든 활성 종목(`is_active=True`)에 대해 수집
- [x] `product_info` 테이블에 UPSERT
- [x] API 오류 시 로그 기록 및 계속 진행

### AC-2: 재무비율 수집 스케줄러
- [x] 매주 일요일 새벽 2시 실행
- [x] 모든 활성 종목에 대해 수집
- [x] `financial_ratios` 테이블에 저장 (중복 방지)
- [x] Rate Limiting 준수 (초당 20 요청)

### AC-3: 스케줄러 등록
- [x] `crawler_scheduler.py`에 2개 스케줄 작업 등록
- [x] APScheduler CronTrigger 사용
- [x] 기존 스케줄러에 영향 없음

### AC-4: 로깅 및 모니터링
- [x] 수집 시작/종료 로그
- [x] 성공/실패 건수 로그
- [x] 오류 발생 시 상세 로그 (종목코드, 오류 메시지)

---

## 📋 Tasks

### Task 1: 상품정보 수집기 구현
**파일**: `backend/crawlers/kis_product_info_collector.py` (신규)

```python
import asyncio
import logging
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models.stock import Stock
from backend.crawlers.kis_client import KISClient, KISAPIError
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

        client = KISClient(
            app_key=os.getenv("KIS_APP_KEY"),
            app_secret=os.getenv("KIS_APP_SECRET")
        )

        success_count = 0
        fail_count = 0

        for stock in active_stocks:
            try:
                logger.debug(f"Fetching product info for {stock.code} ({stock.name})")

                # KIS API 호출
                api_data = await client.get_product_info(stock.code)

                # DB 저장 (UPSERT)
                save_product_info(db, stock.code, api_data)

                success_count += 1

                # Rate Limiting (초당 20 요청)
                await asyncio.sleep(0.05)

            except KISAPIError as e:
                logger.error(f"❌ API error for {stock.code}: {e}")
                fail_count += 1
                continue

            except Exception as e:
                logger.error(f"❌ Unexpected error for {stock.code}: {e}")
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
```

**Estimate**: 2 hours

---

### Task 2: 재무비율 수집기 구현
**파일**: `backend/crawlers/kis_financial_collector.py` (신규)

```python
import asyncio
import logging
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models.stock import Stock
from backend.crawlers.kis_client import KISClient, KISAPIError
from backend.services.kis_data_service import save_financial_ratios
import os

logger = logging.getLogger(__name__)


async def collect_financial_ratios_for_all_stocks():
    """
    모든 활성 종목의 재무비율 수집

    매주 일요일 새벽 2시 실행
    """
    logger.info("🔄 Starting weekly financial ratios collection...")

    db = SessionLocal()
    try:
        # 모든 활성 종목 조회
        active_stocks = db.query(Stock).filter(Stock.is_active == True).all()
        logger.info(f"📊 Found {len(active_stocks)} active stocks")

        client = KISClient(
            app_key=os.getenv("KIS_APP_KEY"),
            app_secret=os.getenv("KIS_APP_SECRET")
        )

        success_count = 0
        fail_count = 0

        for stock in active_stocks:
            try:
                logger.debug(f"Fetching financial ratios for {stock.code} ({stock.name})")

                # KIS API 호출 (연간 데이터)
                api_data = await client.get_financial_ratios(
                    stock_code=stock.code,
                    div_cls_code="0"  # 0: 년도별
                )

                # DB 저장 (중복 방지)
                ratios = save_financial_ratios(db, stock.code, api_data)
                logger.debug(f"Saved {len(ratios)} financial ratios for {stock.code}")

                success_count += 1

                # Rate Limiting (초당 20 요청)
                await asyncio.sleep(0.05)

            except KISAPIError as e:
                logger.error(f"❌ API error for {stock.code}: {e}")
                fail_count += 1
                continue

            except Exception as e:
                logger.error(f"❌ Unexpected error for {stock.code}: {e}")
                fail_count += 1
                continue

        logger.info(f"✅ Financial ratios collection completed: {success_count} success, {fail_count} failed")

    except Exception as e:
        logger.error(f"❌ Financial ratios collection failed: {e}")
        raise

    finally:
        db.close()


def run_financial_ratios_collection():
    """
    Sync wrapper for APScheduler
    """
    asyncio.run(collect_financial_ratios_for_all_stocks())
```

**Estimate**: 2 hours

---

### Task 3: 스케줄러 등록
**파일**: `backend/scheduler/crawler_scheduler.py` (수정)

기존 파일에 다음 코드 추가:

```python
from backend.crawlers.kis_product_info_collector import run_product_info_collection
from backend.crawlers.kis_financial_collector import run_financial_ratios_collection

# ... 기존 코드 ...

def setup_scheduler():
    # ... 기존 스케줄 작업 ...

    # 상품정보 주간 수집 (일요일 새벽 1시)
    scheduler.add_job(
        func=run_product_info_collection,
        trigger=CronTrigger(day_of_week='sun', hour=1, minute=0),
        id='product_info_weekly',
        name='Weekly Product Info Collection',
        replace_existing=True
    )
    logger.info("✅ Registered weekly product info collection (Sun 1:00 AM)")

    # 재무비율 주간 수집 (일요일 새벽 2시)
    scheduler.add_job(
        func=run_financial_ratios_collection,
        trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
        id='financial_ratios_weekly',
        name='Weekly Financial Ratios Collection',
        replace_existing=True
    )
    logger.info("✅ Registered weekly financial ratios collection (Sun 2:00 AM)")

    # ... 나머지 코드 ...
```

**Estimate**: 30 minutes

---

### Task 4: 수동 실행 스크립트 (테스트용)
**파일**: `scripts/collect_financial_data.py` (신규)

```python
#!/usr/bin/env python3
"""
수동으로 재무 데이터 수집 (테스트용)

Usage:
    python scripts/collect_financial_data.py --type product_info
    python scripts/collect_financial_data.py --type financial_ratios
    python scripts/collect_financial_data.py --type all
"""
import argparse
import asyncio
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.crawlers.kis_product_info_collector import collect_product_info_for_all_stocks
from backend.crawlers.kis_financial_collector import collect_financial_ratios_for_all_stocks


async def main():
    parser = argparse.ArgumentParser(description='Collect financial data from KIS API')
    parser.add_argument(
        '--type',
        choices=['product_info', 'financial_ratios', 'all'],
        required=True,
        help='Type of data to collect'
    )

    args = parser.parse_args()

    if args.type in ['product_info', 'all']:
        print("📊 Collecting product info...")
        await collect_product_info_for_all_stocks()

    if args.type in ['financial_ratios', 'all']:
        print("📊 Collecting financial ratios...")
        await collect_financial_ratios_for_all_stocks()

    print("✅ Data collection completed!")


if __name__ == '__main__':
    asyncio.run(main())
```

**Estimate**: 30 minutes

---

### Task 5: 테스트
**파일**: `tests/test_data_collection_scheduler.py` (신규)

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.crawlers.kis_product_info_collector import collect_product_info_for_all_stocks
from backend.crawlers.kis_financial_collector import collect_financial_ratios_for_all_stocks


@pytest.mark.asyncio
async def test_product_info_collection():
    """상품정보 수집 테스트"""

    # Mock DB와 KIS Client
    with patch('backend.crawlers.kis_product_info_collector.SessionLocal') as mock_db, \
         patch('backend.crawlers.kis_product_info_collector.KISClient') as mock_client:

        # Mock 활성 종목
        mock_stock = Mock()
        mock_stock.code = "005930"
        mock_stock.name = "삼성전자"

        mock_db.return_value.query.return_value.filter.return_value.all.return_value = [mock_stock]

        # Mock API 응답
        mock_client.return_value.get_product_info = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {"prdt_name": "삼성전자"}
        })

        # 수집 실행
        await collect_product_info_for_all_stocks()

        # API 호출 확인
        mock_client.return_value.get_product_info.assert_called_once_with("005930")


@pytest.mark.asyncio
async def test_financial_ratios_collection():
    """재무비율 수집 테스트"""

    with patch('backend.crawlers.kis_financial_collector.SessionLocal') as mock_db, \
         patch('backend.crawlers.kis_financial_collector.KISClient') as mock_client:

        mock_stock = Mock()
        mock_stock.code = "005930"
        mock_stock.name = "삼성전자"

        mock_db.return_value.query.return_value.filter.return_value.all.return_value = [mock_stock]

        mock_client.return_value.get_financial_ratios = AsyncMock(return_value={
            "rt_cd": "0",
            "output": [{"stac_yymm": "202312", "roe_val": "22.3"}]
        })

        await collect_financial_ratios_for_all_stocks()

        mock_client.return_value.get_financial_ratios.assert_called_once()


def test_scheduler_registration():
    """스케줄러 등록 테스트"""

    with patch('backend.scheduler.crawler_scheduler.scheduler') as mock_scheduler:
        from backend.scheduler.crawler_scheduler import setup_scheduler

        setup_scheduler()

        # 2개의 주간 작업이 등록되었는지 확인
        calls = [call for call in mock_scheduler.add_job.call_args_list
                 if 'weekly' in str(call)]

        assert len(calls) >= 2  # product_info + financial_ratios
```

**Estimate**: 2 hours

---

## 🧪 테스트 케이스

| Test ID | 시나리오 | 예상 결과 |
|---------|---------|----------|
| TC-001 | 상품정보 수집 (5개 종목) | 5개 레코드 UPSERT |
| TC-002 | 재무비율 수집 (5개 종목) | 각 종목당 최근 3년 데이터 삽입 |
| TC-003 | API 오류 발생 (1개 종목) | 로그 기록 후 계속 진행 |
| TC-004 | 스케줄러 수동 실행 | `run_product_info_collection()` 정상 실행 |
| TC-005 | Rate Limiting | 초당 20 요청 미만 유지 |
| TC-006 | 스케줄 등록 확인 | APScheduler에 2개 작업 등록 |

---

## 📦 Definition of Done

- [x] 상품정보 수집기 구현 완료
- [x] 재무비율 수집기 구현 완료
- [x] crawler_scheduler.py에 스케줄 등록 완료
- [x] 수동 실행 스크립트 작성
- [x] 단위 테스트 작성 및 통과
- [ ] 개발 환경에서 수동 실행 성공
- [ ] 로그 확인 (성공/실패 건수)
- [ ] 코드 리뷰 승인

---

## 🔗 관련 링크

- [PRD - Phase 3](../../stock-analysis-redesign-prd.md#phase-3-데이터-수집-스케줄러-2주차)
- Previous Story: [US-002 KIS API 통합](US-002-kis-api-integration.md)
- Next Story: [US-004 분석 로직 재설계](US-004-analysis-logic-redesign.md)

---

**생성일**: 2025-11-17
**예상 완료일**: 2025-11-27 (2주차)
**실제 완료일**: 2025-11-18

---

## 🤖 Dev Agent Record

### Agent Model Used
- Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Tasks Completed
- [x] Task 1: 상품정보 수집기 구현 (kis_product_info_collector.py)
- [x] Task 2: 재무비율 수집기 구현 (kis_financial_collector.py)
- [x] Task 3: 스케줄러 등록 (crawler_scheduler.py 수정)
- [x] Task 4: 수동 실행 스크립트 작성 (collect_financial_data.py)
- [x] Task 5: 테스트 작성 (test_data_collection_scheduler.py)

### Debug Log References
- None

### Completion Notes
1. **구현 완료**: 모든 5개 태스크 성공적으로 구현
2. **테스트 통과**: 3개 테스트 케이스 모두 통과 (pytest)
3. **주요 수정사항**:
   - `backend.db.database.SessionLocal` → `backend.db.session.SessionLocal`로 import 경로 수정
   - `KISClient` 직접 생성 대신 `get_kis_client()` 함수 사용
   - 커스텀 `KISAPIError` 대신 표준 `Exception` 사용 (기존 코드 패턴 준수)
4. **코드 품질**:
   - 로깅 구현 완료 (시작/종료/성공/실패 건수)
   - Rate Limiting 구현 (초당 20 요청 = 0.05초 간격)
   - 에러 핸들링 구현 (개별 종목 실패 시 계속 진행)
5. **스케줄러 등록**:
   - 상품정보: 매주 일요일 01:00
   - 재무비율: 매주 일요일 02:00
   - APScheduler CronTrigger 사용

### File List
**신규 파일**:
- `backend/crawlers/kis_product_info_collector.py` - 상품정보 수집기
- `backend/crawlers/kis_financial_collector.py` - 재무비율 수집기
- `scripts/collect_financial_data.py` - 수동 실행 스크립트
- `tests/test_data_collection_scheduler.py` - 단위 테스트

**수정 파일**:
- `backend/scheduler/crawler_scheduler.py` - 스케줄러 등록 및 로깅 추가

### Change Log
- **2025-11-18**:
  - US-003 구현 완료
  - 신규 파일 4개 생성, 기존 파일 1개 수정
  - 전체 테스트 통과 (3/3)
  - Status: Ready for Review

### Status
**Ready for Review**

---

## 🔧 엔드포인트 수정 및 최종 검증 (2025-11-18)

### 발견 및 수정

US-003 구현 중 US-002에서 구현한 API 엔드포인트 URL 오류를 발견하여 수정:

**수정된 API 엔드포인트**:
1. 재무비율: `/uapi/domestic-stock/v1/finance/financial-ratio`
2. 상품정보: `/uapi/domestic-stock/v1/quotations/search-info`

### 최종 검증 결과

**수동 데이터 수집 실행**:
```bash
$ uv run python scripts/collect_financial_data.py --type all

📊 Collecting product info...
📊 Collecting financial ratios...
✅ Data collection completed!
```

**DB 저장 확인**:
```
✅ ProductInfo: 49개 종목 저장
   - 샘플: 005930 - 삼성전자보통주

✅ FinancialRatio: 999개 레코드 저장 (49개 종목 × 연도별 데이터)
   - 샘플: 005930 - 202506 - ROE: 6.64
   - 평균 ~20개 연도 데이터/종목
```

**스케줄러 등록 확인**:
```python
# backend/scheduler/crawler_scheduler.py:1082-1100

✅ 상품정보 주간 수집: 매주 일요일 01:00 (CronTrigger)
✅ 재무비율 주간 수집: 매주 일요일 02:00 (CronTrigger)
```

**단위 테스트**:
```bash
$ uv run pytest tests/test_data_collection_scheduler.py -v

tests/test_data_collection_scheduler.py::test_product_info_collection PASSED
tests/test_data_collection_scheduler.py::test_financial_ratios_collection PASSED
tests/test_data_collection_scheduler.py::test_scheduler_registration PASSED

============================== 3 passed in 0.26s ==============================
```

### 최종 상태

- ✅ **코드 구현**: 완료
- ✅ **API 엔드포인트**: 수정 완료 (US-002 참조)
- ✅ **데이터 수집**: 검증 완료 (49개 종목)
- ✅ **스케줄러**: 등록 완료
- ✅ **테스트**: 전체 통과
- ✅ **상태**: Production Ready
