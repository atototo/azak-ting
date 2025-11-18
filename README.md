# Azak

**AI 기반 다중 데이터 소스 통합 투자 인사이트 플랫폼**

Azak은 주가·거래량, 투자자 수급, 재무지표, 기업정보, 기술적 지표, 시장동향(뉴스+공시) 등 6가지 데이터 티어를 통합 분석하여, OpenAI GPT-4o 기반 LLM으로 종목별 단기 주가 방향성을 예측하고, Next.js 웹 대시보드와 텔레그램 봇을 통해 실시간 투자 인사이트를 제공하는 Full-Stack 플랫폼입니다.

## ⭐ 주요 개선사항 (2025.11)

### 1. 데이터 티어 기반 리포트 시스템 (US-005)
기존의 뉴스 중심 분석에서 **6가지 데이터 소스를 통합한 정량적 분석**으로 전환:
- **뉴스 의존도 감소**: 단일 뉴스 의존성을 줄이고 시장 데이터를 우선 활용
- **신뢰도 평가**: 데이터 완전도 기반으로 리포트 신뢰도를 정량화
- **다층적 분석**: 주가/수급/재무/기술적 지표 등을 종합하여 보다 정확한 예측

### 2. 비동기 리포트 생성 시스템 (US-006)
사용자 경험 개선을 위한 백그라운드 처리:
- **즉시 응답**: 리포트 요청 시 즉각 응답하여 대기 시간 제거
- **실시간 알림**: Toast 알림으로 리포트 생성 완료를 실시간 통지
- **상태 추적**: 5초 주기 폴링으로 생성 진행 상태 확인 가능

### 3. KIS API 광범위 연동
한국투자증권 OpenAPI를 통한 실시간 시장 데이터 확보:
- 실시간 주가/호가, 일봉/분봉 데이터
- 투자자별 매매 동향 (외국인/기관/개인)
- 기업 재무비율 및 상품정보
- 업종/지수 데이터

### 4. 자동화 스케줄러 강화
다양한 주기로 데이터를 자동 수집하여 최신 정보 유지:
- 장중 실시간 데이터: 1분/5분 주기
- 일일 배치: 일봉, 투자자 동향, 모델 평가
- 주간 배치: 재무비율, 상품정보
- 자동 리포트 생성: 하루 3회 (10:00, 13:00, 15:45)

## 🎯 주요 기능

### 데이터 수집 및 분석
- **📊 다중 데이터 소스 통합**: 6가지 데이터 티어 기반 종합 분석
  - **주가·거래량**: KIS API를 통한 실시간/일봉/분봉 데이터
  - **투자자 수급**: 외국인/기관/개인 투자자별 매매 동향
  - **재무 지표**: 기업 재무비율 데이터 (ROE, PER, PBR 등)
  - **기업 정보**: KIS 상품정보 (업종, 시가총액, 상장주식수 등)
  - **기술적 지표**: 자체 계산 (이동평균, RSI, MACD 등)
  - **시장 동향**: 뉴스 + DART 공시 통합 분석
- **📰 뉴스 크롤링**: 네이버, 한국경제, 매일경제, Reddit, DART 공시 자동 수집
- **📈 KIS API 연동**: 한국투자증권 OpenAPI를 통한 실시간 시장 데이터
  - 현재가/호가, 일봉/분봉, 시간외 거래가
  - 업종/지수 데이터, 투자자별 거래 현황
  - 기업 상품정보, 재무비율

### AI 예측 및 리포트
- **🤖 데이터 완전도 기반 AI 예측**: GPT-4o를 활용한 다중 데이터 소스 통합 분석
  - 6가지 데이터 티어 완전도에 따른 신뢰도 평가
  - 단일 뉴스 의존도 감소, 정량적 데이터 중심 분석
- **⚡ 비동기 리포트 생성**: 백그라운드 처리 및 실시간 알림
  - 즉시 응답 후 백그라운드에서 리포트 생성
  - 5초 주기 폴링을 통한 생성 상태 추적
  - Toast 알림을 통한 완료 통지
- **🔍 RAG 기반 분석**: Milvus 벡터 DB를 활용한 유사 뉴스 검색 및 과거 패턴 분석
- **🧪 A/B 테스트**: 두 LLM 모델 동시 비교 및 성능 평가 자동화

### 사용자 인터페이스
- **🌐 웹 대시보드**: Next.js 기반 사용자/관리자 대시보드, 종목별 AI 분석 리포트
- **🔗 프리뷰 URL**: 토큰 기반 비로그인 접근 (블로그 자동화용)
- **💬 텔레그램 알림**: 중요 종목에 대한 실시간 예측 결과 푸시

### 자동화 및 스케줄링
- **⏰ 다양한 스케줄러 작업**: APScheduler를 통한 주기적 데이터 수집 및 분석
  - 뉴스 크롤링: 10분마다 (네이버/한경/매경/Reddit)
  - 종목별 뉴스 검색: 10분마다
  - DART 공시: 5분마다
  - KIS 1분봉: 매 1분 (장 시간만, 09:00-15:30)
  - KIS 일봉: 매일 15:40
  - KIS 시장 데이터: 매 5분 (호가, 현재가, 업종지수)
  - 투자자별 매매동향: 매일 16:00
  - 상품정보: 매주 일요일 01:00
  - 재무비율: 매주 일요일 02:00
  - 리포트 생성: 하루 3번 (10:00, 13:00, 15:45)
  - 모델 평가: 매일 16:30

### 법적 보호
- **⚖️ 투자 면책 조항**: 푸터에 명시된 법적 책임 한계
- **📋 데이터 출처 명시**: 모든 데이터의 출처 투명하게 표기

## 🏗️ 아키텍처

- **패턴**: Full-Stack Monolith (Next.js + FastAPI)
- **프론트엔드**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS
- **백엔드**: Python 3.11 + FastAPI
- **배포**: AWS EC2 (t3.small) + Docker Compose
- **데이터베이스**: PostgreSQL (관계형 데이터) + Milvus (벡터 검색) + Redis (예측 캐싱)
- **외부 API**:
  - KIS OpenAPI (한국투자증권): 실시간 주가, 투자자 수급, 재무 데이터
  - OpenAI API: GPT-4o (예측), text-embedding-3-small (임베딩, 768차원)
- **데이터 처리**:
  - 비동기 작업: Celery + Redis (리포트 생성)
  - 스케줄러: APScheduler (주기적 크롤링 및 데이터 수집)
  - 실시간 알림: WebSocket + Server-Sent Events

### 데이터 티어 구조

Azak은 6가지 데이터 티어를 기반으로 종목을 분석합니다:

1. **Tier 1 - 주가·거래량**: KIS API를 통한 가격/거래량 데이터 (필수)
2. **Tier 2 - 투자자 수급**: 외국인/기관/개인 매매 동향 (중요도: 높음)
3. **Tier 3 - 재무 지표**: ROE, PER, PBR 등 기업 재무비율 (중요도: 높음)
4. **Tier 4 - 기업 정보**: 업종, 시가총액, 상장주식수 등 (중요도: 중간)
5. **Tier 5 - 기술적 지표**: 이동평균, RSI, MACD 등 자체 계산 (중요도: 중간)
6. **Tier 6 - 시장 동향**: 뉴스 + DART 공시 (중요도: 보조)

각 티어의 데이터 완전도를 계산하여 리포트 신뢰도를 평가합니다. 기존의 뉴스 중심 분석에서 벗어나 정량적 데이터를 우선하는 구조로 개선되었습니다.

자세한 아키텍처는 [docs/architecture.md](docs/architecture.md)를 참조하세요.

## 🛠️ 기술 스택

| 영역 | 기술 |
|------|------|
| **Frontend** | Next.js 15.1.4, React 19, TypeScript 5.x, Tailwind CSS 3.x |
| **Backend** | Python 3.11, FastAPI 0.104+ |
| **Database** | PostgreSQL 15, Milvus 2.3+, Redis 7.0+ |
| **LLM** | OpenAI GPT-4o, text-embedding-3-small (768d) |
| **Market Data** | KIS OpenAPI (한국투자증권) |
| **Task Queue** | Celery + Redis (비동기 리포트 생성) |
| **Scheduler** | APScheduler 3.10+ |
| **Notification** | python-telegram-bot 20.7+ |
| **Containerization** | Docker 24+, Docker Compose 2.20+ |
| **Cloud** | AWS EC2 |

## 📋 사전 요구사항

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
- Redis (포트 6379)
- Milvus (포트 19530)
- etcd, MinIO (Milvus 의존성)

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

# Milvus 컬렉션 생성
python scripts/init_milvus.py
```

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
- 웹 대시보드: http://localhost:3000
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
│   ├── crawlers/              # 뉴스 크롤러
│   │   ├── crawler_scheduler.py  # 통합 스케줄러
│   │   ├── naver_crawler.py      # 네이버 뉴스
│   │   ├── hankyung_crawler.py   # 한국경제
│   │   ├── maeil_crawler.py      # 매일경제
│   │   ├── reddit_crawler.py     # Reddit
│   │   └── dart_crawler.py       # DART 공시
│   ├── kis/                   # KIS API 연동
│   │   ├── kis_client.py         # KIS API 클라이언트
│   │   ├── kis_scheduler.py      # KIS 데이터 수집 스케줄러
│   │   └── kis_utils.py          # KIS 유틸리티
│   ├── llm/                   # LLM 예측 엔진
│   │   ├── data_tier_builder.py  # 6가지 데이터 티어 구축
│   │   ├── predictor.py          # AI 예측
│   │   └── ab_test.py            # A/B 테스트
│   ├── tasks/                 # 비동기 작업 (Celery)
│   │   └── report_tasks.py       # 리포트 생성 작업
│   ├── notifications/         # 텔레그램 알림
│   ├── db/                    # 데이터베이스 모델 및 리포지토리
│   ├── scheduler/             # APScheduler 작업
│   ├── api/                   # REST API 엔드포인트
│   │   ├── reports.py            # 리포트 API (비동기 생성)
│   │   ├── preview.py            # 프리뷰 URL API
│   │   └── ab_test.py            # A/B 테스트 API
│   └── scripts/               # 유틸리티 스크립트
├── data/                      # 로컬 데이터 저장소
├── docs/                      # 문서 (PRD, 아키텍처)
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

- [PRD (Product Requirements Document)](docs/prd.md)
- [아키텍처 문서](docs/architecture.md)
- [US-005: 데이터 티어 기반 리포트 개선](docs/us-005-data-tier-report.md)
- [US-006: 비동기 리포트 생성 시스템](docs/us-006-async-report-generation.md)

## ⚖️ 법적 고지사항

**투자 면책 조항**

본 플랫폼에서 제공하는 모든 정보, 분석, 예측은 투자 참고용으로만 제공되며, 투자 권유나 매수/매도 추천이 아닙니다. 투자 결정은 본인의 판단과 책임 하에 이루어져야 하며, 투자로 인한 손실에 대해 본 플랫폼은 어떠한 법적 책임도 지지 않습니다.

**데이터 출처**
- 주가/재무 데이터: 한국투자증권 OpenAPI
- 뉴스 데이터: 네이버, 한국경제, 매일경제, Reddit
- 공시 데이터: 금융감독원 DART
- AI 분석: OpenAI GPT-4o

**저작권 보호**

본 플랫폼은 뉴스 원문을 재배포하지 않으며, 요약 및 분석만을 제공합니다. 모든 뉴스 출처는 명시되며, 원문은 해당 언론사의 저작물입니다.

## 📄 라이선스

MIT License

## 👥 기여자

- 프로젝트 관리자: [Your Name]

## 📞 문의

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.
