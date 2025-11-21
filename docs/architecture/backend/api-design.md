# API 설계

## 엔드포인트 구조

모든 엔드포인트는 `/api/*` 패턴 사용 (일부 예외 있음):

### 인증 & 사용자
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `GET /api/users/me` - 현재 사용자 정보

### 헬스체크
- `GET /health` - 서비스 상태 확인 (JWT 불필요)

### 예측 & 분석
- `POST /api/predict` - 주식 예측 생성
- `GET /api/analysis/{stock_code}` - 종목 분석 조회

### 뉴스
- `GET /api/news` - 뉴스 목록 조회
- `GET /api/news/{id}` - 뉴스 상세 조회

### 종목 관리
- `GET /api/stocks` - 종목 목록 조회
- `POST /api/stocks` - 종목 추가
- `PUT /api/stocks/{code}` - 종목 수정

### 대시보드
- `GET /api/dashboard/stats` - 통계 요약
- `GET /api/dashboard/recent` - 최근 활동

### 평가 & 모델
- `GET /api/evaluations` - 모델 평가 결과
- `GET /api/models` - 사용 가능한 모델 목록
- `POST /api/models` - 모델 추가 (관리자)
- `PUT /api/models/{id}` - 모델 수정 (관리자)

### A/B 테스트
- `GET /api/ab-test/config` - A/B 테스트 설정
- `POST /api/ab-test/config` - A/B 테스트 활성화/비활성화

### 공개 프리뷰 링크
- `POST /api/admin/preview-links` - 홍보 링크 생성 (관리자 전용, UUID 기반)
- `GET /api/public-preview/{link_id}` - 링크로 종목 코드 조회 (인증 불필요)
- `GET /api/admin/preview-links/{stock_code}` - 종목별 링크 목록 조회 (관리자)
- `DELETE /api/admin/preview-links/{link_id}` - 링크 삭제 (관리자)

> 상세한 API 명세는 `docs/api/contracts-backend.md` 참조

## 인증

- **JWT 토큰 기반 인증**: `backend/auth/security.py`
- **세션 쿠키**: `azak_session` (24시간 유효)
- **비밀번호 해싱**: bcrypt
- **보호 제외 경로**: `/health`, `/docs`, `/openapi.json`

## API 라우터 구조

도메인별 FastAPI 라우터 (`backend/api/`):
- `auth.py` - 인증 (로그인/로그아웃)
- `users.py` - 사용자 관리
- `health.py` - 헬스체크
- `prediction.py` - 예측 생성
- `dashboard.py` - 대시보드 통계
- `news.py` - 뉴스 CRUD
- `stocks.py` - 종목 조회
- `stock_management.py` - 종목 관리 (추가/수정)
- `ab_test.py` - A/B 테스트 설정
- `models.py` - 모델 관리 (normal/reasoning 모델 지원)
- `evaluations.py` - 모델 평가 조회
- `statistics.py` - 통계 API
- `preview_links.py` - 공개 프리뷰 링크 관리 (블로그/SNS 홍보용)

## 관련 문서

- [API 계약서](../../api/contracts-backend.md) - 상세한 API 명세
- [프로세스 흐름](./processes.md) - API 호출 시퀀스
- [보안](./optimization.md#보안-고려사항) - API 보안 정책
