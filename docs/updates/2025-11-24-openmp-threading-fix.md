# PyTorch/FAISS 멀티프로세싱 충돌 해결 (OpenMP Threading)

**작업 일자**: 2025-11-24
**작업자**: young
**관련 이슈**: Server Crash Loop (Segmentation Fault)

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

PM2 환경에서 PyTorch(임베딩 모델)와 FAISS(벡터 검색)가 실행될 때 발생하는 **Segmentation Fault(서버 비정상 종료)** 문제를 해결했습니다.

**핵심 해결책**:
- **OpenMP 스레드 제한**: `OMP_NUM_THREADS=1` 환경 변수 설정을 통해 멀티프로세싱 환경에서의 스레드 경합 방지
- **상세 로깅 추가**: 임베딩 생성 및 벡터 검색 구간에 디버그 로그 추가로 모니터링 강화

---

## AS-IS (기존 상태)

### 문제점: 원인 불명의 서버 재시작 (Crash Loop)

```bash
# ❌ 서버 로그 (크래시 직전)
17:35:00: 🔔 AI 시장 분석 자동 생성 시작
17:35:00: 🔍 NewsVectorSearch 초기화 완료
17:35:00: ✅ FAISS 인덱스 로드 완료
17:35:00: 처리 중: AI 버블 우려에도...
17:35:03: [PM2] App [azak-backend] ... exited with code [0] via signal [SIGSEGV]
```

**증상**:
- `AI 시장 분석` 단계에서 뉴스 임베딩 생성 또는 유사 뉴스 검색 시점(약 3초 후)에 서버가 조용히 죽음
- Python 예외(Exception) 로그 없이 **Segmentation Fault** 발생
- PM2가 프로세스를 계속 재시작하지만 동일 구간에서 반복적으로 크래시 발생

**근본 원인**:
- **OpenMP Threading Conflict**: PyTorch와 FAISS는 연산 가속을 위해 OpenMP를 사용하여 멀티스레딩을 수행함.
- PM2(멀티프로세스 관리 도구)나 Python의 `asyncio` 루프와 결합될 때, 과도한 스레드 생성으로 인한 **자원 경합(Resource Contention)** 또는 **Deadlock** 발생.

---

## 변경 필요 사유

### 1. 서비스 안정성 확보
- 서버가 주기적으로 다운되면서 스케줄러 작업(뉴스 크롤링, 분석)이 중단됨.
- 사용자 경험 저하 및 데이터 누락 발생.

### 2. 디버깅 가시성 확보
- 기존에는 어디서 멈추는지 알 수 없어 원인 파악이 어려웠음.
- 상세 로그를 통해 병목 지점이나 실패 지점을 명확히 파악할 필요가 있음.

---

## TO-BE (변경 후 상태)

### 핵심 아키텍처: 단일 스레드 강제 (Single Thread Enforcement)

```python
# ✅ backend/main.py (최상단)
import os

# PM2/Multiprocessing 환경에서 PyTorch/FAISS 충돌 방지
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
```

**보장되는 것**:
- PyTorch와 FAISS가 연산 시 **단일 스레드**만 사용하도록 강제.
- 멀티프로세스 환경(PM2)에서 각 프로세스가 독립적으로 안정적으로 동작.
- CPU Context Switching 오버헤드 감소로 오히려 처리량(Throughput)이 개선될 수 있음.

---

## 변경 사항 상세

### 1. 환경 변수 설정 (main.py)

**파일**: `backend/main.py`

PyTorch나 다른 무거운 라이브러리가 로드되기 **전**에 환경 변수를 설정해야 효과가 있습니다. 따라서 `main.py`의 가장 윗부분에 설정을 추가했습니다.

```python
import os

# 0. 환경 변수 설정 (가장 먼저 실행)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import logging
# ... 이후 라이브러리 임포트
```

### 2. 상세 로깅 추가 (Logging)

**파일**: `backend/llm/embedder.py`, `backend/llm/vector_search.py`

크래시가 발생하는 정확한 지점을 파악하기 위해 `DEBUG` 레벨 로그를 추가했습니다.

```python
# backend/llm/embedder.py
with torch.no_grad():
    logger.debug(f"PyTorch 추론 시작: {len(text)}자")  # 시작 로그
    model_output = self.model(**encoded_input)
    logger.debug("PyTorch 추론 완료")                 # 종료 로그
```

```python
# backend/llm/vector_search.py
logger.debug(f"FAISS 검색 시작: k={search_k}")        # 시작 로그
distances, indices = self._index.search(query_vector, search_k)
logger.debug(f"FAISS 검색 완료: found {len(indices[0])}") # 종료 로그
```

---

## 테스트 결과

### 1. 안정성 확인

```bash
# PM2 로그 모니터링
0|azak-backend | 17:55:00: 🔔 AI 시장 분석 자동 생성 시작
0|azak-backend | 17:55:00: PyTorch 추론 시작: 512자
0|azak-backend | 17:55:00: PyTorch 추론 완료
0|azak-backend | 17:55:00: FAISS 검색 시작: k=50
0|azak-backend | 17:55:00: FAISS 검색 완료: found 50 items
0|azak-backend | 17:55:01: ✅ A/B 알림 전송 성공
```

- **결과**: 서버 재시작 없이 모든 AI 분석 파이프라인이 정상적으로 완료됨.
- **성능**: 단일 스레드로 제한했음에도 불구하고, 개별 요청 처리 속도에는 체감할 만한 저하가 없음(오히려 안정적).

---

## 사용 방법

### 적용 방법

코드가 수정되었으므로 PM2 프로세스를 재시작하여 변경된 환경 변수가 적용되도록 해야 합니다.

```bash
# 백엔드 재시작
pm2 restart azak-backend

# 로그 확인 (정상 동작 확인)
pm2 logs azak-backend
```

---

## 참고 사항

### 왜 스레드를 1개로 제한하나요?

AI 모델은 기본적으로 가능한 모든 CPU 코어를 사용하려고 합니다. 예를 들어 8코어 CPU라면 PyTorch가 8개의 스레드를 만듭니다.
하지만 PM2로 여러 프로세스를 띄우거나, 비동기(AsyncIO) 처리를 하면서 동시에 여러 요청이 들어오면:
`8코어 x N개 요청 = 수십/수백 개의 스레드`가 생성되어 CPU가 스레드를 교체하는 비용(Context Switching)이 연산 비용보다 커지거나, 메모리 접근 충돌로 프로세스가 강제 종료될 수 있습니다.

따라서 **서버 환경에서는 `OMP_NUM_THREADS=1`로 설정하는 것이 모범 사례(Best Practice)**입니다.

---

**작성일**: 2025-11-24
