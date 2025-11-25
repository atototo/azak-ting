# 컴포넌트 구조

## 컴포넌트 개요

### `api/` - REST API 라우터

도메인별 FastAPI 라우터:
- `auth.py` - 인증 (로그인/로그아웃)
- `users.py` - 사용자 관리
- `health.py` - 헬스체크
- `prediction.py` - 예측 생성
- `dashboard.py` - 대시보드 통계
- `news.py` - 뉴스 CRUD
- `stocks.py` - 종목 조회
- `stock_management.py` - 종목 관리 (추가/수정)
- `ab_test.py` - A/B 테스트 설정
- `models.py` - 모델 관리 (normal/reasoning 타입 지원)
- `evaluations.py` - 모델 평가 조회
- `statistics.py` - 통계 API
- `preview_links.py` - 공개 프리뷰 링크 관리 (블로그/SNS 홍보용)

### `auth/` - 인증 & 보안

- `security.py` - JWT 생성/검증, 비밀번호 해싱
- `dependencies.py` - FastAPI 의존성 (get_current_user)

### `crawlers/` - 데이터 수집

#### 뉴스 크롤러
- `naver_crawler.py` - 네이버 뉴스
- `hankyung_crawler.py` - 한국경제
- `maeil_crawler.py` - 매일경제
- `naver_search_crawler.py` - 네이버 검색 (종목별)
- `reddit_crawler.py` - Reddit 포스트
- `dart_crawler.py` - 금융감독원 공시

#### 시장 데이터 수집
- `kis_client.py` - KIS API 클라이언트
- `kis_daily_crawler.py` - 일봉 데이터
- `kis_minute_collector.py` - 1분봉 데이터
- `kis_market_data_collector.py` - 호가, 현재가, 투자자 매매동향, 업종지수
- `kis_financial_collector.py` - 재무비율
- `kis_product_info_collector.py` - 종목 상품정보
- `index_daily_collector.py` - 업종/지수 일자별 데이터
- `dual_run_collector.py` - 이중 실행 방지 유틸리티

#### 기타
- `base_crawler.py` - 크롤러 추상 클래스
- `news_saver.py` - 뉴스 DB 저장 로직
- `news_stock_matcher.py` - 뉴스-종목 매칭

### `llm/` - AI & 예측

- `multi_model_predictor.py` - 멀티 LLM 예측 (OpenAI, OpenRouter, normal/reasoning 모델 지원)
  - **병렬 처리**: ThreadPoolExecutor (4 모델 동시 실행, 80s → 30s, 2.6x 개선)
  - **에러 격리**: 개별 모델 실패 시에도 다른 모델 예측 성공
- `investment_report.py` - 투자 리포트 생성 (통합 프롬프트 `build_unified_prompt`)
- `embedder.py` - 뉴스 임베딩 생성
  - **임베딩 모델**: KoSimCSE (BM-K/KoSimCSE-roberta) - 한국어 특화
  - **Thread-Safe**: Double-check lock pattern으로 싱글톤 보장
  - **마이그레이션**: OpenAI text-embedding-3-small → 로컬 KoSimCSE (2025-11-22)
- `vector_search.py` - 벡터 유사도 검색
  - **검색 엔진**: FAISS (로컬 파일 기반, `data/faiss_index/`)
  - **마이그레이션**: Milvus → FAISS (2025-11-22)
- `prediction_cache.py` - 예측 결과 캐싱
- `prompts/` - LLM 프롬프트 템플릿

### `scheduler/` - 백그라운드 작업

- `crawler_scheduler.py` - AsyncIOScheduler 기반 크롤링 스케줄러
  - **스케줄러**: AsyncIOScheduler (Segmentation Fault 해결, 2025-11-24)
  - **트리거**: CronTrigger (뉴스: 0,10,20,30,40,50분 / AI: 5,15,25,35,45,55분)
  - **마이그레이션**: BackgroundScheduler → AsyncIOScheduler
- `evaluation_scheduler.py` - 평가 작업 스케줄러

### `services/` - 비즈니스 로직

- `stock_analysis_service.py` - 종목 분석 및 통합 리포트 생성 (`generate_unified_stock_report`, DB + Prediction 통합)
- `evaluation_service.py` - 모델 평가 로직
- `price_service.py` - 주가 데이터 조회
- `aggregation_service.py` - 데이터 집계
- `kis_data_service.py` - KIS 데이터 서비스

### `db/` - 데이터베이스 레이어

- `session.py` - SQLAlchemy 세션 관리
- `base.py` - 베이스 모델 클래스
- ~~`milvus_client.py`~~ - **제거됨** (Milvus → FAISS 마이그레이션, 2025-11-22)
- `models/` - SQLAlchemy ORM 모델
  - `user.py` - 사용자
  - `stock.py` - 종목
  - `news.py` - 뉴스 (predicted_at 필드 추가, 2025-11-24)
  - `prediction.py` - 예측
  - `stock_analysis.py` - 종목 분석
  - `model.py` - AI 모델 (model_type: normal/reasoning 지원)
  - `model_evaluation.py` - 모델 평가
  - `evaluation_history.py` - 평가 히스토리
  - `ab_test_config.py` - A/B 테스트 설정
  - `daily_performance.py` - 일간 성과
  - `market_data.py` - 시장 데이터
  - `financial.py` - 재무 데이터
  - `match.py` - 뉴스-주가 매칭
  - `public_preview_link.py` - 공개 프리뷰 링크 (UUID 기반)
- `migrations/` - 데이터베이스 마이그레이션 스크립트 (Alembic 스타일)
- `repositories/` - 데이터 접근 레이어

### `notifications/` - 알림

- `telegram.py` - 텔레그램 봇 알림
- `templates/` - 알림 메시지 템플릿

### `utils/` - 유틸리티

- `market_time.py` - 장 시간 체크
- `market_hours.py` - 거래 시간 관리
- `business_days.py` - 영업일 계산
- `prediction_status.py` - 예측 상태 관리
- `background_prediction.py` - 백그라운드 예측 실행
- `technical_indicators.py` - 기술적 지표
- `resample.py` - 데이터 리샘플링
- `deduplicator.py` - 중복 제거
- `embedding_deduplicator.py` - 임베딩 중복 제거
- `data_source_selector.py` - 데이터 소스 선택
- `encoding_normalizer.py` - 인코딩 정규화
- `stock_mapping.py` - 종목 코드 매핑
- `market_index.py` - 시장 지수 관리

### `validators/` - 데이터 검증

- `kis_validator.py` - KIS API 응답 검증

### `tests/` - 테스트

- `test_predictor_impact_analysis.py` - 예측기 영향 분석 테스트
- `test_impact_analysis_integration.py` - 통합 테스트

## 소스 트리 구조

`docs/development/source-tree-analysis.md`의 백엔드 섹션 참조. 주요 디렉터리:

```
backend/
├── api/              # REST API 라우터
├── auth/             # 인증 & 보안
├── crawlers/         # 데이터 수집
├── db/               # 데이터베이스
│   ├── models/       # ORM 모델
│   └── migrations/   # 마이그레이션
├── llm/              # AI & 예측
│   └── prompts/      # 프롬프트
├── scheduler/        # 백그라운드 작업
├── services/         # 비즈니스 로직
├── notifications/    # 알림
├── utils/            # 유틸리티
├── validators/       # 검증
├── tests/            # 테스트
├── config.py         # 설정 관리
└── main.py           # FastAPI 앱 진입점
```

## 관련 문서

- [소스 트리 분석](../../development/source-tree-analysis.md) - 전체 소스 코드 구조
- [API 설계](./api-design.md) - API 라우터 상세
- [데이터 아키텍처](./data-architecture.md) - 데이터베이스 모델
