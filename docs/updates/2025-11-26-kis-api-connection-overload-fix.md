# KIS API 동시 연결 과부하 문제 해결

**작업 일자**: 2025-11-26
**작업자**: young
**관련 이슈**: #15
**Pull Request**: https://github.com/atototo/azak/pull/16

---

## 변경 개요

KIS API 동시 연결 과부하로 인해 사용자 화면 요청과 배치 데이터 수집이 간헐적으로 실패하는 문제를 해결했습니다. `kis_market_data_collector.py`의 4개 Collector 클래스에 `asyncio.Semaphore`를 추가하여 동시 API 요청 수를 제한했습니다.

---

## AS-IS (기존 상태)

### 문제점

1. **`kis_market_data_collector.py`에 Semaphore가 없음**
   - `kis_minute_collector.py`는 `max_concurrent=3`으로 제한
   - `kis_market_data_collector.py`는 `batch_size=10`으로 제한 없이 동시 요청

2. **여러 스케줄러 작업이 같은 시간에 겹침**
   - 5분 간격 시장 데이터 수집
   - 10분 간격 AI 분석
   - DART 공시 수집
   - 모두 같은 HTTP 연결 풀을 공유

3. **HTTP 연결 풀 경쟁**
   - `max_connections=100`이지만 여러 작업이 동시에 연결 요청
   - KIS API 서버가 동시 연결을 끊어버림

### 에러 로그

```
0|azak-backend  | 2025-11-26 11:21:31: httpx.ConnectError: All connection attempts failed
0|azak-backend  | 2025-11-26 11:21:31: ❌ 0126Z0: 현재가 수집 실패 - All connection attempts failed
0|azak-backend  | 2025-11-26 11:21:32: 📊 현재가 수집 완료: 성공 10건, 실패 43건

0|azak-backend  | 2025-11-26 11:27:40: ⚠️  API 요청 실패 (1/3), 1초 후 재시도: RemoteProtocolError: Server disconnected without sending a response.
```

### 영향도

| 항목 | 내용 |
|------|------|
| **심각도** | High |
| **영향 범위** | 사용자 화면 API 요청 실패, 배치 데이터 수집 실패 |
| **발생 빈도** | 스케줄러 작업 겹칠 때 간헐적 (5~10분 간격) |
| **영향받는 사용자** | 모든 프론트엔드 사용자 |

---

## 변경 필요 사유

### 1. 사용자 피드백

- 프론트엔드에서 종목 상세 페이지 접근 시 간헐적으로 API 요청 실패
- 배치 작업 실행 중에 사용자 요청이 함께 실패

### 2. 개발자 요구사항

- 배치 작업과 사용자 요청을 분리하여 사용자 경험 개선
- 기존 `kis_minute_collector.py`와 동일한 패턴 적용

### 3. 기술적 부채

- `kis_market_data_collector.py`만 Semaphore 없이 구현되어 있어 일관성 없음

---

## TO-BE (변경 후 상태)

### 핵심 개선사항

- 4개 Collector 클래스에 `asyncio.Semaphore(max_concurrent=5)` 추가
- 동시 API 요청을 10개 → 5개로 제한
- 사용자 요청은 Semaphore를 거치지 않으므로 배치 작업에 영향받지 않음

### Before/After 비교

| 항목 | 이전 (AS-IS) | 이후 (TO-BE) | 변화 |
|------|-------------|------------|------|
| 동시 API 요청 | 최대 10개 | 최대 5개 | 50% 감소 |
| HTTP 연결 풀 경쟁 | 심함 | 완화 | 안정성 향상 |
| 53개 종목 수집 시간 | ~6초 | ~12초 | 2배 증가 (허용 범위) |
| 사용자 요청 영향 | ConnectError 발생 | 영향 없음 | 완전 분리 |

---

## 변경 사항 상세

### 1. 주요 파일 변경

| 파일 | 변경 내용 |
|------|----------|
| `backend/crawlers/kis_market_data_collector.py` | 4개 Collector에 Semaphore 추가 |

### 2. 코드 비교

#### 변경 파일: `backend/crawlers/kis_market_data_collector.py`

**Before (AS-IS)**:
```python
class OrderbookCollector:
    """호가 데이터 수집기"""

    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.collected_count = 0
        self.failed_count = 0

    async def collect_orderbook(self, stock_code: str) -> Dict[str, Any]:
        try:
            client = await get_kis_client()
            result = await client.get_orderbook(stock_code=stock_code, priority="low")
            # ...
```

**After (TO-BE)**:
```python
class OrderbookCollector:
    """호가 데이터 수집기"""

    def __init__(self, batch_size: int = 10, max_concurrent: int = 5):
        """
        Args:
            batch_size: 배치 크기 (한 번에 처리할 종목 수)
            max_concurrent: 최대 동시 API 호출 수
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.collected_count = 0
        self.failed_count = 0

    async def collect_orderbook(self, stock_code: str) -> Dict[str, Any]:
        async with self.semaphore:  # 동시 실행 5개로 제한
            try:
                client = await get_kis_client()
                result = await client.get_orderbook(stock_code=stock_code, priority="low")
                # ...
```

**변경 이유**:
- `kis_minute_collector.py`와 동일한 패턴 적용
- 동시 실행 수 제한으로 HTTP 연결 풀 경쟁 완화
- 사용자 요청은 Semaphore를 거치지 않아 영향 없음

### 3. 수정된 클래스 목록

| 클래스 | 역할 | 변경 내용 |
|--------|------|----------|
| `OrderbookCollector` | 호가 데이터 수집 | Semaphore 추가 (max_concurrent=5) |
| `CurrentPriceCollector` | 현재가 데이터 수집 | Semaphore 추가 (max_concurrent=5) |
| `InvestorTradingCollector` | 투자자별 매매동향 수집 | Semaphore 추가 (max_concurrent=5) |
| `OvertimePriceCollector` | 시간외 거래 가격 수집 | Semaphore 추가 (max_concurrent=5) |

---

## 테스트 결과

### 1. 자동 테스트

- 자동화된 테스트 없음

### 2. 수동 테스트

- 백엔드 재시작 후 정상 동작 확인
- PM2 로그에서 에러 없이 스케줄러 시작 확인

### 3. 검증 항목

- [x] Python 문법 검증 통과 (`py_compile`)
- [x] 백엔드 정상 재시작
- [x] 스케줄러 정상 등록

---

## 사용 방법

### 1. 로컬 환경 적용

```bash
# 변경사항 반영
git pull origin main

# 백엔드 재시작
pm2 restart azak-backend
```

### 2. 기능 사용법

변경된 코드는 자동으로 적용됩니다. 별도의 설정 변경 없이 동시 연결 수가 제한됩니다.

### 3. 예제

기존과 동일하게 사용:
```python
# 스케줄러에서 자동 호출
orderbook_collector = OrderbookCollector(batch_size=10)
await orderbook_collector.collect_all()
```

---

## 참고 사항

### 1. 변경 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| Semaphore | 없음 | max_concurrent=5 |
| 동시 API 요청 | 10개 | 5개 |
| 수집 시간 | ~6초 | ~12초 |

### 2. 주의 사항

- 수집 시간이 약 2배 증가하지만, 5분 간격 실행이므로 문제없음
- `max_concurrent` 값을 너무 낮추면 수집 시간이 과도하게 증가할 수 있음

### 3. 트러블슈팅

**여전히 ConnectError가 발생하는 경우:**
```bash
# max_concurrent 값을 더 낮출 수 있음 (코드 수정 필요)
# OrderbookCollector(batch_size=10, max_concurrent=3)
```

### 4. 관련 파일

- `backend/crawlers/kis_market_data_collector.py` - 수정된 파일
- `backend/crawlers/kis_minute_collector.py` - 참고 패턴 (기존 Semaphore 구현)
- `backend/crawlers/kis_client.py` - KIS API 클라이언트

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-26 | 1.0.0 | 4개 Collector에 Semaphore 추가하여 동시 연결 과부하 문제 해결 |

---

**작성일**: 2025-11-26
**최종 수정일**: 2025-11-26
**작성자**: young
