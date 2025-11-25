# 주요 프로세스 흐름

## 예측 생성 프로세스

사용자가 종목 예측을 요청할 때의 전체 흐름:

```mermaid
sequenceDiagram
    participant Client as 클라이언트
    participant API as API 라우터
    participant Auth as 인증 모듈
    participant Service as 분석 서비스
    participant Cache as Redis 캐시
    participant DB as PostgreSQL
    participant Vector as FAISS
    participant LLM as GPT-4o/DeepSeek-V3
    participant TG as 텔레그램

    Client->>API: POST /api/predict {stock_code}
    API->>Auth: JWT 토큰 검증
    Auth-->>API: 사용자 인증 완료

    API->>Service: generate_prediction(stock_code, user)

    Service->>Cache: 캐시 확인
    alt 캐시 있음 (15분 이내)
        Cache-->>Service: 캐시된 예측 반환
        Service-->>API: 캐시된 결과
    else 캐시 없음
        Service->>DB: 종목 정보 조회
        DB-->>Service: 종목 데이터

        Service->>DB: 최근 뉴스 조회
        DB-->>Service: 뉴스 리스트

        Service->>Vector: 유사 뉴스 검색
        Vector-->>Service: 임베딩 결과

        Service->>DB: 과거 주가 조회
        DB-->>Service: 주가 데이터

        Service->>LLM: 분석 요청 (프롬프트 + 데이터)
        LLM-->>Service: AI 분석 결과

        Service->>DB: 예측 저장
        Service->>Cache: 결과 캐싱 (TTL 15분)

        Service-->>API: 예측 결과
    end

    API-->>Client: 200 OK {prediction}

    opt 자동 알림 활성화
        Service->>TG: 알림 전송
        TG-->>Service: 전송 완료
    end
```

## 스케줄러 작업 흐름

백그라운드 스케줄러의 일일 작업 프로세스:

```mermaid
sequenceDiagram
    participant Scheduler as AsyncIOScheduler
    participant Crawler as 뉴스 크롤러
    participant Matcher as 매칭 서비스
    participant Embedder as 임베딩 생성기
    participant Reporter as 리포트 생성기
    participant Evaluator as 평가 서비스
    participant DB as PostgreSQL
    participant Vector as FAISS
    participant TG as 텔레그램

    Note over Scheduler: 09:00 - 장 시작

    loop 10분마다
        Scheduler->>Crawler: 뉴스 크롤링 실행
        Crawler->>Crawler: 네이버/한경/매경/Reddit
        Crawler->>DB: 뉴스 저장 (중복 제거)

        Scheduler->>TG: 신규 뉴스 알림
    end

    Note over Scheduler: 10:00 - 장초 리포트
    Scheduler->>Reporter: 리포트 생성 (전체 종목)
    Reporter->>DB: 데이터 조회
    Reporter->>DB: 리포트 저장

    Note over Scheduler: 15:40 - 장 마감 후
    Scheduler->>Matcher: 뉴스-종목 매칭
    Matcher->>DB: 매칭 결과 저장

    Scheduler->>Reporter: 장마감 리포트 생성
    Reporter->>DB: 리포트 저장

    Note over Scheduler: 16:00 - 임베딩
    Scheduler->>Embedder: 신규 뉴스 임베딩
    Embedder->>Vector: 임베딩 저장

    Note over Scheduler: 16:30 - 평가
    Scheduler->>Evaluator: 모델 평가 실행
    Evaluator->>DB: 오늘 리포트 조회
    Evaluator->>DB: 실제 주가 조회
    Evaluator->>Evaluator: 정확도 계산
    Evaluator->>DB: 평가 결과 저장

    Note over Scheduler: 18:00 - 시간외 거래 종료
    Scheduler->>Crawler: 시간외 가격 수집
    Crawler->>DB: 시간외 가격 저장
```

## 스케줄러 작업 목록

`backend/scheduler/crawler_scheduler.py` - AsyncIOScheduler 기반 크롤링 스케줄러:

### 데이터 수집 (CronTrigger - 0,10,20,30,40,50분)
- **뉴스 크롤링**: 네이버, 한국경제, 매일경제, Reddit (10분 간격)
- **종목별 뉴스 검색**: 네이버 검색 API (10분 간격)
- **DART 공시**: 5분 간격
- **자동 알림**: 10분 간격 (predicted_at 기준 필터링)

### AI 분석 (CronTrigger - 5,15,25,35,45,55분)
- **투자 리포트 생성**: 10:05, 13:05, 15:45 (병렬 처리, 80s → 30s)
- **뉴스 임베딩**: 매일 16:05 (KoSimCSE 로컬 모델)

### 시장 데이터 (장 시간 기반)
- **KIS 일봉 수집**: 매일 15:40
- **KIS 1분봉 수집**: ~~1분 간격~~ → **비활성화** (19,500 API 호출 절감)
- **KIS 시장 데이터**: 5분 간격 (호가, 현재가)
- **시간외 거래 가격**: 매일 18:00

### 평가 및 매칭 (종가 후)
- **뉴스-주가 매칭**: 매일 15:40
- **모델 평가 생성**: 매일 16:30

### 주간 배치 작업
- **투자자별 매매동향**: 매일 16:00
- **업종/지수 일자별**: 매일 18:00
- **상품정보**: 매주 일요일 01:00
- **재무비율**: 매주 일요일 02:00

**주요 변경사항 (2025-11-24)**:
- BackgroundScheduler → AsyncIOScheduler (Segmentation Fault 해결)
- IntervalTrigger → CronTrigger (뉴스 수집과 AI 분석 분리)
- predicted_at 필드 활용 (알림 전송 중복 방지)
- 1분봉 수집 비활성화 (API 비용 절감)

## 관련 문서

- [데이터 플로우](./data-architecture.md#데이터-플로우-다이어그램) - 데이터 처리 흐름
- [컴포넌트](./components.md) - 스케줄러 및 크롤러 구조
- [개발 가이드](./development.md) - 스케줄러 테스트 방법
