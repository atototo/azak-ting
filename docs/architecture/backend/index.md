# 백엔드 아키텍처 (FastAPI 서비스)

AI 기반 주식 인사이트를 제공하는 FastAPI 기반 API 및 스케줄러 서비스입니다. PostgreSQL로 관계형 데이터를 관리하고, Milvus로 임베딩을 저장하며, Redis로 캐싱을 처리하고, APScheduler로 비동기 작업을 스케줄링합니다.

## 문서 구조

백엔드 아키텍처 문서는 다음과 같이 주제별로 구성되어 있습니다:

### 📋 [시스템 개요](./overview.md)
- 개요 및 기술 스택
- 아키텍처 패턴 (SOA)
- 시스템 아키텍처 다이어그램

### 💾 [데이터 아키텍처](./data-architecture.md)
- PostgreSQL 관계형 데이터
- Milvus 벡터 임베딩
- Redis 캐싱
- 데이터베이스 ERD
- 데이터 플로우 다이어그램

### 🔌 [API 설계](./api-design.md)
- REST API 엔드포인트 구조
- 인증 & 권한
- API 라우터 구조

### 🔄 [프로세스 흐름](./processes.md)
- 예측 생성 프로세스
- 스케줄러 작업 흐름
- 시퀀스 다이어그램

### 🧩 [컴포넌트 구조](./components.md)
- 컴포넌트 개요
- 소스 트리 구조
- 주요 모듈 설명

### 👨‍💻 [개발 가이드](./development.md)
- 환경 설정
- 서버 실행
- 테스트 실행
- 코드 품질 도구
- 주요 설정 파일

### 🚀 [배포 가이드](./deployment.md)
- Docker 컨테이너 구조
- 프로덕션 배포
- 환경 변수 설정
- 모니터링

### ⚡ [최적화 & 보안](./optimization.md)
- 성능 최적화
- 보안 고려사항
- 문제 해결

## 빠른 시작

### 개발 환경 설정
```bash
# Python 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집
```

### 서버 실행
```bash
# 개발 모드
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 주요 엔드포인트
- **API 문서**: http://localhost:8000/docs
- **헬스체크**: http://localhost:8000/health

## 주요 기능

### API 라우터 (13개)
- 인증 & 사용자 관리
- 종목 관리 및 조회
- AI 예측 생성
- 뉴스 크롤링 데이터
- 모델 평가 및 A/B 테스트
- 대시보드 통계

### 데이터 수집
- 뉴스 크롤링 (네이버, 한경, 매경, Reddit)
- DART 공시
- KIS 시장 데이터 (일봉, 1분봉, 호가, 재무)

### AI 통합
- OpenAI GPT-4o (예측)
- OpenAI text-embedding-3-small (임베딩)
- OpenRouter DeepSeek v3.2 (대체 LLM)
- 멀티 모델 A/B 테스트

### 스케줄러
- 10분마다: 뉴스 크롤링, 자동 알림
- 장 시간: 1분봉 수집, 시장 데이터
- 장 마감 후: 리포트 생성, 모델 평가, 임베딩 생성

## 관련 문서

### 다른 아키텍처 문서
- [전체 아키텍처 개요](../overview.md)
- [Frontend 아키텍처](../frontend.md)
- [Infrastructure 아키텍처](../infrastructure.md)
- [통합 아키텍처](../integration.md)

### API 및 데이터 모델
- [Backend API 계약](../../api/contracts-backend.md)
- [Backend 데이터 모델](../../data/models-backend.md)

### 개발 및 배포
- [개발 가이드](../../development/guide.md)
- [소스 트리 분석](../../development/source-tree-analysis.md)
- [배포 설정](../../deployment/configuration.md)
- [인프라 구성](../../deployment/infrastructure.md)

---

**📝 문서 버전:** 2.0.0
**마지막 업데이트:** 2025-11-20
**변경사항:** 단일 문서에서 주제별 다중 문서로 재구성
