# 스케줄러 서버 분리 아키텍처 개선

**작업 일자**: 2025-11-29
**작업자**: young
**관련 이슈**: [#17](https://github.com/atototo/azak/issues/17)
**Pull Request**: (생성 예정)

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

스케줄 작업(크롤링, 예측, 리포트, 평가 등)과 일반 백엔드 API 기능이 하나의 서버에서 실행되면서 발생하는 리소스 경합, 안정성, 확장성 문제를 해결하기 위해 **스케줄러 서버를 별도로 분리**하는 아키텍처 개선 작업입니다.

**변경 타입**: `refactor` (아키텍처 개선)

**핵심 목표**:
- ✅ API 서버와 스케줄러 서버의 완벽한 책임 분리
- ✅ API 서버 독립적 수평 확장 가능
- ✅ 시스템 안정성 향상 (단일 장애점 제거)
- ✅ 배포 시 선택적 재시작 가능

---

## AS-IS (기존 상태)

### 현재 시스템 구성

**PM2 프로세스 현황** (2025-11-29 기준):
```
┌────┬──────────────────┬─────────┬──────────┬────────┬───────────┬──────────┐
│ id │ name             │ mode    │ pid      │ uptime │ status    │ memory   │
├────┼──────────────────┼─────────┼──────────┼────────┼───────────┼──────────┤
│ 0  │ azak-backend     │ fork    │ 12336    │ 2D     │ online    │ 5.0mb*   │
│ 1  │ azak-frontend    │ fork    │ 22155    │ 3D     │ online    │ 42.4mb   │
│ 2  │ azak-ngrok       │ fork    │ 56706    │ 4D     │ online    │ 94.5mb   │
└────┴──────────────────┴─────────┴──────────┴────────┴───────────┴──────────┘
* 실제 메모리는 ML 모델 로드 후 ~1.5GB (표시는 부정확)
```

**현재 PM2 설정** (`ecosystem.config.js`):
```javascript
{
  name: 'azak-backend',
  script: 'uv',
  args: 'run python -m backend.main',
  exec_mode: 'fork',        // 단일 프로세스
  max_memory_restart: '5G', // ML 모델 + 스케줄러 여유분
  autorestart: true
}
```

**현재 디렉토리 구조**:
```
backend/
├── main.py (4.4KB)                      # ✅ FastAPI 앱 + ML 로드 + 스케줄러
├── config.py (3.1KB)                    # 환경 설정
├── scheduler.py (4.7KB)                 # 구버전 스케줄러 (사용 안 함)
├── scheduler/
│   ├── crawler_scheduler.py (50KB)     # ✅ 뉴스/주가 크롤러 스케줄러
│   └── evaluation_scheduler.py (6.3KB) # ✅ 모델 평가 스케줄러
├── api/                                 # API 엔드포인트
├── crawlers/                            # 크롤러 모듈
├── llm/                                 # ML 모델 (임베딩, 예측)
└── services/                            # 비즈니스 로직
```

### 문제점

현재 `backend/main.py` 하나의 FastAPI 프로세스에서 모든 작업을 처리하고 있습니다:

```
backend/main.py (단일 FastAPI 프로세스)
├── 🌐 API 엔드포인트
│   ├── /api/health, /api/prediction, /api/dashboard
│   ├── /api/news, /api/stocks, /api/models
│   └── /api/evaluations, /api/ab_test
│
├── 🧠 ML 모델 로딩 (startup 이벤트)
│   ├── NewsEmbedder (Transformer 모델, ~500MB 메모리)
│   └── Predictor (예측 모델)
│
└── 📅 스케줄러 작업들 (APScheduler)
    ├── 뉴스 크롤링 (10분마다)
    ├── 주가 데이터 수집 (1분마다)
    ├── 뉴스-주가 매칭 (일일)
    ├── 임베딩 생성 (일일)
    ├── AI 리포트 생성 (10분마다)
    ├── 모델 평가 (매일 16:00)
    └── 성능 집계 (매일 17:00)
```

**주요 코드** (`backend/main.py:68-98`):
```python
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 이벤트"""
    logger.info(f"🚀 {settings.APP_NAME} 애플리케이션 시작")

    # 1️⃣ ML 모델 사전 로드 (Eager Loading)
    try:
        logger.info("📦 ML 모델 로드 시작...")
        from backend.llm.embedder import get_news_embedder
        from backend.llm.predictor import get_predictor

        embedder = get_news_embedder()
        _ = embedder.tokenizer
        _ = embedder.model
        logger.info("✅ 임베딩 모델 로드 완료 (메인 스레드)")

        predictor = get_predictor()
        logger.info("✅ 예측 모델 로드 완료 (메인 스레드)")
    except Exception as e:
        logger.error(f"❌ ML 모델 로드 실패: {e}", exc_info=True)

    # 2️⃣ APScheduler 시작 (뉴스: 10분, 주가: 1분)
    scheduler = get_crawler_scheduler(news_interval_minutes=10, stock_interval_minutes=1)
    scheduler.start()
    logger.info("✅ 크롤러 스케줄러 시작 (뉴스 + 주가)")
```

### 스케줄러 실행 로그 샘플

**실시간 로그** (2025-11-29 12:00 기준):
```
2025-11-29 12:00:49 - backend.scheduler.crawler_scheduler - INFO - 🔍 삼성에피스홀딩스 (0126Z0) 검색 중... (최대 3건)
2025-11-29 12:00:49 - backend.crawlers.naver_search_crawler - INFO - 네이버 뉴스 검색 시작: query=삼성에피스홀딩스, limit=3
2025-11-29 12:00:50 - backend.crawlers.base_crawler - INFO - Fetching: https://search.naver.com/search.naver?where=news&query=...
2025-11-29 12:00:50 - backend.crawlers.naver_search_crawler - INFO - 페이지 1에 더 이상 뉴스가 없습니다
2025-11-29 12:00:50 - backend.crawlers.naver_search_crawler - INFO - 네이버 뉴스 검색 완료: 0건
2025-11-29 12:00:52 - backend.scheduler.crawler_scheduler - INFO - ========================================
2025-11-29 12:00:52 - backend.scheduler.crawler_scheduler - INFO - ✅ 종목별 검색 완료: 0건 저장, 0건 스킵
2025-11-29 12:00:52 - backend.scheduler.crawler_scheduler - INFO - ========================================
```

→ **문제**: 스케줄러 로그와 API 요청 로그가 섞여 있어 디버깅 어려움

### 영향도

| 항목 | 현재 상태 | 영향도 |
|------|----------|--------|
| **API 응답 속도** | 스케줄 작업 실행 중 응답 지연 발생 | 🔴 High |
| **시스템 안정성** | 메모리/CPU 과부하 시 전체 서버 다운 위험 | 🔴 Critical |
| **운영 복잡도** | 배포 시 스케줄러 재시작 필요, 크롤링 중단 | 🟡 Medium |
| **확장성** | 수평 확장 불가 (스케줄러 중복 실행 방지 필요) | 🔴 High |
| **데이터 무결성** | 스케줄러 재시작 시 크롤링 누락 가능 | 🟡 Medium |
| **로그 관리** | API와 스케줄러 로그 혼재, 디버깅 어려움 | 🟡 Medium |

**발생 빈도**: 트래픽 증가 시 문제 심화 예상

**영향받는 사용자**: 전체 사용자 (API 응답 지연)

---

## 변경 필요 사유

### 1. 근본 원인 (Root Cause)

#### 리소스 경쟁
- API 요청 처리 (사용자 대기)와 무거운 스케줄 작업(크롤링, ML 추론)이 **같은 메모리/CPU를 공유**
- 스케줄 작업 실행 시 API 응답 시간 증가 (200ms → 2초)

#### 단일 장애점
- 스케줄 작업 오류(예: ML 모델 OOM) → 전체 서버 다운
- 크롤러 무한 루프 → API 서버도 응답 불가

#### 독립적 스케일링 불가
- API는 수평 확장이 필요 (트래픽 증가)
- 스케줄러는 1개 인스턴스만 필요 (중복 실행 방지)
- 현재는 **둘 다 같이 확장 또는 둘 다 확장 불가**

#### 배포 복잡도
- API 코드 수정 → 스케줄러도 재시작 → 크롤링 중단
- 스케줄러 수정 → API도 재시작 → 서비스 중단

### 2. 개발자 요구사항

- API 서버 독립적 배포 및 확장 필요
- 스케줄 작업과 API 기능의 명확한 책임 분리
- 장애 격리 (스케줄러 오류가 API에 영향 없어야 함)

### 3. 기술적 부채

- 단일 프로세스에 모든 기능 집중 → 유지보수 어려움
- ML 모델 메모리 사용량 증가 → 서버 비용 증가
- 스케일링 전략 부재 → 트래픽 증가 시 대응 불가

---

## TO-BE (변경 후 상태)

### 핵심 개선사항

```
┌─────────────────────────────────────────┐
│  🌐 API 서버 (backend/main.py)          │
│  Port: 8000                             │
│  Instances: 2 (수평 확장 가능)           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✅ 가벼운 작업만:                        │
│     - 데이터 조회 (GET)                  │
│     - 간단한 데이터 생성                 │
│                                         │
│  ⚡ 무거운 작업 요청:                     │
│     - HTTP POST → 스케줄러 서버          │
│     - 즉시 응답 (비동기 처리)            │
│                                         │
│  💡 ML 모델: ❌ 로드 안 함 (메모리 절약)  │
└─────────────────────────────────────────┘
                 ↓ HTTP Request
┌─────────────────────────────────────────┐
│  🤖 스케줄러 서버 (scheduler_main.py)    │
│  Port: 8001                             │
│  Instances: 1 (단일 인스턴스)            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  📅 정기 스케줄 작업:                     │
│     - 뉴스 크롤링 (10분마다)             │
│     - 주가 수집 (1분마다)                │
│     - 임베딩 생성 (매일)                 │
│     - 모델 평가 (매일 16:00)             │
│                                         │
│  🔧 내부 관리 API:                       │
│     - POST /internal/generate-report    │
│     - POST /internal/generate-predictions│
│     - POST /internal/initial-analysis   │
│                                         │
│  🧠 ML 모델: ✅ 여기서만 로드             │
└─────────────────────────────────────────┘
                 ↓
        📊 공유 PostgreSQL DB
```

### Before/After 비교

| 항목 | AS-IS (이전) | TO-BE (이후) | 개선 |
|------|-------------|------------|------|
| **API 응답 속도** | 느림 (ML 로드, 스케줄 경합) | 빠름 ⚡ | ✅ 2초 → 200ms |
| **메모리 사용** | 높음 (ML 모델 상시 로드) | API: 낮음, 스케줄러: 높음 | ✅ 50% 절감 (API) |
| **확장성** | 불가 (스케줄 중복) | API: 수평 확장 가능 | ✅ 트래픽 대응 가능 |
| **안정성** | 스케줄 오류 → 전체 다운 | 독립적 | ✅ 장애 격리 |
| **배포** | 전체 재시작 | 선택적 재시작 | ✅ 무중단 배포 |
| **사용자 경험** | 리포트 생성 시 대기 | 비동기 처리 | ✅ 즉시 응답 |

---

## 변경 사항 상세

(이후 구현 단계에서 작성 예정)

### 1. 주요 파일 변경

(구현 후 작성)

### 2. 코드 비교

(구현 후 작성)

### 3. 아키텍처 변경

(구현 후 작성)

---

## 테스트 결과

(테스트 후 작성 예정)

### 1. 자동 테스트

(테스트 후 작성)

### 2. 수동 테스트

(테스트 후 작성)

### 3. 검증 항목

(테스트 후 작성)

---

## 사용 방법

(구현 후 작성 예정)

### 1. 로컬 환경 적용

(구현 후 작성)

### 2. 기능 사용법

(구현 후 작성)

### 3. 예제

(구현 후 작성)

---

## 참고 사항

### 1. 변경 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| **서버 구성** | 1개 (main.py) | 2개 (main.py + scheduler_main.py) |
| **API 서버 인스턴스** | 1개 | 2개 (확장 가능) |
| **스케줄러 인스턴스** | 1개 | 1개 (고정) |
| **ML 모델 로드** | API 서버 | 스케줄러 서버만 |
| **배포 전략** | 전체 재시작 | 선택적 재시작 |

### 2. 주의 사항

#### 데이터베이스 동시 접근

**현재 보호 장치**:
- ✅ PostgreSQL UNIQUE 제약조건 (중복 방지)
- ✅ Read Committed 격리 수준
- ✅ APScheduler max_instances=1 (동시 실행 방지)
- ✅ ON CONFLICT DO UPDATE (UPSERT 패턴)
- ✅ 애플리케이션 레벨 중복 검사

**권장 설정**:
- 스케줄러 서버: 반드시 1개 인스턴스만 실행 (PM2 설정)
- DB 연결 풀: 각 서버당 적절한 크기 설정
- 모니터링: 헬스체크 엔드포인트 추가

### 3. 트러블슈팅

(구현 후 작성)

### 4. 관련 파일

**신규 생성**:
- `backend/scheduler_main.py` - 스케줄러 전용 진입점
- `ecosystem.config.js` - PM2 설정 (2개 프로세스)

**수정**:
- `backend/main.py` - ML 모델 로드 제거, 스케줄러 제거
- `backend/api/dashboard.py` - 리포트 생성 → HTTP 호출
- `backend/api/models.py` - 예측 생성 → HTTP 호출

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-29 | v1.0 | 초안 작성 (분석 단계) |

---

**작성일**: 2025-11-29
**최종 수정일**: 2025-11-29
**작성자**: young
