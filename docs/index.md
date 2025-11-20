## 프로젝트 문서 인덱스

### 프로젝트 개요
- **타입:** 3개 파트로 구성된 멀티파트 저장소 (backend, frontend, infrastructure)
- **주요 언어:** Python 3.11 + TypeScript/React
- **아키텍처:** FastAPI 서비스 + Next.js 대시보드 + Docker Compose 데이터 스택

### 파트별 빠른 참조
#### Backend API (backend)
- **기술 스택:** FastAPI, SQLAlchemy, Celery, APScheduler
- **진입점:** `backend/main.py`
- **패턴:** API + 비동기 워커

#### 웹 대시보드 (frontend)
- **기술 스택:** Next.js 15, React 19, Tailwind, React Query
- **루트:** `frontend/`
- **패턴:** App Router (하이브리드 SSR/CSR) + 보호된 라우트

#### 인프라 스택 (infrastructure)
- **기술 스택:** Docker Compose 3.8 (Postgres, Redis, Milvus, MinIO, etcd)
- **루트:** `infrastructure/`
- **패턴:** EC2 배포를 위한 데이터 서비스 우선 스택

### 📐 아키텍처
- [전체 아키텍처 개요](./architecture/overview.md)
- [Backend 아키텍처](./architecture/backend.md)
- [Frontend 아키텍처](./architecture/frontend.md)
- [Infrastructure 아키텍처](./architecture/infrastructure.md)
- [통합 아키텍처 (멀티파트)](./architecture/integration.md)

### 🔌 API
- [Backend API 계약](./api/contracts-backend.md)
- [Frontend API 계약](./api/contracts-frontend.md)

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

### 📋 기획 & 분석
- [PRD (제품 요구사항 문서)](./planning/prd.md)
- [BMM 아키텍처 (2025-11-11)](./planning/bmm-architecture-2025-11-11.md)
- [구현 준비도 리포트](./planning/implementation-readiness-report-2025-11-11.md)
- [스프린트 변경 제안](./planning/sprint-change-proposal-2025-11-02.md)
- [종합 분석 - Backend](./analysis/comprehensive-analysis-backend.md)
- [종합 분석 - Frontend](./analysis/comprehensive-analysis-frontend.md)
- [주식 분석 리포트 업데이트 시스템](./analysis/stock-analysis-report-update-system.md)

### 📚 레거시 문서 (참고용)
- [API 마이그레이션 Epic 3](./legacy/api-migration-epic3.md)
- [크롤링 전략](./legacy/crawling-strategy.md)
- [대시보드 UX 디자인](./legacy/dashboard-ux-design.md)
- [멀티 모델 설계](./legacy/multi-model-design.md)
- [멀티 모델 구현](./legacy/multi-model-implementation.md)
- [Reddit 통합 설계](./legacy/reddit-integration-design.md)
- [토큰 아키텍처](./legacy/token-architecture.md)

### 🚀 시작하기
1. **개발 환경 설정**: [개발 가이드](./development/guide.md)를 참고하여 의존성 설치 및 로컬 환경 구축
2. **배포 환경 구축**: [배포 설정](./deployment/configuration.md) + [인프라 구성](./deployment/infrastructure.md)으로 EC2 스택 프로비저닝
3. **시스템 통합**: [통합 아키텍처](./architecture/integration.md)로 Frontend ↔ Backend ↔ Data Services 연결
4. **프로젝트 기획**: 새 기능 개발 시 [PRD](./planning/prd.md)를 참고하여 요구사항 정의
