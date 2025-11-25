# 인프라 아키텍처 (Docker Compose 스택)

## 개요

Docker Compose를 사용한 멀티 컨테이너 스택으로 PostgreSQL, Redis, Backend (FastAPI), Frontend (Next.js)를 단일 호스트에서 실행합니다. 벡터 검색은 FAISS 로컬 파일 시스템을 사용합니다. 개발 환경 및 소규모 프로덕션 환경에 적합합니다.

## 기술 스택

### 컨테이너 오케스트레이션
- **Docker 24+**: 컨테이너 런타임
- **Docker Compose v3.8**: 멀티 컨테이너 정의 및 관리

### 데이터베이스 & 스토리지
- **PostgreSQL 13-alpine**: 주 데이터베이스
- **Redis 7-alpine**: 캐싱 및 작업 큐
- **FAISS (로컬 파일)**: 벡터 임베딩 저장소 (파일 기반, 2025-11-22 마이그레이션 완료)
- **KoSimCSE 임베딩 모델**: 로컬 한국어 특화 임베딩 모델 (BM-K/KoSimCSE-roberta)

### 애플리케이션 컨테이너
- **Backend (FastAPI)**: Python 3.11-slim 기반
- **Frontend (Next.js)**: Node.js 20 기반

## 시스템 아키텍처 다이어그램

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        subgraph "애플리케이션"
            Frontend[Frontend<br/>Next.js 15<br/>:3030]
            Backend[Backend<br/>FastAPI<br/>:8000]
        end

        subgraph "데이터베이스"
            Postgres[(PostgreSQL 13<br/>:5432)]
            Redis[(Redis 7<br/>:6380→6379)]
        end
    end

    subgraph "로컬 파일 시스템"
        FAISS[FAISS Index<br/>로컬 파일<br/>7,040 벡터]
        EmbedModel[KoSimCSE<br/>한국어 임베딩 모델<br/>BM-K/KoSimCSE-roberta]
    end

    subgraph "볼륨 (데이터 지속성)"
        PGVol[postgres_data]
        RedisVol[redis_data]
    end

    Frontend -->|API 프록시| Backend
    Backend --> Postgres
    Backend --> Redis
    Backend -->|벡터 검색| FAISS
    Backend -->|임베딩 생성| EmbedModel

    Postgres -.-> PGVol
    Redis -.-> RedisVol

    style Frontend fill:#4A90E2
    style Backend fill:#50C878
    style Postgres fill:#336791
    style Redis fill:#DC382D
    style FAISS fill:#00ADD8
    style EmbedModel fill:#90EE90
```

## 서비스 구성

### 1. PostgreSQL (postgres)

```yaml
image: postgres:13-alpine
ports: 5432:5432
volumes: postgres_data:/var/lib/postgresql/data
```

**역할**: 주 데이터베이스 (종목, 뉴스, 예측, 사용자 등)

**환경 변수**:
- `POSTGRES_USER`: postgres (기본값)
- `POSTGRES_PASSWORD`: password (기본값, 프로덕션에서 변경 필수)
- `POSTGRES_DB`: azak

**초기화 스크립트**:
- `db-init/01-schema.sql`: 테이블 스키마 생성
- `db-init/02-data.sql`: 초기 데이터 삽입

**헬스체크**:
```bash
pg_isready -U postgres
# 10초 간격, 5초 타임아웃, 5회 재시도
```

### 2. Redis (redis)

```yaml
image: redis:7-alpine
ports: 6380:6379
volumes: redis_data:/data
```

**역할**: 캐싱 (예측 결과, 메트릭), 작업 큐

**특수 설정**:
- **RDB 스냅샷 완전 비활성화**: 디스크 저장 문제 방지
- `--save ''`: 스냅샷 저장 비활성화
- `--dbfilename ''`: RDB 파일명 빈 값 설정
- `--stop-writes-on-bgsave-error no`: 저장 실패 시에도 쓰기 허용

**포트 매핑**: 6380 (호스트) → 6379 (컨테이너)

**헬스체크**:
```bash
redis-cli ping
# 10초 간격, 3초 타임아웃, 5회 재시도
```

### 3. Backend (backend)

```yaml
build: ../backend/Dockerfile
ports: 8000:8000
env_file: ../.env
```

**역할**: FastAPI REST API 서버

**Dockerfile**: `infrastructure/Dockerfile`
- 베이스 이미지: `python:3.11-slim`
- 시스템 의존성: gcc, postgresql-client
- Python 의존성: `requirements.txt`

**의존성**: postgres, redis

**벡터 검색**: FAISS 로컬 파일 (`data/faiss_index/`)
**임베딩 모델**: KoSimCSE (BM-K/KoSimCSE-roberta) 로컬 실행

**명령어**:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Frontend (frontend)

```yaml
build: ../frontend/Dockerfile
ports: 3030:3030
env_file: ../.env
```

**역할**: Next.js 웹 대시보드

**환경 변수**:
- `NODE_ENV`: production
- `PORT`: 3030
- `NEXT_PUBLIC_API_URL`: http://backend:8000

**의존성**: backend

## 네트워킹

### 포트 매핑

| 서비스 | 컨테이너 포트 | 호스트 포트 | 프로토콜 |
|--------|---------------|-------------|----------|
| PostgreSQL | 5432 | 5432 | TCP |
| Redis | 6379 | 6380 | TCP |
| Backend | 8000 | 8000 | HTTP |
| Frontend | 3030 | 3030 | HTTP |

### 내부 네트워크

- **네트워크**: Docker Compose 기본 브리지 네트워크
- **DNS**: 서비스 이름으로 서로 통신 (예: `backend`, `postgres`, `redis`)

## 볼륨 및 데이터 지속성

### Named Volumes

```yaml
volumes:
  postgres_data:       # PostgreSQL 데이터
  redis_data:          # Redis RDB (비활성화됨)
```

**로컬 파일 시스템**:
- `data/faiss_index/`: FAISS 벡터 인덱스 파일 (7,040개 벡터, 768차원)
- `~/.cache/huggingface/`: KoSimCSE 임베딩 모델 캐시

### 볼륨 위치

Docker Named Volume은 Docker가 관리하는 위치에 저장됩니다:

- **macOS/Linux**: `/var/lib/docker/volumes/`
- **확인 방법**:
  ```bash
  docker volume inspect infrastructure_postgres_data
  ```

### 백업 전략

```bash
# PostgreSQL 백업
docker exec azak-postgres pg_dump -U postgres azak > backup.sql

# 볼륨 백업
docker run --rm -v infrastructure_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# 복원
docker run --rm -v infrastructure_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## 환경 변수 설정

### .env 파일

프로젝트 루트에 `.env` 파일 생성:

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=azak

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380

# FAISS (로컬 파일, 설정 불필요)
# data/faiss_index/ 경로에 자동 저장

# Backend
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/azak
REDIS_URL=redis://localhost:6380

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# KIS (한국투자증권)
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
```

## 헬스체크 및 재시작 정책

### 헬스체크

모든 주요 서비스에 헬스체크 설정:

| 서비스 | 헬스체크 명령 | 간격 | 타임아웃 | 재시도 |
|--------|---------------|------|----------|--------|
| PostgreSQL | `pg_isready -U postgres` | 10초 | 5초 | 5회 |
| Redis | `redis-cli ping` | 10초 | 3초 | 5회 |

### 재시작 정책

```yaml
restart: unless-stopped
```

- 컨테이너 실패 시 자동 재시작
- 수동 중지한 경우 재시작하지 않음
- Docker 데몬 재시작 시 자동 시작

## 배포 워크플로우

### 로컬 개발 환경

```bash
# 1. 저장소 클론
git clone <repository>
cd azak

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 3. Infrastructure 시작
cd infrastructure
docker-compose up -d

# 4. 서비스 상태 확인
docker-compose ps

# 5. 로그 확인
docker-compose logs -f

# 6. Backend 개별 실행 (선택사항)
cd ../backend
uvicorn backend.main:app --reload

# 7. Frontend 개별 실행 (선택사항)
cd ../frontend
npm run dev
```

### 프로덕션 배포

```bash
# 1. 프로덕션 .env 설정
vi .env

# 2. 전체 스택 시작
cd infrastructure
docker-compose up -d

# 3. 서비스 확인
docker-compose ps
docker-compose logs -f backend frontend

# 4. 데이터베이스 초기화 확인
docker exec azak-postgres psql -U postgres -d azak -c "\dt"
```

### 서비스 관리 명령어

```bash
# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d postgres redis

# 서비스 재시작
docker-compose restart backend

# 서비스 중지
docker-compose stop

# 서비스 및 네트워크 제거 (볼륨 유지)
docker-compose down

# 서비스, 네트워크, 볼륨 모두 제거
docker-compose down -v

# 서비스 로그 확인
docker-compose logs -f backend

# 컨테이너 내부 접속
docker exec -it azak-postgres psql -U postgres
docker exec -it azak-redis redis-cli
docker exec -it azak-backend bash
```

## 모니터링 및 운영

### 리소스 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# 특정 컨테이너만
docker stats azak-postgres azak-backend
```

### 로그 관리

```bash
# 로그 확인
docker-compose logs -f --tail=100 backend

# 로그 파일 위치
# Backend: data/logs/app.log (컨테이너 내부)
```

### 데이터베이스 관리

```bash
# PostgreSQL 접속
docker exec -it azak-postgres psql -U postgres -d azak

# 테이블 목록
\dt

# 백업
docker exec azak-postgres pg_dump -U postgres azak > backup_$(date +%Y%m%d).sql

# 복원
cat backup_20250120.sql | docker exec -i azak-postgres psql -U postgres -d azak
```

### Redis 관리

```bash
# Redis CLI 접속
docker exec -it azak-redis redis-cli

# 캐시 통계
INFO stats

# 모든 키 확인
KEYS *

# 특정 키 확인
GET prediction:005930
```

## 성능 최적화

### PostgreSQL

```sql
-- 연결 풀 설정 (backend/db/session.py)
pool_size=30
max_overflow=50
pool_recycle=3600
```

### Redis

- RDB 스냅샷 비활성화로 디스크 I/O 감소
- 메모리 내 캐싱만 사용

### FAISS

- 파일 기반 인메모리 검색: 빠른 벡터 유사도 검색
- 7,040개 벡터 (768차원) 처리 시 밀리초 단위 응답
- 대규모 확장 필요 시 Milvus/Qdrant 등 서버 기반 DB로 전환 고려

## 보안 고려사항

### 1. 기본 패스워드 변경

프로덕션에서 반드시 변경:
- PostgreSQL: `POSTGRES_PASSWORD`

### 2. 포트 접근 제한

외부 접근이 필요 없는 포트는 내부 네트워크만 허용:
```yaml
# 외부 노출 제거
# ports:
#   - "5432:5432"  # PostgreSQL
```

### 3. 환경 변수 관리

- `.env` 파일을 `.gitignore`에 추가
- 프로덕션: AWS Secrets Manager 또는 Vault 사용

### 4. 네트워크 격리

```yaml
networks:
  frontend:
  backend:
    internal: true  # 외부 접근 차단
```

## 문제 해결

### 1. PostgreSQL 연결 실패

```bash
# 컨테이너 상태 확인
docker-compose ps postgres

# 로그 확인
docker-compose logs postgres

# 헬스체크 확인
docker inspect azak-postgres | grep Health -A 10

# 직접 연결 테스트
docker exec -it azak-postgres psql -U postgres
```

### 2. Redis 연결 실패

```bash
# Redis 핑 테스트
docker exec azak-redis redis-cli ping

# 메모리 사용량 확인
docker exec azak-redis redis-cli INFO memory
```

### 3. FAISS 인덱스 로드 실패

```bash
# FAISS 인덱스 파일 확인
ls -lh data/faiss_index/

# 백엔드 로그 확인
docker-compose logs backend | grep -i faiss

# 임베딩 모델 캐시 확인
ls -lh ~/.cache/huggingface/
```

### 4. 디스크 공간 부족

```bash
# 볼륨 사용량 확인
docker system df -v

# 미사용 볼륨 정리
docker volume prune

# 미사용 이미지 정리
docker image prune -a
```

### 5. 포트 충돌

```bash
# 포트 사용 확인
lsof -i :5432
lsof -i :6380
lsof -i :8000

# 포트 변경
# docker-compose.yml에서 포트 매핑 수정
ports:
  - "5433:5432"  # 호스트 포트 변경
```

## 관련 문서

- [Backend 아키텍처](./backend/index.md) - FastAPI 서비스 상세
- [Frontend 아키텍처](./frontend/index.md) - Next.js 대시보드 상세
- [배포 설정](../deployment/configuration.md) - 배포 가이드
- [PM2 가이드](../../PM2.md) - 프로세스 관리

---

**📝 문서 버전:** 3.0.0
**마지막 업데이트:** 2025-11-25
**변경사항**:
- Milvus → FAISS 마이그레이션 반영 (2025-11-22)
- OpenAI → KoSimCSE 로컬 임베딩 모델 전환
- 벡터 DB 아키텍처 단순화 (서버 기반 → 파일 기반)
