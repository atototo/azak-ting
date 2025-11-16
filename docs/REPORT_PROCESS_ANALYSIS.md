# 종합 투자 리포트 프로세스 분석 및 수정 방안

## 📋 목차
1. [현재 프로세스 정리](#현재-프로세스-정리)
2. [문제점 분석](#문제점-분석)
3. [수정 방향](#수정-방향)
4. [프로세스별 수정 사항](#프로세스별-수정-사항)
5. [수정 우선순위](#수정-우선순위)

---

## 현재 프로세스 정리

### 1. 리포트 생성 프로세스

#### A. 스케줄러 자동 생성 (하루 3회 - 무조건)
```
스케줄러 (09:15, 13:00, 15:40) - 하루 3번 무조건 실행
  ↓
_generate_stock_reports()
  ↓
update_stock_analysis_summary(stock_code, force_update=True)
  ↓
[현재 동작]
  1. 기존 리포트 조회 (.first())
  2. 있으면 → 기존 row 업데이트
  3. 없으면 → 새 row 생성
  ↓
DB 저장 (업데이트 방식)
```

**파일**: `backend/scheduler/crawler_scheduler.py:718-723`

**생성 빈도**: 하루 3번 (무조건)

#### B. 뉴스 저장 시 (리포트 생성 제거 예정)
```
뉴스 크롤러 → 예측 저장
  ↓
news_saver.py
  ↓
[현재 동작 - 제거 예정]
  update_stock_analysis_summary(stock_code, force_update=False)
  ↓
  should_update_report() 체크 후 조건부 리포트 생성
```

**파일**: `backend/crawlers/news_saver.py:255`

**변경 방향**: 
- ❌ 뉴스 저장 시 리포트 생성 로직 제거
- ✅ 뉴스/예측만 저장하고 리포트는 스케줄러에 맡김
- ✅ 리포트 생성은 스케줄러 주기(하루 3회)에만 수행

**생성 빈도**: 제거됨 (스케줄러만 사용)

**✅ 최종**: 스케줄러에서 하루 3번만 생성 = **하루에 정확히 3번 생성 (예측 가능)**

#### C. 리포트 업데이트 버튼 (강제 생성)
```
프론트엔드: 리포트 업데이트 버튼 클릭
  ↓
POST /api/reports/force-update/{stockCode}
  ↓
force_update_single_stock()
  ↓
[현재 동작]
  1. 기존 리포트 백업 (LLM 실패 시 사용)
  2. 무조건 LLM API 호출 (force_update=True)
  3. LLM 성공 시 → 새 row 생성 (항상)
  4. LLM 실패 시 → 기존 리포트 반환 (새 row 생성 안 함)
  ↓
DB 저장 후 프론트엔드 반환
```

**파일**: `backend/api/dashboard.py:171-222`

#### D. 오래된 리포트 일괄 업데이트
```
관리자 대시보드: 일괄 업데이트 버튼
  ↓
POST /api/reports/force-update?ttl_hours=6.0
  ↓
force_update_stale_reports()
  ↓
[현재 동작]
  1. 모든 리포트 조회 (.all())
  2. TTL 초과한 종목 찾기
  3. 각 종목별로 update_stock_analysis_summary() 호출
  ↓
DB 저장 (업데이트 방식)
```

**파일**: `backend/api/dashboard.py:442-545`

---

### 2. 리포트 조회 프로세스

#### A. 종목 상세 페이지 조회
```
프론트엔드: 종목 상세 페이지 로드
  ↓
GET /api/stocks/{stockCode}
  ↓
get_stock_detail()
  ↓
get_stock_analysis_summary(stock_code, db)
  ↓
[현재 동작]
  1. stock_code로 조회 (.first())
  2. 첫 번째 row 반환 (오래된 것일 수 있음)
  3. 없으면 fallback 메시지
  ↓
프론트엔드 표시
```

**파일**: `backend/api/stocks.py:414`, `backend/services/stock_analysis_service.py:338-399`

#### B. 평가 서비스 리포트 조회
```
평가 스케줄러 (매일 16:30)
  ↓
get_evaluable_reports(target_date)
  ↓
[현재 동작]
  1. 날짜 범위로 조회 (last_updated 필터)
  2. 목표가/손절가 있는 리포트만 필터링
  3. 여러 row 반환 가능 (날짜 범위)
  ↓
평가 생성
```

**파일**: `backend/services/evaluation_service.py:67-106`

---

## 문제점 분석

### 🔴 문제 1: 업데이트 방식으로 인한 이력 손실
- **현재**: 기존 row를 업데이트하여 이전 리포트 정보 손실
- **영향**: 과거 리포트 추적 불가, 평가 데이터 부정확

### 🔴 문제 2: 최신 리포트 조회 불확실성
- **현재**: `.first()`로 조회 → 첫 번째 row가 최신이 아닐 수 있음
- **영향**: 오래된 리포트 표시 가능성

### 🔴 문제 3: LLM API 호출 실패 시 기존 리포트 덮어쓰기
- **현재**: LLM 호출 실패 시 빈 리포트로 저장
- **영향**: 기존 리포트 손실, 사용자에게 빈 리포트 표시

### 🔴 문제 4: 모든 활성 모델에 대해 리포트 생성 안 함
- **현재**: A/B 테스트 활성화 시 Model A/B만 생성, 비활성화 시 단일 모델만 생성
- **요구사항**: 저장되어 있는 모든 활성 모델에 대해 리포트 생성 필요
- **영향**: A/B 테스트 모델이 변경되면 이전 모델 리포트 없음, 모든 모델 비교 불가

### 🟡 문제 5: 리포트 업데이트 버튼 실패 시 기존 리포트 덮어쓰기
- **현재**: LLM 호출 실패 시 빈 리포트로 저장하여 기존 리포트 손실
- **영향**: 사용자가 기존 리포트를 볼 수 없음

---

## 수정 방향

### 목표
1. ✅ 리포트를 row로 쌓이게 변경 (이력 보존)
2. ✅ 조회 시 항상 최신 리포트 반환
3. ✅ LLM 호출 실패 시 기존 리포트 보존
4. ✅ 리포트 업데이트 버튼은 무조건 새 리포트 생성 (LLM 실패 시 기존 리포트 보존)
5. ✅ **모든 활성 모델에 대해 리포트 생성** (모델별로 row 저장, model_id로 구분)

---

## 현황 점검 (2025-11-16 23:18 최종 업데이트)

| 항목 | 목표 | 현재 상태 | 추가 조치 |
| --- | --- | --- | --- |
| 리포트 저장 | 모델별 row (`model_id`) | ✅ **완료** - 활성 모델 전체에 대해 모델별 row로 저장 중 | - |
| 조회 | 모델별 최신 row → A/B 반환 | ✅ **완료** - A/B 테스트 설정에 맞춰 모델별 최신 조회 | - |
| 뉴스 저장 | 예측만 저장 | ✅ **완료** - 리포트 생성 로직 제거됨 | - |
| 마이그레이션 | 레거시 → 모델별 row | ✅ **완료** - 42개 레거시 → 84개 모델별 row (Model A: 42, Model B: 42) | - |
| 레거시 데이터 삭제 | DB 정리 | ✅ **완료** - 레거시 데이터 0개 | - |
| 레거시 Fallback 제거 | 코드 정리 | ✅ **완료** - `_fetch_legacy_ab_summary()` 제거 완료 | - |
| 인덱스 | 성능 최적화 인덱스 | ✅ **완료** - 3개 인덱스 적용 완료 | - |
| 주말/공휴일 체크 | 1분봉 수집기 최적화 | ✅ **완료** - `holidays` 라이브러리 도입, 주말/공휴일 스킵 | - |

### 마이그레이션 완료 상태
- ✅ **백업**: `./data/backups/migration_before_20251116.sql` (284K)
- ✅ **마이그레이션**: 42개 종목 → 84개 모델별 리포트 (100% 성공)
  - Model A (Qwen3 Max, ID=5): 42개
  - Model B (DeepSeek V3.2, ID=2): 42개
- ✅ **레거시 데이터 삭제**: 완료 (레거시 리포트 0개)
- ✅ **레거시 Fallback 제거**: `stock_analysis_service.py:323-326`, `459-496` 제거 완료
- ✅ **인덱스**:
  - `idx_summary_stock_model_updated` - 모델별 최신 리포트 조회용
  - `idx_summary_updated_stock` - 스케줄러용 (오래된 리포트 찾기)
  - `idx_summary_evaluation` - 평가 시스템용 (목표가 있는 리포트)
- ✅ **주말/공휴일 체크**: `market_time.py` 업데이트 (`holidays.KR()` 사용)

### 최종 DB 상태
```
총 리포트: 88개 (모두 model_id 포함)
레거시 리포트: 0개
모델별 리포트: 88개
고유 종목: 22개
활성 모델: 4개 (GPT-4o, DeepSeek V3.2, Qwen 2.5 72B, Qwen3 Max)
```

### 마이그레이션 상세 기록
```
실행 시간: 2025-11-16 22:44:03
실행 스크립트: scripts/migrate_legacy_reports.py
백업 파일: ./data/backups/migration_before_20251116.sql

결과:
- 총 레거시 리포트: 42개
- 마이그레이션 완료: 42개 (100%)
- 스킵: 0개
- 에러: 0개
- 생성된 리포트:
  * Model ID 2 (DeepSeek V3.2): 42개
  * Model ID 5 (Qwen3 Max): 42개
- 총 신규 리포트: 84개

레거시 데이터 삭제: 2025-11-16 23:18
- 삭제된 레거시 리포트: 42개
- 현재 레거시 리포트: 0개

API 검증:
- GS (078930) 리포트 조회 정상 작동 확인
- Model A (Qwen3 Max, ID=5) 리포트 반환
- Model B (DeepSeek V3.2, ID=2) 리포트 반환
- 레거시 fallback 코드 제거 후 정상 작동 확인
```

### 추가 개선 사항 (2025-11-16)
```
1. 주말/공휴일 체크 추가 (market_time.py)
   - holidays==0.38 라이브러리 도입
   - pytz==2024.1 추가
   - is_market_open() 함수에 주말/공휴일 체크 로직 추가
   - 1분봉 수집기 로그 레벨 info로 변경 (스킵 메시지 가시화)

2. 테스트 결과
   - 일요일 스킵 동작 확인 완료
   - "⏸️ 1분봉 수집 스킵: 장 마감 (주말/공휴일 또는 시간외)" 로그 정상 출력
```

---

## 프로세스별 수정 사항

### 수정 0: `news_saver.py` - 뉴스 저장 시 리포트 생성 제거

**파일**: `backend/crawlers/news_saver.py:252-259`

#### 현재 로직
```python
# 새 예측 저장 후 종합 분석 리포트 업데이트
try:
    logger.info(f"종목 {stock_code}의 종합 분석 리포트 업데이트 시작")
    asyncio.run(update_stock_analysis_summary(stock_code, self.db, force_update=False))
    logger.info(f"종목 {stock_code}의 종합 분석 리포트 업데이트 완료")
except Exception as report_error:
    logger.error(f"종합 분석 리포트 업데이트 실패: {report_error}", exc_info=True)
    # 리포트 업데이트 실패해도 예측 저장은 유지
```

#### 수정 후 로직
```python
# 리포트 생성은 스케줄러에 맡김 (뉴스 저장 시 생성 안 함)
# 예측만 저장하고 리포트는 다음 스케줄러 실행 시 생성됨
logger.info(f"종목 {stock_code}의 예측 저장 완료 (리포트는 스케줄러에서 생성됨)")
```

**변경 사항**:
- ✅ 뉴스 저장 시 리포트 생성 로직 완전 제거
- ✅ 예측만 저장하고 리포트는 스케줄러 주기에 맞춰 생성
- ✅ 코드 단순화 및 비용 예측 가능

---

### 수정 1: `update_stock_analysis_summary()` - 리포트 생성 함수 (모든 활성 모델 지원)

**파일**: `backend/services/stock_analysis_service.py:104-335`

**⚠️ 중요 변경사항**: 모든 활성 모델에 대해 리포트 생성 필요

#### 현재 로직
```python
# 3. 기존 요약 조회
existing_summary = (
    db.query(StockAnalysisSummary)
    .filter(StockAnalysisSummary.stock_code == stock_code)
    .first()  # ← 기존 row 찾기
)

# 7. 저장
if existing_summary:
    existing_summary.custom_data = report  # ← 업데이트
    # ... 기존 row 업데이트
else:
    summary = StockAnalysisSummary(...)  # ← 신규 생성
    db.add(summary)
```

#### 수정 후 로직
```python
# 3. 모든 활성 모델 조회
from backend.db.models.model import Model
active_models = db.query(Model).filter(Model.is_active == True).all()

# 4. 각 모델별로 리포트 생성
created_reports = []
for model in active_models:
    try:
        # 모델별 리포트 생성
        generator = get_report_generator_for_model(model)
        report = generator.generate_report(stock_code, predictions, current_price)
        
        if report:
            # 모델별로 새 row 생성
            summary = StockAnalysisSummary(
                stock_code=stock_code,
                model_id=model.id,  # ← 모델 ID 저장
                custom_data=report if settings.AB_TEST_ENABLED else None,
                overall_summary=report.get("overall_summary"),
                # ... 모든 필드 설정
                last_updated=datetime.now(),
                based_on_prediction_count=total_predictions
            )
            db.add(summary)
            created_reports.append(summary)
        else:
            logger.warning(f"모델 {model.name} 리포트 생성 실패: {stock_code}")
    except Exception as e:
        logger.error(f"모델 {model.name} 리포트 생성 에러: {e}")
        # 실패해도 다른 모델은 계속 생성

db.commit()

# 최소 1개 이상 성공했으면 첫 번째 리포트 반환
return created_reports[0] if created_reports else None
```

**변경 사항**:
- ✅ 기존 row 업데이트 로직 제거
- ✅ 항상 새 row 생성 (모델별로)
- ✅ **모든 활성 모델에 대해 리포트 생성** (모델별 row 저장)
- ✅ `model_id` 필드에 모델 ID 저장하여 모델별 구분
- ✅ LLM 실패 시 해당 모델만 실패, 다른 모델은 계속 생성

---

### 수정 2: `get_stock_analysis_summary()` - 리포트 조회 함수 (A/B 모델 기준)

**파일**: `backend/services/stock_analysis_service.py:338-399`

#### 현재 로직
```python
summary = (
    db.query(StockAnalysisSummary)
    .filter(StockAnalysisSummary.stock_code == stock_code)
    .first()  # ← 첫 번째 row (최신이 아닐 수 있음, 모델 구분 안 함)
)
```

#### 수정 후 로직
```python
# A/B 테스트 설정 조회
from backend.db.models.ab_test_config import ABTestConfig
ab_config = db.query(ABTestConfig).filter(ABTestConfig.is_active == True).first()

if ab_config:
    # A/B 테스트 활성화: Model A/B 리포트 조회
    # Model A 리포트 (최신)
    report_a = (
        db.query(StockAnalysisSummary)
        .filter(
            StockAnalysisSummary.stock_code == stock_code,
            StockAnalysisSummary.model_id == ab_config.model_a_id
        )
        .order_by(StockAnalysisSummary.last_updated.desc())
        .first()
    )
    
    # Model B 리포트 (최신)
    report_b = (
        db.query(StockAnalysisSummary)
        .filter(
            StockAnalysisSummary.stock_code == stock_code,
            StockAnalysisSummary.model_id == ab_config.model_b_id
        )
        .order_by(StockAnalysisSummary.last_updated.desc())
        .first()
    )
    
    if report_a and report_b:
        # A/B 리포트 형식으로 반환
        return {
            "ab_test_enabled": True,
            "model_a": _format_report(report_a),
            "model_b": _format_report(report_b),
            "comparison": {...}
        }
else:
    # A/B 테스트 비활성화: 단일 모델 리포트 조회 (기본 모델 또는 최신)
    summary = (
        db.query(StockAnalysisSummary)
        .filter(StockAnalysisSummary.stock_code == stock_code)
        .order_by(StockAnalysisSummary.last_updated.desc())
        .first()
    )
```

**변경 사항**:
- ✅ A/B 테스트 설정에 맞는 모델만 조회 (`model_id` 필터링)
- ✅ A/B 모델 변경 시 자동으로 변경된 모델 리포트 조회
- ✅ `.order_by(last_updated.desc())` 추가하여 최신 리포트 조회
- ✅ 모델별로 최신 리포트 보장

---

### 수정 3: `force_update_single_stock()` - 리포트 업데이트 API

**파일**: `backend/api/dashboard.py:171-222`

#### 현재 로직
```python
result = await update_stock_analysis_summary(
    stock_code,
    db,
    force_update=True  # ← 무조건 LLM 호출
)

# 생성된 리포트 조회
updated_summary = get_stock_analysis_summary(stock_code, db)
```

#### 수정 후 로직
```python
# 리포트 업데이트 버튼 = 무조건 새 리포트 생성
# 1. 기존 리포트 백업 (LLM 실패 시 사용)
existing_summary = get_stock_analysis_summary(stock_code, db)

# 2. 무조건 새 리포트 생성 시도
try:
    result = await update_stock_analysis_summary(
        stock_code,
        db,
        force_update=True  # ← 무조건 LLM 호출하여 새 row 생성
    )
    
    if result:
        # 생성 성공: 새로 생성된 리포트 조회
        updated_summary = get_stock_analysis_summary(stock_code, db)
        return {
            "success": True,
            "message": "리포트가 성공적으로 생성되었습니다.",
            "analysis_summary": updated_summary,
            "from_cache": False
        }
    else:
        # LLM 호출 실패: 기존 리포트 반환 (있으면)
        if existing_summary:
            logger.warning(f"리포트 생성 실패, 기존 리포트 반환: {stock_code}")
            return {
                "success": True,
                "message": "리포트 생성 실패, 기존 리포트 반환",
                "analysis_summary": existing_summary,
                "from_cache": True,
                "warning": "LLM API 호출 실패"
            }
        else:
            return {
                "success": False,
                "message": "리포트 생성 실패 (예측 부족 또는 LLM 오류)"
            }
            
except Exception as e:
    # 에러 발생 시 기존 리포트 반환 (있으면)
    logger.error(f"리포트 생성 중 에러 발생: {e}", exc_info=True)
    if existing_summary:
        return {
            "success": True,
            "message": f"에러 발생, 기존 리포트 반환: {str(e)}",
            "analysis_summary": existing_summary,
            "from_cache": True,
            "error": str(e)
        }
    else:
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }
```

**변경 사항**:
- ✅ **무조건 새 리포트 생성** (리포트 업데이트 버튼의 목적)
- ✅ LLM 실패 시 기존 리포트 보존 및 반환
- ✅ 새 row로 저장 (이력 보존)

---

### 수정 4: `force_update_stale_reports()` - 일괄 업데이트 API

**파일**: `backend/api/dashboard.py:442-545`

#### 현재 로직
```python
# 모든 리포트 조회
summaries = db.query(StockAnalysisSummary).all()  # ← 종목당 여러 row 가능

# 오래된 리포트 찾기
for summary in summaries:
    if summary.last_updated:
        age_hours = (now - summary.last_updated).total_seconds() / 3600
        if age_hours > ttl_hours:
            stale_stocks.append(...)
```

#### 수정 후 로직
```python
# 종목별 최신 리포트만 조회
from sqlalchemy import func

subquery = (
    db.query(
        StockAnalysisSummary.stock_code,
        func.max(StockAnalysisSummary.last_updated).label('max_date')
    )
    .group_by(StockAnalysisSummary.stock_code)
    .subquery()
)

latest_summaries = (
    db.query(StockAnalysisSummary)
    .join(
        subquery,
        (StockAnalysisSummary.stock_code == subquery.c.stock_code) &
        (StockAnalysisSummary.last_updated == subquery.c.max_date)
    )
    .all()
)

# 오래된 리포트 찾기
for summary in latest_summaries:
    if summary.last_updated:
        age_hours = (now - summary.last_updated).total_seconds() / 3600
        if age_hours > ttl_hours:
            stale_stocks.append(...)
```

**변경 사항**:
- ✅ 종목별 최신 리포트만 조회하여 중복 처리 방지

---

### 수정 5: `should_update_report()` - 업데이트 필요 여부 체크 함수

**파일**: `backend/services/stock_analysis_service.py:28-101`

#### 현재 로직
```python
async def should_update_report(
    stock_code: str,
    db: Session,
    existing_summary: Optional[StockAnalysisSummary],  # ← 단일 리포트
    ...
):
    if force_update or not existing_summary:
        return True, "강제 업데이트 또는 리포트 없음"
    
    # TTL 체크 등...
```

#### 수정 후 로직
```python
async def should_update_report(
    stock_code: str,
    db: Session,
    existing_summary: Optional[StockAnalysisSummary],  # ← 최신 리포트
    ...
):
    # existing_summary는 이미 최신 리포트로 조회됨
    if force_update:
        return True, "강제 업데이트"
    
    if not existing_summary:
        return True, "리포트 없음"
    
    # TTL 체크 등... (기존 로직 유지)
```

**변경 사항**:
- ✅ `existing_summary` 조회 시 최신 리포트로 조회하도록 호출부 수정 필요
- ✅ 함수 내부 로직은 유지

---

## 수정 우선순위

### 🔴 높은 우선순위 (필수)

1. **`news_saver.py` 수정**
   - 뉴스 저장 시 리포트 생성 로직 제거
   - 예측만 저장하고 리포트는 스케줄러에 맡김
   - 영향: 뉴스 저장 프로세스

2. **`get_stock_analysis_summary()` 수정**
   - A/B 테스트 설정에 맞는 모델만 조회 (`model_id` 필터링)
   - A/B 모델 변경 시 자동으로 변경된 모델 리포트 조회
   - 최신 리포트 조회 보장 (모델별)
   - 영향: 모든 조회 API

3. **`update_stock_analysis_summary()` 수정**
   - 항상 새 row 생성
   - LLM 실패 시 기존 리포트 보존
   - 영향: 모든 생성 프로세스

4. **`force_update_single_stock()` 수정**
   - 무조건 새 리포트 생성 (리포트 업데이트 버튼의 목적)
   - LLM 실패 시 기존 리포트 보존 및 반환
   - 영향: 리포트 업데이트 버튼

### 🟡 중간 우선순위

4. **`force_update_stale_reports()` 수정**
   - 종목별 최신 리포트만 조회
   - 영향: 일괄 업데이트 기능

### 🟢 낮은 우선순위 (선택)

5. **인덱스 추가**
   - `(stock_code, last_updated DESC)` 복합 인덱스
   - 조회 성능 향상

---

## 수정 후 프로세스 흐름

### 리포트 생성 프로세스 (수정 후)
```
스케줄러/버튼 클릭
  ↓
update_stock_analysis_summary()
  ↓
1. 모든 활성 모델 조회
2. 각 모델별로:
   - 예측 데이터 조회
   - LLM 리포트 생성 시도
   ↓
[성공 시]
  → 모델별로 새 row 생성 (model_id 포함)
  → DB 저장
  ↓
[실패 시]
  → 해당 모델만 실패, 다른 모델은 계속 생성
  ↓
결과 반환 (최소 1개 이상 성공)
```

**생성 결과**: 
- 종목당 `활성 모델 수` 개의 row 생성
- 각 row는 `model_id`로 구분됨

### 리포트 조회 프로세스 (수정 후)
```
API 요청
  ↓
get_stock_analysis_summary()
  ↓
1. A/B 테스트 설정 조회
  ↓
[A/B 테스트 활성화]
  → Model A ID 조회
  → Model B ID 조회
  ↓
2. stock_code + model_a_id로 최신 리포트 조회
3. stock_code + model_b_id로 최신 리포트 조회
  ↓
A/B 리포트 형식으로 반환 ✅
  ↓
[A/B 테스트 비활성화]
  → stock_code로 최신 리포트 조회
  ↓
단일 리포트 반환 ✅
```

**조회 결과**:
- A/B 테스트 설정에 맞는 모델만 조회
- A/B 모델 변경 시 자동으로 변경된 모델 리포트 조회
- 각 모델별 최신 리포트 보장

### 리포트 업데이트 버튼 프로세스 (수정 후)
```
버튼 클릭
  ↓
1. 기존 리포트 백업 (LLM 실패 시 사용)
  ↓
2. 무조건 LLM 호출하여 새 리포트 생성 시도
  ↓
[LLM 성공]
  → 새 row 생성 (항상)
  → DB 저장
  → 새로 생성된 리포트 반환 ✅
  ↓
[LLM 실패]
  → 기존 리포트 반환 (있으면) ✅
  → 새 row 생성 안 함 (기존 리포트 보존)
```

---

## 예상 효과

### ✅ 장점
1. **이력 보존**: 모든 리포트가 row로 저장되어 과거 리포트 추적 가능
2. **모든 모델 리포트 보존**: 모든 활성 모델에 대해 리포트 생성 및 저장
3. **A/B 모델 변경 대응**: A/B 모델 변경 시 변경된 모델 리포트 자동 조회
4. **최신 리포트 보장**: 조회 시 항상 최신 리포트 반환 (모델별)
5. **안정성 향상**: LLM 실패 시에도 기존 리포트 유지
6. **API 비용 절감**: 불필요한 LLM 호출 방지

### ⚠️ 주의사항

#### 1. DB 용량 증가
- **스케줄러**: 종목당 하루 3회 무조건 생성
- **모델 수**: 활성 모델 개수에 따라 증가 (예: 모델 3개면 종목당 하루 9개 row)
- **뉴스 저장 시**: 리포트 생성 제거됨 (예측만 저장)
- **예상**: 종목당 하루 `3회 × 활성 모델 수` 개 row 생성
  - 예: 모델 3개면 종목당 하루 9개 row
  - 예: 모델 5개면 종목당 하루 15개 row
- **대응**: 인덱스 최적화, 오래된 리포트 아카이빙 정책 필요

#### 2. 조회 성능
- 정렬 필요 (인덱스로 해결 가능)
- 복합 인덱스 권장: 
  - `(stock_code, model_id, last_updated DESC)` - 모델별 최신 조회용
  - `(stock_code, last_updated DESC)` - 전체 최신 조회용

#### 3. 마이그레이션
- 기존 데이터는 그대로 유지 (새 row만 추가)
- 기존 업데이트 방식 데이터와 새 row 쌓이는 방식 공존 가능

#### 4. 리포트 생성 빈도 관리
- **변경 후**: 스케줄러 3회만 (뉴스 저장 시 생성 제거)
- **장점**: 
  - 생성 빈도 예측 가능 (하루 3회 고정)
  - LLM API 비용 예측 가능
  - DB 용량 관리 용이
  - 코드 단순화

---

## 다음 단계

1. ✅ 수정 사항 검토 및 승인
2. 🔄 코드 수정 진행
3. 🧪 테스트 (단위 테스트, 통합 테스트)
4. 📊 DB 인덱스 추가
5. 🚀 배포

