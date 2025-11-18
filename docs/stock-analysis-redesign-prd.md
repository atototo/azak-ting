# 제품 요구사항 명세서 (PRD)
# 주식 분석 시스템 개편 - 뉴스 독립성 확보 및 펀더멘털 분석 강화

**문서 유형**: Brownfield PRD (기존 시스템 개편)
**프로젝트 ID**: CRAVENY-2025-001
**작성일**: 2025-11-17
**최종 수정일**: 2025-11-17
**작성자**: John (Product Manager)
**상태**: 초안 → 검토 → 승인 → 개발 중

---

## 문서 이력

| 버전 | 날짜 | 작성자 | 변경 사항 |
|------|------|--------|-----------|
| 1.0 | 2025-11-17 | John (PM) | Mary의 브리프 기반 초기 PRD 작성 |

---

## 📋 요약

### 문제 정의
현재 주식 분석 시스템은 뉴스 발생에 전적으로 의존하여, 뉴스가 없는 종목은 사용자가 등록해도 **분석이 전혀 수행되지 않는** 치명적인 문제가 있습니다. 사용자가 종목을 등록했을 때 "추적 중인 종목" 목록에 나타나지 않아 사용자 경험과 제품 가치가 근본적으로 훼손되고 있습니다.

### 솔루션 개요
분석 시스템을 **뉴스 주도형**에서 **데이터 주도형**으로 전환:
1. 펀더멘털 재무 데이터 수집 (성장성, 수익성, 안정성 지표)
2. 종목 등록 즉시 분석 실행
3. 뉴스 유무와 관계없이 모든 활성 종목 정기 분석 제공
4. Priority 시스템을 활성/비활성 단순 구조로 개편

### 비즈니스 임팩트
- **사용자 경험**: 즉시 분석 제공 (0% → 100% 커버리지)
- **제품 차별화**: 뉴스만 의존하는 경쟁사 대비 펀더멘털 분석 강점
- **시스템 안정성**: 뉴스 의존도 제거로 예측 가능한 동작
- **비용 효율**: 스케줄 기반 배치 수집으로 API 호출 최적화

---

## 🎯 목표 및 성공 지표

### 핵심 목표

| 목표 | 현재 상태 | 목표 상태 | 성공 지표 |
|------|----------|-----------|----------|
| 분석 커버리지 | ~60% (뉴스 의존) | 100% (모든 활성 종목) | 분석 보유 종목 비율 |
| 첫 분석까지 시간 | 무한대 (뉴스 대기) | < 1분 | 등록 후 첫 리포트까지 평균 시간 |
| 리포트 생성 빈도 | Priority 1-2만 3회/일 | 모든 활성 종목 3회/일 | 종목당 일일 리포트 수 |
| API 효율성 | 리포트당 0-5회 호출 | 리포트당 0회 호출 | 리포트 생성 시 API 호출 수 |

### 부가 목표
- Priority 시스템 단순화 (혼란 제거)
- 분석 깊이 증가 (펀더멘털 지표 추가)
- 데이터 투명성 향상 (사용 데이터 명시)
- 우아한 성능 저하 (가용 데이터로 분석)

### 범위 외 항목 (Non-Goals)
- 실시간 장중 분석 (기존 3회/일 유지)
- 뉴스/공시/Reddit 수집 로직 변경
- LLM 모델 선택 또는 A/B 테스트 프레임워크 수정
- Priority UI 제거 외 프론트엔드 재설계

---

## 👥 이해관계자 및 사용자

### 주요 이해관계자
- **최종 사용자**: 플랫폼을 이용하는 개인 투자자
- **개발팀**: 백엔드/프론트엔드 개발자
- **비즈니스 오너**: 사용자 만족도 및 참여도 추적

### 사용자 페르소나
**페르소나 1: 액티브 트레이더 "민수"**
- 20-30개 종목 모니터링 등록
- 종목 등록 시 즉각적인 피드백 기대
- 뉴스 없어서 종목이 "사라지면" 불만
- 중요 가치: 속도, 신뢰성, 포괄적 데이터

**페르소나 2: 장기 투자자 "지혜"**
- 5-10개 우량주 추적
- 뉴스 중심 감성 분석보다 펀더멘털 분석에 관심
- 중요 가치: 펀더멘털 지표 (ROE, PER, 부채비율), 안정성

---

## 🔍 현황 분석

### 시스템 아키텍처 (현재)

```
사용자 종목 등록
     ↓
stocks 테이블 (priority, is_active)
     ↓
뉴스 크롤러 (10분 간격) → news_articles 테이블
     ↓
뉴스에 stock_code 있으면 → 예측 분석 실행
     ↓
주식 분석 요약 (Priority 1-2만, 하루 3회)
```

### 주요 문제점

**문제점 1: 뉴스 의존성**
- **영향도**: 높음 (핵심 기능 차단)
- **빈도**: 상시 (모든 비Priority-1-2 종목)
- **증거**: "추적 중인 종목(43개)"에 사용자 등록 종목이 뉴스 없으면 미표시

**문제점 2: Priority 혼란**
- **영향도**: 중간 (사용성 문제)
- **빈도**: 종목 등록 시마다
- **증거**: Priority 1-5 척도가 실제로는 이진(자동리포트 vs 수동만)으로 동작

**문제점 3: 수집 데이터 미활용**
- **영향도**: 중간 (리소스 낭비)
- **빈도**: 지속적 (5분마다)
- **증거**: 시장 데이터, 투자자 수급 수집하지만 분석 트리거에 미사용

### 기술 부채
1. `crawler_scheduler.py:706-709` - 하드코딩된 `priority <= 2` 필터
2. `news_saver.py` - `article.stock_code` 존재 시에만 분석 실행
3. `stocks` 테이블 - `priority` 컬럼이 `is_active`와 중복 역할

---

## ✅ 제안 솔루션

### 솔루션 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   사용자 종목 등록                           │
│  UI: 종목 관리 → POST /api/admin/stocks                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              즉시 초기 분석 실행 (신규!)                     │
│  1. KIS API: get_current_price()                            │
│  2. KIS API: get_investor_trading()                         │
│  3. KIS API: get_product_info() ⭐                          │
│  4. KIS API: get_financial_ratios() ⭐                      │
│  5. DB 저장: product_info, financial_ratios 테이블          │
│  6. 초기 리포트 생성 (뉴스 무관)                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                정기 데이터 수집                               │
├─────────────────────────────────────────────────────────────┤
│ 5분마다:    현재가, 호가                                     │
│ 매일:       투자자 수급, 일봉                                │
│ 주 1회:     상품정보, 재무비율 ⭐                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│            정기 리포트 생성 (수정)                            │
│  하루 3회 (10:00, 13:00, 15:45)                             │
│  대상: 모든 활성 종목 (priority 필터 제거)                   │
│  데이터 소스: DB만 (API 호출 0회)                            │
└─────────────────────────────────────────────────────────────┘
```

### 핵심 아키텍처 변경

**변경 1: 뉴스 독립 분석**
- **기존**: `if news.stock_code: analyze()`
- **변경**: 가용 데이터 계층에 따라 항상 분석

**변경 2: 데이터 수집 전략**
- **신규**: 주간 재무비율 + 상품 메타데이터 수집
- **유지**: 기존 시장 데이터 수집 스케줄
- **최적화**: 리포트 생성 시 DB 캐시 데이터 사용 (API 호출 0회)

**변경 3: Priority 시스템 단순화**
- **기존**: `priority (1-5)`가 자동 리포트 자격 결정
- **변경**: `is_active (boolean)` - 모든 활성 종목 동일 대우

---

## 📊 상세 요구사항

### 기능 요구사항

#### FR-1: 종목 등록 즉시 분석
**우선순위**: P0 (필수)
**사용자 스토리**: 사용자로서, 새 종목을 등록했을 때 1분 이내에 분석 결과를 확인하여 즉시 추적을 시작하고 싶다.

**인수 기준**:
- [ ] POST `/api/admin/stocks` 시 시스템이 `trigger_initial_analysis(stock_code)` 실행
- [ ] 초기 분석이 60초 이내 완료
- [ ] 분석 후 종목이 "추적 중인 종목" 목록에 즉시 표시
- [ ] 분석 리포트에 data_sources_used 메타데이터 포함
- [ ] KIS API 실패 시 오류 로그 기록하되 placeholder 리포트 생성

**기술 사양**:
```python
# backend/api/stock_management.py
async def register_stock(stock_code: str, name: str, db: Session):
    # 1. DB 저장
    stock = Stock(code=stock_code, name=name, is_active=True)
    db.add(stock)
    db.commit()

    # 2. 즉시 초기 분석 실행 (신규)
    await trigger_initial_analysis(stock_code, db)

    return stock
```

---

#### FR-2: 재무비율 데이터 수집
**우선순위**: P0 (필수)
**사용자 스토리**: 시스템으로서, 주간 단위로 재무비율(성장성, 수익성, 안정성)을 수집하여 뉴스 없이도 펀더멘털 분석이 가능해야 한다.

**인수 기준**:
- [ ] 신규 KIS API 메서드: `get_financial_ratios(stock_code, div_cls_code="0")`
- [ ] 스케줄러가 매주 일요일 새벽 2시 실행
- [ ] `financial_ratios` 테이블에 데이터 저장 (stock_code, stac_yymm, grs, roe_val, eps, bps, lblt_rate 등)
- [ ] 최근 3년 연간 데이터 수집
- [ ] API 오류 시 우아한 처리 (로그 + 스킵)

**DB 스키마**:
```sql
CREATE TABLE financial_ratios (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    stac_yymm VARCHAR(6) NOT NULL,  -- 결산년월 YYYYMM
    div_cls_code VARCHAR(1) DEFAULT '0',  -- 0: 년, 1: 분기
    grs FLOAT,  -- 매출액 증가율
    bsop_prfi_inrt FLOAT,  -- 영업이익 증가율
    ntin_inrt FLOAT,  -- 순이익 증가율
    roe_val FLOAT,  -- ROE
    eps FLOAT,  -- EPS
    bps FLOAT,  -- BPS
    lblt_rate FLOAT,  -- 부채비율
    rsrv_rate FLOAT,  -- 유보율
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_financial_stock FOREIGN KEY (stock_code) REFERENCES stocks(code),
    CONSTRAINT uq_financial_ratios UNIQUE (stock_code, stac_yymm, div_cls_code)
);
```

---

#### FR-3: 상품정보 데이터 수집
**우선순위**: P1 (높음)
**사용자 스토리**: 시스템으로서, 주간 단위로 종목 상품 메타데이터(이름, 분류, 위험등급)를 수집하여 분석 컨텍스트를 풍부하게 만들어야 한다.

**인수 기준**:
- [ ] 신규 KIS API 메서드: `get_product_info(stock_code)`
- [ ] 스케줄러가 매주 일요일 새벽 1시 실행
- [ ] `product_info` 테이블에 데이터 저장
- [ ] 기존 레코드 업데이트 (UPSERT 동작)

**DB 스키마**:
```sql
CREATE TABLE product_info (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL UNIQUE,
    prdt_name VARCHAR(120),  -- 상품명
    prdt_clsf_name VARCHAR(100),  -- 상품분류명
    ivst_prdt_type_cd_name VARCHAR(100),  -- 투자상품유형명
    prdt_risk_grad_cd VARCHAR(10),  -- 위험등급코드
    frst_erlm_dt VARCHAR(8),  -- 최초등록일
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_stock FOREIGN KEY (stock_code) REFERENCES stocks(code)
);
```

---

#### FR-4: DB 기반 리포트 생성
**우선순위**: P0 (필수)
**사용자 스토리**: 시스템으로서, DB 캐시 데이터만 사용하여 리포트를 생성함으로써 API Rate Limit을 회피하고 빠른 생성 속도를 달성해야 한다.

**인수 기준**:
- [ ] `build_analysis_context_from_db()` 함수가 DB만 쿼리 (KIS API 호출 0회)
- [ ] 컨텍스트 포함: current_price, investor_trading, financial_ratios, product_info, technical_indicators, news(선택)
- [ ] 종목당 리포트 생성이 5초 이내 완료
- [ ] 누락 데이터 우아한 처리 (null 체크, 기본값)

**기술 사양**:
```python
async def build_analysis_context_from_db(stock_code: str, db: Session) -> Dict:
    context = {"stock_code": stock_code, "data_sources": {}}

    # Tier 1: DB 쿼리 (API 호출 없음)
    current_price = db.query(StockCurrentPrice).filter(...).first()
    investor_trading = db.query(InvestorTrading).filter(...).limit(5).all()
    financial_ratios = db.query(FinancialRatio).filter(...).limit(3).all()
    product_info = db.query(ProductInfo).filter(...).first()

    # Tier 2: 계산
    technical_indicators = calculate_indicators(stock_code, db)

    # Tier 3: 선택
    news = db.query(NewsArticle).filter(...).limit(10).all()

    # 데이터 소스 메타데이터 구축
    context["data_sources"] = {
        "market_data": bool(current_price),
        "investor_trading": bool(investor_trading),
        "financial_ratios": bool(financial_ratios),
        "product_info": bool(product_info),
        "technical_indicators": bool(technical_indicators),
        "news": bool(news)
    }

    return context
```

---

#### FR-5: Priority 시스템 제거
**우선순위**: P1 (높음)
**사용자 스토리**: 사용자로서, 종목 등록 시 Priority 1-5 선택으로 혼란스럽지 않고 활성/비활성만 선택하면 되도록 간소화되기를 원한다.

**인수 기준**:
- [ ] 마이그레이션이 모든 기존 `priority` 값을 1로 설정
- [ ] `crawler_scheduler.py`에서 `priority <= 2` 필터 제거
- [ ] 모든 활성 종목(`is_active=True`)이 하루 3회 리포트 수신
- [ ] 프론트엔드 UI에서 Priority 드롭다운 제거
- [ ] API는 여전히 `priority` 파라미터 수용 (하위 호환성) 하지만 무시

**마이그레이션**:
```python
# backend/db/migrations/deprecate_priority_column.py
def upgrade():
    conn.execute(text("UPDATE stocks SET priority = 1 WHERE priority != 1"))
    conn.commit()
```

---

#### FR-6: 적응형 분석 프롬프트
**우선순위**: P1 (높음)
**사용자 스토리**: 사용자로서, 분석 리포트를 읽을 때 어떤 데이터가 사용되었고 어떤 한계가 있는지 알아서 정보에 입각한 투자 결정을 내리고 싶다.

**인수 기준**:
- [ ] LLM 프롬프트에 "데이터 가용성" 섹션 포함 (가용/누락 데이터 소스 목록)
- [ ] 리포트 JSON에 `data_sources_used` 객체 포함
- [ ] 리포트 JSON에 `limitations` 배열 포함
- [ ] 리포트 JSON에 데이터 완전도 기반 `confidence_level` ("high", "medium", "low") 포함
- [ ] 프론트엔드에 데이터 소스 배지 표시 (✅ 재무 데이터, ✅ 투자자 수급, ❌ 뉴스)

**출력 예시**:
```json
{
  "stock_code": "005930",
  "overall_summary": "...",
  "fundamental_analysis": "매출 성장률 12.5%, ROE 22.3%로 양호한 펀더멘털...",
  "recommendation": "매수",
  "confidence_level": "medium",
  "data_sources_used": {
    "market_data": true,
    "investor_trading": true,
    "financial_ratios": true,
    "product_info": true,
    "technical_indicators": false,
    "news": false
  },
  "limitations": [
    "과거 가격 데이터 부족으로 기술적 지표 불완전",
    "최근 7일간 뉴스 없음"
  ],
  "data_completeness_score": 0.75
}
```

---

### 비기능 요구사항

#### NFR-1: 성능
- 리포트 생성: 종목당 < 5초
- 등록 시 초기 분석: < 60초
- 스케줄 배치 리포트 생성 (50개 종목): < 5분
- DB 쿼리 응답 시간: 쿼리당 < 100ms

#### NFR-2: 신뢰성
- API 실패 처리: 우아한 성능 저하 (오류 로그, 가용 데이터로 계속)
- DB 트랜잭션 안전성: 모든 마이그레이션에 롤백 기능 포함
- 데이터 일관성: financial_ratios의 (stock_code, stac_yymm)에 UNIQUE 제약

#### NFR-3: 확장성
- 성능 저하 없이 최대 200개 활성 종목 지원
- 주간 데이터 수집이 1시간 내 200 API 호출 처리
- Rate Limiting: KIS API에 초당 최대 20 요청

#### NFR-4: 유지보수성
- 마이그레이션 파일에 upgrade() 및 downgrade() 함수 포함
- 모든 신규 함수에 파라미터/반환 타입 설명이 포함된 docstring
- 코드 변경이 식별된 파일로 제한 (영향 범위 최소화)

---

## 🏗️ 기술 구현 계획

### Phase 1: 데이터베이스 마이그레이션 (1주차)

**작업**:
1. 마이그레이션 생성: `add_product_info_table.py`
2. 마이그레이션 생성: `add_financial_ratios_table.py`
3. 마이그레이션 생성: `deprecate_priority_column.py`
4. 개발 환경에서 마이그레이션 테스트
5. 롤백 계획 수립

**수정/생성 파일**:
- `backend/db/migrations/add_product_info_table.py` (신규)
- `backend/db/migrations/add_financial_ratios_table.py` (신규)
- `backend/db/migrations/deprecate_priority_column.py` (신규)
- `backend/db/models/financial.py` (신규 - SQLAlchemy 모델)

**인수 기준**:
- [ ] 3개 마이그레이션 모두 개발 DB에서 성공적으로 실행
- [ ] 롤백 스크립트 테스트 및 작동 확인
- [ ] 프로덕션 마이그레이션 전 DB 백업 생성

---

### Phase 2: KIS API 통합 (1-2주차)

**작업**:
1. kis_client.py에 `get_financial_ratios()` 구현
2. kis_client.py에 `get_product_info()` 구현
3. 신규 API 메서드 단위 테스트 작성
4. 실제 KIS API로 테스트 (실전 계정)

**수정/생성 파일**:
- `backend/crawlers/kis_client.py` (수정 - 메서드 2개 추가)
- `backend/crawlers/kis_financial_collector.py` (신규)
- `backend/crawlers/kis_product_info_collector.py` (신규)
- `tests/test_kis_client.py` (수정)

**API 명세**:

```python
# TR_ID: FHKST66430300 (재무비율)
async def get_financial_ratios(
    self,
    stock_code: str,
    div_cls_code: str = "0"  # 0: 년, 1: 분기
) -> Dict[str, Any]:
    """
    재무비율 조회

    Returns:
        {
            "rt_cd": "0",
            "output": [
                {
                    "stac_yymm": "202312",
                    "grs": "12.5",  # 매출액 증가율
                    "roe_val": "22.3",  # ROE
                    "eps": "5500",
                    ...
                }
            ]
        }
    """

# TR_ID: CTPF1604R (상품기본조회)
async def get_product_info(self, stock_code: str) -> Dict[str, Any]:
    """
    상품 기본정보 조회

    Returns:
        {
            "rt_cd": "0",
            "output": {
                "prdt_name": "삼성전자",
                "prdt_clsf_name": "전기전자",
                ...
            }
        }
    """
```

**인수 기준**:
- [ ] 두 API 메서드 모두 테스트 종목 코드에 유효한 데이터 반환
- [ ] API 실패에 대한 오류 처리 (타임아웃, 잘못된 응답)
- [ ] Rate Limiting 준수 (초당 최대 20 요청)

---

### Phase 3: 데이터 수집 스케줄러 (2주차)

**작업**:
1. 주간 스케줄로 `kis_financial_collector.py` 생성
2. 주간 스케줄로 `kis_product_info_collector.py` 생성
3. `crawler_scheduler.py`에 스케줄러 등록
4. 로깅 및 오류 추적 추가

**수정/생성 파일**:
- `backend/crawlers/kis_financial_collector.py` (신규)
- `backend/crawlers/kis_product_info_collector.py` (신규)
- `backend/scheduler/crawler_scheduler.py` (수정)

**스케줄러 설정**:
```python
# 일요일 새벽 1시 - 상품정보 수집
scheduler.add_job(
    func=run_async_job,
    args=(collect_product_info,),
    trigger=CronTrigger(day_of_week='sun', hour=1, minute=0),
    id='product_info_weekly'
)

# 일요일 새벽 2시 - 재무비율 수집
scheduler.add_job(
    func=run_async_job,
    args=(collect_financial_ratios,),
    trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
    id='financial_ratios_weekly'
)
```

**인수 기준**:
- [ ] 개발 환경에서 스케줄러가 정시 실행
- [ ] 수집 후 데이터가 DB에 성공적으로 저장
- [ ] API 실패 시 오류 로그 생성
- [ ] 기존 스케줄러 영향 없음

---

### Phase 4: 분석 로직 재설계 (2-3주차)

**작업**:
1. stock_management.py에 `trigger_initial_analysis()` 구현
2. stock_analysis_service.py에 `build_analysis_context_from_db()` 구현
3. 데이터 가용성 섹션 포함하도록 LLM 프롬프트 업데이트
4. 리포트 생성에서 `priority <= 2` 필터 제거
5. 분석 요약 모델에 data_sources_used 추가

**수정 파일**:
- `backend/api/stock_management.py` (초기 분석 트리거 추가)
- `backend/services/stock_analysis_service.py` (DB 기반 컨텍스트 구축)
- `backend/llm/investment_report.py` (적응형 프롬프트)
- `backend/scheduler/crawler_scheduler.py` (priority 필터 제거)
- `backend/db/models/stock_analysis.py` (메타데이터 필드 추가)

**핵심 함수**:

```python
# stock_management.py
async def trigger_initial_analysis(stock_code: str, db: Session):
    """신규 종목 등록 시 즉시 분석 실행"""
    kis_client = get_kis_client()

    # KIS API 호출 (1회만)
    current_price = await kis_client.get_current_price(stock_code)
    product_info = await kis_client.get_product_info(stock_code)
    financial_ratios = await kis_client.get_financial_ratios(stock_code)

    # DB 저장
    save_product_info(db, stock_code, product_info)
    save_financial_ratios(db, stock_code, financial_ratios)

    # 초기 리포트 생성
    await update_stock_analysis_summary(stock_code, db, force_update=True)

# stock_analysis_service.py
async def build_analysis_context_from_db(stock_code: str, db: Session):
    """DB 쿼리만으로 분석 컨텍스트 생성 (API 호출 없음)"""
    # DB 쿼리만 실행
    # ...
    return context
```

**인수 기준**:
- [ ] 신규 종목 등록 시 즉시 분석 트리거
- [ ] 분석이 60초 이내 완료
- [ ] 리포트 생성 시 API 호출 0회 (DB만)
- [ ] 모든 활성 종목이 하루 3회 리포트 수신 (priority 제거)
- [ ] 리포트에 data_sources_used 메타데이터 포함

---

### Phase 5: 프론트엔드 업데이트 (3주차)

**작업**:
1. 종목 관리 UI에서 Priority 드롭다운 제거
2. 분석 리포트 표시에 데이터 소스 배지 추가
3. 리포트 UI에 제한사항 섹션 표시

**수정 파일**:
- `frontend/components/StockManagement.tsx` (priority 필드 제거)
- `frontend/components/AnalysisReport.tsx` (데이터 소스 배지 추가)

**UI 목업**:

**이전 (종목 관리)**:
```
[ 종목 코드 ] [ 종목명 ] [ 우선순위 ▼ 1-5 ] [ 활성화 ✓ ]
```

**이후 (종목 관리)**:
```
[ 종목 코드 ] [ 종목명 ] [ 활성화 ✓ ]
```

**신규 (분석 리포트)**:
```
📊 분석 리포트: 삼성전자 (005930)

데이터 소스:
✅ 시장 데이터  ✅ 투자자 수급  ✅ 재무비율  ❌ 뉴스

⚠️ 제한사항:
- 최근 7일간 뉴스 없음
- 분석은 펀더멘털과 수급 기반
```

**인수 기준**:
- [ ] UI에서 Priority 드롭다운 제거
- [ ] 데이터 소스 배지 올바르게 표시
- [ ] 제한사항이 있을 때 제한사항 섹션 표시

---

### Phase 6: 테스트 및 배포 (4주차)

**테스트 케이스**:

| 테스트 ID | 시나리오 | 예상 결과 | 상태 |
|----------|---------|----------|------|
| TC-001 | 신규 종목 등록 (뉴스 없음) | 60초 이내 분석 표시 | ☐ |
| TC-002 | 신규 종목 등록 (뉴스 있음) | 뉴스 + 펀더멘털 포함 분석 | ☐ |
| TC-003 | 스케줄 리포트 (하루 3회) | 모든 활성 종목 리포트 수신 | ☐ |
| TC-004 | 재무 데이터 수집 | 데이터가 DB에 올바르게 저장 | ☐ |
| TC-005 | 수집 중 API 실패 | 우아한 오류 처리, 로그 생성 | ☐ |
| TC-006 | 재무 데이터 누락 리포트 | 제한사항 명시하여 리포트 생성 | ☐ |
| TC-007 | 50개 종목 배치 리포트 | 5분 이내 완료 | ☐ |

**배포 계획**:
1. **개발 환경**: 배포 + 48시간 모니터링
2. **스테이징**: 배포 + 전체 회귀 테스트
3. **프로덕션**: Blue-Green 배포
   - 50% 트래픽으로 배포
   - 24시간 모니터링
   - 문제 없으면 전체 롤아웃
4. **롤백 계획**: DB 스냅샷 + 코드 되돌리기 준비

**모니터링**:
- 리포트 생성 시간 (5초 초과 시 알림)
- KIS API 오류율 (5% 초과 시 알림)
- 분석 커버리지 (95% 미만 시 알림)
- 사용자 만족도 ("추적 중인 종목" 사용량 추적)

---

## 📊 성공 지표 및 KPI

### 론칭 지표 (론칭 후 1주)

| 지표 | 기준선 | 목표 | 측정 방법 |
|-----|------|------|----------|
| 분석 커버리지 | 60% | 95% | (리포트 보유 종목 / 활성 종목) × 100 |
| 첫 분석까지 평균 시간 | ∞ | < 1분 | Timestamp(첫_리포트) - Timestamp(등록) |
| 종목당 일일 리포트 수 | 0.6 | 2.8 | 총 리포트 / 활성 종목 / 일수 |
| 주간 사용자 등록 수 | 기준선 | +20% | 주당 신규 종목 등록 수 |

### 장기 지표 (1-3개월)

| 지표 | 1개월 | 3개월 | 성공 기준 |
|-----|------|-------|----------|
| 사용자 재방문율 | 기준선 | +15% | 종목 추적하는 월간 활성 사용자 |
| 분석 정확도 | 기준선 | 유지 | 예측 정확도 vs 실제 가격 움직임 |
| 시스템 가동률 | 99.5% | 99.9% | 리포트 생성 성공률 |
| API 비용 | 기준선 | -30% | 일일 총 KIS API 호출 수 |

---

## ⚠️ 리스크 및 완화 방안

### 기술 리스크

| 리스크 | 확률 | 영향도 | 완화 방안 |
|-------|------|--------|----------|
| 재무비율 API 실패 (모의투자 미지원) | 높음 | 높음 | 실전 계정 사용; 우아한 성능 저하 구현 |
| DB 마이그레이션 데이터 손실 | 낮음 | 치명적 | 마이그레이션 전 전체 백업; 롤백 테스트 |
| 성능 저하 (모든 종목 분석) | 중간 | 중간 | 배치 병렬화 구현; 타임아웃 설정 |
| KIS API rate limit 초과 | 낮음 | 중간 | 스케줄러 실행 분산; backoff 구현 |

### 비즈니스 리스크

| 리스크 | 확률 | 영향도 | 완화 방안 |
|-------|------|--------|----------|
| 사용자 혼란 (Priority 제거) | 낮음 | 낮음 | 명확한 UI 메시지; 도움말 문서 |
| 분석 품질 저하 (뉴스 없음) | 중간 | 높음 | 펀더멘털 분석 강점 강조; 데이터 한계 표시 |
| 서버 부하 증가 | 중간 | 중간 | 리소스 사용량 모니터링; 필요 시 확장 |

---

## 🗓️ 타임라인 및 마일스톤

### 4주 전달 계획

**1주차: 기초 작업**
- 1-2일: PRD 최종 확정 + 킥오프
- 3-4일: DB 마이그레이션 + 테스트
- 5일: KIS API 구현

**2주차: 핵심 개발**
- 1-2일: 데이터 수집 스케줄러
- 3-4일: 분석 로직 재설계
- 5일: 통합 테스트

**3주차: 다듬기 및 테스트**
- 1-2일: 프론트엔드 업데이트
- 3-4일: 종단 간 테스트
- 5일: 성능 최적화

**4주차: 론칭**
- 1일: 스테이징 배포
- 2-3일: QA + 버그 수정
- 4일: 프로덕션 배포
- 5일: 모니터링 + 지원

### 마일스톤

| 마일스톤 | 날짜 | 산출물 | 담당자 |
|---------|------|--------|-------|
| PRD 승인 | 2일차 | 본 문서 승인 | PM |
| DB 마이그레이션 완료 | 5일차 | 3개 마이그레이션 테스트 완료 | 백엔드 개발자 |
| KIS API 통합 | 8일차 | 2개 신규 API 메서드 작동 | 백엔드 개발자 |
| 스케줄러 가동 | 10일차 | 주간 데이터 수집 중 | 백엔드 개발자 |
| 분석 재설계 완료 | 13일차 | 뉴스 독립 분석 | 백엔드 개발자 |
| 프론트엔드 업데이트 | 16일차 | UI에서 Priority 제거 | 프론트엔드 개발자 |
| 스테이징 배포 | 18일차 | 스테이징 전체 시스템 | DevOps |
| 프로덕션 론칭 | 23일차 | 100% 사용자 대상 라이브 | DevOps |

---

## 📚 부록

### 부록 A: 데이터베이스 스키마 변경

**신규 테이블**:
1. `product_info` - 종목 상품 메타데이터
2. `financial_ratios` - 재무 성과 지표

**수정 테이블**:
1. `stocks` - Priority deprecated (1로 설정, 하위 호환성 유지)

**추가 인덱스**:
- `idx_financial_ratios_stock_code` on financial_ratios(stock_code)
- `idx_financial_ratios_stock_stac` on financial_ratios(stock_code, stac_yymm DESC)
- `idx_product_info_stock_code` on product_info(stock_code)

### 부록 B: 수정된 API 엔드포인트

**수정**:
- `POST /api/admin/stocks` - 이제 즉시 분석 트리거
- `GET /api/stocks/{stock_code}` - data_sources_used 포함 분석 반환

**변경 없음**:
- 모든 기존 엔드포인트 하위 호환성 유지

### 부록 C: 참고 문서

- Mary의 프로젝트 브리프: `docs/stock-analysis-redesign-brief.md`
- KIS API 문서: 재무비율 [v1_국내주식-080], 상품기본조회 [v1_국내주식-029]
- 현재 코드베이스: `/Users/young/ai-work/craveny/backend/`

---

## ✅ 승인 및 서명

### 승인 체크리스트

- [ ] **제품 관리자** (John): PRD 완전하고 정확함
- [ ] **비즈니스 애널리스트** (Mary): 요구사항이 브리프와 일치
- [ ] **기술 리드**: 기술적 실현 가능성 확인
- [ ] **백엔드 개발자**: 구현 계획 검토 완료
- [ ] **프론트엔드 개발자**: UI 변경 사항 이해
- [ ] **QA 리드**: 테스트 계획 적절함
- [ ] **DevOps**: 배포 계획 실행 가능

### 미결정 사항

1. **Priority 제거**: 컬럼 완전 삭제 vs 1로 설정? → **결정**: 1로 설정 (더 안전, 가역적)
2. **재무 데이터 수집 주기**: 주간 vs 월간? → **결정**: 주간 (더 최신 데이터)
3. **리포트 생성 빈도**: 현행 유지 vs 변경? → **결정**: 현행 유지 하루 3회 (변경 불필요)

---

**문서 상태**: 검토 준비 완료
**다음 조치**: 이해관계자 검토 회의 일정 잡기
**목표 승인일**: 2025-11-18

---

*PRD 작성: John (Product Manager)*
*기반 리서치: Mary (Business Analyst)*
*문서 버전: 1.0*
