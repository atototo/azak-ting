# 라우팅 & 페이지 구조

## 라우팅 개요

Next.js 15 App Router를 사용하여 파일 시스템 기반 라우팅을 구현합니다. 모든 페이지는 `app/` 디렉터리 아래에 위치하며, `page.tsx` 파일이 해당 경로의 페이지가 됩니다.

## 페이지 목록

### 공개 페이지

#### `/login` - 로그인
- **파일**: `app/login/page.tsx`
- **설명**: 이메일/비밀번호 로그인 폼
- **인증**: 불필요
- **기능**: 로그인 성공 시 `/`로 리다이렉트

### 인증 필요 페이지

#### `/` - 메인 대시보드
- **파일**: `app/page.tsx`
- **설명**: 전체 투자 인사이트 대시보드
- **주요 기능**:
  - 최근 뉴스 요약
  - 주요 종목 현황
  - 모델 성능 지표
  - 예측 정확도 차트
  - 빠른 액션 버튼

#### `/stocks` - 종목 목록
- **파일**: `app/stocks/page.tsx`
- **설명**: 추적 중인 종목 목록
- **주요 기능**:
  - 종목 검색 및 필터링
  - 우선순위별 정렬
  - 현재가 및 등락률 표시

#### `/stocks/[stockCode]` - 종목 상세
- **파일**: `app/stocks/[stockCode]/page.tsx`
- **설명**: 개별 종목 상세 정보
- **동적 라우팅**: URL 파라미터로 종목 코드 전달
- **주요 기능**:
  - 종목 기본 정보
  - 가격 차트 (Recharts)
  - 최근 뉴스
  - AI 예측 결과
  - 뉴스 임팩트 분석

#### `/predictions` - 예측 목록
- **파일**: `app/predictions/page.tsx`
- **설명**: AI 예측 내역 조회
- **주요 기능**:
  - 예측 목록 (페이지네이션)
  - 필터링 (종목, 날짜, 모델)
  - 예측 정확도 표시

#### `/models` - 모델 관리
- **파일**: `app/models/page.tsx`
- **설명**: AI 모델 레지스트리
- **주요 기능**:
  - 등록된 모델 목록
  - 모델 활성화/비활성화
  - 모델 성능 지표

#### `/ab-test` - A/B 테스트 결과
- **파일**: `app/ab-test/page.tsx`
- **설명**: 멀티 모델 A/B 테스트 결과
- **주요 기능**:
  - 모델 간 성능 비교
  - 통계적 유의성 검증

#### `/ab-config` - A/B 테스트 설정
- **파일**: `app/ab-config/page.tsx`
- **설명**: A/B 테스트 구성
- **주요 기능**:
  - 테스트 활성화/비활성화
  - 모델 A/B 선택
  - 테스트 기간 설정

### 관리자 페이지 (`/admin/*`)

모든 관리자 페이지는 `role: "admin"` 권한이 필요합니다.

#### `/admin/dashboard` - 관리자 대시보드
- **파일**: `app/admin/dashboard/page.tsx`
- **설명**: 시스템 전체 현황
- **주요 기능**:
  - 전체 통계 요약
  - 시스템 헬스 체크
  - 최근 활동 로그

#### `/admin/evaluations` - 모델 평가 관리
- **파일**: `app/admin/evaluations/page.tsx`
- **설명**: 모델 평가 결과 관리
- **주요 기능**:
  - 평가 내역 조회
  - 모델별 성능 비교
  - 평가 재실행

#### `/admin/evaluations/model/[id]` - 모델 상세 평가
- **파일**: `app/admin/evaluations/model/[id]/page.tsx`
- **설명**: 개별 모델 평가 상세
- **동적 라우팅**: 모델 ID
- **주요 기능**:
  - 모델 정확도 차트
  - 예측 성공/실패 분석
  - 메트릭 브레이크다운

#### `/admin/stocks` - 종목 관리
- **파일**: `app/admin/stocks/page.tsx`
- **설명**: 추적 종목 관리
- **주요 기능**:
  - 종목 추가/수정/삭제
  - 우선순위 설정
  - 활성화/비활성화

#### `/admin/users` - 사용자 관리
- **파일**: `app/admin/users/page.tsx`
- **설명**: 사용자 계정 관리
- **주요 기능**:
  - 사용자 목록
  - 권한 설정 (user/admin)
  - 계정 활성화/비활성화

#### `/admin/performance` - 성능 모니터링
- **파일**: `app/admin/performance/page.tsx`
- **설명**: 시스템 성능 지표
- **주요 기능**:
  - API 응답 시간
  - 데이터베이스 성능
  - 캐시 히트율

### 특수 페이지 (`/preview/*`)

블로그 포스트용 스크린샷 캡처를 위한 프리뷰 페이지입니다. `?token=xxx` 쿼리 파라미터로 인증합니다.

#### `/preview/dashboard` - 대시보드 프리뷰
- **파일**: `app/preview/dashboard/page.tsx`
- **설명**: 블로그용 대시보드 스크린샷
- **인증**: 프리뷰 토큰 (`PREVIEW_TOKEN`)

#### `/preview/stocks` - 종목 목록 프리뷰
- **파일**: `app/preview/stocks/page.tsx`
- **설명**: 블로그용 종목 목록 스크린샷

#### `/preview/stocks/[stockCode]` - 종목 상세 프리뷰
- **파일**: `app/preview/stocks/[stockCode]/page.tsx`
- **설명**: 블로그용 종목 상세 스크린샷

## 레이아웃 구조

### 루트 레이아웃 (`app/layout.tsx`)

모든 페이지에 적용되는 최상위 레이아웃:

```tsx
<html lang="ko">
  <body>
    <AuthProvider>
      <LayoutWrapper>{children}</LayoutWrapper>
    </AuthProvider>
  </body>
</html>
```

- **AuthProvider**: 전역 인증 상태 제공
- **LayoutWrapper**: 네비게이션 및 푸터 포함

### LayoutWrapper 구조

```tsx
<LayoutWrapper>
  <Navigation />      {/* 상단 네비게이션 바 */}
  <main>{children}</main>
  <Footer />          {/* 하단 푸터 */}
</LayoutWrapper>
```

## 라우팅 플로우 다이어그램

```mermaid
flowchart TD
    Start([사용자 요청])

    Middleware{Middleware<br/>인증 체크}

    Login[/login<br/>로그인 페이지]

    Public{공개 페이지?}

    Auth{세션 쿠키<br/>존재?}

    AdminCheck{관리자<br/>권한?}

    Dashboard[/dashboard<br/>메인 대시보드]
    AdminPage[/admin/*<br/>관리자 페이지]
    UserPage[일반 페이지]

    Start --> Middleware

    Middleware --> Public
    Public -->|로그인 페이지| Login
    Public -->|인증 필요| Auth

    Auth -->|세션 없음| Login
    Auth -->|세션 있음| AdminCheck

    AdminCheck -->|관리자 페이지 요청| AdminPage
    AdminCheck -->|일반 페이지| UserPage
    AdminCheck -->|메인| Dashboard

    style Login fill:#FFE4B5
    style Dashboard fill:#87CEEB
    style AdminPage fill:#FFB6C1
    style Middleware fill:#F39C12
```

## 네비게이션 메뉴

### 메인 네비게이션 (`components/Navigation.tsx`)

- **홈**: `/`
- **종목**: `/stocks`
- **예측**: `/predictions`
- **모델**: `/models`
- **A/B 테스트**: `/ab-test`
- **A/B 설정**: `/ab-config`
- **관리자** (관리자만): `/admin/dashboard`

### 관리자 서브 메뉴

- **대시보드**: `/admin/dashboard`
- **평가**: `/admin/evaluations`
- **종목 관리**: `/admin/stocks`
- **사용자 관리**: `/admin/users`
- **성능**: `/admin/performance`

## 동적 라우팅

### URL 파라미터

- `/stocks/[stockCode]`: 종목 코드 (예: `/stocks/005930`)
- `/admin/evaluations/model/[id]`: 모델 ID (예: `/admin/evaluations/model/1`)

### 쿼리 파라미터

- `/login?redirect=/stocks`: 로그인 후 리다이렉트 경로
- `/preview/*?token=xxx`: 프리뷰 인증 토큰

## 관련 문서

- [컴포넌트 구조](./components.md) - 페이지별 컴포넌트
- [상태 관리](./state-management.md) - 인증 및 데이터 페칭
- [개요](./overview.md) - 전체 아키텍처
