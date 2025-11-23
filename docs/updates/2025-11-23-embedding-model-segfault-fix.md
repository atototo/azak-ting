# 임베딩 모델 로드 시 Segmentation Fault 수정

**날짜**: 2025-11-23
**이슈**: #7
**PR**: #8

---

## 요약

임베딩 모델(BM-K/KoSimCSE-roberta)을 통합한 후 백엔드가 계속 크래시되는 문제가 발생했다. PM2 재시작 카운트가 ↺ 8 → 24로 계속 증가하고, exit code 139(SIGSEGV)로 죽는 상황이었다.

**한 줄로 정리하면**: 멀티스레드 환경에서 락 없이 ML 모델을 lazy loading 하다가 race condition이 발생해서 Segmentation Fault가 났고, thread-safe singleton + eager loading으로 해결했다.

---

## 문제 상황

### 증상

```bash
# PM2 로그
PM2: App exited with code [139] via signal [SIGINT]
↺ 8 → 24회 재시작 (계속 증가 중)

# Backend 로그
19:12:40 - 임베딩 모델 로드 중: BM-K/KoSimCSE-roberta
19:12:43 - [크래시]

# Frontend
Error: connect ECONNREFUSED 127.0.0.1:8000
```

DART 크롤러(5분 주기), 뉴스 크롤러(10분 주기)가 돌 때마다 백엔드가 죽었다. 특히 "임베딩 모델 로드 중" 메시지가 나온 직후 크래시가 발생했다.

### 뭘 했었나

새로운 한글 임베딩 모델을 백엔드에 붙였다. 모델이 무거워서(~500MB) 싱글톤처럼 만들어서 전역에서 한 번만 로드하고 재사용하려고 했다. 크롤러들이 뉴스/공시를 저장할 때 이 모델로 임베딩을 만든다.

그런데 DART 크롤러, 뉴스 크롤러가 돌 때마다 로그에 "임베딩 모델 로드 중"이 계속 찍히고, 백엔드 프로세스가 exit code 139로 죽었다. PM2가 "죽었네?" 하고 계속 재시작 → ↺ 카운트 증가 → 그 사이 프론트는 백엔드에 붙으려다 ECONNREFUSED.

---

## 근본 원인

결론부터 말하면 3가지 문제가 겹쳤다:

1. **Thread-safety 문제**: 여러 스레드가 동시에 모델 로드 시도
2. **Lazy loading 타이밍**: 실제 로딩이 startup이 아니라 크롤러 실행 시점에 발생
3. **DEBUG 모드**: uvicorn auto-reload로 프로세스/스레드가 더 많이 생김

### 1. Thread-safety 문제 - 락이 없는 싱글톤

기존 코드:

```python
# backend/llm/embedder.py (수정 전)
_news_embedder: Optional[NewsEmbedder] = None

def get_news_embedder() -> NewsEmbedder:
    global _news_embedder
    if _news_embedder is None:
        _news_embedder = NewsEmbedder()  # ❌ 여기가 문제
    return _news_embedder
```

싱글톤처럼 보이지만 사실 **락이 없다**. 그래서 멀티스레드 환경에서 이런 일이 벌어진다:

```
Thread 1 (DART Crawler):
  ├─ if _news_embedder is None: True ✅
  ├─ NewsEmbedder() 생성 시작... (모델 로드 중, 500MB)
  └─ [아직 생성 중...]

Thread 2 (News Crawler):
  ├─ if _news_embedder is None: True ✅ (아직 None!)
  ├─ NewsEmbedder() 생성 시작... (또 로드?!)
  └─ 💥 Crash
```

두 스레드가 거의 동시에 `None`을 보고 각자 모델을 로드하려고 했다. 이게 **race condition**이다.

### 2. 왜 Segmentation Fault까지 났을까?

보통 Python에서 race condition이 나면 그냥 예외가 뜨거나 데이터가 꼬이는 정도인데, 왜 **exit code 139(SIGSEGV)** 같은 심각한 크래시가 났을까?

PyTorch/Transformers 모델은 내부적으로 **C/C++, CUDA로 구현**되어 있다:

```
Python 코드:
  └─ AutoModel.from_pretrained()
     └─ C++ Backend (libtorch)
        └─ CUDA / MKL / OpenMP
           └─ Memory Allocation ← 여기서 충돌
```

Python GIL이 있어도, **C/C++ 확장 모듈은 GIL을 release하고 동작**할 수 있다. 그래서 네이티브 레벨에서는 진짜 멀티스레드가 동시에 돌고, 여러 스레드가 동시에 메모리를 할당하려고 하면서 내부 구조가 깨진다.

**Segmentation Fault**는 OS가 "이 프로그램이 허용되지 않은 메모리 영역을 건드렸다"며 바로 죽여버리는 것이다. Python 레벨 Exception이 아니라, C/C++ 레벨에서 메모리가 꼬여서 OS가 강제 종료시킨 것.

> 중요한 교훈: **"Python은 GIL이 있으니 thread-safe하다"는 착각은 위험하다.** 특히 네이티브 라이브러리를 쓸 때는 별도의 thread-safety 조치가 필요하다.

### 3. Lazy Loading의 함정

`NewsEmbedder` 내부는 이렇게 되어 있었다:

```python
class NewsEmbedder:
    def __init__(self):
        self._tokenizer = None  # 아직 로드 안 됨
        self._model = None      # 아직 로드 안 됨

    @property
    def model(self):
        if self._model is None:
            self._model = AutoModel.from_pretrained(...)  # 여기서 처음 로드
        return self._model
```

`@property`로 lazy loading을 구현했다. 그래서 startup에서 이렇게 했을 때:

```python
@app.on_event("startup")
async def startup_event():
    embedder = get_news_embedder()  # 인스턴스만 생성
    # 실제 모델은 아직 로드 안 됨!
```

**인스턴스만 만들어졌을 뿐, 실제 모델은 로드되지 않았다**. 진짜 로딩은 처음으로 `.model` 속성에 접근할 때 일어난다. 그게 언제냐면... 크롤러가 처음 임베딩을 만들려고 할 때다.

그래서 이런 타이밍이 발생했다:

```
Startup:
  └─ get_news_embedder() ✅ 인스턴스 생성
     └─ self._model = None (로드 안 됨)

DART Crawler (5분 후):
  └─ embedder.model 접근 ← 여기서 처음 로드!
     └─ AutoModel.from_pretrained() 실행
        └─ 💥 여러 스레드가 동시에 실행 → SIGSEGV
```

### 4. DEBUG 모드가 문제를 키웠다

`.env`에 `DEBUG=True`로 되어 있었다. 이러면 uvicorn이 **auto-reload 모드**로 동작한다:

- 코드 파일을 감시하다가 변경되면 자동으로 재시작
- 내부적으로 별도 프로세스/스레드를 추가로 생성
- 결과: 프로세스/스레드가 더 많이 생기고, 모델 로딩 코드가 더 자주 동시에 실행될 가능성 증가

---

## 해결 방법

### 1. Thread-safe Singleton - Double-checked Locking

락을 추가해서 critical section을 보호했다:

```python
# backend/llm/embedder.py
import threading

_news_embedder: Optional[NewsEmbedder] = None
_embedder_lock = threading.Lock()

def get_news_embedder() -> NewsEmbedder:
    global _news_embedder

    # 첫 번째 체크 (락 없이)
    if _news_embedder is None:
        with _embedder_lock:  # 락 획득
            # 두 번째 체크 (락 안에서)
            if _news_embedder is None:
                _news_embedder = NewsEmbedder()

    return _news_embedder
```

**왜 두 번 체크할까?**

- **첫 번째 체크** (락 없음): 이미 생성되어 있으면 락을 안 잡고 바로 리턴 → 성능 최적화
- **두 번째 체크** (락 안): 첫 체크를 통과한 여러 스레드가 락 앞에서 대기할 수 있는데, 먼저 들어간 스레드가 객체를 만들면 나중에 들어온 스레드는 다시 체크해서 중복 생성 방지

이렇게 하면:

```
Thread 1:
  ├─ if _news_embedder is None: True
  ├─ Lock 획득
  ├─ if _news_embedder is None: True (재확인)
  └─ NewsEmbedder() 생성 ✅

Thread 2 (동시 진입):
  ├─ if _news_embedder is None: True
  ├─ Lock 대기... (Thread 1이 Lock 보유 중)
  ├─ [Thread 1 완료 후 Lock 획득]
  ├─ if _news_embedder is None: False (이미 생성됨!)
  └─ return 기존 인스턴스 ✅
```

**한 번에 하나의 스레드만** NewsEmbedder를 생성할 수 있게 되었다.

### 2. Eager Loading으로 로딩 시점 제어

startup 이벤트에서 **실제로 모델을 로드**하도록 강제했다:

```python
# backend/main.py
@app.on_event("startup")
async def startup_event():
    logger.info("📦 ML 모델 로드 시작...")

    embedder = get_news_embedder()

    # Lazy loading 속성을 강제로 호출해서 실제 로딩 발생
    _ = embedder.tokenizer  # 토크나이저 로드
    _ = embedder.model      # 모델 로드

    logger.info("✅ 임베딩 모델 로드 완료 (메인 스레드)")

    predictor = get_predictor()
    logger.info("✅ 예측 모델 로드 완료 (메인 스레드)")
```

이제 타이밍이 이렇게 바뀌었다:

```
Startup (메인 스레드):
  └─ embedder = get_news_embedder() ✅
     └─ _ = embedder.model ✅
        └─ AutoModel.from_pretrained() ✅
           └─ self._model = <loaded> ✅

DART Crawler (5분 후):
  └─ embedder.model 접근
     └─ self._model is not None ✅ (이미 로드됨)
        └─ return self._model ✅ (추가 로딩 없음)
```

**메인 스레드에서 안전하게 한 번만 로드**되고, 이후 크롤러들은 이미 로드된 모델을 재사용한다.

### 3. 싱글톤 패턴 전파

기존에 매번 새 인스턴스를 만들던 코드들을 싱글톤 사용으로 변경:

```python
# backend/crawlers/news_saver.py
# Before: self.predictor = StockPredictor()
# After:
self.predictor = get_predictor()  # 싱글톤 사용
```

```python
# backend/llm/vector_search.py
# Before: self.embedder = NewsEmbedder()
# After:
self.embedder = get_news_embedder()  # 싱글톤 사용
```

### 4. DEBUG 모드 비활성화

```bash
# .env
DEBUG=false
```

```javascript
// ecosystem.config.js
env: {
  PYTHONUNBUFFERED: '1',
  DEBUG: 'false',  // 환경변수 override
},
```

프로덕션에서는 auto-reload를 끄고 PM2가 프로세스를 관리하도록 했다.

---

## 검증 결과

### 수정 전 (문제)

```bash
# 로그
19:12:40 - 임베딩 모델 로드 중  ← Startup
19:17:40 - 임베딩 모델 로드 중  ← DART Crawler 때!
19:22:40 - 임베딩 모델 로드 중  ← News Crawler 때!
[크래시]

# PM2
↺ 8 → 24 (계속 증가)
status: errored
exit code: 139
```

### 수정 후 (해결)

```bash
# 로그
19:20:05 - 📦 ML 모델 로드 시작...
19:20:08 - ✅ 임베딩 모델 로드 완료 (메인 스레드)
19:20:08 - ✅ 예측 모델 로드 완료 (메인 스레드)
19:20:08 - ✅ 크롤러 스케줄러 시작

19:25:05 - DART 크롤러 실행 ✅ (모델 재로드 없음!)
19:30:05 - 뉴스 크롤러 실행 ✅ (모델 재로드 없음!)

# PM2
↺ 25 (고정, 더 이상 증가 안 함)
status: online
uptime: 11분+
```

### 타임라인

```
19:20:05 - Backend 시작
19:21:05 - 1분봉 수집 ✅
19:22:05 - 1분봉 수집 ✅
19:23:05 - 1분봉 수집 ✅
19:24:05 - 1분봉 수집 ✅
19:25:05 - DART 크롤러 ✅ (재로드 없음)
19:26:05 - 1분봉 수집 ✅
19:27:05 - 1분봉 수집 ✅
19:28:05 - 1분봉 수집 ✅
19:29:05 - 1분봉 수집 ✅
19:30:05 - 뉴스 크롤러 ✅ (재로드 없음)

최종: 11분+ 안정적 작동, 재시작 없음
```

---

## 핵심 개념 정리

이번 문제를 해결하면서 배운 것들을 정리해보면:

### Race Condition

여러 스레드가 같은 자원(여기서는 `_news_embedder`)에 동시에 접근/수정하면서 실행 순서에 따라 결과가 달라지는 상황. 간단한 예:

```python
# 공유 변수
x = 0

def increase():
    temp = x      # 1. 읽기
    temp += 1     # 2. 계산
    x = temp      # 3. 쓰기
```

두 스레드가 동시에 실행하면:
- Thread A: `temp = 0` → `temp = 1` → `x = 1`
- Thread B: `temp = 0` → `temp = 1` → `x = 1`

2번 증가해서 `x=2`가 되어야 하는데 `x=1`이 될 수 있다. 읽기-수정-쓰기 중간에 다른 스레드가 끼어들기 때문.

우리 케이스도 마찬가지다:
- Thread A: `None 확인` → `생성 시작`
- Thread B: `None 확인` (A가 아직 완료 안 함) → `생성 시작`
- 결과: 두 스레드가 동시에 모델 로드 → 💥

### Critical Section과 Lock

**Critical Section**은 공유 자원을 건드리는 중요한 코드 구간이다. 여기는 **한 번에 하나의 스레드만** 들어가야 한다.

이를 보장하기 위해 **Lock**을 사용한다:

```python
_lock = threading.Lock()

with _lock:  # Lock 획득
    # 여기는 한 번에 하나의 스레드만 실행
    _news_embedder = NewsEmbedder()
```

한 스레드가 Lock을 잡고 있으면, 다른 스레드는 Lock이 풀릴 때까지 대기한다.

### Python GIL의 한계

**GIL(Global Interpreter Lock)**은 Python 바이트코드 실행을 한 번에 하나의 스레드만 하도록 보장한다. 하지만:

- **C/C++ 확장 모듈은 GIL을 release하고 동작**할 수 있다
- PyTorch, NumPy 같은 네이티브 라이브러리는 GIL 밖에서 돌 수 있다
- 따라서 네이티브 레벨에서는 진짜 멀티스레드 동시 실행이 일어난다

그래서 "Python은 GIL이 있으니까 thread-safe하다"는 생각은 위험하다. 특히 ML 라이브러리처럼 C/C++로 구현된 무거운 라이브러리를 쓸 때는 더욱.

### Lazy Loading vs Eager Loading

**Lazy Loading**: 필요한 순간까지 로드를 미룬다
- 장점: 안 쓸 수도 있는 리소스를 미리 로드 안 함
- 단점: 처음 사용하는 순간이 언제인지 예측하기 어려움 (특히 멀티스레드에서)

**Eager Loading**: 시작할 때 미리 로드한다
- 장점: 로딩 타이밍을 제어할 수 있고, 첫 요청이 느려지지 않음
- 단점: 시작 시간이 느려질 수 있음

우리는 **코드는 lazy하게 유지**하되, **startup에서 강제로 접근**해서 사실상 eager loading처럼 동작하게 만들었다. 이러면:
- 테스트 시 모델 없이 인스턴스만 만들 수 있고 (유연성)
- 실제 서버에서는 안전하게 미리 로드됨 (안정성)

### ML 모델 로딩의 특수성

ML 모델의 생명주기는 두 단계로 나뉜다:

1. **로딩/초기화** (Write): 메모리 할당, 가중치 로딩 → **Thread-unsafe**
2. **추론** (Read): forward pass만 실행 → **Thread-safe**

그래서 보통:
- 로딩은 메인 스레드에서 한 번만 안전하게
- 추론은 여러 스레드에서 병렬로 처리

이렇게 하면 안정성(초기화 시 race condition 방지)과 성능(병렬 추론) 둘 다 달성할 수 있다.

---

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `backend/llm/embedder.py` | threading.Lock() 추가, double-checked locking 구현 |
| `backend/llm/predictor.py` | threading.Lock() 추가, double-checked locking 구현 |
| `backend/main.py` | startup에서 eager loading, lazy loading trigger 추가 |
| `backend/crawlers/news_saver.py` | `StockPredictor()` → `get_predictor()` 싱글톤 사용 |
| `backend/llm/vector_search.py` | `NewsEmbedder()` → `get_news_embedder()` 싱글톤 사용 |
| `backend/config.py` | Pydantic V2 문법 업데이트 |

총 6개 파일, +75 lines

---

## 배운 점

### 1. ML 모델은 메인 스레드에서 로드해야 한다

PyTorch/Transformers 같은 라이브러리는 내부적으로 C/C++를 사용하고, 초기화 과정이 thread-safe하지 않다. 여러 스레드가 동시에 로드하면 메모리 충돌이 나서 Segmentation Fault까지 갈 수 있다.

```python
# ❌ Bad: Worker thread에서 로드
def crawler():
    embedder = get_news_embedder()

# ✅ Good: Main thread에서 한 번만
@app.on_event("startup")
async def startup():
    embedder = get_news_embedder()
    _ = embedder.model  # 실제 로딩 강제
```

### 2. Lazy Loading의 실제 로딩 시점을 파악해야 한다

`@property`로 lazy loading을 구현하면 코드가 깔끔하지만, 실제 로딩이 언제 일어나는지 명확하지 않다. 특히 startup에서 "로드했다"고 생각했는데 사실 인스턴스만 만들고 실제 모델은 안 올렸을 수 있다.

명시적으로 속성에 접근해서 로딩을 트리거해야 한다:

```python
embedder = get_news_embedder()  # 인스턴스만
_ = embedder.model              # 실제 로딩 트리거
```

### 3. 싱글톤은 항상 thread-safe하게

"한 번만 생성"과 "thread-safe"는 다른 문제다. Python GIL이 있어도 멀티스레드에서 싱글톤은 위험하다. Lock을 명시적으로 써야 한다.

Double-checked locking이 업계 표준이다:
- 첫 체크 (Lock 없음): 성능 최적화
- 둘째 체크 (Lock 안): thread-safety 보장

### 4. 로그가 디버깅의 전부

"임베딩 모델 로드 중" 로그가 계속 찍힌 것이 문제의 핵심 단서였다. 모델 로딩 같은 중요한 작업은 명확하게 로깅해야 한다:

```python
logger.info("✅ 임베딩 모델 로드 완료 (메인 스레드)")  # Startup
logger.info("🎯 자동 예측 시스템 활성화 (싱글톤)")  # Runtime
```

Startup vs Runtime을 구분해서 로깅하면 문제 파악이 쉽다.

### 5. Python GIL ≠ 네이티브 라이브러리 안전

"Python은 GIL이 있으니까 괜찮다"는 착각은 위험하다. C/C++로 구현된 라이브러리는 GIL을 release하고 동작할 수 있어서, 네이티브 레벨에서는 진짜 멀티스레드 동시 실행이 일어난다.

특히 ML 모델처럼 무거운 네이티브 라이브러리를 쓸 때는 별도의 thread-safety 설계가 필요하다.

---

## 참고 자료

- [PyTorch Threading 가이드](https://pytorch.org/docs/stable/notes/multiprocessing.html)
- [HuggingFace Transformers - Model Loading](https://huggingface.co/docs/transformers/main_classes/model)
- [Python threading.Lock 문서](https://docs.python.org/3/library/threading.html#threading.Lock)
- [Double-checked Locking Pattern](https://en.wikipedia.org/wiki/Double-checked_locking)

---

**관련 링크**:
- Issue: [#7](https://github.com/atototo/azak/issues/7)
- PR: [#8](https://github.com/atototo/azak/pull/8)
- Commit: `2842afc`
