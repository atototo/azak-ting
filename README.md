# Azak (아작)

> **AI가 당신의 투자 판단을 도와주는 스마트 주식 분석 플랫폼**

## 🎯 Azak은 무엇인가요?

Azak(아작)은 **복잡한 주식 시장 데이터를 AI가 자동으로 분석하여 투자 인사이트를 제공하는 서비스**입니다. 매일 쏟아지는 수많은 시장 정보, 공시, 주가 데이터를 일일이 확인할 시간이 없는 투자자들을 위해, AI가 24시간 시장을 모니터링하고 핵심 정보를 정리해드립니다.

### 💡 어떤 문제를 해결하나요?

개인 투자자들이 겪는 대표적인 어려움:
- 📰 **정보 과부하**: 하루에도 수천 건의 시장 정보와 공시가 쏟아지는데 다 읽을 수 없음
- 📊 **데이터 해석의 어려움**: 주가, 재무제표, 투자자 동향 등 복잡한 데이터를 이해하기 어려움
- ⏰ **시간 부족**: 직장인은 실시간으로 시장을 모니터링할 시간이 없음
- 🤔 **정보의 신뢰성**: 어떤 정보를 믿어야 할지, 어떻게 해석해야 할지 모호함

### ✨ Azak의 해결책

Azak은 이러한 문제를 다음과 같이 해결합니다:

1. **자동 데이터 수집**: 주가, 재무지표, 시장 동향, 공시 등 6가지 데이터를 자동으로 수집
2. **AI 기반 분석**: GPT-4o와 DeepSeek-V3 등 여러 AI 모델이 데이터를 종합 분석
3. **실시간 알림**: 중요한 종목의 변동사항을 텔레그램으로 즉시 알림
4. **웹 대시보드**: 언제 어디서나 분석 결과를 확인할 수 있는 웹 인터페이스
5. **객관적 신뢰도 평가**: 6가지 데이터 완전도를 기반으로 리포트 신뢰도를 정량화

### 👥 누가 사용하나요?

- **직장인 투자자**: 업무 중에도 중요한 시장 변화를 놓치지 않고 싶은 분
- **데이터 기반 투자자**: 감이 아닌 데이터와 AI 분석을 기반으로 투자하고 싶은 분
- **투자 초보자**: 복잡한 데이터 해석에 어려움을 겪는 분
- **효율적 투자를 원하는 분**: 시간을 절약하면서도 정확한 정보를 얻고 싶은 분

### 🚀 시스템 동작 흐름

Azak은 다음과 같은 자동화된 흐름으로 24시간 시장을 모니터링합니다:

```
┌─────────────────────────────────────────────────────────────────┐
│  1️⃣ 자동 데이터 수집 (10분마다)                                   │
│  ├─ 주가/거래량 (KIS API)                                         │
│  ├─ 투자자 수급 (외국인/기관/개인)                                │
│  ├─ 재무지표 (ROE, PER, PBR)                                      │
│  ├─ 기업 정보 (시가총액, 업종)                                    │
│  ├─ 기술적 지표 (이동평균, RSI, MACD)                             │
│  └─ 시장 정보 + 공시 (네이버/한경/매경/DART)                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  2️⃣ AI 병렬 분석 (하루 3회: 10:05, 13:05, 15:45)                 │
│  ├─ GPT-4o 분석 (OpenAI)                                          │
│  ├─ DeepSeek-V3 분석 (OpenRouter)                                 │
│  ├─ 과거 패턴 비교 (7,040개 데이터)                               │
│  └─ 신뢰도 평가 (6가지 데이터 완전도 기반)                        │
│     ⚡ 병렬 처리로 30초 내 완료                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  3️⃣ 실시간 알림 & 대시보드 업데이트                               │
│  ├─ 📱 텔레그램 푸시 알림 (중요 종목)                             │
│  ├─ 💻 웹 대시보드 자동 갱신                                       │
│  └─ 📊 차트 및 신뢰도 점수 표시                                   │
└─────────────────────────────────────────────────────────────────┘
```

**📐 더 자세한 시스템 아키텍처는?**
→ **[전체 아키텍처 문서 보기](docs/architecture/overview.md)** - 17개 DB 모델, 42개 API 엔드포인트, 상세 데이터 흐름도 포함

---

## 📖 사용 사례

### 시나리오 1: 직장인 투자자 김씨의 하루
> "점심시간에 스마트폰으로 확인하니, 관심 종목인 삼성전자에 대한 AI 분석 리포트가 생성되어 있었습니다. 외국인 매수세, 호실적 전망, 기술적 지표 상승이 모두 긍정적이라는 종합 분석을 5분 만에 파악했습니다."

### 시나리오 2: 투자 초보자 이씨의 공부
> "시장 정보만 보면 잘 모르겠는데, Azak은 'AI가 시장 동향이 주가에 긍정적일지 부정적일지'를 분석해서 알려주니까 시장 흐름을 배우기 좋아요. 신뢰도 점수도 함께 표시되어 어떤 리포트를 더 신뢰해야 할지 알 수 있습니다."

### 시나리오 3: 데이터 중심 투자자 박씨의 활용
> "여러 AI 모델의 예측을 동시에 비교할 수 있어서 좋습니다. GPT-4o와 DeepSeek-V3가 동시에 상승을 예측하면 신뢰도가 높아지고, 의견이 갈리면 더 신중하게 판단합니다. 6가지 데이터 티어가 모두 확보된 리포트는 신뢰도가 높게 표시되어 판단하기 쉽습니다."

---

## ⭐ 주요 개선사항 (2025.11)

### 1. 데이터 티어 기반 리포트 시스템 (US-005)
기존의 단일 정보원 중심 분석에서 **6가지 데이터 소스를 통합한 정량적 분석**으로 전환:
- **다층적 데이터 활용**: 정량적 시장 데이터를 우선 활용하고 정성적 정보를 보조로 활용
- **신뢰도 평가**: 데이터 완전도 기반으로 리포트 신뢰도를 정량화
- **다층적 분석**: 주가/수급/재무/기술적 지표 등을 종합하여 보다 정확한 예측

### 2. 비동기 리포트 생성 시스템 (US-006)
사용자 경험 개선을 위한 백그라운드 처리:
- **즉시 응답**: 리포트 요청 시 즉각 응답하여 대기 시간 제거
- **실시간 알림**: Toast 알림으로 리포트 생성 완료를 실시간 통지
- **상태 추적**: 5초 주기 폴링으로 생성 진행 상태 확인 가능

### 3. KIS API 광범위 연동
한국투자증권 OpenAPI를 통한 실시간 시장 데이터 확보:
- 실시간 주가/호가, 일봉 데이터 (1분봉 수집 비활성화로 19,500 API 호출 절감)
- 투자자별 매매 동향 (외국인/기관/개인)
- 기업 재무비율 및 상품정보
- 업종/지수 데이터

### 4. 멀티 LLM 병렬 처리 최적화 (Issue #13, 2025-11-24)
ThreadPoolExecutor를 활용한 동시 예측 생성:
- **성능 개선**: 80초 → 30초 (2.6배 향상)
- **처리량 증대**: 45개/시간 → 120개/시간
- **에러 격리**: 개별 모델 실패 시에도 다른 모델 예측 성공
- **predicted_at 필드**: 예측 생성 추적 분리, 알림 중복 방지 (762건 데이터 마이그레이션)

### 5. FAISS 마이그레이션 (2025-11-22)
Milvus 서버 기반 벡터 DB에서 로컬 파일 기반 FAISS로 전환:
- **인프라 단순화**: Milvus + etcd + MinIO 제거 (5개 → 4개 컨테이너)
- **비용 절감**: 임베딩 비용 $0.00002/embedding → $0 (OpenAI → KoSimCSE 로컬 모델)
- **한국어 성능 향상**: KoSimCSE (BM-K/KoSimCSE-roberta) 한국어 특화 모델
- **마이그레이션 완료**: 7,040개 벡터 마이그레이션

### 6. AsyncIOScheduler 안정화 (2025-11-24)
Segmentation Fault 해결 및 스케줄러 개선:
- **안정성 향상**: BackgroundScheduler → AsyncIOScheduler (Segmentation Fault 해결)
- **작업 분리**: CronTrigger 기반 시장 정보 수집(0,10,20,30,40,50분)과 AI 분석(5,15,25,35,45,55분) 분리
- **동시 실행 방지**: PyTorch 모델 로딩 충돌 방지
- **싱글톤 RateLimiter**: Thread-safe 구현

### 7. 자동화 스케줄러 강화
다양한 주기로 데이터를 자동 수집하여 최신 정보 유지:
- **시장 정보 수집**: 0,10,20,30,40,50분 (CronTrigger)
- **AI 분석**: 5,15,25,35,45,55분 (CronTrigger)
- **일일 배치**: 일봉, 투자자 동향, 모델 평가
- **주간 배치**: 재무비율, 상품정보
- **자동 리포트 생성**: 하루 3회 (10:05, 13:05, 15:45)

## 🎯 주요 기능

### 1. 📊 종합 데이터 분석
**"주가만 보는 게 아니라, 시장 전체를 봅니다"**

Azak은 6가지 데이터 소스를 통합하여 종목을 입체적으로 분석합니다:
- **주가·거래량**: 실시간 가격 및 거래 흐름 추적
- **투자자 수급**: 외국인/기관/개인의 매수/매도 동향
- **재무 지표**: ROE, PER, PBR 등 기업의 재무 건전성
- **기업 정보**: 업종, 시가총액, 상장주식수 등 기본 정보
- **기술적 지표**: 이동평균, RSI, MACD 등 기술적 분석
- **시장 동향**: 시장 정보 + DART 공시를 통한 시장 분위기 파악

각 데이터의 완전도를 계산하여 **리포트 신뢰도를 정량화**합니다.

### 2. 🤖 멀티 AI 모델 분석
**"하나의 AI만 믿지 않습니다"**

- GPT-4o와 DeepSeek-V3 등 **여러 AI 모델이 동시에 분석**
- 의견이 일치하면 신뢰도 상승, 의견이 갈리면 더 신중한 판단 가능
- 과거 7,040개 시장 정보 데이터를 학습하여 유사 패턴 비교
- 병렬 처리로 빠른 분석 (80초 → 30초)

### 3. 📱 실시간 알림 시스템
**"중요한 순간을 놓치지 마세요"**

- 관심 종목의 AI 분석 리포트가 생성되면 **텔레그램으로 즉시 알림**
- 하루 3회 (10:05, 13:05, 15:45) 자동 리포트 생성
- 10분마다 새로운 시장 정보와 공시를 자동 수집
- 중복 알림 방지 시스템으로 꼭 필요한 정보만 전달

### 4. 💻 웹 대시보드
**"언제 어디서나 확인하세요"**

- PC/모바일에서 접근 가능한 반응형 웹 인터페이스
- 종목별 AI 분석 리포트 및 신뢰도 점수 확인
- 예측 이력 및 성과 추적
- 관리자 페이지에서 시스템 전체 모니터링 가능

### 5. ⚖️ 투명성과 책임
**"AI를 맹신하지 않습니다"**

- 모든 데이터 출처를 명확하게 표기
- 리포트 신뢰도 점수를 함께 제공
- 투자 면책 조항을 명시하여 법적 책임 한계 안내
- AI는 참고용 정보만 제공, 최종 판단은 투자자 본인의 책임

## 🏗️ 시스템 아키텍처

### 기술 스택 요약

| 계층 | 기술 |
|------|------|
| **Frontend** | Next.js 15, React 19, TypeScript |
| **Backend** | Python 3.11, FastAPI, AsyncIOScheduler |
| **Database** | PostgreSQL 13, FAISS (벡터 검색), Redis |
| **AI** | GPT-4o, DeepSeek-V3 (병렬), KoSimCSE (임베딩) |
| **Market Data** | KIS OpenAPI (한국투자증권) |
| **배포** | Docker Compose + PM2 |

### 6가지 데이터 티어 구조

Azak의 핵심 차별화 포인트는 **다층적 데이터 통합**입니다:

| 티어 | 데이터 종류 | 중요도 | 출처 |
|------|------------|--------|------|
| **Tier 1** | 주가·거래량 | 필수 | KIS API |
| **Tier 2** | 투자자 수급 (외국인/기관) | 높음 | KIS API |
| **Tier 3** | 재무지표 (ROE, PER, PBR) | 높음 | KIS API |
| **Tier 4** | 기업정보 (시가총액, 업종) | 중간 | KIS API |
| **Tier 5** | 기술적 지표 (RSI, MACD) | 중간 | 자체 계산 |
| **Tier 6** | 시장 동향 (정보 + 공시) | 보조 | 다중 소스 |

→ 각 티어의 데이터 완전도를 계산하여 **리포트 신뢰도를 정량화**합니다.

### 📚 상세 아키텍처 문서

더 자세한 시스템 구조가 궁금하시다면:
- **[전체 아키텍처 개요](docs/architecture/overview.md)** - 17개 DB 모델, 42개 API 엔드포인트
- **[데이터 처리 프로세스](docs/analysis/report-process-analysis.md)** - 리포트 생성 상세 흐름
- **[프로젝트 문서 인덱스](docs/index.md)** - 전체 문서 목록

---

## 📋 개발 환경 및 사전 요구사항

- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Node.js**: 20+ (Frontend 개발 시)
- **Python**: 3.11+ (Backend 개발 시)
- **OpenAI API Key**: GPT-4o 액세스 권한
- **KIS OpenAPI**: 한국투자증권 OpenAPI 앱키/시크릿 (실시간 주가 데이터)
- **Telegram Bot Token**: 텔레그램 봇 생성 필요 (선택사항)

## 🚀 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/azak.git
cd azak
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 다음 값을 설정하세요:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# KIS OpenAPI (한국투자증권)
KIS_APP_KEY=your-app-key-here
KIS_APP_SECRET=your-app-secret-here
KIS_ACCOUNT_NUMBER=your-account-number  # 선택사항 (조회용)

# Telegram (선택사항)
TELEGRAM_BOT_TOKEN=your-bot-token-here

# PostgreSQL (기본값 사용 가능)
POSTGRES_PASSWORD=your_secure_password

# JWT Secret (프리뷰 URL용)
JWT_SECRET=your-random-secret-key
```

### 3. 인프라 서비스 시작 (Docker Compose)

```bash
cd infrastructure
docker-compose up -d
```

다음 서비스가 시작됩니다:
- PostgreSQL (포트 5432)
- Redis (포트 6380)

**참고**: FAISS는 로컬 파일 기반이므로 별도의 Docker 서비스가 필요 없습니다.

### 4. Python 가상 환경 설정 (로컬 개발)

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발 도구
```

### 5. 데이터베이스 초기화

```bash
# PostgreSQL 테이블 생성
python scripts/init_db.py
```

**FAISS 인덱스 초기화**:
FAISS 인덱스는 첫 임베딩 생성 시 자동으로 `data/faiss_index/` 디렉터리에 생성됩니다.

### 6. Backend 서버 실행

```bash
# FastAPI 서버 시작 (포트 8000, 스케줄러 포함)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 URL에서 접근 가능합니다:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

### 7. Frontend 개발 서버 실행

```bash
cd frontend
npm install
npm run dev
```

프론트엔드가 실행되면:
- 웹 대시보드: http://localhost:3030
- API 프록시: `/api/*` → `http://localhost:8000/api/*`

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=backend --cov-report=html

# 특정 테스트만 실행
pytest tests/unit/test_crawler.py
```

## 📝 코드 품질 도구

```bash
# 코드 포맷팅 (Black)
black backend/ tests/

# Import 정렬 (isort)
isort backend/ tests/

# Linting (Flake8)
flake8 backend/ tests/

# 타입 체크 (mypy)
mypy backend/
```

## 📁 프로젝트 구조

```
azak/
├── frontend/                    # Next.js 애플리케이션
│   ├── app/                    # App Router
│   │   ├── page.tsx           # 사용자 대시보드 (/)
│   │   ├── admin/             # 관리자 페이지
│   │   ├── stocks/            # 종목 분석 페이지
│   │   ├── predictions/       # 예측 이력
│   │   ├── preview/           # 프리뷰 URL (토큰 기반 접근)
│   │   └── components/        # 공통 컴포넌트
│   ├── next.config.ts         # Next.js 설정
│   └── package.json           # Node 의존성
├── backend/                    # FastAPI 애플리케이션
│   ├── main.py                # 진입점
│   ├── config.py              # 설정 관리
│   ├── crawlers/              # 시장 정보 수집기
│   │   ├── crawler_scheduler.py  # AsyncIOScheduler 통합 스케줄러
│   │   ├── naver_crawler.py      # 네이버 정보 수집
│   │   ├── hankyung_crawler.py   # 한국경제 정보 수집
│   │   ├── maeil_crawler.py      # 매일경제 정보 수집
│   │   ├── reddit_crawler.py     # Reddit 정보 수집
│   │   └── dart_crawler.py       # DART 공시 수집
│   ├── kis/                   # KIS API 연동
│   │   ├── kis_client.py         # KIS API 클라이언트
│   │   ├── kis_scheduler.py      # KIS 데이터 수집 스케줄러
│   │   └── kis_utils.py          # KIS 유틸리티
│   ├── llm/                   # LLM 예측 엔진
│   │   ├── multi_model_predictor.py  # 멀티 모델 병렬 처리 (ThreadPoolExecutor)
│   │   ├── investment_report.py      # 투자 리포트 생성
│   │   ├── embedder.py               # KoSimCSE 임베딩 (Thread-Safe)
│   │   ├── vector_search.py          # FAISS 벡터 검색
│   │   ├── data_tier_builder.py      # 6가지 데이터 티어 구축
│   │   └── ab_test.py                # A/B 테스트
│   ├── notifications/         # 텔레그램 알림
│   ├── db/                    # 데이터베이스 모델 및 리포지토리
│   │   └── models/
│   │       └── news.py           # predicted_at 필드 포함
│   ├── scheduler/             # AsyncIOScheduler 작업
│   ├── api/                   # REST API 엔드포인트
│   │   ├── reports.py            # 리포트 API (비동기 생성)
│   │   ├── preview.py            # 프리뷰 URL API
│   │   └── ab_test.py            # A/B 테스트 API
│   └── scripts/               # 유틸리티 스크립트
├── data/                      # 로컬 데이터 저장소
│   └── faiss_index/           # FAISS 벡터 인덱스 (7,040개 시장 정보 벡터)
├── docs/                      # 문서 (PRD, 아키텍처)
│   ├── index.md               # 문서 메인 인덱스
│   ├── architecture/          # 아키텍처 문서
│   └── updates/               # 업데이트 이력
│       ├── 2025-11-22-faiss-migration.md
│       ├── 2025-11-24-async-scheduler-segfault-fix.md
│       └── issue-13-predicted-at-field.md
├── infrastructure/            # Docker 설정
├── scripts/                   # 프로젝트 레벨 스크립트
├── tests/                     # 테스트 코드
├── requirements.txt           # Python 의존성
└── .env.example               # 환경 변수 템플릿
```

## 🔧 개발 워크플로우

1. **기능 브랜치 생성**: `git checkout -b feature/new-feature`
2. **코드 작성 및 테스트**: 테스트 커버리지 70% 이상 유지
3. **코드 품질 검사**: Black, Flake8, mypy 통과
4. **커밋**: 명확한 커밋 메시지 작성
5. **Pull Request**: `main` 브랜치로 PR 생성

## 📚 문서

- **[프로젝트 문서 인덱스](docs/index.md)** - 전체 문서 목록 및 참조
- **아키텍처**:
  - [전체 아키텍처 개요](docs/architecture/overview.md)
  - [Infrastructure](docs/architecture/infrastructure.md)
  - [Backend 아키텍처](docs/architecture/backend/)
  - [Frontend 아키텍처](docs/architecture/frontend/)
- **업데이트 이력**:
  - [Issue #13: predicted_at 필드 추가 (2025-11-24)](docs/updates/issue-13-predicted-at-field.md)
  - [AsyncIOScheduler Segfault 해결 (2025-11-24)](docs/updates/2025-11-24-async-scheduler-segfault-fix.md)
  - [FAISS 마이그레이션 (2025-11-22)](docs/updates/2025-11-22-faiss-migration.md)
- **기능 문서**:
  - [US-005: 데이터 티어 기반 리포트 개선](docs/us-005-data-tier-report.md)
  - [US-006: 비동기 리포트 생성 시스템](docs/us-006-async-report-generation.md)

## 🔄 최근 주요 업데이트 (2025-11-24 ~ 2025-11-25)

### 성능 최적화
- **멀티 LLM 병렬 처리**: 80초 → 30초 (2.6배 향상, ThreadPoolExecutor)
- **처리량 증대**: 45개/시간 → 120개/시간
- **API 비용 절감**: 1분봉 수집 비활성화로 19,500 호출/일 감소
- **임베딩 비용 절감**: OpenAI → KoSimCSE 로컬 모델 ($0.00002 → $0)

### 안정성 향상
- **AsyncIOScheduler**: Segmentation Fault 해결 (BackgroundScheduler → AsyncIOScheduler)
- **CronTrigger 분리**: 시장 정보 수집과 AI 분석 분리로 PyTorch 모델 로딩 충돌 방지
- **Thread-Safe Embedder**: Double-check lock pattern 구현
- **에러 격리**: 개별 LLM 모델 실패 시에도 다른 모델 예측 성공

### 인프라 단순화
- **FAISS 마이그레이션**: Milvus + etcd + MinIO 제거 (5개 → 4개 컨테이너)
- **로컬 벡터 검색**: 서버 기반 DB → 파일 기반 검색
- **한국어 성능 향상**: KoSimCSE 한국어 특화 모델

### 데이터베이스
- **predicted_at 필드 추가**: 예측 생성 추적 분리, 알림 중복 방지
- **마이그레이션 완료**: 762건 기존 데이터 업데이트

## ⚖️ 법적 고지사항

**투자 면책 조항**

본 플랫폼에서 제공하는 모든 정보, 분석, 예측은 투자 참고용으로만 제공되며, 투자 권유나 매수/매도 추천이 아닙니다. 투자 결정은 본인의 판단과 책임 하에 이루어져야 하며, 투자로 인한 손실에 대해 본 플랫폼은 어떠한 법적 책임도 지지 않습니다.

**데이터 출처**
- 주가/재무 데이터: 한국투자증권 OpenAPI
- 시장 정보: 네이버, 한국경제, 매일경제, Reddit
- 공시 데이터: 금융감독원 DART
- AI 분석: OpenAI GPT-4o, DeepSeek-V3
- 임베딩: KoSimCSE (BM-K/KoSimCSE-roberta)

**저작권 보호**

본 플랫폼은 원문을 재배포하지 않으며, AI 분석 및 요약만을 제공합니다. 모든 정보 출처는 명시되며, 원문은 해당 언론사 및 정보 제공자의 저작물입니다.

## 📄 라이선스

MIT License

## 👥 기여자

- 프로젝트 관리자: [Your Name]

## 📞 문의

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**📝 문서 버전:** 2.0.0
**마지막 업데이트:** 2025-11-25
**주요 변경사항:**
- FAISS 마이그레이션 반영 (Milvus → FAISS)
- AsyncIOScheduler 안정화 반영
- 멀티 LLM 병렬 처리 최적화 반영
- predicted_at 필드 추가 반영
- 최신 스케줄러 작업 목록 업데이트
