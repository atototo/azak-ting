# Azak 프로젝트 문서

**생성일:** 2025-11-20
**프로젝트명:** Azak (아작)
**설명:** AI 기반 주식 뉴스 분석 및 예측 시스템

---

## 프로젝트 개요

### 프로젝트 타입
- **Repository Type:** Multi-part (3개 파트)
- **주요 언어:** Python 3.11 + TypeScript 5
- **아키텍처:** Microservices (FastAPI + Next.js + Docker Compose)

### 파트별 구성

#### 1. Backend (FastAPI)
- **타입:** Backend API
- **기술 스택:** Python 3.11, FastAPI 0.104, SQLAlchemy 2.0
- **루트:** `backend/`
- **엔트리포인트:** `backend/main.py`

#### 2. Frontend (Next.js)
- **타입:** 웹 대시보드
- **기술 스택:** Next.js 15.1.4, React 19, TypeScript 5
- **루트:** `frontend/`
- **엔트리포인트:** `frontend/app/page.tsx`

#### 3. Infrastructure (Docker Compose)
- **타입:** 인프라 스택
- **기술 스택:** Docker Compose 3.8, PostgreSQL 13, Redis 7, Milvus 2.3
- **루트:** `infrastructure/`
- **설정 파일:** `infrastructure/docker-compose.yml`

---

## 빠른 참조

### Backend API
- **프레임워크:** FastAPI 0.104
- **데이터베이스:** PostgreSQL 13 + Milvus 2.3 (벡터 DB)
- **캐시/큐:** Redis 7 + Celery 5.3
- **스케줄러:** APScheduler 3.10
- **AI 통합:** OpenAI GPT-4o, text-embedding-3-small
- **알림:** Telegram Bot (python-telegram-bot 20.7)

### Frontend Dashboard
- **프레임워크:** Next.js 15 (App Router)
- **UI 라이브러리:** React 19, Tailwind CSS 3
- **상태 관리:** React Query 5, AuthContext
- **차트:** Recharts 2.15
- **아이콘:** Lucide React

### Infrastructure
- **컨테이너:** Docker 24+ / Docker Compose 3.8
- **서비스:**
  - PostgreSQL 13-alpine
  - Redis 7-alpine
  - Milvus 2.3.0 (+ etcd + MinIO)
  - Backend (FastAPI 컨테이너)
  - Frontend (Next.js 컨테이너)

---

## 생성된 문서

### 📐 아키텍처
- [전체 아키텍처 개요](./architecture/overview.md)
- [Backend 아키텍처](./architecture/backend/index.md) - 8개 주제별 문서
  - [시스템 개요](./architecture/backend/overview.md)
  - [데이터 아키텍처](./architecture/backend/data-architecture.md)
  - [API 설계](./architecture/backend/api-design.md)
  - [프로세스 흐름](./architecture/backend/processes.md)
  - [컴포넌트 구조](./architecture/backend/components.md)
  - [개발 가이드](./architecture/backend/development.md)
  - [배포 가이드](./architecture/backend/deployment.md)
  - [최적화 & 보안](./architecture/backend/optimization.md)
- [Frontend 아키텍처](./architecture/frontend.md)
- [Infrastructure 아키텍처](./architecture/infrastructure.md)
- [통합 아키텍처](./architecture/integration.md)

### 🔌 API
- [Backend API 계약](./api/contracts-backend.md)
- [Frontend API 통합](./api/contracts-frontend.md)

### 💾 데이터
- [Backend 데이터 모델](./data/models-backend.md)
- [Frontend 데이터 모델](./data/models-frontend.md)

### 🧩 컴포넌트
- [컴포넌트 인벤토리](./components/inventory.md)
- [Frontend UI 컴포넌트](./components/ui-components-frontend.md)

### 👨‍💻 개발
- [개발 가이드](./development/guide.md)
- [소스 트리 분석](./development/source-tree-analysis.md)
- [기여 가이드라인](./development/contribution-guidelines.md)

### 🚀 배포
- [배포 설정](./deployment/configuration.md)
- [인프라 구성](./deployment/infrastructure.md)
- [PM2 프로세스 관리](../PM2.md) - 운영 환경 프로세스 관리 가이드

### 📋 기획 & 분석
- [PRD (제품 요구사항 문서)](./planning/prd.md)
- [BMM 아키텍처 (2025-11-11)](./planning/bmm-architecture-2025-11-11.md)
- [구현 준비도 리포트](./planning/implementation-readiness-report-2025-11-11.md)
- [종합 분석 - Backend](./analysis/comprehensive-analysis-backend.md)
- [종합 분석 - Frontend](./analysis/comprehensive-analysis-frontend.md)
- [주식 분석 리포트 업데이트 시스템](./analysis/stock-analysis-report-update-system.md)

### 📚 레거시 문서 (참고용)
- [레거시 문서 목록](./legacy/README.md)

---

## 시작하기

### 1. 개발 환경 설정
```bash
# Python 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# Backend 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend 의존성 설치
cd frontend
npm install
```

### 2. 인프라 스택 시작
```bash
cd infrastructure
docker-compose up -d
```

### 3. Backend 실행
```bash
# 프로젝트 루트에서
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Frontend 실행
```bash
cd frontend
npm run dev
# http://localhost:3030 접속
```

### 5. 주요 엔드포인트
- **Frontend Dashboard:** http://localhost:3030
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6380
- **Milvus:** localhost:19530

---

## 프로젝트 구조

```
azak/
├── backend/                 # FastAPI 백엔드
│   ├── api/                 # API 라우터 (13개 모듈)
│   ├── auth/                # JWT 인증
│   ├── crawlers/            # 뉴스 크롤러
│   ├── db/                  # 데이터베이스 (모델, 마이그레이션)
│   ├── llm/                 # OpenAI GPT 통합
│   ├── scheduler/           # APScheduler 작업
│   ├── telegram/            # Telegram Bot
│   ├── utils/               # 유틸리티
│   └── main.py              # 애플리케이션 진입점
│
├── frontend/                # Next.js 프론트엔드
│   ├── app/                 # App Router (18개 페이지)
│   │   ├── admin/           # 관리자 대시보드
│   │   ├── components/      # 공용 컴포넌트
│   │   ├── contexts/        # React Context (Auth)
│   │   ├── login/           # 로그인
│   │   ├── models/          # 모델 관리
│   │   ├── predictions/     # 예측 조회
│   │   ├── stocks/          # 종목 상세
│   │   └── ...
│   ├── next.config.ts       # Next.js 설정
│   └── package.json
│
├── infrastructure/          # Docker Compose 스택
│   ├── docker-compose.yml   # 서비스 정의
│   ├── db-init/             # PostgreSQL 초기화
│   ├── milvus-init/         # Milvus 초기화
│   └── redis-init/          # Redis 초기화
│
├── docs/                    # 프로젝트 문서 (이 폴더)
├── scripts/                 # 유틸리티 스크립트
├── tests/                   # 테스트 코드
├── data/                    # 데이터 캐시
├── .env                     # 환경 변수
├── requirements.txt         # Python 의존성
└── pyproject.toml           # Python 프로젝트 설정
```

---

## 주요 기능

### Backend API (13개 라우터)
1. **health** - 헬스체크 및 모니터링
2. **auth** - JWT 로그인 및 인증
3. **users** - 사용자 관리 (관리자)
4. **stocks** - 종목 메타데이터
5. **stock_management** - 종목 관리 (관리자)
6. **prediction** - AI 예측 조회
7. **evaluations** - 모델 평가 지표
8. **statistics** - 통계 및 KPI
9. **dashboard** - 대시보드 데이터
10. **news** - 뉴스 크롤링 데이터
11. **ab_test** - A/B 테스트 설정
12. **models** - AI 모델 레지스트리

### 데이터 모델 (14개 테이블)
- `user` - 사용자 계정
- `stock` - 종목 마스터
- `market_data` - 시장 데이터 (OHLCV)
- `news` - 크롤링된 뉴스
- `prediction` - AI 예측 결과
- `model` - AI 모델 설정
- `model_evaluation` - 모델 평가
- `evaluation_history` - 평가 히스토리
- `daily_performance` - 일별 성과
- `stock_analysis` - 종목 분석
- `ab_test_config` - A/B 테스트 설정
- `match` - 뉴스-종목 매칭
- `financial` - 재무 데이터

### Frontend 라우트 (18개 페이지)
- `/` - 메인 대시보드
- `/login` - 로그인
- `/predictions` - 예측 목록
- `/stocks` - 종목 목록
- `/stocks/[code]` - 종목 상세
- `/models` - 모델 관리
- `/ab-test` - A/B 테스트
- `/ab-config` - A/B 설정
- `/admin/*` - 관리자 페이지 (evaluations, stocks, users, dashboard, performance)
- `/preview/*` - 미리보기 페이지

---

## 통합 아키텍처

### 데이터 흐름
1. **뉴스 크롤링** (APScheduler) → PostgreSQL (`news`)
2. **임베딩 생성** (OpenAI) → Milvus (벡터 DB)
3. **예측 생성** (GPT-4o) → PostgreSQL (`prediction`)
4. **Telegram 알림** (python-telegram-bot)
5. **대시보드 조회** (Next.js) → FastAPI → PostgreSQL/Milvus

### 인증 흐름
1. Frontend → `/api/auth` (로그인)
2. Backend → JWT 토큰 발급
3. Frontend → AuthContext 저장
4. 이후 요청 → Authorization 헤더

---

## 다음 단계

### 새로운 기능 개발 시
1. [PRD 문서](./planning/prd.md) 검토
2. [아키텍처 문서](./architecture/overview.md) 확인
3. 해당 파트별 아키텍처 참조:
   - Backend: [Backend 아키텍처](./architecture/backend.md)
   - Frontend: [Frontend 아키텍처](./architecture/frontend.md)
   - 전체 스택: [통합 아키텍처](./architecture/integration.md)

### 배포 시
1. [배포 설정](./deployment/configuration.md) 확인
2. [인프라 구성](./deployment/infrastructure.md) 검토
3. Docker Compose로 전체 스택 배포

---

**📝 문서 버전:** 1.1.0
**마지막 업데이트:** 2025-11-20 (Backend 아키텍처 문서 주제별 분리)
**생성 도구:** BMad document-project workflow (Deep Scan)
