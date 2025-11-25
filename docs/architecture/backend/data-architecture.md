# 데이터 아키텍처

## 개요

백엔드 시스템은 세 가지 주요 데이터 저장소를 사용합니다:
- **PostgreSQL**: 관계형 데이터 (종목, 뉴스, 예측, 사용자 등)
- **FAISS**: 벡터 임베딩 (뉴스 기사 유사도 검색, 로컬 파일 기반)
- **Redis**: 캐싱 (예측 결과, 핫 메트릭)

## 관계형 데이터 (PostgreSQL)

`docs/data-models-backend.md`에 문서화된 엔티티들:
- **사용자**: `user` (인증 정보)
- **종목**: `stock` (종목 정보, 우선순위)
- **뉴스**: `news` (크롤링된 뉴스 기사)
- **예측**: `prediction`, `stock_analysis` (AI 예측 결과)
- **평가**: `model_evaluation`, `evaluation_history` (모델 성능 추적)
- **시장 데이터**: `daily_price`, `minute_price`, `index_daily_price`, `overtime_price` (KIS API)
- **재무 데이터**: `financial_ratios`, `product_info` (기업 재무 정보)
- **A/B 테스트**: `ab_test_config`, `model` (멀티 모델 실험, normal/reasoning 타입 지원)
- **매칭**: `match` (뉴스-주가 연결)
- **공개 프리뷰**: `public_preview_links` (블로그/SNS 홍보용 공개 링크)

## 벡터 임베딩 (FAISS)

- `backend/llm/vector_search.py`를 통해 FAISS 인덱스 관리
- 뉴스 기사 임베딩 저장 및 유사도 검색
- **저장 위치**: `data/faiss_index/` (로컬 파일)
- **임베딩 모델**: KoSimCSE (BM-K/KoSimCSE-roberta) - 한국어 특화
- **마이그레이션 완료**: 2025-11-22, Milvus → FAISS (7,040개 벡터)

## 캐싱 (Redis)

- 핫 메트릭 캐싱
- 예측 결과 캐시 (`backend/llm/prediction_cache.py`)

## 데이터베이스 ERD

```mermaid
erDiagram
    USER ||--o{ PREDICTION : creates
    USER {
        int id PK
        string username
        string email
        string password_hash
        datetime created_at
    }

    STOCK ||--o{ NEWS : related_to
    STOCK ||--o{ PREDICTION : predicts
    STOCK ||--o{ DAILY_PRICE : has
    STOCK ||--o{ MINUTE_PRICE : has
    STOCK ||--o{ STOCK_ANALYSIS : analyzes
    STOCK {
        string code PK
        string name
        string market
        int priority
        boolean is_active
        datetime created_at
    }

    NEWS ||--o{ MATCH : matches
    NEWS {
        int id PK
        string title
        text content
        string source
        string url
        datetime published_at
        string stock_code FK
        boolean has_embedding
    }

    STOCK ||--o{ MATCH : matches
    MATCH {
        int id PK
        int news_id FK
        string stock_code FK
        float relevance_score
        datetime matched_at
    }

    PREDICTION {
        int id PK
        string stock_code FK
        int user_id FK
        int model_id FK
        text analysis
        float target_price
        string direction
        float confidence
        datetime created_at
    }

    MODEL ||--o{ PREDICTION : generates
    MODEL ||--o{ MODEL_EVALUATION : evaluated_by
    MODEL {
        int id PK
        string name
        string provider
        string model_identifier
        string model_type "normal/reasoning"
        boolean is_active
        string description
        datetime created_at
    }

    STOCK_ANALYSIS ||--o{ MODEL_EVALUATION : evaluates
    STOCK_ANALYSIS {
        int id PK
        string stock_code FK
        int model_id FK
        float base_price
        float short_term_target
        float long_term_target
        text summary
        datetime last_updated
    }

    MODEL_EVALUATION {
        int id PK
        int model_id FK
        int analysis_id FK
        float accuracy_score
        float direction_score
        float final_score
        datetime evaluated_at
    }

    EVALUATION_HISTORY {
        int id PK
        int model_id FK
        date evaluation_date
        float avg_score
        int total_predictions
        int correct_predictions
    }

    AB_TEST_CONFIG ||--|| MODEL : tests_model_a
    AB_TEST_CONFIG ||--|| MODEL : tests_model_b
    AB_TEST_CONFIG {
        int id PK
        int model_a_id FK
        int model_b_id FK
        boolean is_active
        datetime start_date
        datetime end_date
    }

    DAILY_PRICE {
        int id PK
        string stock_code FK
        date trade_date
        decimal open_price
        decimal high_price
        decimal low_price
        decimal close_price
        bigint volume
    }

    MINUTE_PRICE {
        int id PK
        string stock_code FK
        datetime timestamp
        decimal price
        bigint volume
    }

    FINANCIAL_RATIOS {
        int id PK
        string stock_code FK
        date quarter
        decimal per
        decimal pbr
        decimal roe
        decimal debt_ratio
    }

    STOCK ||--o{ PUBLIC_PREVIEW_LINK : has_preview
    USER ||--o{ PUBLIC_PREVIEW_LINK : creates
    PUBLIC_PREVIEW_LINK {
        string link_id PK "UUID"
        string stock_code FK
        int created_by FK
        datetime created_at
        datetime expires_at "nullable"
    }
```

## 데이터 플로우 다이어그램

전체 데이터 수집부터 예측, 평가까지의 흐름:

```mermaid
flowchart TD
    Start([시작: 스케줄러 실행])

    subgraph "데이터 수집 (10분마다)"
        A1[뉴스 크롤링<br/>네이버/한경/매경]
        A2[종목별 검색<br/>네이버 검색]
        A3[DART 공시<br/>5분마다]
        A4[Reddit 크롤링]
    end

    subgraph "시장 데이터 (실시간)"
        B1[KIS 1분봉<br/>1분마다, 장시간만]
        B2[KIS 호가/현재가<br/>5분마다, 장시간만]
        B3[KIS 일봉<br/>15:40 장마감후]
    end

    subgraph "데이터 처리"
        C1[뉴스 저장<br/>중복 제거]
        C2[뉴스-종목 매칭<br/>15:40]
        C3[임베딩 생성<br/>16:00]
    end

    subgraph "AI 분석"
        D1[벡터 검색<br/>유사 뉴스 찾기]
        D2[리포트 생성<br/>10:00/13:00/15:45]
        D3[멀티 모델 예측<br/>GPT-4o/DeepSeek]
    end

    subgraph "평가 & 알림"
        E1[모델 평가<br/>16:30]
        E2[텔레그램 알림<br/>10분마다]
    end

    DB[(PostgreSQL)]
    VectorDB[(FAISS<br/>로컬 파일)]
    Cache[(Redis)]

    Start --> A1 & A2 & A3 & A4
    Start --> B1 & B2 & B3

    A1 & A2 & A3 & A4 --> C1
    B1 & B2 & B3 --> DB

    C1 --> DB
    C1 --> C2
    C2 --> DB
    C2 --> C3
    C3 --> VectorDB

    DB --> D1
    VectorDB --> D1
    D1 --> D2
    D2 --> D3
    D3 --> Cache
    D3 --> DB

    DB --> E1
    E1 --> DB
    D3 --> E2

    E2 --> End([종료: 알림 전송])

    style A1 fill:#FFE4B5
    style D3 fill:#87CEEB
    style E2 fill:#90EE90
    style DB fill:#336791
    style VectorDB fill:#00ADD8
    style Cache fill:#DC382D

    classDef localFile fill:#E0F7FA,stroke:#00796B,stroke-width:2px
    class VectorDB localFile
```

## 관련 문서

- [데이터 모델 상세](../../data/models-backend.md) - 전체 데이터 모델 명세
- [API 설계](./api-design.md) - 데이터 접근 API
- [프로세스 흐름](./processes.md) - 데이터 처리 프로세스
