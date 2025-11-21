# 컴포넌트 구조

## 컴포넌트 개요

프론트엔드는 재사용 가능한 공통 컴포넌트와 페이지별 컴포넌트로 구성됩니다.

## 공통 컴포넌트 (`app/components/`)

### 레이아웃 컴포넌트

#### `LayoutWrapper.tsx`
- **역할**: 전체 레이아웃 래퍼
- **기능**:
  - 네비게이션 바 표시
  - 메인 콘텐츠 영역
  - 푸터 표시
- **사용 위치**: `app/layout.tsx`

#### `Navigation.tsx`
- **역할**: 상단 네비게이션 바
- **기능**:
  - 로고 및 앱 이름
  - 메인 메뉴 (홈, 종목, 예측, 모델, A/B 테스트)
  - 사용자 프로필 및 로그아웃
  - 관리자 메뉴 (관리자만)
- **상태**: `useAuth()` 훅 사용

#### `Footer.tsx`
- **역할**: 하단 푸터
- **기능**:
  - 저작권 정보
  - 링크 (이용약관, 개인정보처리방침 등)

### 인증 컴포넌트

#### `ProtectedRoute.tsx`
- **역할**: 인증 필요 페이지 보호
- **기능**:
  - 인증 상태 확인
  - 비인증 사용자 로그인 페이지로 리다이렉트
  - 관리자 권한 체크 (옵션)
- **사용 예시**:
```tsx
<ProtectedRoute requireAdmin={true}>
  <AdminDashboard />
</ProtectedRoute>
```

### 데이터 표시 컴포넌트

#### `StockChart.tsx`
- **역할**: 주가 차트 표시
- **라이브러리**: Recharts
- **기능**:
  - OHLCV 캔들스틱 차트
  - 일봉/1분봉 전환
  - 기간 선택 (1일, 1주, 1개월, 3개월)
  - 툴팁 및 축 레이블
- **Props**:
  - `stockCode`: 종목 코드
  - `chartType`: 차트 유형 (line, candle)
  - `period`: 조회 기간

#### `NewsImpact.tsx`
- **역할**: 뉴스 임팩트 분석 표시
- **기능**:
  - 뉴스 제목 및 출처
  - 예상 임팩트 (긍정/부정/중립)
  - 신뢰도 점수
  - 뉴스 상세 링크
- **Props**:
  - `news`: 뉴스 데이터 배열

#### `PredictionStatusBanner.tsx`
- **역할**: 예측 생성 상태 배너
- **기능**:
  - 예측 생성 중 로딩 표시
  - 완료 시 성공 메시지
  - 실패 시 에러 메시지
- **상태**: React Query의 mutation 상태 사용

#### `DataSourceBadges.tsx`
- **역할**: 데이터 출처 뱃지 표시
- **기능**:
  - KIS API 연동 상태
  - 뉴스 크롤러 상태
  - 마지막 업데이트 시간
- **스타일**: Tailwind CSS 뱃지

#### `StockDetailView.tsx` ⭐ **신규 공통 컴포넌트**
- **역할**: 종목 상세 정보 표시 (공통 컴포넌트로 추출, 1369줄 감소)
- **기능**:
  - 종목 기본 정보 및 현재가
  - 주가 차트 (Recharts)
  - AI 종합 투자 리포트
  - 최근 뉴스 & AI 분석
  - 시장 동향 통계
- **Props**:
  - `data`: 종목 상세 데이터
  - `abConfig`: A/B 테스트 설정 (옵션)
  - `showBackButton`: 뒤로가기 버튼 표시 여부 (기본값: false)
  - `showForceUpdate`: 리포트 업데이트 버튼 표시 여부 (기본값: false)
  - `onForceUpdate`: 업데이트 핸들러 (옵션)
  - `updating`: 업데이트 중 상태 (옵션)
  - `updateMessage`: 업데이트 메시지 (옵션)
- **사용 위치**:
  - `/stocks/[stockCode]/page.tsx` (인증 필요, 전체 기능)
  - `/public/[linkId]/page.tsx` (인증 불필요, 제한된 기능)
- **리팩토링 효과**:
  - 코드 중복 제거: 1369줄 감소
  - UI 일관성 보장: 두 페이지가 항상 동일한 UI
  - 유지보수 향상: UI 수정 시 1곳만 수정

### 평가 관련 컴포넌트 (`app/components/evaluations/`)

#### `MetricBreakdownChart.tsx`
- **역할**: 모델 평가 메트릭 차트
- **라이브러리**: Recharts
- **기능**:
  - 정확도, 방향성, 최종 점수 바 차트
  - 모델별 비교
  - 기간별 추이

#### `StockPerformanceTable.tsx`
- **역할**: 종목별 성과 테이블
- **기능**:
  - 종목 코드 및 이름
  - 예측 정확도
  - 목표가 달성률
  - 정렬 및 필터링

## 페이지별 컴포넌트

### 메인 대시보드 (`app/page.tsx`)

- **StatCard**: 통계 카드 (총 예측, 평균 정확도 등)
- **RecentNewsCard**: 최근 뉴스 카드
- **ModelPerformanceChart**: 모델 성능 차트
- **QuickActionButtons**: 빠른 액션 버튼

### 종목 상세 (`app/stocks/[stockCode]/page.tsx`)

**리팩토링**: StockDetailView 공통 컴포넌트 사용 (1107줄 → 449줄, 59% 감소)

- **StockDetailView**: 종목 상세 UI (공통 컴포넌트)
  - Props: `showBackButton={true}`, `showForceUpdate={true}`
- **데이터 페칭**: useEffect로 종목 데이터 로드
- **상태 관리**: 로컬 상태로 업데이트 관리

### 공개 프리뷰 (`app/public/[linkId]/page.tsx`) ⭐ **신규 페이지**

**UUID 기반 공개 프리뷰 링크 시스템 (블로그/SNS 홍보용)**

- **StockDetailView**: 종목 상세 UI (공통 컴포넌트 재사용)
  - Props: `showBackButton={false}`, `showForceUpdate={false}`
- **2단계 데이터 페칭**:
  1. UUID → stock_code 조회 (`/api/public-preview/{linkId}`)
  2. stock_code → 종목 상세 조회 (`/api/stocks/{stockCode}`)
- **특징**:
  - 인증 불필요 (middleware에서 `/public/*` 우회)
  - URL에 종목코드 노출 안 됨 (보안)
  - 관리자 전용 버튼 미표시

### 관리자 평가 (`app/admin/evaluations/page.tsx`)

- **EvaluationList**: 평가 목록
- **ModelComparisonChart**: 모델 비교 차트
- **DateRangePicker**: 날짜 범위 선택기

### 관리자 사용자 (`app/admin/users/page.tsx`)

- **UserTable**: 사용자 테이블
- **UserRoleToggle**: 권한 토글
- **UserStatusToggle**: 계정 상태 토글

## 컴포넌트 계층 구조

```
RootLayout (layout.tsx)
├── AuthProvider (contexts/AuthContext.tsx)
└── LayoutWrapper (components/LayoutWrapper.tsx)
    ├── Navigation (components/Navigation.tsx)
    ├── Main Content
    │   ├── ProtectedRoute (조건부)
    │   └── Page Content
    │       ├── StockChart
    │       ├── NewsImpact
    │       ├── PredictionStatusBanner
    │       └── DataSourceBadges
    └── Footer (components/Footer.tsx)
```

## 컴포넌트 설계 원칙

### 1. 재사용성
- 공통으로 사용되는 UI는 `app/components/`에 배치
- Props로 커스터마이징 가능하게 설계

### 2. 관심사 분리
- 데이터 페칭: React Query 훅 사용
- 비즈니스 로직: 커스텀 훅으로 분리
- UI 렌더링: 컴포넌트에만 집중

### 3. 타입 안전성
- 모든 컴포넌트 Props는 TypeScript 인터페이스 정의
- API 응답 DTO도 타입 정의

### 4. 접근성
- 시맨틱 HTML 태그 사용
- ARIA 속성 적용 (해당 시)
- 키보드 네비게이션 지원

## 스타일링 규칙

### Tailwind CSS 유틸리티 클래스

- **레이아웃**: `flex`, `grid`, `container`
- **간격**: `p-4`, `m-2`, `space-x-4`
- **색상**: `bg-blue-500`, `text-gray-700`
- **반응형**: `sm:`, `md:`, `lg:` 접두사

### 컴포넌트 Variant

`class-variance-authority` 사용:

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center",
  {
    variants: {
      variant: {
        primary: "bg-blue-500 text-white",
        secondary: "bg-gray-200 text-gray-800",
      },
      size: {
        sm: "px-3 py-1 text-sm",
        md: "px-4 py-2",
        lg: "px-6 py-3 text-lg",
      },
    },
  }
);
```

## 아이콘 사용

**lucide-react** 라이브러리 사용:

```tsx
import { Home, TrendingUp, Settings } from "lucide-react";

<Home className="w-5 h-5" />
<TrendingUp className="w-6 h-6 text-green-500" />
<Settings className="w-4 h-4" />
```

## 관련 문서

- [UI 컴포넌트 인벤토리](../../components/ui-components-frontend.md) - 전체 컴포넌트 목록
- [상태 관리](./state-management.md) - React Query, AuthContext
- [라우팅 & 페이지](./routing-pages.md) - 페이지 구조
