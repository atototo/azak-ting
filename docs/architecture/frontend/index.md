# 프론트엔드 아키텍처 (Next.js 대시보드)

Next.js 15 App Router 기반의 투자 인사이트 대시보드입니다. FastAPI 백엔드와 REST API로 통신하며, React Query로 데이터 캐싱, AuthContext로 세션 관리, Tailwind CSS로 UI를 구현합니다.

## 문서 구조

프론트엔드 아키텍처 문서는 다음과 같이 주제별로 구성되어 있습니다:

### 📋 [시스템 개요](./overview.md)
- 개요 및 기술 스택
- 아키텍처 패턴
- 시스템 아키텍처 다이어그램
- 프로젝트 구조
- API 프록시 설정
- 인증 구조

### 🗺️ [라우팅 & 페이지](./routing-pages.md)
- 페이지 목록 (18개 라우트)
- 레이아웃 구조
- 동적 라우팅
- 네비게이션 메뉴
- 라우팅 플로우 다이어그램

### 🧩 [컴포넌트 구조](./components.md)
- 공통 컴포넌트
- 페이지별 컴포넌트
- 컴포넌트 계층 구조
- 스타일링 규칙
- 아이콘 사용

### 📊 [상태 관리](./state-management.md)
- AuthContext (인증 상태)
- React Query (서버 상태)
- 로컬 상태 (useState, useReducer)
- 캐싱 전략
- 상태 관리 흐름

### 👨‍💻 [개발 가이드](./development.md)
- 환경 요구사항
- 프로젝트 설정
- 개발 서버 실행
- 코드 품질 (ESLint, TypeScript)
- 디버깅
- 문제 해결

### 🚀 [배포 가이드](./deployment.md)
- Node.js 서버 배포
- Docker 배포
- Nginx 리버스 프록시
- 성능 최적화
- 모니터링
- 보안 고려사항

## 빠른 시작

### 개발 환경 설정
```bash
# Frontend 디렉터리로 이동
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
# http://localhost:3030
```

### 프로덕션 빌드
```bash
# 빌드
npm run build

# 프로덕션 서버 실행
npm run start
```

## 주요 기능

### 페이지 (18개 라우트)

#### 공개 페이지
- 로그인 (`/login`)

#### 인증 필요 페이지
- 메인 대시보드 (`/`)
- 종목 목록 (`/stocks`)
- 종목 상세 (`/stocks/[stockCode]`)
- 예측 목록 (`/predictions`)
- 모델 관리 (`/models`)
- A/B 테스트 결과 (`/ab-test`)
- A/B 테스트 설정 (`/ab-config`)

#### 관리자 페이지 (`/admin/*`)
- 관리자 대시보드
- 모델 평가 관리
- 종목 관리
- 사용자 관리
- 성능 모니터링

#### 특수 페이지 (`/preview/*`)
- 블로그 캡처용 프리뷰 페이지 (토큰 인증)

### 주요 컴포넌트

#### 레이아웃
- `LayoutWrapper`: 전체 레이아웃
- `Navigation`: 네비게이션 바
- `Footer`: 푸터

#### 인증
- `ProtectedRoute`: 인증 보호

#### 데이터 표시
- `StockChart`: 주가 차트 (Recharts)
- `NewsImpact`: 뉴스 임팩트 분석
- `PredictionStatusBanner`: 예측 상태 배너
- `DataSourceBadges`: 데이터 출처 뱃지

#### 평가
- `MetricBreakdownChart`: 메트릭 차트
- `StockPerformanceTable`: 성과 테이블

### 기술 스택

- **Next.js 15.1.4**: React 프레임워크
- **React 19**: UI 라이브러리
- **TypeScript 5**: 타입 안전성
- **Tailwind CSS 3.4**: 스타일링
- **React Query 5.61**: 데이터 페칭 및 캐싱
- **Recharts 2.15**: 차트
- **lucide-react**: 아이콘
- **date-fns**: 날짜 포맷팅

### 인증

- **세션 쿠키**: `azak_session` (24시간)
- **Middleware**: 자동 인증 체크
- **AuthContext**: 클라이언트 상태 관리

### API 통합

- **프록시**: `/api/*` → `http://127.0.0.1:8000/*`
- **REST API**: FastAPI 백엔드와 통신
- **React Query**: 자동 캐싱 및 재검증

## 관련 문서

### 다른 아키텍처 문서
- [전체 아키텍처 개요](../overview.md)
- [Backend 아키텍처](../backend/index.md)
- [Infrastructure 아키텍처](../infrastructure.md)
- [통합 아키텍처](../integration.md)

### API 및 데이터 모델
- [Frontend API 통합](../../api/contracts-frontend.md)
- [Frontend 데이터 모델](../../data/models-frontend.md)

### 컴포넌트 및 UI
- [UI 컴포넌트 인벤토리](../../components/ui-components-frontend.md)

### 개발 및 배포
- [개발 가이드](../../development/guide.md)
- [소스 트리 분석](../../development/source-tree-analysis.md)
- [배포 설정](../../deployment/configuration.md)
- [PM2 가이드](../../../PM2.md)

---

**📝 문서 버전:** 1.0.0
**마지막 업데이트:** 2025-11-20
**특징**: Backend와 동일한 수준의 상세 문서, 6개 주제별 문서로 구성
