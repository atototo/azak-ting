# 개발 가이드

## 환경 요구사항

- **Node.js**: >=20.0.0
- **npm**: >=10.0.0
- **운영체제**: macOS, Linux, Windows

## 프로젝트 설정

### 1. 저장소 클론 및 의존성 설치

```bash
# 프로젝트 루트로 이동
cd azak

# Frontend 디렉터리로 이동
cd frontend

# 의존성 설치
npm install
```

### 2. 환경 변수 설정 (선택사항)

환경 변수가 필요한 경우 `.env.local` 파일 생성:

```bash
# .env.local
NEXT_PUBLIC_API_BASE=http://localhost:8000
PREVIEW_TOKEN=your-preview-token-here
```

> **참고**: `NEXT_PUBLIC_` 접두사가 붙은 변수만 클라이언트에서 접근 가능합니다.

## 개발 서버 실행

### 개발 모드 (Hot Reload)

```bash
npm run dev
```

- **URL**: http://localhost:3030
- **자동 리로드**: 파일 저장 시 자동으로 브라우저 새로고침
- **Fast Refresh**: React 컴포넌트 상태 유지하면서 Hot Reload

### 백엔드와 함께 실행

```bash
# 터미널 1: Backend 실행 (프로젝트 루트에서)
cd backend
uvicorn backend.main:app --reload --port 8000

# 터미널 2: Frontend 실행
cd frontend
npm run dev
```

프론트엔드의 `/api/*` 요청은 자동으로 `http://127.0.0.1:8000/*`로 프록시됩니다 (next.config.ts 설정).

## 빌드 및 프로덕션

### 프로덕션 빌드

```bash
npm run build
```

- `.next/` 폴더에 최적화된 빌드 생성
- 정적 페이지는 HTML로 사전 렌더링
- 서버 컴포넌트와 클라이언트 컴포넌트 분리

### 프로덕션 서버 실행

```bash
npm run start
```

- **URL**: http://localhost:3000 (기본 포트)
- 빌드된 `.next/` 폴더를 서빙

### 빌드 최적화 확인

```bash
# 빌드 분석
npm run build

# 번들 크기 확인
npx @next/bundle-analyzer
```

## 코드 품질

### ESLint

```bash
# 린팅 실행
npm run lint

# 자동 수정
npm run lint -- --fix
```

**ESLint 규칙** (`.eslintrc.json`):
- `eslint-config-next` 기본 규칙
- React Hooks 규칙
- TypeScript 규칙

### TypeScript 타입 체크

```bash
# 타입 체크
npx tsc --noEmit
```

모든 컴포넌트와 함수에 타입 정의가 필수입니다.

### 코드 포맷팅 (선택사항)

Prettier 설정:

```bash
# 설치
npm install --save-dev prettier

# 실행
npx prettier --write "app/**/*.{ts,tsx,js,jsx,json,css}"
```

## 테스트 (미구현)

### Jest + React Testing Library

```bash
# 설치
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# 테스트 실행
npm test
```

### E2E 테스트 (Playwright)

```bash
# 설치
npm install --save-dev @playwright/test

# 테스트 실행
npx playwright test
```

## 디버깅

### React DevTools

브라우저에 React DevTools 확장 설치:
- **Chrome**: [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- **Firefox**: [React Developer Tools](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

### React Query DevTools

개발 모드에서 자동으로 활성화:

```tsx
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

<QueryClientProvider client={queryClient}>
  {children}
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

### 브라우저 콘솔

Next.js는 개발 모드에서 유용한 에러 메시지와 경고를 제공합니다:
- 컴포넌트 렌더링 에러
- Hydration 에러
- 라우팅 에러

### 네트워크 요청 디버깅

브라우저 개발자 도구 → Network 탭:
- API 요청/응답 확인
- 쿠키 확인 (`azak_session`)
- 응답 시간 측정

## 개발 팁

### 1. 컴포넌트 개발 순서

1. **타입 정의**: Props 인터페이스 먼저 작성
2. **마크업**: JSX 구조 작성
3. **스타일링**: Tailwind CSS 클래스 적용
4. **로직**: 데이터 페칭 및 상태 관리
5. **테스트**: 단위 테스트 작성 (해당 시)

### 2. 데이터 페칭 패턴

```tsx
// ✅ 좋은 예: React Query 사용
function StockList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["stocks"],
    queryFn: fetchStocks,
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;

  return <List items={data} />;
}

// ❌ 나쁜 예: useEffect + useState
function StockList() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStocks().then(setData).finally(() => setLoading(false));
  }, []);

  // ...
}
```

### 3. 파일 구조 규칙

```
app/
├── page.tsx              # 페이지 컴포넌트
├── layout.tsx            # 레이아웃
├── loading.tsx           # 로딩 상태
├── error.tsx             # 에러 핸들링
└── [dynamic]/            # 동적 라우팅
    └── page.tsx
```

### 4. 네이밍 컨벤션

- **컴포넌트**: PascalCase (`StockChart.tsx`)
- **훅**: camelCase, `use` 접두사 (`useAuth.ts`)
- **유틸리티**: camelCase (`formatDate.ts`)
- **타입/인터페이스**: PascalCase (`User`, `StockData`)

## 일반적인 문제 해결

### 1. 포트 충돌

```bash
# 3030 포트가 사용 중인 경우
lsof -ti:3030 | xargs kill -9

# 또는 다른 포트 사용
npm run dev -- -p 3031
```

### 2. 캐시 문제

```bash
# Next.js 캐시 삭제
rm -rf .next

# node_modules 재설치
rm -rf node_modules package-lock.json
npm install
```

### 3. TypeScript 에러

```bash
# 타입 정의 재생성
npx tsc --noEmit

# node_modules의 @types 재설치
npm install --save-dev @types/react @types/node
```

### 4. API 프록시 문제

`next.config.ts`의 rewrites 설정 확인:

```typescript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://127.0.0.1:8000/:path*',
    },
  ];
}
```

백엔드가 8000 포트에서 실행 중인지 확인:

```bash
curl http://127.0.0.1:8000/health
```

## 관련 문서

- [배포 가이드](./deployment.md) - 프로덕션 배포
- [컴포넌트](./components.md) - 컴포넌트 구조
- [상태 관리](./state-management.md) - React Query, AuthContext
