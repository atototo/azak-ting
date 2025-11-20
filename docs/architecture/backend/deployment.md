# 배포 가이드

## 배포 아키텍처

### Docker 컨테이너 구조

```yaml
# infrastructure/docker-compose.yml
services:
  postgres:
    image: postgres:15
    ports: ["5432:5432"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  milvus:
    image: milvusdb/milvus:latest
    ports: ["19530:19530"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on:
      - postgres
      - redis
      - milvus
```

## 프로덕션 배포

### 1. Docker 이미지 빌드
```bash
docker build -t azak-backend:latest -f backend/Dockerfile .
```

### 2. 환경 변수 설정
- `POSTGRES_HOST`, `POSTGRES_PASSWORD`
- `REDIS_HOST`
- `MILVUS_HOST`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `KIS_APP_KEY`, `KIS_APP_SECRET` (한국투자증권)

### 3. 리버스 프록시 설정
- Nginx 또는 AWS ALB 뒤에서 실행
- HTTPS 인증서 설정
- CORS 설정 확인 (`config.py`)

### 4. 모니터링 설정
- 로그: `data/logs/app.log`
- 헬스체크: `GET /health`
- 메트릭: APScheduler 통계 API

상세한 배포 가이드는 `docs/deployment/configuration.md` 참조.

## 관련 문서

- [배포 설정](../../deployment/configuration.md) - 상세 배포 가이드
- [인프라 구성](../../deployment/infrastructure.md) - 인프라 아키텍처
- [PM2 프로세스 관리](../../../PM2.md) - 운영 환경 프로세스 관리
