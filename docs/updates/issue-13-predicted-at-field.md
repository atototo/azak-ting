# Issue #13: predicted_at 필드 추가 및 예측 처리 안정화

> **완료일**: 2025-11-24
> **PR**: [#14](https://github.com/atototo/azak/pull/14)
> **상태**: ✅ 완료

## 📋 개요

뉴스 예측 생성 추적을 알림 기능과 분리하고, 병렬 처리를 통해 처리 속도를 2.6배 개선했습니다.

## 🎯 해결한 문제

### 1. 예측 생성 추적 문제
**문제 상황:**
- `notified_at` 필드가 **알림 전송 여부**와 **예측 생성 여부**를 동시에 추적
- 알림 기능 비활성화 시 예측이 생성되지 않음
- AI 시장 분석에서 `notified_at IS NULL` 조건으로 조회 → 처리 대상 없음

**해결:**
- `predicted_at` 필드 추가로 예측 생성 독립적으로 추적
- 알림 실패 시에도 예측 생성 보장
- 재처리 가능성 확보

### 2. 처리 속도 병목
**문제 상황:**
- 4개 LLM 모델 순차 실행 (GPT-4o → DeepSeek → Qwen3 → gpt-5-mini)
- 처리 속도: 80초/건
- 시간당 처리량: 45건
- 하루 수집량(10-15건/시간) 대비 여유 부족

**해결:**
- ThreadPoolExecutor로 4개 모델 병렬 실행
- 처리 속도: 30초/건 (2.6배 개선)
- 시간당 처리량: 120건 (2.7배 개선)

### 3. 안정성 이슈
**문제 상황:**
- 임베딩 모델 동시 로드 시 thread-safety 미보장
- FAISS 레거시 인덱스에 `published_at` 필드 없음
- HuggingFace tokenizer fork 경고 반복 출력

**해결:**
- 이중 체크 락 패턴으로 thread-safe 모델 로딩
- `meta.get("published_at")` 사용으로 레거시 호환성 확보
- `TOKENIZERS_PARALLELISM=false` 설정으로 경고 제거

## ✨ 주요 변경사항

### 1. DB 스키마 변경

#### 새로운 필드 추가
```python
# backend/db/models/news.py
class NewsArticle(Base):
    # ... 기존 필드 ...

    # 예측 생성 시각 (알림 전송과 독립)
    predicted_at = Column(DateTime, nullable=True)

    # 알림 전송 시각 (기존 유지)
    notified_at = Column(DateTime, nullable=True)

    # ... 테이블 args ...
    __table_args__ = (
        # ... 기존 인덱스 ...
        Index("idx_news_articles_predicted_at", "predicted_at"),
    )
```

#### 데이터 마이그레이션
```python
# scripts/migrate_predicted_at.py
UPDATE news_articles
SET predicted_at = notified_at
WHERE notified_at IS NOT NULL AND predicted_at IS NULL;

# 결과: 762건 업데이트 완료
```

### 2. 병렬 처리 구현

#### Before: 순차 실행
```python
# backend/llm/predictor.py (기존)
for model_id, model_info in self.active_models.items():
    prediction = self._predict_with_model(...)  # 순차 실행
    results[model_id] = prediction

# 처리 시간: 5-7초 + 20-25초 + 20-28초 + 30-32초 = 75-92초
```

#### After: 병렬 실행
```python
# backend/llm/predictor.py (개선)
with ThreadPoolExecutor(max_workers=len(self.active_models)) as executor:
    futures = [
        executor.submit(predict_one_model, model_id, model_info)
        for model_id, model_info in self.active_models.items()
    ]

    for future in futures:
        model_id, prediction = future.result()
        results[model_id] = prediction

# 처리 시간: max(5-7초, 20-25초, 20-28초, 30-32초) = 30-32초
```

### 3. 조회 조건 변경

#### Before
```python
# backend/notifications/auto_notify.py (기존)
recent_news = (
    db.query(NewsArticle)
    .filter(
        NewsArticle.created_at >= cutoff_time,
        NewsArticle.stock_code.isnot(None),
        NewsArticle.notified_at.is_(None),  # 알림 여부로 조회
    )
    .limit(10)
    .all()
)
```

#### After
```python
# backend/notifications/auto_notify.py (개선)
recent_news = (
    db.query(NewsArticle)
    .filter(
        NewsArticle.created_at >= cutoff_time,
        NewsArticle.stock_code.isnot(None),
        NewsArticle.predicted_at.is_(None),  # 예측 여부로 조회
    )
    .order_by(NewsArticle.created_at.desc())
    .limit(20)  # 병렬 처리로 20건 처리 가능
    .all()
)

# 예측 완료 시
news.predicted_at = datetime.utcnow()  # 항상 업데이트
db.commit()

# 알림 전송 성공 시
if notifier.send_prediction(...):
    news.notified_at = datetime.utcnow()  # 조건부 업데이트
    db.commit()
```

### 4. Thread-safe 개선

#### Embedder 이중 체크 락
```python
# backend/llm/embedder.py
@property
def tokenizer(self):
    """토크나이저 lazy loading (Thread-safe)"""
    if self._tokenizer is None:
        with self._inference_lock:  # 첫 번째 체크
            if self._tokenizer is None:  # 두 번째 체크
                logger.info(f"토크나이저 로드 중: {self.model_name}")
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    return self._tokenizer

@property
def model(self):
    """모델 lazy loading (Thread-safe)"""
    if self._model is None:
        with self._inference_lock:
            if self._model is None:
                self._model = AutoModel.from_pretrained(self.model_name)
                self._model.eval()
    return self._model
```

#### Tokenizer 경고 제거
```python
# backend/llm/embedder.py
def __init__(self):
    # HuggingFace tokenizer fork 경고 방지
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    self.model_name = settings.EMBEDDING_MODEL_NAME
    # ...
```

### 5. 버그 수정

#### FAISS 레거시 인덱스 호환성
```python
# backend/llm/vector_search.py:264 (Before)
"published_at": meta["published_at"],  # KeyError 발생

# backend/llm/vector_search.py:264 (After)
"published_at": meta.get("published_at"),  # None 허용
```

#### 필드명 오류 수정
```python
# backend/llm/vector_search.py:341 (Before)
.filter(NewsStockMatch.news_article_id == news_id)  # AttributeError

# backend/llm/vector_search.py:341 (After)
.filter(NewsStockMatch.news_id == news_id)  # 정상
```

## 📊 성능 개선 결과

### 처리 속도 비교

| 지표 | 기존 (순차) | 개선 (병렬) | 증가율 |
|------|-------------|-------------|--------|
| GPT-4o | 5-7초 | 5-7초 (병렬) | - |
| DeepSeek V3.2 | 20-25초 | 20-25초 (병렬) | - |
| Qwen3 Max | 20-28초 | 20-28초 (병렬) | - |
| gpt-5-mini | 30-32초 | 30-32초 (병렬) | - |
| **총 처리 시간** | **75-92초** | **30-32초** | **2.6배** |

### 처리량 비교

| 주기 | 기존 | 개선 후 | 증가율 |
|------|------|---------|--------|
| 건/분 | 0.75 | 2.0 | 2.7배 |
| 건/시간 | 45 | 120 | 2.7배 |
| 건/일 | 1,080 | 2,880 | 2.7배 |

### 수집량 대비 처리 능력

| 구분 | 수집량 (예상) | 처리 능력 | 여유율 |
|------|---------------|-----------|--------|
| 기존 | 10-15건/시간 | 45건/시간 | 3-4.5배 |
| 개선 | 10-15건/시간 | 120건/시간 | **8-12배** |

## 🧪 테스트 및 검증

### 1. 마이그레이션 실행
```bash
$ uv run python scripts/migrate_predicted_at.py

=== 기존 뉴스 데이터 마이그레이션 시작 ===
대상: notified_at IS NOT NULL AND predicted_at IS NULL

처리 대상: 762건
✅ 마이그레이션 완료: 762건 업데이트

=== 마이그레이션 완료 ===
```

### 2. 검증 스크립트 실행
```bash
$ uv run python scripts/verify_issue_13.py

=== Issue #13 검증 시작 ===

1. predicted_at 필드 존재 확인: ✅ PASS
2. predicted_at 인덱스 생성 확인: ✅ PASS
3. 마이그레이션 데이터 확인: ✅ PASS (762건)
4. 새로운 조회 조건 테스트: ✅ PASS

=== 모든 검증 통과 ===
```

### 3. 운영 환경 테스트

#### PM2 재시작 후 로그
```
2025-11-24 21:31:16: ✅ 활성 모델 4개 로드 완료
2025-11-24 21:31:16: ✅ 크롤러 스케줄러 시작 (뉴스 + 주가)
2025-11-24 21:31:16: INFO: Application startup complete.
```

#### 병렬 처리 로그
```
2025-11-24 21:35:01: 🔬 모든 활성 모델로 병렬 예측 시작: news_id=7245, models=4
2025-11-24 21:35:01: 📊 GPT-4o 예측 중...
2025-11-24 21:35:01: 📊 DeepSeek V3.2 예측 중...
2025-11-24 21:35:01: 📊 Qwen3 Max 예측 중...
2025-11-24 21:35:01: 📊 gpt-5-mini 예측 중...
2025-11-24 21:35:07: ✅ gpt-4o 예측 완료: positive (영향도: medium)
2025-11-24 21:35:23: ✅ qwen/qwen3-max 예측 완료: positive (영향도: medium)
2025-11-24 21:35:24: ✅ deepseek/deepseek-v3.2-exp 예측 완료: positive (영향도: medium)
2025-11-24 21:35:34: ✅ openai/gpt-5-mini 예측 완료: positive (영향도: medium)
2025-11-24 21:35:34: ✅ 전체 4개 모델 병렬 예측 완료
```

**실제 처리 시간: 33초** (21:35:01 → 21:35:34)

#### Tokenizer 경고 제거 확인
- Before: fork 경고 20줄 출력
- After: 경고 없음 ✅

## 📁 변경 파일 목록

### 핵심 파일
- `backend/db/models/news.py` (+2 lines)
  - `predicted_at` 필드 추가
  - 인덱스 생성

- `backend/notifications/auto_notify.py` (+62 lines, -60 lines)
  - 조회 조건 변경: `notified_at` → `predicted_at`
  - limit 증가: 10 → 20
  - 예측 완료 시각 기록 로직 추가

- `backend/llm/predictor.py` (+63 lines, -60 lines)
  - ThreadPoolExecutor 병렬 처리 구현
  - `predict_all_models()` 함수 리팩토링

- `backend/llm/embedder.py` (+29 lines, -27 lines)
  - 이중 체크 락 패턴 적용
  - tokenizer/model lazy loading thread-safe 개선
  - `TOKENIZERS_PARALLELISM=false` 설정

- `backend/llm/vector_search.py` (+4 lines, -2 lines)
  - `meta.get("published_at")` 레거시 호환성
  - `news_article_id` → `news_id` 필드명 수정

### 마이그레이션 스크립트
- `scripts/migrate_predicted_at.py` (신규)
  - 기존 데이터 마이그레이션
  - `notified_at` → `predicted_at` 복사

- `scripts/verify_issue_13.py` (신규)
  - 필드 존재 확인
  - 인덱스 생성 확인
  - 데이터 마이그레이션 검증

## 🚀 배포 가이드

### 사전 준비
1. DB 백업 (필수)
2. 테스트 환경에서 마이그레이션 테스트
3. PM2 프로세스 정상 동작 확인

### 배포 순서

#### 1. 코드 배포
```bash
git checkout main
git pull origin main
git merge feature/issue-13-predicted-at-field
```

#### 2. 마이그레이션 실행
```bash
# 스크립트 실행
uv run python scripts/migrate_predicted_at.py

# 검증
uv run python scripts/verify_issue_13.py
```

#### 3. 서버 재시작
```bash
# PM2 재시작
pm2 restart azak-backend

# 로그 확인
pm2 logs azak-backend --lines 50
```

#### 4. 모니터링 (10분)
```bash
# 실시간 로그 모니터링
pm2 logs azak-backend

# 확인 사항:
# - "🔬 모든 활성 모델로 병렬 예측 시작" 로그
# - 처리 시간 30-35초 이내
# - 경고 메시지 없음
# - 에러 없음
```

### 롤백 계획
문제 발생 시:
```bash
# 1. 이전 버전으로 롤백
git reset --hard HEAD~1

# 2. PM2 재시작
pm2 restart azak-backend

# 3. predicted_at 필드는 유지 (NULL 값)
# 4. 다음 배포 시 재시도
```

## 📈 예상 효과

### 즉시 효과
1. ✅ 예측 생성 안정성 확보
   - 알림 실패 시에도 예측 생성 보장
   - 재처리 가능성 확보

2. ✅ 처리 속도 2.6배 개선
   - 80초 → 30초
   - 하루 처리량 2.7배 증가

3. ✅ 시스템 안정성 향상
   - Thread-safe 모델 로딩
   - 경고 메시지 제거

### 장기 효과
1. 확장성 확보
   - 하루 수집량 증가 대비 충분한 여유
   - 모델 추가 시에도 처리 시간 유지

2. 운영 효율성
   - 알림 기능과 예측 생성 독립 운영
   - 문제 발생 시 격리 가능

## ⚠️ 주의사항

### 1. ThreadPoolExecutor 제약
- Python GIL로 인해 CPU-bound 작업은 병렬화 효과 제한
- 현재는 I/O-bound (API 호출)라서 효과적
- CPU 연산 많은 작업 추가 시 ProcessPoolExecutor 고려 필요

### 2. 메모리 사용량
- 4개 모델 동시 실행으로 메모리 사용량 소폭 증가
- 현재 환경에서는 문제없음 (48GB RAM)
- 모니터링 필요

### 3. API Rate Limit
- 병렬 처리로 순간 API 호출 증가
- OpenRouter, OpenAI Rate Limit 여유 확인 필요
- 현재는 문제없음 (충분한 여유)

## 🔗 관련 문서

- [Issue #13](https://github.com/atototo/azak/issues/13)
- [Pull Request #14](https://github.com/atototo/azak/pull/14)
- [AsyncIOScheduler 전환 (Issue #10)](./issue-10-asyncio-scheduler.md)
- [Side Effect 해결 (Issue #11)](./issue-11-side-effects.md)

## 📝 후속 작업

### 완료 예정 (Phase 2)
- [ ] 모니터링 대시보드에 predicted_at 필드 추가
- [ ] 예측 생성 지연 알림 추가
- [ ] Lock 대기 시간 로깅

### 검토 예정 (Phase 3)
- [ ] Celery/RQ 도입 검토 (장기)
- [ ] 예측 결과 캐싱 전략
- [ ] 모델별 처리 시간 최적화

## ✅ 완료 체크리스트

- [x] 코드 작성 완료
- [x] 마이그레이션 스크립트 작성 및 실행
- [x] 검증 스크립트 작성 및 실행
- [x] 운영 환경 테스트 완료
- [x] PM2 재시작 후 정상 동작 확인
- [x] 성능 개선 확인 (2.6배)
- [x] 경고 메시지 제거 확인
- [x] Pull Request 생성
- [x] 문서 작성 완료
