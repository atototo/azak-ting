# 배포 가이드

## 배포 옵션

Next.js는 다양한 배포 방식을 지원합니다:
1. **Node.js 서버**: `next start`로 프로덕션 서버 실행
2. **Docker 컨테이너**: Dockerfile로 컨테이너화
3. **정적 사이트**: 완전한 정적 HTML 내보내기

## Node.js 서버 배포

### 1. 프로덕션 빌드

```bash
# frontend 디렉터리에서
npm run build
```

생성된 `.next/` 폴더가 프로덕션 빌드입니다.

### 2. 프로덕션 서버 실행

```bash
npm run start
```

또는 포트 지정:

```bash
npx next start -p 3030
```

### 3. 환경 변수 설정

`.env.production` 파일 생성:

```bash
# .env.production
NEXT_PUBLIC_API_BASE=https://api.your-domain.com
PREVIEW_TOKEN=your-secure-token
```

### 4. PM2로 프로세스 관리

PM2를 사용하여 백그라운드에서 실행:

```bash
# PM2 설치
npm install -g pm2

# 프로세스 시작
pm2 start npm --name "azak-frontend" -- start

# 부팅 시 자동 시작
pm2 startup
pm2 save

# 로그 확인
pm2 logs azak-frontend

# 재시작
pm2 restart azak-frontend
```

`ecosystem.config.js` 설정 파일:

```javascript
module.exports = {
  apps: [{
    name: 'azak-frontend',
    script: 'npm',
    args: 'start',
    cwd: '/path/to/frontend',
    env: {
      NODE_ENV: 'production',
      PORT: 3030,
    },
  }]
};
```

실행:

```bash
pm2 start ecosystem.config.js
```

## Docker 배포

### Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS base

# 의존성 설치
FROM base AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# 빌드
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# 프로덕션
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### Docker Compose

```yaml
# infrastructure/docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "3030:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=http://backend:8000
      - PREVIEW_TOKEN=${PREVIEW_TOKEN}
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build: ../backend
    ports:
      - "8000:8000"
    # ... 기타 설정
```

실행:

```bash
cd infrastructure
docker-compose up -d frontend
```

## Nginx 리버스 프록시

### Nginx 설정

```nginx
# /etc/nginx/sites-available/azak
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3030;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API (FastAPI)
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Nginx 활성화:

```bash
sudo ln -s /etc/nginx/sites-available/azak /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### HTTPS (Let's Encrypt)

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 확인
sudo certbot renew --dry-run
```

## Ngrok 터널 (개발/테스트용)

로컬 개발 환경을 외부에 노출:

```bash
# Ngrok 설치
brew install ngrok/ngrok/ngrok

# 인증
ngrok authtoken YOUR_AUTH_TOKEN

# 터널 생성
ngrok http 3030
```

생성된 URL (예: `https://abc123.ngrok.io`)을 통해 접근 가능합니다.

## 성능 최적화

### 1. 이미지 최적화

Next.js의 `<Image>` 컴포넌트 사용:

```tsx
import Image from "next/image";

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={50}
  priority // LCP 이미지에 적용
/>
```

### 2. 코드 분할

```tsx
// 동적 import로 번들 크기 감소
import dynamic from "next/dynamic";

const HeavyChart = dynamic(() => import("./HeavyChart"), {
  loading: () => <Skeleton />,
  ssr: false, // 클라이언트에서만 렌더링
});
```

### 3. 정적 생성 (SSG)

가능한 페이지는 빌드 시 정적 생성:

```tsx
// app/stocks/[stockCode]/page.tsx
export async function generateStaticParams() {
  const stocks = await fetchStocks();
  return stocks.map((stock) => ({
    stockCode: stock.code,
  }));
}

export default async function StockPage({ params }) {
  const stock = await fetchStock(params.stockCode);
  return <StockDetail stock={stock} />;
}
```

### 4. 캐싱

```tsx
// 페이지 레벨 캐싱 (60초)
export const revalidate = 60;

// fetch 레벨 캐싱
fetch('https://api.example.com/data', {
  next: { revalidate: 3600 } // 1시간
});
```

## 모니터링

### 1. 로그 수집

```bash
# PM2 로그
pm2 logs azak-frontend --lines 100

# Docker 로그
docker logs azak-frontend -f
```

### 2. 에러 추적

Sentry 통합 (선택사항):

```bash
npm install @sentry/nextjs
```

```typescript
// next.config.ts
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig = {
  // ... 기존 설정
};

export default withSentryConfig(nextConfig, {
  org: "your-org",
  project: "your-project",
});
```

### 3. 성능 모니터링

Next.js는 기본적으로 Web Vitals를 측정합니다:

```tsx
// app/layout.tsx
export function reportWebVitals(metric) {
  console.log(metric);
  // Google Analytics나 다른 서비스로 전송
}
```

## 보안 고려사항

### 1. 환경 변수 보호

- `.env*` 파일을 `.gitignore`에 추가
- 민감한 정보는 서버에서만 사용 (`NEXT_PUBLIC_` 접두사 없이)

### 2. Content Security Policy (CSP)

```typescript
// next.config.ts
const nextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
          },
        ],
      },
    ];
  },
};
```

### 3. HTTPS 강제

Nginx 또는 Next.js에서 HTTPS 리다이렉트 설정.

## 배포 체크리스트

- [ ] 프로덕션 빌드 성공 (`npm run build`)
- [ ] 환경 변수 설정 완료
- [ ] API 엔드포인트 정상 동작 확인
- [ ] HTTPS 인증서 설정 (프로덕션)
- [ ] 로그 수집 설정
- [ ] 에러 추적 설정 (선택사항)
- [ ] 백업 계획 수립
- [ ] 모니터링 대시보드 설정

## 관련 문서

- [개발 가이드](./development.md) - 개발 환경 설정
- [인프라 구성](../../deployment/infrastructure.md) - 전체 인프라
- [PM2 가이드](../../../PM2.md) - PM2 프로세스 관리
