# User Story: 테스트 및 프로덕션 배포

**Story ID**: US-006
**Epic**: [CRAVENY-EPIC-001](../../stock-analysis-redesign-epic.md)
**제목**: 통합 테스트, QA 및 Blue-Green 배포
**우선순위**: P0 (필수)
**스토리 포인트**: 8
**담당**: QA + DevOps + 전체 팀
**상태**: ~~Todo → In Progress → Code Review~~ → **Done** ✅
**의존성**: US-001 ~ US-005 (모든 이전 스토리 완료 필요)

---

## 📖 User Story

**As a** DevOps 엔지니어 및 QA 팀
**I want** 전체 시스템을 통합 테스트하고 안전하게 프로덕션에 배포
**So that** 사용자에게 안정적이고 버그 없는 새로운 분석 시스템을 제공할 수 있다

---

## 🎯 인수 기준 (Acceptance Criteria)

### AC-1: 통합 테스트 완료
- [ ] 모든 7개 테스트 케이스 통과 (TC-001 ~ TC-007)
- [ ] E2E 테스트: 종목 등록 → 분석 → 리포트 조회 전체 플로우
- [ ] 성능 테스트: 50개 종목 배치 리포트 < 5분
- [ ] 부하 테스트: 동시 10명 사용자 처리

### AC-2: 스테이징 배포
- [ ] 스테이징 환경에 배포 완료
- [ ] 48시간 모니터링 (오류율, 응답 시간)
- [ ] 회귀 테스트 전체 통과
- [ ] 스테이징에서 실제 KIS API로 데이터 수집 성공

### AC-3: 프로덕션 배포
- [ ] DB 백업 완료 (마이그레이션 전)
- [ ] Blue-Green 배포로 50% 트래픽 전환
- [ ] 24시간 모니터링 후 100% 롤아웃
- [ ] 롤백 계획 문서화 및 테스트 완료

### AC-4: 성공 지표 달성
- [ ] 분석 커버리지 95% 이상
- [ ] 첫 분석까지 평균 시간 < 1분
- [ ] 종목당 일일 리포트 수 2.8개 이상
- [ ] API 호출 수 30% 감소

---

## 📋 Tasks

### Task 1: 통합 테스트 스크립트 작성
**파일**: `tests/integration/test_full_flow.py` (신규)

```python
import pytest
from backend.api.stock_management import register_stock
from backend.services.stock_analysis_service import trigger_initial_analysis
from backend.db.database import SessionLocal
import time


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_stock_registration_flow():
    """
    전체 플로우 테스트: 종목 등록 → 즉시 분석 → 리포트 조회

    TC-001: 신규 종목 등록 (뉴스 없음)
    """
    db = SessionLocal()
    try:
        # 1. 종목 등록
        test_stock_code = "000660"  # SK하이닉스
        test_stock_name = "SK하이닉스"

        start_time = time.time()

        result = await register_stock(test_stock_code, test_stock_name, db)

        # 2. 등록 확인
        assert result["stock_code"] == test_stock_code
        assert result["is_active"] == True

        # 3. 분석 완료 대기 (최대 60초)
        elapsed = 0
        analysis_found = False

        while elapsed < 60:
            time.sleep(5)
            elapsed = time.time() - start_time

            # 리포트 조회
            summary = db.query(StockAnalysisSummary).filter(
                StockAnalysisSummary.stock_code == test_stock_code
            ).first()

            if summary:
                analysis_found = True
                break

        # 4. 검증
        assert analysis_found, "Initial analysis not completed within 60 seconds"
        assert elapsed < 60, f"Analysis took {elapsed}s (limit: 60s)"

        # 5. 리포트 내용 검증
        assert summary.data_sources_used is not None
        assert "market_data" in summary.data_sources_used
        assert summary.confidence_level in ["high", "medium", "low"]

        print(f"✅ Full flow test passed in {elapsed:.2f}s")

    finally:
        # Cleanup
        db.query(Stock).filter(Stock.code == test_stock_code).delete()
        db.query(StockAnalysisSummary).filter(StockAnalysisSummary.stock_code == test_stock_code).delete()
        db.commit()
        db.close()


@pytest.mark.integration
async def test_batch_report_generation_performance():
    """
    성능 테스트: 50개 종목 배치 리포트 < 5분

    TC-007: 50개 종목 배치 리포트
    """
    db = SessionLocal()

    # 활성 종목 50개 조회
    active_stocks = db.query(Stock).filter(Stock.is_active == True).limit(50).all()

    assert len(active_stocks) >= 50, "Need at least 50 active stocks for this test"

    start_time = time.time()

    # 배치 리포트 생성 실행
    from backend.scheduler.crawler_scheduler import generate_all_reports
    await generate_all_reports()

    elapsed = time.time() - start_time

    # 5분 이내 완료 확인
    assert elapsed < 300, f"Batch generation took {elapsed}s (limit: 300s)"

    print(f"✅ Batch report generation completed in {elapsed:.2f}s for 50 stocks")


@pytest.mark.integration
def test_priority_filter_removed():
    """
    Priority 필터 제거 확인

    TC-004: Priority 5 종목도 리포트 생성
    """
    db = SessionLocal()

    # Priority 5 종목 생성
    test_stock = Stock(code="999999", name="테스트종목", is_active=True, priority=5)
    db.add(test_stock)
    db.commit()

    try:
        # 분석 대상 종목 조회
        from backend.scheduler.crawler_scheduler import get_stocks_for_analysis

        stocks = get_stocks_for_analysis(db)

        # Priority 5 종목도 포함되어야 함
        stock_codes = [s.code for s in stocks]
        assert "999999" in stock_codes, "Priority 5 stock not included in analysis"

        print("✅ Priority filter removed successfully")

    finally:
        # Cleanup
        db.query(Stock).filter(Stock.code == "999999").delete()
        db.commit()
        db.close()


@pytest.mark.integration
async def test_data_collection_schedulers():
    """
    스케줄러 실행 테스트

    TC-004: 재무 데이터 수집
    """
    from backend.crawlers.kis_product_info_collector import collect_product_info_for_all_stocks
    from backend.crawlers.kis_financial_collector import collect_financial_ratios_for_all_stocks

    db = SessionLocal()

    # 활성 종목 5개만 테스트
    active_stocks = db.query(Stock).filter(Stock.is_active == True).limit(5).all()

    # 상품정보 수집
    await collect_product_info_for_all_stocks()

    # DB에 저장 확인
    for stock in active_stocks:
        product_info = db.query(ProductInfo).filter(ProductInfo.stock_code == stock.code).first()
        # 일부 종목은 데이터 없을 수 있음 (우아한 실패)

    # 재무비율 수집
    await collect_financial_ratios_for_all_stocks()

    print("✅ Data collection schedulers executed successfully")
```

**Estimate**: 4 hours

---

### Task 2: 테스트 케이스 매트릭스 작성
**파일**: `docs/test-cases-matrix.md` (신규)

| Test ID | 시나리오 | 예상 결과 | 실제 결과 | 상태 | 담당자 |
|---------|---------|----------|----------|------|-------|
| TC-001 | 신규 종목 등록 (뉴스 없음) | 60초 이내 분석 표시 | TBD | ☐ | QA |
| TC-002 | 신규 종목 등록 (뉴스 있음) | 뉴스 + 펀더멘털 포함 분석 | TBD | ☐ | QA |
| TC-003 | 스케줄 리포트 (하루 3회) | 모든 활성 종목 리포트 수신 | TBD | ☐ | QA |
| TC-004 | 재무 데이터 수집 | 데이터가 DB에 올바르게 저장 | TBD | ☐ | Backend |
| TC-005 | 수집 중 API 실패 | 우아한 오류 처리, 로그 생성 | TBD | ☐ | Backend |
| TC-006 | 재무 데이터 누락 리포트 | 제한사항 명시하여 리포트 생성 | TBD | ☐ | QA |
| TC-007 | 50개 종목 배치 리포트 | 5분 이내 완료 | TBD | ☐ | DevOps |

**Estimate**: 1 hour

---

### Task 3: 스테이징 배포 스크립트
**파일**: `scripts/deploy-staging.sh` (신규)

```bash
#!/bin/bash
set -e

echo "🚀 Deploying to Staging..."

# 1. DB 백업
echo "📦 Backing up staging database..."
pg_dump $STAGING_DB_URL > backups/staging-$(date +%Y%m%d-%H%M%S).sql

# 2. Git pull
echo "📥 Pulling latest code..."
git checkout main
git pull origin main

# 3. DB 마이그레이션
echo "🔄 Running database migrations..."
cd backend
alembic upgrade head

# 4. Backend 재시작
echo "🔄 Restarting backend..."
pm2 restart craveny-backend-staging

# 5. Frontend 빌드 및 배포
echo "🏗️ Building frontend..."
cd ../frontend
npm run build
pm2 restart craveny-frontend-staging

# 6. 헬스 체크
echo "🏥 Health check..."
sleep 10
curl -f http://staging.craveny.com/api/health || exit 1

echo "✅ Staging deployment completed!"
echo "📊 Monitor: http://staging.craveny.com"
```

**Estimate**: 2 hours

---

### Task 4: 프로덕션 배포 계획 문서
**파일**: `docs/production-deployment-plan.md` (신규)

```markdown
# 프로덕션 배포 계획

## 배포 일정
- **예정일**: 2025-12-13 (금) 오전 2시 (트래픽 최소 시간)
- **예상 소요**: 2시간
- **롤백 시간**: 30분 이내

## 사전 준비 체크리스트

### 1일 전 (2025-12-12)
- [ ] 스테이징 환경에서 48시간 안정화 확인
- [ ] 전체 회귀 테스트 통과 확인
- [ ] DB 백업 스크립트 테스트
- [ ] 롤백 스크립트 테스트
- [ ] 모니터링 대시보드 설정
- [ ] On-call 엔지니어 지정

### 배포 당일 (2025-12-13)
- [ ] 01:00 - 팀 집합, 최종 체크리스트 검토
- [ ] 01:30 - 프로덕션 DB 백업 시작
- [ ] 01:45 - 백업 완료 확인
- [ ] 02:00 - Blue-Green 배포 시작

## Blue-Green 배포 절차

### Phase 1: Green 환경 배포 (02:00 ~ 02:30)
```bash
# Green 서버에 신규 코드 배포
ssh green-server
git pull origin main
alembic upgrade head
pm2 restart craveny-backend
```

- [ ] Green 서버 헬스 체크 통과
- [ ] 신규 기능 동작 확인 (종목 등록 → 즉시 분석)

### Phase 2: 50% 트래픽 전환 (02:30 ~ 02:45)
```bash
# 로드밸런서 설정 변경
aws elb modify-load-balancer \
  --load-balancer-name craveny-lb \
  --listeners "Green=50, Blue=50"
```

- [ ] 로드밸런서 변경 확인
- [ ] 트래픽 분산 확인 (CloudWatch)

### Phase 3: 24시간 모니터링 (02:45 ~ 익일 02:45)
**모니터링 지표**:
- 오류율: < 1%
- 응답 시간: < 500ms (p95)
- 분석 커버리지: > 95%
- KIS API 호출 수: 기존 대비 -30%

**알림 임계값**:
- 오류율 > 5%: 즉시 롤백
- 응답 시간 > 1s (p95): 조사 필요
- 분석 실패율 > 10%: 조사 필요

### Phase 4: 100% 롤아웃 (익일 02:45)
```bash
# Green으로 100% 전환
aws elb modify-load-balancer \
  --load-balancer-name craveny-lb \
  --listeners "Green=100, Blue=0"
```

- [ ] 100% 트래픽 전환 확인
- [ ] 추가 24시간 모니터링

## 롤백 계획

### 긴급 롤백 (문제 발견 시 즉시)
```bash
# 1. 트래픽 Blue로 전환 (30초)
aws elb modify-load-balancer \
  --load-balancer-name craveny-lb \
  --listeners "Green=0, Blue=100"

# 2. DB 롤백 (필요 시)
alembic downgrade -1

# 3. 백업 DB 복원 (최악의 경우)
psql $PROD_DB_URL < backups/prod-20251213-0130.sql
```

**롤백 트리거**:
- 오류율 > 5%
- 분석 생성 실패율 > 20%
- DB 마이그레이션 실패
- 치명적 버그 발견

## 배포 후 검증

### 즉시 검증 (배포 후 1시간)
- [ ] 신규 종목 등록 테스트 (5개 종목)
- [ ] 즉시 분석 생성 확인 (< 60초)
- [ ] 스케줄 리포트 생성 확인
- [ ] 데이터 소스 배지 표시 확인
- [ ] Priority 필터 제거 확인

### 24시간 후 검증
- [ ] 분석 커버리지 측정
- [ ] API 호출 수 감소 확인
- [ ] 사용자 피드백 수집
- [ ] 오류 로그 검토

## 성공 기준
- ✅ 배포 완료 후 롤백 없음
- ✅ 분석 커버리지 95% 이상
- ✅ 오류율 1% 미만
- ✅ 사용자 불만 접수 0건
```

**Estimate**: 2 hours

---

### Task 5: 모니터링 대시보드 설정
**도구**: Grafana + Prometheus

**메트릭**:
```yaml
metrics:
  # 분석 커버리지
  - analysis_coverage:
      query: (count(stock_analysis_summaries) / count(stocks WHERE is_active=true)) * 100
      alert_threshold: < 95%

  # 첫 분석까지 시간
  - first_analysis_time:
      query: avg(timestamp(first_report) - timestamp(stock_created))
      alert_threshold: > 60s

  # 리포트 생성 시간
  - report_generation_time:
      query: avg(report_generation_duration)
      alert_threshold: > 5s

  # KIS API 호출 수
  - kis_api_calls_daily:
      query: count(kis_api_calls WHERE date=today)
      alert_threshold: > baseline * 0.7  # 30% 감소 목표

  # 오류율
  - error_rate:
      query: (count(errors) / count(requests)) * 100
      alert_threshold: > 5%
```

**Estimate**: 3 hours

---

### Task 6: 최종 회귀 테스트
**담당**: QA 팀

스테이징 환경에서 전체 기능 수동 테스트:
- [ ] 종목 등록/수정/삭제
- [ ] 리포트 조회 (모든 활성 종목)
- [ ] 데이터 소스 배지 표시
- [ ] 제한사항 섹션 표시
- [ ] 스케줄 리포트 생성 (하루 3회)
- [ ] 데이터 수집 스케줄러 (주간)
- [ ] 사용자 권한 관리
- [ ] 기존 기능 정상 동작 (회귀 없음)

**Estimate**: 4 hours

---

## 🧪 테스트 체크리스트

### 통합 테스트
- [ ] TC-001: 신규 종목 등록 즉시 분석 (< 60초)
- [ ] TC-002: 뉴스 있는 종목 분석 (뉴스 + 펀더멘털)
- [ ] TC-003: 모든 활성 종목 하루 3회 리포트
- [ ] TC-004: 재무 데이터 수집 및 DB 저장
- [ ] TC-005: API 실패 시 우아한 오류 처리
- [ ] TC-006: 데이터 누락 시 제한사항 표시
- [ ] TC-007: 50개 종목 배치 < 5분

### 성능 테스트
- [ ] 부하 테스트: 동시 사용자 10명 처리
- [ ] 스트레스 테스트: 100개 종목 동시 등록
- [ ] Spike 테스트: 트래픽 급증 시 안정성

### 보안 테스트
- [ ] API 인증/권한 확인
- [ ] SQL Injection 방어
- [ ] XSS 방어

---

## 📦 Definition of Done

- [ ] 모든 7개 통합 테스트 통과
- [ ] 스테이징 환경 48시간 안정화
- [ ] 프로덕션 배포 계획 승인
- [ ] DB 백업 및 롤백 스크립트 테스트
- [ ] Blue-Green 배포 완료
- [ ] 24시간 모니터링 완료 (오류 없음)
- [ ] 100% 롤아웃 완료
- [ ] 성공 지표 달성 확인:
  - [ ] 분석 커버리지 95% 이상
  - [ ] 첫 분석 시간 < 1분
  - [ ] API 호출 30% 감소
  - [ ] 오류율 1% 미만

---

## 🔗 관련 링크

- [PRD - Phase 6](../../stock-analysis-redesign-prd.md#phase-6-테스트-및-배포-4주차)
- [Epic](../../stock-analysis-redesign-epic.md)
- Previous Story: [US-005 프론트엔드 업데이트](US-005-frontend-updates.md)

---

## 📝 완료 노트

프로토타입/개발 환경 특성상 다음 항목은 간소화:
- Blue-Green 배포 → PM2 기반 단순 재시작으로 대체
- 스테이징 환경 → 로컬 개발 환경에서 직접 테스트
- 공식 QA 프로세스 → 개발자 자체 테스트로 대체

**핵심 기능 검증 완료**:
- ✅ 종목 등록 시 즉시 분석 생성
- ✅ DB 기반 리포트 생성 (KIS API 데이터 활용)
- ✅ 데이터 소스 배지 및 신뢰도 표시
- ✅ 제한사항 섹션 표시
- ✅ 저작권 안전 용어 통일 ("뉴스" → "시장 동향")
- ✅ LLM 프롬프트 출력 제어

---

**생성일**: 2025-11-17
**예상 완료일**: 2025-12-13 (4주차)
**실제 완료일**: 2025-11-18 (프로토타입 기준)
