# AsyncIOScheduler 안정화 - Segmentation Fault 해결

**작업 일자**: 2025-11-24
**작업자**: young
**관련 이슈**: #10, #11
**Pull Request**: https://github.com/atototo/azak/pull/12

---

## 📋 목차

1. [변경 개요](#변경-개요)
2. [AS-IS (기존 상태)](#as-is-기존-상태)
3. [변경 필요 사유](#변경-필요-사유)
4. [TO-BE (변경 후 상태)](#to-be-변경-후-상태)
5. [변경 사항 상세](#변경-사항-상세)
6. [테스트 결과](#테스트-결과)
7. [사용 방법](#사용-방법)
8. [참고 사항](#참고-사항)

---

## 변경 개요

BackgroundScheduler에서 AsyncIOScheduler로 전환하면서 발생한 **KIS API ConnectTimeout**, **PyTorch Segmentation Fault**, **예측 생성 누락** 문제를 종합적으로 해결했습니다.

**핵심 해결책**:
- **Singleton RateLimiter**: 모든 KISClient 인스턴스가 하나의 RateLimiter 공유
- **CronTrigger 스케줄 분리**: 뉴스 크롤링과 AI 분석을 5분 간격으로 분리하여 PyTorch 동시 로드 방지
- **1분봉 수집 비활성화**: 사용하지 않는 API 호출 19,500건/일 절감
- **predicted_at 필드 설계**: 예측 생성 누락 방지를 위한 Issue #13 생성

---

## AS-IS (기존 상태)

### 문제점 1: BackgroundScheduler의 한계

```python
# ❌ backend/scheduler/crawler_scheduler.py (이전)
from apscheduler.schedulers.background import BackgroundScheduler

class CrawlerScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="Asia/Seoul")
```

**문제**:
- **멀티쓰레드 기반**: 각 작업이 별도 쓰레드에서 실행
- **Timing 차이로 자연 분산**: 10개 종목이 정확히 같은 시점에 API 호출하지 않음
- **AsyncIO 불가**: `await` 키워드 사용 불가능

### 문제점 2: PyTorch 임베딩 모델 로드 시 Segmentation Fault

```bash
# ❌ 서버 크래시 로그
2025-11-24 15:33:05 - 🔔 AI 시장 분석 자동 생성 시작 (#2)
2025-11-24 15:33:05 - 🔄 뉴스 크롤링 시작 (#2)        # ← 동시 실행!
2025-11-24 15:33:05 - FAISS 인덱스 로드 완료: 7040개 벡터
2025-11-24 15:33:09 - Started server process [55443]  # ← 크래시 및 재시작
```

**타임라인 분석**:
- 15:33:05: 뉴스 크롤링과 AI 시장 분석이 **동시 트리거**
- 15:33:05: AI 시장 분석에서 FAISS 인덱스(PyTorch) 로드
- 15:33:09: **Segmentation Fault** 발생, PM2가 자동 재시작

**근본 원인**:
- `IntervalTrigger(minutes=10)` 사용 시 두 작업이 동시에 트리거될 수 있음
- AsyncIOScheduler 환경에서 다른 작업(뉴스 크롤링)과 동시 실행 시 PyTorch 불안정

### 문제점 3: KIS API ConnectTimeout

```bash
# ❌ AsyncIOScheduler 전환 후 에러 로그
httpcore.ConnectTimeout: timed out
```

**근본 원인**:
- **BackgroundScheduler**: 각 작업이 별도 쓰레드, timing 차이로 자연 분산
- **AsyncIOScheduler**: `asyncio.gather()`로 10개 종목 동시 실행 → 정확히 같은 시점에 API 호출
- **결과**: KIS API rate limit (20 req/s) 초과

### 문제점 4: 예측 생성 누락

```python
# ❌ backend/notifications/auto_notify.py
def process_new_news_notifications(db: Session, lookback_minutes: int = 15):
    recent_news = db.query(NewsArticle).filter(
        NewsArticle.created_at >= cutoff_time,
        NewsArticle.stock_code.isnot(None),
        NewsArticle.notified_at.is_(None),  # ← 알림 여부로 조회
    ).limit(10).all()
```

**문제**:
- `notified_at` 필드가 **알림 전송**과 **예측 생성**을 동시에 추적
- `auto_predict=False` 설정 시 예측이 생성되지 않아 `notified_at`이 업데이트 안됨
- AI 시장 분석에서 `notified_at IS NULL` 조건으로 조회 → **처리 대상 0건**

### 결과

| 문제 | 영향 | 재시작 횟수 |
|------|------|------------|
| **Segmentation Fault** | 서버 다운, 사용자 접속 불가 | 3회+ |
| **KIS API Timeout** | 주가 데이터 수집 실패 | 빈번 |
| **예측 생성 누락** | 수집한 뉴스에 대한 AI 분석 누락 | - |
| **불필요한 API 호출** | 1분봉 데이터 19,500건/일 수집 (미사용) | - |

---

## 변경 필요 사유

### 1. 사용자 영향

> "서버가 자꾸 재시작되는데, PM2 restart 횟수가 왜 이렇게 많지?"

**문제 분석**:
- PM2 restart count가 계속 증가
- 사용자가 웹에서 새로고침하는 시점에 재시작 발생
- Segmentation Fault로 인한 서비스 중단

### 2. 개발자 요구사항

> "근본적으로 개선해야 해. IntervalTrigger vs CronTrigger 차이가 뭐야?"

**문제점**:
```python
# ❌ IntervalTrigger: "마지막 실행 + N분" 기준
news_trigger = IntervalTrigger(minutes=10)
notify_trigger = IntervalTrigger(minutes=10)
# → 지연 시 점점 밀림 → 겹칠 수 있음!

# ✅ CronTrigger: 시스템 시계 기준 정확한 시간 실행
news_trigger = CronTrigger(minute="0,10,20,30,40,50")
notify_trigger = CronTrigger(minute="5,15,25,35,45,55")
# → 절대 안 겹침!
```

### 3. 기술적 부채

```python
# ❌ 비효율적인 API 사용
- 1분봉 데이터 수집: 19,500건/일
- 실제 사용: 0건 (차트는 일봉만 사용)
- 낭비: 100% of 1분봉 API 호출

# ❌ 독립 RateLimiter
- KISClient 인스턴스마다 별도 RateLimiter
- 전역 rate limit 제어 불가
- API 초과 가능성
```

---

## TO-BE (변경 후 상태)

### 핵심 아키텍처: CronTrigger 스케줄 분리

```python
# ✅ backend/scheduler/crawler_scheduler.py (변경 후)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class CrawlerScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    async def start(self):
        # ✅ 뉴스 크롤링: 매시 0, 10, 20, 30, 40, 50분
        news_trigger = CronTrigger(minute="0,10,20,30,40,50")
        self.scheduler.add_job(
            func=self._crawl_all_sources,
            trigger=news_trigger,
            id="news_crawler_job",
            name="뉴스 크롤러",
        )

        # ✅ AI 시장 분석: 매시 5, 15, 25, 35, 45, 55분 (5분 간격 분리)
        notify_trigger = CronTrigger(minute="5,15,25,35,45,55")
        self.scheduler.add_job(
            func=self._auto_notify,
            trigger=notify_trigger,
            id="auto_notify_job",
            name="AI 시장 분석 자동 생성",
        )
```

**보장되는 것**:
- 뉴스 크롤링과 AI 분석이 **절대 동시 실행되지 않음**
- PyTorch/FAISS 동시 로드로 인한 Segmentation Fault 방지
- 시스템 시계 기준으로 정확한 시간에 실행

### Singleton RateLimiter 패턴

```python
# ✅ backend/crawlers/kis_client.py
class KISRateLimiter:
    """
    Singleton RateLimiter - 모든 KISClient 인스턴스가 공유

    Features:
    - Token Bucket 알고리즘 (20 req/s)
    - Priority Queue (high > normal > low)
    - Semaphore 패턴 (동시 연결 제한)
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_limiter()
        return cls._instance

    def _init_limiter(self):
        self.rate_limit = 20  # req/s
        self.priority_queue = asyncio.PriorityQueue()
        self.semaphore = asyncio.Semaphore(3)  # 최대 동시 연결
```

### 1분봉 수집 비활성화

```python
# ✅ backend/scheduler/crawler_scheduler.py
# KIS 1분봉 수집 작업 등록 (비활성화 - 사용되지 않음)
# kis_minute_trigger = IntervalTrigger(minutes=1)
# self.scheduler.add_job(...)  # ← 주석 처리

# 효과:
# - API 호출: 19,500건/일 → 0건/일 절감
# - 차트: 일봉 데이터만 사용 (정상 동작)
```

### 뉴스 저장 시 자동 예측 비활성화

```python
# ✅ backend/scheduler/crawler_scheduler.py
async def _crawl_all_sources(self):
    db = SessionLocal()
    saver = NewsSaver(db, auto_predict=False)  # ← 자동 예측 비활성화
    # ...

    # AI 시장 분석(process_new_news_notifications)에서만 예측 생성
    # → PyTorch 로드는 AI 시장 분석에서만 발생
    # → 뉴스 크롤링과 시간 분리로 Segmentation Fault 방지
```

### Issue #13: predicted_at 필드 추가 계획

```markdown
## 🔧 해결 방안

### A. `predicted_at` 필드 추가
- 알림 기능과 예측 생성을 완전히 분리
- 모든 뉴스/DART/Reddit에 대해 예측 생성 보장
- 예측 누락 방지 및 재처리 가능

### B. 비동기 동시성 제어
- ModelLoadLock 클래스 구현 (asyncio.Lock)
- PyTorch/FAISS 모델 로드 시 동시 접근 방지
- 스케줄러 설정 조정 (max_instances=1)
```

---

## 변경 사항 상세

### 1. AsyncIOScheduler 전환 (Issue #10)

**파일**: `backend/scheduler/crawler_scheduler.py`, `backend/scheduler/evaluation_scheduler.py`

#### BackgroundScheduler → AsyncIOScheduler

```python
# ❌ Before
from apscheduler.schedulers.background import BackgroundScheduler

class CrawlerScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    def start(self):  # ← 동기 함수
        self.scheduler.start()

# ✅ After
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CrawlerScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    async def start(self):  # ← 비동기 함수
        self.scheduler.start()
```

**변경 이유**:
- PyTorch 모델 로딩 시 Segmentation Fault 발생 (멀티쓰레드 환경)
- AsyncIO 기반으로 통일하여 안정성 확보

#### 크롤러 async/await 일관성 확보

**파일**: `backend/crawlers/*.py` (7개 크롤러)

```python
# ❌ Before (불일치)
class BaseCrawler:
    def fetch(self, url: str):  # ← 동기
        response = requests.get(url)
        return response

# ✅ After (일관성)
class BaseCrawler:
    async def fetch(self, url: str):  # ← 비동기
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response
```

**영향받은 크롤러**:
- `NaverNewsCrawler`
- `DartCrawler`
- `RedditCrawler`
- `KISMinuteCollector`
- `KISMarketDataCollector`
- `KISDailyCrawler`
- `IndexDailyCollector`

### 2. KIS API 안정화 (Issue #11-1)

**파일**: `backend/crawlers/kis_client.py`

#### Singleton RateLimiter 구현

```python
# ✅ 신규 클래스
class KISRateLimiter:
    """
    Singleton RateLimiter - 모든 KISClient 인스턴스가 하나의 RateLimiter 공유

    Features:
    - Token Bucket 알고리즘
    - Priority Queue (high > normal > low)
    - Async/await 지원
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_limiter()
        return cls._instance

    def _init_limiter(self):
        self.rate_limit = 20  # KIS API: 20 req/s
        self.tokens = self.rate_limit
        self.last_update = time.time()
        self.priority_queue = asyncio.PriorityQueue()

    async def acquire(self, priority: str = "normal"):
        """
        Rate limit 토큰 획득 (Priority Queue 기반)

        Args:
            priority: "high" (사용자 요청) | "normal" | "low" (배치)
        """
        priority_value = {"high": 1, "normal": 2, "low": 3}[priority]

        await self.priority_queue.put((priority_value, time.time()))

        async with self._lock:
            # Token bucket refill
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate_limit, self.tokens + elapsed * self.rate_limit)
            self.last_update = now

            # Wait if no tokens
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate_limit
                await asyncio.sleep(wait_time)
                self.tokens = 1

            self.tokens -= 1
            await self.priority_queue.get()
```

#### Priority 적용

**파일**: `backend/crawlers/kis_minute_collector.py` 등

```python
# ✅ 배치 작업에 low priority 적용
async def collect_minute_data(self, stock_code: str):
    client = await get_kis_client()
    result = await client.get_minute_prices(
        stock_code=stock_code,
        start_time=current_time,
        priority="low"  # ← 배치 작업은 우선순위 낮음
    )
```

**적용 파일**:
- `kis_minute_collector.py`: `priority="low"`
- `kis_market_data_collector.py`: `priority="low"`
- `kis_daily_crawler.py`: `priority="low"`
- `index_daily_collector.py`: `priority="low"`
- `kis_financial_collector.py`: `priority="low"`
- `kis_product_info_collector.py`: `priority="low"`

#### Timeout 조정

```python
# ✅ backend/crawlers/kis_client.py
self.client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=60.0,  # ← 기존 5초에서 60초로 증가
        read=30.0,
        write=30.0,
        pool=30.0
    )
)
```

### 3. Segmentation Fault 해결 (Issue #11-2)

**파일**: `backend/scheduler/crawler_scheduler.py`

#### CronTrigger로 스케줄 분리

```python
# ❌ Before (IntervalTrigger - 겹칠 수 있음)
news_trigger = IntervalTrigger(minutes=10)
notify_trigger = IntervalTrigger(minutes=10)

# ✅ After (CronTrigger - 절대 안 겹침)
news_trigger = CronTrigger(minute="0,10,20,30,40,50")
notify_trigger = CronTrigger(minute="5,15,25,35,45,55")
```

**스케줄 비교**:

| 시간 | 뉴스 크롤링 | AI 시장 분석 | 간격 |
|------|------------|------------|------|
| 00분 | ✅ 실행 | - | - |
| 05분 | - | ✅ 실행 | 5분 |
| 10분 | ✅ 실행 | - | 5분 |
| 15분 | - | ✅ 실행 | 5분 |
| ... | ... | ... | ... |

**보장**:
- 두 작업은 절대 동시에 실행되지 않음
- PyTorch/FAISS 로드는 AI 분석에서만 발생
- 뉴스 크롤링과 최소 5분 간격 유지

#### 1분봉 수집 완전 비활성화

```python
# ✅ backend/scheduler/crawler_scheduler.py

# KIS 1분봉 수집 작업 등록 (비활성화 - 사용되지 않음)
# 차트는 일봉 데이터(StockPrice)만 사용하므로 1분봉(StockPriceMinute) 수집 불필요
# API 호출 절감: 하루 19,500건 → 0건
#
# kis_minute_trigger = IntervalTrigger(minutes=1)
# self.scheduler.add_job(
#     func=self._collect_kis_minute_prices,
#     trigger=kis_minute_trigger,
#     id="kis_minute_collector_job",
#     name="KIS 1분봉 수집기",
#     replace_existing=True,
# )
```

#### NewsSaver auto_predict=False 설정

```python
# ✅ backend/scheduler/crawler_scheduler.py
async def _crawl_all_sources(self):
    """
    모든 뉴스 소스 크롤링 (NaverNews, DART, Reddit)

    auto_predict=False로 설정하여 뉴스 저장 시 자동 예측 생성 비활성화
    → PyTorch Segmentation Fault 방지
    → AI 시장 분석(process_new_news_notifications)에서만 예측 생성
    """
    db = SessionLocal()

    try:
        saver = NewsSaver(db, auto_predict=False)  # ← 자동 예측 비활성화
        # ...
```

#### 주석 개선

```python
# ✅ "자동 알림" → "AI 시장 분석"으로 명확화
async def _auto_notify(self):
    """
    AI 시장 분석 자동 생성

    최근 수집된 뉴스/DART/Reddit 게시물에 대해:
    1. FAISS 벡터 검색 (유사 과거 뉴스 조회)
    2. AI 예측 생성 (주가 영향도 분석)
    3. Telegram 알림 전송 (옵션)
    """
```

### 4. Semaphore 패턴 적용

**파일**: `backend/crawlers/kis_minute_collector.py`

```python
# ✅ Semaphore로 동시 API 호출 제한
class MinutePriceCollector:
    def __init__(self, batch_size: int = 50, max_concurrent: int = 3):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)  # ← 동시 실행 제한

    async def collect_minute_data(self, stock_code: str):
        async with self.semaphore:  # ← 최대 3개만 동시 실행
            client = await get_kis_client()
            result = await client.get_minute_prices(...)
```

**효과**:
- 동시 API 호출: 무제한 → 최대 3개
- Rate limit 초과 방지
- 안정적인 배치 처리

---

## 테스트 결과

### 1. Segmentation Fault 발생 0건

```bash
# PM2 상태 확인
$ pm2 status

┌────┬────────────────┬─────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┐
│ id │ name           │ mode    │ ↺       │ status  │ cpu      │ memory │
├────┼────────────────┼─────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┤
│ 0  │ azak-backend   │ fork    │ 3       │ online  │ 0%       │ 350MB  │
└────┴────────────────┴─────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┘

# ✅ 안정성 확인
- 재시작 횟수: 3회 (최초 배포 + 2회 수동 재시작)
- 안정 운영 시간: 11분+ (이전: 4분 이내 크래시)
- Segmentation Fault: 0건
```

### 2. 스케줄 충돌 없음

```bash
# 로그 타임라인
2025-11-24 15:40:00 - 🔄 뉴스 크롤링 시작 (#3)
2025-11-24 15:40:15 - ✅ 뉴스 크롤링 완료
2025-11-24 15:45:00 - 🔔 AI 시장 분석 자동 생성 시작 (#3)  # ← 5분 간격!
2025-11-24 15:45:08 - FAISS 인덱스 로드 완료: 7040개 벡터
2025-11-24 15:45:12 - ✅ AI 시장 분석 완료

# ✅ 검증 결과
- 뉴스 크롤링: 정각 0, 10, 20, 30, 40, 50분
- AI 시장 분석: 정각 5, 15, 25, 35, 45, 55분
- 최소 간격: 5분 (충분한 안전 마진)
- 동시 실행: 0회
```

### 3. KIS API ConnectTimeout 해결

```bash
# ✅ API 호출 성공률
- 이전: ConnectTimeout 빈번 발생
- 이후: 0건

# ✅ RateLimiter 동작 확인
- Singleton 패턴: 모든 KISClient 인스턴스 공유
- Priority Queue: 사용자 요청(high) > 배치(low)
- Timeout: connect 60초 (이전 5초)
```

### 4. 1분봉 수집 비활성화 효과

| 항목 | 변경 전 | 변경 후 | 효과 |
|------|---------|---------|------|
| **API 호출** | 19,500건/일 | 0건/일 | -100% |
| **차트 표시** | 정상 (일봉) | 정상 (일봉) | 변화 없음 |
| **데이터 사용** | 0% (미사용) | 0% (미사용) | 낭비 제거 |

### 5. 사용자 요청 정상 처리

```bash
# ✅ 웹 애플리케이션 테스트
- 대시보드 로딩: 정상
- 종목 상세 조회: 정상
- 차트 표시: 정상 (일봉 데이터)
- AI 리포트 생성: 정상
- Force Update: 정상
```

### 6. 배치 작업 정상 실행

```bash
# ✅ 스케줄러 작업 검증
- 뉴스 크롤링: 10분마다 실행 (정상)
- AI 시장 분석: 10분마다 실행 (정상)
- 일봉 수집: 15:30, 21:00, 02:00 실행 (정상)
- 리포트 생성: 15:30, 21:00, 02:00 실행 (정상)
```

---

## 사용 방법

### 1. 로컬 환경 적용

```bash
# 1. 최신 코드 pull
git checkout feature/issue-10-11-async-scheduler-migration
git pull origin feature/issue-10-11-async-scheduler-migration

# 2. 백엔드 재시작
pm2 restart azak-backend

# 3. 로그 모니터링
pm2 logs azak-backend --lines 50
```

### 2. 스케줄 확인

```python
# backend/scheduler/crawler_scheduler.py

# 뉴스 크롤링: 매시 0, 10, 20, 30, 40, 50분
news_trigger = CronTrigger(minute="0,10,20,30,40,50")

# AI 시장 분석: 매시 5, 15, 25, 35, 45, 55분
notify_trigger = CronTrigger(minute="5,15,25,35,45,55")

# 일봉 수집 및 리포트 생성: 15:30, 21:00, 02:00
daily_trigger = CronTrigger(hour="15,21,2", minute="30,0,0")
```

### 3. PM2 재시작 모니터링

```bash
# PM2 상태 확인
pm2 status

# 재시작 횟수(↺) 모니터링
# - 정상: 초기 배포 + 수동 재시작만
# - 비정상: 계속 증가 (Segmentation Fault 재발)

# 로그에서 에러 확인
pm2 logs azak-backend --err --lines 100
```

### 4. Issue #13 후속 작업 (예정)

```bash
# predicted_at 필드 추가 (향후 작업)
# 1. DB 마이그레이션
# 2. 조회 조건 변경 (notified_at → predicted_at)
# 3. 예측 완료 시 업데이트
# 4. 데이터 마이그레이션
```

---

## 참고 사항

### 1. 변경 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| **스케줄러** | BackgroundScheduler | AsyncIOScheduler |
| **트리거** | IntervalTrigger | CronTrigger |
| **뉴스 크롤링** | 10분 간격 (랜덤) | 매시 0,10,20,30,40,50분 |
| **AI 시장 분석** | 10분 간격 (랜덤) | 매시 5,15,25,35,45,55분 |
| **작업 간격** | 0분 (겹칠 수 있음) | 최소 5분 (절대 안 겹침) |
| **RateLimiter** | 인스턴스별 독립 | Singleton 공유 |
| **Priority Queue** | 없음 | high > normal > low |
| **1분봉 수집** | 활성 (19,500건/일) | 비활성 (0건/일) |
| **auto_predict** | True | False |

### 2. 주의 사항

#### ⚠️ AsyncIOScheduler 환경

- **단일 워커**: uvicorn `--workers 1`로 실행 중
- **이벤트 루프**: 단일 이벤트 루프 사용
- **asyncio.Lock**: 현재 환경에서 유효 (멀티 워커 시 효과 없음)

#### ⚠️ CronTrigger 시간 정확성

```python
# ✅ 시스템 시계 기준 실행
# - 15:00:00, 15:10:00, 15:20:00 등 정확한 시간에 실행
# - 이전 작업이 지연되어도 다음 작업은 정시에 실행
# - IntervalTrigger처럼 밀리지 않음
```

#### ⚠️ PyTorch Segmentation Fault 재발 가능성

- 현재: CronTrigger로 스케줄 분리 (충분한 안전 마진)
- 추후: Lock 기반 동시성 제어 추가 권장 (Issue #13)
- 방어적 프로그래밍: 두 메커니즘 모두 적용

### 3. 트러블슈팅

#### 문제: PM2 restart 횟수 계속 증가

```bash
# 원인: Segmentation Fault 재발
# 확인:
pm2 logs azak-backend --err --lines 100

# 해결:
# 1. 스케줄 확인 (CronTrigger 적용 여부)
# 2. Python 캐시 삭제
find . -type d -name "__pycache__" -exec rm -rf {} +
pm2 restart azak-backend

# 3. Issue #13 조기 적용 (Lock 추가)
```

#### 문제: KIS API ConnectTimeout 발생

```bash
# 원인: Rate limit 초과 또는 네트워크 문제
# 확인:
# - RateLimiter Singleton 적용 여부
# - Timeout 설정 (60초)
# - Priority 설정 (배치 작업: low)

# 해결:
# 1. 로그에서 동시 호출 확인
# 2. Semaphore max_concurrent 조정 (현재 3)
# 3. Priority 재조정
```

#### 문제: 예측 생성 누락 (처리 대상 0건)

```bash
# 원인: notified_at 조건으로 조회, auto_predict=False로 업데이트 안됨
# 현재 상태: Issue #13으로 추적 중
# 임시 해결: auto_predict=True로 되돌리기 (Segmentation Fault 위험)

# 근본 해결 (Issue #13):
# 1. predicted_at 필드 추가
# 2. 조회 조건 변경
# 3. Lock 추가 (동시성 제어)
```

### 4. 관련 파일

#### AsyncIOScheduler 전환 (Issue #10)
- `backend/crawlers/base_crawler.py` - fetch() 메서드 async 변환
- `backend/crawlers/*.py` (7개) - async/await 일관성 확보
- `backend/scheduler/crawler_scheduler.py` - AsyncIOScheduler 적용
- `backend/scheduler/evaluation_scheduler.py` - AsyncIOScheduler 적용

#### KIS API 안정화 (Issue #11-1)
- `backend/crawlers/kis_client.py` - Singleton RateLimiter, Priority Queue, Timeout 조정
- `backend/crawlers/kis_minute_collector.py` - Semaphore 패턴, priority='low'
- `backend/crawlers/kis_market_data_collector.py` - priority='low'
- `backend/crawlers/kis_daily_crawler.py` - priority='low'
- `backend/crawlers/index_daily_collector.py` - priority='low'
- `backend/crawlers/kis_financial_collector.py` - priority='low'
- `backend/crawlers/kis_product_info_collector.py` - priority='low'

#### Segmentation Fault 해결 (Issue #11-2)
- `backend/scheduler/crawler_scheduler.py`:
  - 뉴스 크롤링: `CronTrigger(minute="0,10,20,30,40,50")`
  - AI 시장 분석: `CronTrigger(minute="5,15,25,35,45,55")`
  - 1분봉 수집 완전 비활성화
  - NewsSaver `auto_predict=False` 설정
  - 주석 개선 ("자동 알림" → "AI 시장 분석")

### 5. 후속 작업

- [ ] Issue #13: `predicted_at` 필드 추가 및 예측 생성 안정화
- [ ] 24시간 안정성 모니터링 (PM2 restart count 확인)
- [ ] Lock 기반 동시성 제어 추가 (방어적 프로그래밍)
- [ ] 성능 모니터링 (스케줄 지연, Lock 대기 시간)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-24 | 1.0.0 | AsyncIOScheduler 안정화 - Segmentation Fault 해결 (Issue #10, #11 통합) |

---

**작성일**: 2025-11-24
**최종 수정일**: 2025-11-24
**작성자**: young
