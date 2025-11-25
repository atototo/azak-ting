# Backend Data Models & Storage Surfaces (Quick Scan)

_Source: filenames under `backend/db/models` and `backend/db/migrations` – derived via quick scan._

## ORM Models

| Model File | Domain Aggregate | Storage Backend | Notes |
| --- | --- | --- | --- |
| `user.py` | Operator accounts, roles, API keys | PostgreSQL (`users` table) | Secured with bcrypt + JWT claims |
| `stock.py` | Master list of tickers + metadata | PostgreSQL | Primary key used by crawlers & analytics |
| `market_data.py` | Minute/daily OHLC data cache | PostgreSQL + Redis | Seeds analytics & charting |
| `news.py` | Crawled articles & metadata | PostgreSQL + FAISS vector IDs | Linked to embeddings for RAG. **Updated 2025-11-24**: `predicted_at` 필드 추가 (예측 생성 추적, 알림과 분리) |
| `prediction.py` | GPT-4o inference outputs | PostgreSQL | Includes probability & confidence bands |
| `model.py` | Registered AI model configs | PostgreSQL | Tracks prompt, temperature, provider |
| `model_evaluation.py` | Offline evaluation scores | PostgreSQL | Feeds `/evaluations` API |
| `evaluation_history.py` | Trend of evaluation metrics | PostgreSQL | Used for regression detection |
| `daily_performance.py` | Aggregated KPI snapshots | PostgreSQL | Surfaces on dashboard cards |
| `stock_analysis.py` | AI explanations per stock | PostgreSQL | Displayed in `stocks` route |
| `ab_test_config.py` | Experiment variants | PostgreSQL | Toggles alternative prompts |
| `match.py` | News-stock link table | PostgreSQL | Maintains relevance graph |

## Schema / Migration Inventory

`backend/db/migrations/` contains incremental DDL scripts. Key operations inferred from filenames:

- `add_minute_table.py`, `add_structured_price_fields.py` – extend market data granularity.
- `add_evaluation_tables.py`, `add_impact_analysis_fields.py` – support new analytics KPIs.
- `add_source_column.py`, `add_table_comments.py` – governance & lineage metadata.
- `remove_foreign_keys.py`, `remove_stock_code_unique_constraint.sql` – loosen constraints for brownfield imports.

## Vector & Search Assets

- **FAISS (로컬 파일)**: `backend/llm/vector_search.py`가 FAISS 인덱스 관리
- **임베딩 모델**: KoSimCSE (BM-K/KoSimCSE-roberta) - 한국어 특화 모델
- **마이그레이션 완료**: 2025-11-22, Milvus → FAISS (7,040개 벡터)
- Embedding IDs stored alongside `news` rows for RAG lookups.

## Recent Schema Changes (2025-11-24)

### NewsArticle Model - `predicted_at` 필드 추가
**목적**: 예측 생성 추적을 알림 전송과 분리
- **필드명**: `predicted_at` (DateTime, nullable)
- **인덱스**: `idx_news_articles_predicted_at`
- **마이그레이션**: 762건 기존 데이터 업데이트 완료
- **관련 이슈**: [Issue #13](https://github.com/atototo/azak/issues/13), [PR #14](https://github.com/atototo/azak/pull/14)

## Data Governance To-Dos

- Confirm Alembic/Flyway tracking; migrations are Python scripts but no version table observed (consider standardizing).
- Add ER diagram export before production deployment to document FK relationships between `news`, `predictions`, and `evaluations`.
