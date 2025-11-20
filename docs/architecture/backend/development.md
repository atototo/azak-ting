# 개발 가이드

## 환경 설정

```bash
# Python 3.11 설치
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발 도구

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (PostgreSQL, Redis, OpenAI API 키 등)
```

## 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m backend.main

# 프로덕션 모드
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=backend --cov-report=html

# 특정 테스트 파일
pytest backend/tests/test_predictor_impact_analysis.py -v
```

## 코드 품질

```bash
# 포매팅 (Black)
black backend/ --line-length 100

# Import 정렬 (isort)
isort backend/

# 타입 체크 (mypy)
mypy backend/

# 린팅 (선택사항)
flake8 backend/
```

## 데이터베이스 마이그레이션

```bash
# 마이그레이션 스크립트 실행
python backend/db/migrations/add_table_comments.py
python backend/db/migrations/add_impact_analysis_fields.py

# 새 마이그레이션 작성
# backend/db/migrations/ 폴더에 Python 스크립트 작성
```

## 테스트 전략

### 테스트 유형

- **단위 테스트**: `tests/test_*.py`
  - 각 컴포넌트 독립 테스트
  - Mocking 활용 (DB, 외부 API)

- **통합 테스트**: `tests/test_*_integration.py`
  - 여러 컴포넌트 연동 테스트
  - 실제 DB 연결 (테스트 DB 사용)

- **E2E 테스트**: (선택사항)
  - API 엔드포인트 전체 플로우 테스트

### 테스트 설정

- **프레임워크**: pytest 8.4.2
- **비동기 테스트**: pytest-asyncio 1.2.0
- **시간 조작**: freezegun 1.5.5
- **커버리지 목표**: 80% 이상 (코어 로직)

`pyproject.toml` 참조:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.coverage.run]
source = ["backend"]
omit = ["*/tests/*", "*/migrations/*"]
```

## 주요 설정 파일

### `config.py` - 애플리케이션 설정

모든 환경 변수를 `pydantic_settings.BaseSettings`로 관리:
- 데이터베이스 URL
- Redis URL
- OpenAI/OpenRouter API 키
- 텔레그램 설정
- CORS 허용 도메인
- 로깅 레벨
- A/B 테스트 설정

### `main.py` - FastAPI 앱

- API 라우터 등록
- CORS 미들웨어
- 시작/종료 이벤트 (APScheduler 시작/종료)
- 로깅 설정

## 관련 문서

- [개발 가이드](../../development/guide.md) - 전체 프로젝트 개발 가이드
- [API 설계](./api-design.md) - API 개발 가이드
- [컴포넌트](./components.md) - 컴포넌트 구조
