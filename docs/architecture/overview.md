---
title: "Azak Architecture Overview"
created: 2025-11-11
updated: 2025-11-20
author: young
version: 1.3.0
status: active
environment: local-macos
revision: "실제 구현 기반 전면 업데이트 - 17개 DB 모델, 42개 API 엔드포인트, 17개 프론트엔드 라우트, 14개 크롤러, 123개 스크립트 반영"
---

# 아키텍처 (Architecture)

## 개요 (Executive Summary)

Azak은 맥북에서 PM2로 관리되는 로컬 개발/운영 환경입니다: Docker Compose가 Postgres, Redis, Milvus(etcd + MinIO 포함)를 오케스트레이션하며, PM2가 FastAPI와 Next.js 애플리케이션을 데몬 프로세스로 관리합니다. ngrok을 통해 외부 접근이 가능하며, 24/7 가동 시간, 자동 재시작, 간편한 로그 관리를 제공합니다. 이 아키텍처는 빠른 개발 반복, 쉬운 디버깅, 스크립트 기반 설정을 강조합니다.

## 프로젝트 초기화 (Project Initialization)

맥북 환경에서 프로젝트를 시작하는 방법:

**1. 인프라 서비스 시작 (Docker Compose):**
```bash
cd infrastructure && docker-compose up -d
```

**2. 애플리케이션 서비스 시작 (PM2):**
```bash
pm2 start ecosystem.config.js
```

이는 핵심 인프라 서비스(Postgres/Redis/Milvus)를 Docker Compose로 구축하고, PM2가 FastAPI 백엔드, Next.js 프론트엔드, ngrok 터널을 데몬 프로세스로 관리합니다. 자세한 내용은 [PM2 프로세스 관리 가이드](../../PM2.md)를 참조하세요.

## 의사결정 요약 (Decision Summary)

| 카테고리 (Category) | 결정 사항 (Decision) | 버전 (Version) | 영향 받는 에픽 (Affects Epics) | 근거 (Rationale) |
| -------- | -------- | ------- | ------------- | --------- |
| 호스팅 (Hosting) | 맥북 로컬, macOS, Docker 24 + Compose 2.20 + PM2 | 24.0.5 / 2.20 / 5.x | 전체 | 빠른 개발 반복, 쉬운 디버깅, 로컬 환경 최적화 |
| 프로세스 관리 (Process Management) | PM2 데몬 + ngrok 터널 | PM2 5.x | 전체 | 24/7 가동, 자동 재시작, 로그 관리, 외부 접근 |
| 백엔드 런타임 (Backend Runtime) | FastAPI + Uvicorn + Celery + APScheduler | Python 3.11 / FastAPI 0.104 | 데이터 수집, 예측, 알림 | 기존 코드베이스와 일치, 비동기 친화적 |
| 프론트엔드 (Frontend) | Next.js 15 App Router, React 19, React Query | 15.1.4 / 19.0.0 | 대시보드/모델 비교 | SSR/CSR 혼합 및 캐싱 가능 |
| 데이터 레이어 (Data Layer) | Postgres 13, Redis 7, FAISS (로컬 파일) | 13.12 / 7.0 / latest | 저장소, 임베딩, 캐싱 | FAISS 마이그레이션 완료 (2025-11-22) |
| 알림 (Notifications) | `python-telegram-bot`을 통한 Telegram 봇 | v20.7 | 알림 에픽 | 투자자에게 이미 검증됨, 새 채널 불필요 |
| 보안 (Security) | JWT 인증 + HTTPS (ngrok), `.env` 시크릿 관리 | n/a | 전체 | 간단한 인증, 로컬 시크릿 관리 |
| 관측성 (Observability) | PM2 모니터링 + `/health` 엔드포인트 | n/a | 운영 | 실시간 프로세스 모니터링, 로그 파일 관리 |

## 프로젝트 구조 (Project Structure)

```
azak/
├── backend/                      # FastAPI 애플리케이션, 서비스, 스케줄러, 크롤러
│   ├── api/                      # 10개 도메인 라우터 (auth, stocks, prediction, news, evaluations, ab_test, models, dashboard, users, health)
│   ├── services/                 # 비즈니스 로직 (price, kis_data, evaluation, stock_analysis, aggregation 등)
│   ├── db/                       # SQLAlchemy 모델 (17개), 마이그레이션, Milvus 클라이언트
│   ├── llm/                      # AI 예측 엔진 (predictor, multi_model, embedder, vector_search)
│   ├── notifications/            # Telegram 알림 시스템
│   ├── scheduler/                # APScheduler 자동화 (crawler, evaluation)
│   ├── crawlers/                 # 14개 크롤러 (뉴스, KIS API, DART)
│   ├── auth/                     # JWT 인증 및 의존성
│   ├── utils/                    # 헬퍼 함수 (시장 시간, 기술적 지표, 중복 제거 등)
│   └── main.py                   # FastAPI 앱 진입점
├── frontend/                     # Next.js 15 App Router 대시보드
│   ├── app/                      # 17개 페이지 라우트
│   │   ├── page.tsx             # 메인 사용자 대시보드
│   │   ├── login/, stocks/, predictions/, models/, ab-test/, ab-config/
│   │   ├── admin/               # 관리자 페이지 (dashboard, stocks, users, evaluations, performance)
│   │   └── preview/             # 비로그인 공개 페이지 (dashboard, stocks)
│   ├── components/              # 공통 UI 컴포넌트 (Navigation, StockChart, evaluations/ 등)
│   └── contexts/                # React Context (AuthContext)
├── infrastructure/               # docker-compose.yml, Dockerfiles
├── docs/                         # PRD, 아키텍처, 배포 가이드, 상태 추적
├── scripts/                      # 123개 유틸리티 스크립트
│   ├── 초기화: init_db.py, init_milvus.py, init_auth_db.py
│   ├── 백필: backfill_kis_daily_prices.py, backfill_market_data.py, backfill_predictions.py
│   ├── 마이그레이션: migrate_*.py, apply_migration.py
│   ├── 데이터 정제: fix_naver_news.py, cleanup_broken_news.py
│   ├── 검증: check_predictions.py, verify_prediction_data.py, daily_validation_report.py
│   └── 테스트/비교: test_*.py, compare_fdr_kis_data.py
├── data/                         # 로컬 데이터/임베딩 캐시
└── tests/                        # pytest 테스트 스위트
```

## 에픽과 아키텍처 매핑 (Epic to Architecture Mapping)

| 에픽 / 기능 (Epic / Capability) | 아키텍처 요소 (Architectural Elements) |
| --- | --- |
| 투자자 대시보드 / 모델 비교 (Investor Dashboard / Model Comparison) | frontend `app/predictions`, `app/stocks` + backend `/api/predictions`, `/api/stocks`; React Query 캐시 + Postgres 뷰 + Milvus 조회 |
| Telegram 알림 (Telegram Alerts) | backend `notifications/` 워커, APScheduler 작업, Redis 브로커, Telegram 봇 토큰 |
| 데이터 수집 및 스케줄링 (Data Ingestion & Scheduling) | backend `crawlers/`, `scheduler/`, Compose 관리 Milvus/Postgres 볼륨 |
| 관리자 제어 (AB 테스트, 모델) | frontend `app/ab-test`, `app/models`; backend `/api/ab-test`, `/api/models`; DB 테이블 `ab_test_config`, `model` |

## 기술 스택 상세 (Technology Stack Details)

### 핵심 기술 (Core Technologies)

- **프론트엔드 (Frontend):** Next.js 15.1.4, React 19.0.0, TypeScript 5.x, Tailwind CSS 3.4.1, React Query 5.61.5, Recharts 2.15.0, lucide-react 0.468.0, react-hot-toast 2.6.0, date-fns 4.1.0, clsx 2.1.1, class-variance-authority 0.7.1, tailwind-merge 2.5.0
- **백엔드 (Backend):** Python 3.11, FastAPI 0.104+, SQLAlchemy 2, Pydantic v2, Uvicorn, Celery 5.3, APScheduler 3.10
- **데이터 및 인프라 (Data & Infra):** Postgres 13-alpine (포트 5432), Redis 7-alpine (포트 6380→6379), FAISS (로컬 파일 기반), Docker Compose v3.8
- **AI 프로바이더 (AI Providers):** OpenAI GPT-4o (예측), KoSimCSE (BM-K/KoSimCSE-roberta, 로컬 임베딩)

### 통합 지점 (Integration Points)

1. **프론트엔드 ↔ 백엔드 (Frontend ↔ Backend):** JWT 인증 헤더와 함께 `/api/*`로 HTTPS REST 요청; React Query가 캐싱/무효화 처리.
2. **백엔드 ↔ Postgres:** `backend/db/session.py`의 SQLAlchemy 세션 팩토리를 리포지토리 전체에서 사용.
3. **백엔드 ↔ Redis:** Celery 브로커 + 단기 캐시(시장 스냅샷, 쓰로틀링)를 `redis://` 환경 변수를 통해 사용.
4. **백엔드 ↔ FAISS:** `backend/llm/vector_search.py`가 뉴스 임베딩을 로컬 파일(`data/faiss_index/`)에 저장하고 조회.
5. **백엔드 ↔ Telegram:** `python-telegram-bot` 클라이언트가 시크릿의 봇 토큰을 사용하여 알림 게시.
6. **스케줄러 ↔ 서비스 (Schedulers ↔ Services):** APScheduler + Celery 태스크가 설정된 간격으로 크롤러와 평가 작업 실행.

## 새로운 패턴 디자인 (Novel Pattern Designs)

_이번 릴리스에서는 새로운 패턴이 필요하지 않으며, 표준 서비스/라우터 계층화로 충분합니다._

## 구현 패턴 (Implementation Patterns)

- **라우터-서비스-리포지토리 (Router-Service-Repository):** API 모듈을 얇게 유지하고, 리포지토리/LLM 호출을 오케스트레이션하는 서비스 클래스에 위임.
- **작업 멱등성 (Job Idempotency):** 스케줄러 작업은 Redis 락 또는 타임스탬프 가드를 통해 중복 방지 보장.
- **React Query 훅 (React Query Hooks):** 각 기능은 훅(예: `usePredictions`, `useStockDetail`)을 정의하여 fetch/transform 로직을 중앙화.
- **환경 분리 (Environment Separation):** `.env`가 로컬 Compose를 구동; 프로덕션은 코드 변경 없이 AWS SSM 또는 EC2 user-data에서 동일한 키 로드.

## 일관성 규칙 (Consistency Rules)

### 명명 규칙 (Naming Conventions)

- Python 모듈/함수는 snake_case; 클래스는 PascalCase.
- React 컴포넌트는 PascalCase; 훅은 `use`로 시작. DB 테이블은 단수형 소문자.
- API 라우트는 `/api/{domain}`으로 시작; Telegram 명령어는 kebab-case.

### 코드 구성 (Code Organization)

- 새로운 백엔드 도메인은 `api/`, `services/`, `db/models/`에 병렬 폴더 생성.
- 공유 유틸리티는 중복을 피하기 위해 `backend/utils/`에 위치.
- 프론트엔드 기능 폴더는 `app/` 내부에서 라우트 로직과 컴포넌트를 함께 배치.

### 오류 처리 (Error Handling)

- FastAPI 라우터는 의미 있는 상태 코드와 함께 `HTTPException` 발생.
- 스케줄러 작업은 중요 섹션을 try/except로 감싸고 구조화된 오류 로그 기록.

### 로깅 전략 (Logging Strategy)

- Python `logging` 모듈은 상관 ID(요청 ID, 작업 이름)와 함께 JSON 유사 라인 출력.
- Compose 로그는 journald/CloudWatch 에이전트로 집계; `/health` 실패 시 알림 트리거.

## 데이터 아키텍처 (Data Architecture)

### PostgreSQL 테이블 (17개 모델)

**핵심 엔티티:**
- `User`, `TelegramUser` - 사용자 및 텔레그램 연동
- `Stock`, `StockPrice`, `StockPriceMinute` - 종목 기본 정보, 일봉, 분봉
- `NewsArticle` - 뉴스 데이터
- `NewsStockMatch` - 뉴스-주식 매칭
- `Prediction` - AI 예측 결과
- `Model` - LLM 모델 정보
- `ABTestConfig` - A/B 테스트 설정
- `StockAnalysis` - 주식 분석 리포트

**시장 데이터 (KIS API):**
- `StockOrderbook` - 호가 데이터
- `StockCurrentPrice` - 현재가
- `StockOvertimePrice` - 시간외 주가
- `InvestorTrading` - 투자자별 매매 동향 (외국인/기관/개인)
- `SectorIndex` - 섹터 지수
- `IndexDailyPrice` - 시장 지수 일봉

**재무 데이터:**
- `ProductInfo` - 상품 정보 (업종, 시가총액)
- `FinancialRatio` - 재무비율 (ROE, PER, PBR 등)

**평가 및 성과:**
- `ModelEvaluation` - 모델 평가
- `EvaluationHistory` - 평가 이력
- `DailyPerformance` - 일일 성과

**관계 (Relationships):**
- `Prediction` FK → `Stock`, `Model`
- `NewsStockMatch`는 `NewsArticle` ↔ `Stock` 연결
- `EvaluationHistory` → `Model` 추세 추적
- `StockAnalysis` → `Stock`, `Model`

### FAISS 벡터 인덱스
- `news_embeddings` - KoSimCSE (BM-K/KoSimCSE-roberta, 768차원)
- Postgres ID로 키잉, 메타데이터는 SQL 테이블에 미러링
- 로컬 파일 저장: `data/faiss_index/`
- 마이그레이션 완료: 2025-11-22 (7,040개 벡터)

## API 계약 (API Contracts - 42개 엔드포인트)

### 1. 인증 (`/api/auth`) - 4개
- POST `/api/auth/login` - 이메일/비밀번호 로그인
- POST `/api/auth/logout` - 로그아웃
- GET `/api/auth/me` - 현재 사용자 정보
- GET `/api/auth/check` - 인증 상태 확인

### 2. 종목 (`/api/stocks`) - 5개
- GET `/api/stocks/summary` - 모든 활성 종목 요약
- GET `/api/stocks/{stock_code}` - 종목 상세 정보
- GET `/api/stocks/{stock_code}/prices` - 주가 히스토리
- GET `/api/stocks/{stock_code}/predictions` - 예측 목록
- GET `/api/stocks/{stock_code}/analysis-reports` - 모델별 AI 리포트

### 3. 예측 (`/api/predict`) - 4개
- POST `/api/predict` - 뉴스 기반 예측
- GET `/api/predict/cache/stats` - 캐시 통계
- GET `/api/predict/{news_id}` - 예측 결과 조회
- DELETE `/api/predict/cache` - 캐시 삭제

### 4. 뉴스 (`/api/news`) - 2개
- GET `/api/news` - 뉴스 목록 (검색/필터/페이지네이션)
- GET `/api/news/{news_id}` - 뉴스 상세

### 5. 평가 (`/api/evaluations`) - 7개
- GET `/api/evaluations/all` - 평가 목록
- GET `/api/evaluations/queue` - 평가 대기 목록
- GET `/api/evaluations/daily` - 특정 날짜 평가
- POST `/api/evaluations/{evaluation_id}/rate` - 사람 평가 저장
- GET `/api/evaluations/dashboard` - 평가 대시보드
- GET `/api/evaluations/model/{model_id}` - 모델 상세 분석
- GET `/api/evaluations/model/{model_id}/stocks` - 종목별 성능

### 6. A/B 테스트 (`/api/ab-test`) - 6개
- POST `/api/ab-test/predict` - 모델 비교 예측
- GET `/api/ab-test/status` - 설정 상태 (레거시)
- GET `/api/ab-test/config` - 현재 A/B 설정
- POST `/api/ab-test/config` - 설정 변경
- GET `/api/ab-test/prediction-status` - 예측 진행 상태
- GET `/api/ab-test/history` - 설정 변경 이력

### 7. 모델 (`/api/models`) - 6개
- GET `/api/models` - 모델 목록
- GET `/api/models/{model_id}` - 모델 조회
- POST `/api/models` - 모델 추가 (백그라운드 예측 자동 생성)
- PUT `/api/models/{model_id}` - 모델 수정
- PATCH `/api/models/{model_id}/toggle` - 활성화/비활성화
- DELETE `/api/models/{model_id}` - 모델 삭제

### 8. 대시보드 (`/api/dashboard`) - 7개
- GET `/api/dashboard/summary` - 대시보드 요약
- GET `/api/predictions/recent` - 최근 예측
- GET `/api/system/status` - 시스템 상태
- POST `/api/reports/force-update/{stock_code}` - 종목 리포트 강제 업데이트 (비동기)
- POST `/api/reports/force-update` - 오래된 리포트 일괄 업데이트
- GET `/api/dashboard/data-check` - 데이터 존재 확인
- GET `/api/dashboard/market-momentum` - 실시간 시장 모멘텀

### 9. 사용자 (`/api/users`) - 4개 (관리자 전용)
- GET `/api/users` - 사용자 목록
- POST `/api/users` - 사용자 생성
- PATCH `/api/users/{user_id}` - 사용자 수정
- DELETE `/api/users/{user_id}` - 사용자 삭제

### 10. 헬스체크 - 4개
- GET `/health` - 전체 시스템 헬스 (PostgreSQL, Milvus, Redis)
- GET `/health/liveness` - Liveness Probe
- GET `/health/readiness` - Readiness Probe
- GET `/stats` - 시스템 통계

## 보안 아키텍처 (Security Architecture)

- JWT 토큰은 `AuthContext`를 통해 클라이언트 측에 저장; 백엔드는 라우트별로 역할 검증.
- HTTPS는 ngrok 터널을 통해 제공; 백엔드는 localhost에서 수신, Compose 네트워크는 비공개.
- 시크릿 (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, DB 자격 증명)은 `.env` 파일을 통해 로컬 관리.
- DB/Redis/Milvus 포트는 localhost로 제한; ngrok만 공개적으로 노출.

## 성능 고려사항 (Performance Considerations)

- React Query 캐싱은 중복 페치를 줄임; 대시보드에 stale-while-revalidate 접근 방식.
- Redis는 자주 요청되는 메트릭을 캐시; TTL은 오래된 데이터를 피하도록 조정.
- APScheduler는 무거운 작업(크롤, 임베딩)을 분산하여 로컬 시스템 부하 관리.
- PM2 메모리 제한 (백엔드 2GB, 프론트엔드 1GB)으로 안정성 보장.
- 헬스체크는 저하된 서비스 감지; Compose 재시작 정책과 PM2 자동 재시작으로 안정성 유지.

## 배포 아키텍처 (Deployment Architecture)

### 인프라 서비스 (Infrastructure Services) - Docker Compose

- `infrastructure/docker-compose.yml`이 Postgres/Redis/Milvus/MinIO/etcd 관리.
- 모든 데이터베이스 및 벡터 저장소 서비스는 컨테이너화된 데몬으로 실행.
- 영구 볼륨은 컨테이너 재시작 시 데이터 생존 보장.

### 애플리케이션 서비스 (Application Services) - PM2

**프로덕션 배포는 24/7 데몬 프로세스 관리를 위해 PM2 사용:**

- **azak-backend**: FastAPI 애플리케이션 (`uv run python -m backend.main`, 자동 재시작, 2GB 메모리 제한)
- **azak-frontend**: Next.js 개발 서버 (`npm run dev`, 포트 3030, 자동 재시작, 1GB 메모리 제한)
- **azak-ngrok**: 외부 접근을 위한 공개 터널 (`ngrok http 3030 --domain=azak.ngrok.app`, 예약 도메인 사용)

**장점 (Benefits):**
- 크래시 또는 시스템 재부팅 시 자동 재시작
- 중앙화된 로그 관리 (`logs/` 디렉토리)
- `pm2 reload`로 무중단 재로드
- `pm2 monit`를 통한 실시간 모니터링

자세한 운영 지침은 [PM2 프로세스 관리 가이드](../../PM2.md)를 참조하세요.

### PM2 vs Docker Compose 전략

| 컴포넌트 (Component) | 오케스트레이터 (Orchestrator) | 이유 (Reason) |
|-----------|--------------|--------|
| Postgres, Redis, Milvus | Docker Compose | 상태 저장 서비스는 컨테이너 격리의 이점 |
| Backend, Frontend | PM2 | 빠른 반복, 쉬운 디버깅, 네이티브 프로세스 관리 |
| ngrok | PM2 | 호스트 네트워크 접근 필요 |

### 외부 접근 및 모니터링 (External Access & Monitoring)

- **ngrok 터널**: 외부 접근을 위한 HTTPS 터널 (https://azak.ngrok.app, 예약 도메인)
- **백엔드**: PM2로 관리되는 FastAPI 서비스 (localhost:8000, uv 런타임)
- **프론트엔드**: PM2로 관리되는 Next.js 개발 서버 (localhost:3030)
- **모니터링**:
  - `pm2 monit` - 실시간 프로세스 모니터링 (CPU, 메모리)
  - `pm2 logs` - 통합 로그 관리
  - `/health` 엔드포인트 - 서비스 상태 확인
  - Telegram 봇 - 중요 작업 알림

## 개발 환경 (Development Environment)

### 사전 요구사항 (Prerequisites)

- **Python 3.11** (uv 패키지 관리자 권장)
- **Node.js >= 20.0.0** (npm >= 10.0.0)
- **Docker 24.0.5**, **Compose 2.20**
- **PM2 5.x** (프로세스 관리)
- **ngrok** (외부 접근용 터널)
- OpenAI/OpenRouter API 키, Telegram 봇 토큰, Postgres 자격 증명

### 설정 명령어 (Setup Commands)

```bash
# 1. Python 가상환경 설정 (uv 사용 권장)
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -r requirements-dev.txt

# 또는 uv 사용:
# uv sync

# 2. Frontend 의존성 설치
cd frontend && npm install && cd ..

# 3. 인프라 서비스 시작 (Docker Compose)
cd infrastructure && docker-compose up -d && cd ..

# 4. 애플리케이션 서비스 시작 (PM2)
pm2 start ecosystem.config.js

# 5. 서비스 확인
pm2 status
pm2 logs
```

자세한 PM2 운영 가이드는 [PM2.md](../../PM2.md)를 참조하세요.

## 아키텍처 의사결정 기록 (Architecture Decision Records - ADRs)

1. **맥북 로컬 환경 (Local macOS deployment):** 빠른 개발 반복과 쉬운 디버깅을 위해 선택; 필요 시 클라우드로 확장 가능.
2. **PM2 프로세스 관리 (PM2 process management):** Docker 컨테이너보다 빠른 반복, 쉬운 로그 접근, 네이티브 프로세스 관리.
3. **uv 패키지 관리자 (uv package manager):** 빠른 Python 패키지 설치 및 의존성 관리; pip 대비 속도 향상.
4. **ngrok 예약 도메인 (ngrok reserved domain):** 외부 접근을 위한 고정 HTTPS 도메인 (azak.ngrok.app); 별도 인증서 불필요.
5. **Compose 오케스트레이터 (Compose orchestrator):** 인프라 서비스(DB, 캐시)는 Docker Compose로 격리하여 안정성 확보.
6. **FAISS 로컬 임베딩 (FAISS local embeddings):** Milvus 서버 의존성 제거, 파일 기반 단순화 (2025-11-22 마이그레이션).
7. **Telegram 알림 유지 (Telegram alerts retained):** 간단하고 효과적인 알림 채널로 검증됨.
8. **React 19 + Next.js 15 (Latest stable):** 최신 안정화 버전으로 성능 및 개발 경험 향상.

## 개발 워크플로우 (Development Workflow)

```bash
# 인프라 시작
cd infrastructure && docker-compose up -d

# 백엔드 (로컬 개발)
uv run python -m backend.main
# 또는
python -m backend.main

# 프론트엔드 (로컬 개발)
cd frontend && npm run dev

# PM2로 전체 스택 관리 (권장)
pm2 start ecosystem.config.js
pm2 save                    # 현재 프로세스 목록 저장
pm2 startup                 # 부팅 시 자동 시작 설정

# 모니터링
pm2 monit                   # 실시간 모니터링
pm2 logs                    # 통합 로그
pm2 status                  # 프로세스 상태

# 인프라 중지
cd infrastructure && docker-compose down
```

---
_Last Updated: 2025-11-25 by young_
_Initial Version: 2025-11-11_
_Major Update (v1.4.0): FAISS Migration, AsyncIOScheduler, predicted_at field_
