# Reasoning Model Support 구현

**작업 일자**: 2025-11-21
**작업자**: Development Team
**관련 이슈**: Reasoning 모델(gpt-5-mini, o1, o3 등) 지원 추가

---

## 📋 목차

1. [변경 개요](#변경-개요)
2. [AS-IS (기존 상태)](#as-is-기존-상태)
3. [변경 필요 사유](#변경-필요-사유)
4. [TO-BE (변경 후 상태)](#to-be-변경-후-상태)
5. [변경 사항 상세](#변경-사항-상세)
6. [테스트 결과](#테스트-결과)
7. [사용 방법](#사용-방법)
8. [참고 사항](#참고-사항)

---

## 변경 개요

OpenAI의 reasoning 모델(gpt-5-mini, o1, o3 등)은 일반 모델과 다른 API 응답 구조를 사용합니다. 이를 지원하기 위해 모델 타입 구분 시스템을 구축하고, reasoning 모델에 대한 특별 처리 로직을 추가했습니다.

---

## AS-IS (기존 상태)

### 데이터베이스
```python
# backend/db/models/model.py
class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)
    model_identifier = Column(String(200), nullable=False)
    # ❌ model_type 필드 없음
    is_active = Column(Boolean, default=True)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)
```

### API
```python
# backend/api/models.py
class ModelCreate(BaseModel):
    name: str
    provider: str
    model_identifier: str
    # ❌ model_type 필드 없음
    description: Optional[str] = None
```

### Predictor 로직
```python
# backend/llm/predictor.py
def _predict_with_model(self, client, model_name, provider, prompt, similar_count):
    # ❌ 모든 모델을 동일하게 처리
    if provider == "openai":
        response = client.chat.completions.create(
            model=model_name,
            messages=[...],
            response_format={"type": "json_object"},  # 모든 모델에 적용
            max_tokens=1000  # 고정값
        )

    # ❌ content 필드만 사용
    result_text = response.choices[0].message.content
```

### 문제점
1. **모든 모델을 동일하게 처리**: normal vs reasoning 구분 없음
2. **Reasoning 모델 호출 실패**: `response_format` 미지원으로 API 오류 발생
3. **응답 파싱 실패**: reasoning 필드 처리 불가
4. **토큰 부족**: reasoning 모델의 긴 Chain of Thought를 담기에 1000 토큰 부족

---

## 변경 필요 사유

### 1. Reasoning 모델의 특수성

OpenAI의 reasoning 모델(gpt-5-mini, o1, o3)은 다음과 같은 차이점이 있습니다:

#### API 요청 차이
```python
# ❌ Normal 모델 - response_format 지원
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    response_format={"type": "json_object"},  # ✅ 지원
    max_tokens=1000
)

# ❌ Reasoning 모델 - response_format 미지원
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[...],
    response_format={"type": "json_object"},  # ❌ 오류 발생!
    max_tokens=1000  # ❌ 부족함
)
```

#### API 응답 구조 차이
```python
# Normal 모델 응답
ChatCompletionMessage(
    content='{"sentiment_direction": "positive", ...}',  # JSON 직접 반환
    reasoning=None  # 없음
)

# Reasoning 모델 응답
ChatCompletionMessage(
    content='{"sentiment_direction": "positive", ...}',  # JSON 반환
    reasoning='**Analyzing market impact**\n\n...',  # Chain of Thought 추가!
    reasoning_details=[...]  # 암호화된 상세 분석
)
```

### 2. 필요한 변경 사항

1. **모델 타입 구분**: `normal` vs `reasoning` 타입 추가
2. **API 호출 분기**: reasoning 모델은 `response_format` 제거
3. **토큰 제한 완화**: 1000 → 4000 토큰으로 증가
4. **응답 파싱 개선**: content 비어있을 때 reasoning 필드 활용
5. **JSON 추출 강화**: Chain of Thought에서 JSON 객체 추출

---

## TO-BE (변경 후 상태)

### 데이터베이스
```python
# backend/db/models/model.py
class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)
    model_identifier = Column(String(200), nullable=False)
    model_type = Column(
        SQLEnum("normal", "reasoning", name="model_type_enum"),
        default="normal",
        nullable=False
    )  # ✅ 추가됨
    is_active = Column(Boolean, default=True)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)
```

### API
```python
# backend/api/models.py
class ModelCreate(BaseModel):
    name: str
    provider: str
    model_identifier: str
    model_type: Literal["normal", "reasoning"] = Field(
        default="normal",
        description="모델 타입 (normal: 일반, reasoning: 추론형)"
    )  # ✅ 추가됨
    description: Optional[str] = None

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_identifier: Optional[str] = None
    model_type: Optional[Literal["normal", "reasoning"]] = None  # ✅ 추가됨
    description: Optional[str] = None
    is_active: Optional[bool] = None
```

### Predictor 로직
```python
# backend/llm/predictor.py
def _load_active_models(self):
    """활성 모델 로드 (model_type 포함)"""
    for model in models:
        result[model.id] = {
            "name": model.name,
            "provider": model.provider,
            "model_identifier": model.model_identifier,
            "model_type": model.model_type,  # ✅ 추가됨
            "client": client,
        }

def _predict_with_model(
    self,
    client: OpenAI,
    model_name: str,
    provider: str,
    prompt: str,
    similar_count: int,
    model_type: str = "normal",  # ✅ 파라미터 추가
) -> Dict[str, Any]:
    # ✅ 모델 타입에 따라 시스템 프롬프트 변경
    is_reasoning_model = model_type == "reasoning"

    if is_reasoning_model:
        system_content = (
            "당신은 한국 주식 시장 분석 전문가입니다. "
            "뉴스 분석을 통해 주가 예측을 수행합니다. "
            "사고 과정을 거친 후, 반드시 마지막에 JSON 형식의 결과만 출력하세요."
        )
    else:
        system_content = (
            "당신은 한국 주식 시장 분석 전문가입니다. "
            "뉴스 분석을 통해 주가 예측을 수행합니다. "
            "반드시 JSON 형식으로만 응답하세요."
        )

    # ✅ API 호출 분기
    if provider == "openrouter":
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000 if is_reasoning_model else 1000,  # ✅ 동적 토큰
        )
    else:  # openai
        api_params = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4000 if is_reasoning_model else 1000,  # ✅ 동적 토큰
        }

        # ✅ 일반 모델만 response_format 사용
        if not is_reasoning_model:
            api_params["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**api_params)

    # ✅ 응답 파싱 개선
    message = response.choices[0].message
    result_text = message.content

    # content가 비어있으면 reasoning 필드 확인
    if not result_text and hasattr(message, 'reasoning') and message.reasoning:
        result_text = message.reasoning
        logger.info(f"💡 content 비어있음, reasoning 필드 사용")

    # ✅ JSON 추출 강화 (```json``` 코드 블록 제거)
    if "```json" in result_text:
        match = re.search(r"```json\s*(\{.*?\})\s*```", result_text, re.DOTALL)
        if match:
            result_text = match.group(1)

    # ✅ 마지막 JSON 객체 추출 시도
    if is_reasoning_model and not result_text.strip().startswith('{'):
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}(?=[^{}]*$)', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(0)
```

### 개선 사항

1. ✅ **모델 타입 시스템**: `normal` / `reasoning` 구분
2. ✅ **API 호출 최적화**: 모델별 적절한 파라미터 사용
3. ✅ **토큰 제한 완화**: 4000 토큰으로 Chain of Thought 완전 수용
4. ✅ **응답 파싱 강화**: reasoning 필드 및 JSON 추출 로직
5. ✅ **시스템 프롬프트 최적화**: 모델별 특성에 맞는 지시사항

---

## 변경 사항 상세

### 1. 데이터베이스 마이그레이션

#### PostgreSQL ENUM 타입 생성
```sql
-- /tmp/add_model_type_column.py
DO $$ BEGIN
    CREATE TYPE model_type_enum AS ENUM ('normal', 'reasoning');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
```

#### 컬럼 추가
```sql
DO $$ BEGIN
    ALTER TABLE models
    ADD COLUMN model_type model_type_enum DEFAULT 'normal' NOT NULL;
EXCEPTION
    WHEN duplicate_column THEN
        RAISE NOTICE 'column model_type already exists';
END $$;
```

**실행 방법**:
```bash
uv run python /tmp/add_model_type_column.py
```

### 2. API 스키마 업데이트

**파일**: `backend/api/models.py`

#### 변경 내용
```python
from typing import Literal

class ModelCreate(BaseModel):
    model_type: Literal["normal", "reasoning"] = Field(
        default="normal",
        description="모델 타입 (normal: 일반, reasoning: 추론형)"
    )

class ModelUpdate(BaseModel):
    model_type: Optional[Literal["normal", "reasoning"]] = None

class ModelResponse(BaseModel):
    model_type: str
```

#### 모델 생성 로직 수정
```python
@router.post("/models", response_model=ModelResponse, status_code=201)
async def create_model(model: ModelCreate):
    new_model = Model(
        name=model.name,
        provider=model.provider,
        model_identifier=model.model_identifier,
        model_type=model.model_type,  # ✅ 추가
        description=model.description,
        is_active=True,
    )
    # ... 나머지 로직
```

### 3. Predictor 로직 업데이트

**파일**: `backend/llm/predictor.py`

#### 주요 변경 함수

##### `_load_active_models()` - 모델 로드 시 model_type 포함
```python
def _load_active_models(self) -> Dict[int, Dict[str, Any]]:
    result[model.id] = {
        "name": model.name,
        "provider": model.provider,
        "model_identifier": model.model_identifier,
        "model_type": model.model_type,  # ✅ 추가
        "client": client,
        "description": model.description,
    }
    logger.info(
        f"  📊 Model loaded: {model.name} "
        f"({model.provider}/{model.model_identifier}, "
        f"type={model.model_type})"  # ✅ 로깅 추가
    )
```

##### `_predict_with_model()` - model_type 파라미터 추가
```python
def _predict_with_model(
    self,
    client: OpenAI,
    model_name: str,
    provider: str,
    prompt: str,
    similar_count: int,
    model_type: str = "normal",  # ✅ 추가
) -> Dict[str, Any]:
    # ... 구현
```

##### 모든 호출부 업데이트
```python
# predict_all_models()
model_info = self.models[model_id]
result = self._predict_with_model(
    client=model_info["client"],
    model_name=model_info["model_identifier"],
    provider=model_info["provider"],
    prompt=prompt,
    similar_count=similar_count,
    model_type=model_info["model_type"],  # ✅ 추가
)

# dual_predict() - A/B 테스트
self.model_a_type = self.models[model_a_id]["model_type"]  # ✅ 추가
self.model_b_type = self.models[model_b_id]["model_type"]  # ✅ 추가

# A/B 예측 호출 시
result_a = self._predict_with_model(..., model_type=self.model_a_type)
result_b = self._predict_with_model(..., model_type=self.model_b_type)
```

### 4. 모델 재등록 스크립트

**파일**: `/tmp/register_gpt5mini_reasoning.py`

```python
"""gpt-5-mini를 reasoning 타입으로 등록"""
import sys
sys.path.insert(0, '/Users/young/ai-work/craveny')

from backend.db.session import SessionLocal
from backend.db.models.prediction import Prediction
from backend.db.models.model import Model
import requests
import time

db = SessionLocal()

try:
    # 1. 기존 모델 삭제
    model = db.query(Model).filter(Model.name.like('%gpt-5-mini%')).first()

    if model:
        # 예측 데이터 삭제
        pred_count = db.query(Prediction).filter(
            Prediction.model_id == model.id
        ).delete()
        db.commit()

        # 모델 삭제
        db.delete(model)
        db.commit()
        print(f"🗑️  모델 삭제 완료: {pred_count}건 예측 포함")

    time.sleep(1)

    # 2. reasoning 타입으로 재등록
    response = requests.post(
        'http://127.0.0.1:8000/api/models',
        json={
            "name": "gpt-5-mini",
            "provider": "openrouter",
            "model_identifier": "openai/gpt-5-mini",
            "model_type": "reasoning",  # ✅ reasoning 타입
            "description": "OpenAI GPT-5 Mini (Reasoning Model)"
        }
    )

    if response.status_code in [200, 201]:
        print("✅ 모델 등록 완료")
    else:
        print(f"❌ 등록 실패: {response.status_code}")

finally:
    db.close()
```

---

## 테스트 결과

### 1. 모델 등록 테스트

```bash
✅ 모델 추가 완료: gpt-5-mini (ID: 15)
🔄 Predictor 모델 목록 재로드 완료
🔄 백그라운드 예측 생성 시작: model=gpt-5-mini, total=20, scheduled=20
```

### 2. 예측 생성 테스트

**뉴스 ID 6797**에 대해 4개 모델 모두 예측 완료:

| 모델 | ID | 타입 | 상태 | sentiment_score | impact_level |
|------|----|----|------|-----------------|--------------|
| gpt-5-mini | 15 | reasoning | ✅ | 0.35 | medium |
| Qwen3 Max | 5 | normal | ✅ | 0.65 | medium |
| DeepSeek V3.2 | 2 | normal | ✅ | 0.65 | medium |
| GPT-4o | 1 | normal | ✅ | 0.60 | medium |

### 3. Reasoning 모델 데이터 검증

```python
# gpt-5-mini (reasoning) 예측 결과
{
    "id": 7582,
    "model_id": 15,
    "sentiment_direction": "positive",
    "sentiment_score": 0.35,
    "impact_level": "medium",
    "relevance_score": 0.6,
    "urgency_level": "notable",
    "reasoning": "한화자산운용의 TDF 2040·2045 빈티지 수익률 1위 발표는...",  # 501 chars
    "impact_analysis": {
        "business_impact": "자산운용 부문에 직접적 긍정...",
        "market_sentiment_impact": "투자심리 개선 효과는...",
        "competitive_impact": "TDF 시장 내 순위·브랜드...",
        "regulatory_impact": "규제·정책 측면의 즉각적 변화 없음..."
    },
    "pattern_analysis": {
        "note": "유사 시장 동향 데이터 없음",
        "avg_1d": null,
        "avg_3d": null,
        ...
    }
}
```

✅ **모든 필드가 정상적으로 저장됨**

### 4. API 응답 구조 확인

```python
# Reasoning 모델 응답 (로그 발췌)
ChatCompletionMessage(
    content='{\n  "sentiment_direction": "positive",\n  "sentiment_score": 0.35, ...}',
    reasoning='**Analyzing market impact**\n\nI notice the market info...',
    reasoning_details=[
        {
            'format': 'openai-responses-v1',
            'index': 0,
            'type': 'reasoning.summary',
            'summary': '...'
        },
        {
            'id': 'rs_...',
            'format': 'openai-responses-v1',
            'type': 'reasoning.encrypted',
            'data': 'gAAAAABp...'
        }
    ]
)
```

✅ **reasoning 필드 및 reasoning_details 정상 수신**

---

## 사용 방법

### 1. 새 Reasoning 모델 등록

#### API를 통한 등록
```bash
curl -X POST http://localhost:8000/api/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "o1-preview",
    "provider": "openai",
    "model_identifier": "o1-preview",
    "model_type": "reasoning",
    "description": "OpenAI o1 Preview (Reasoning Model)"
  }'
```

#### Python 스크립트로 등록
```python
import requests

response = requests.post(
    'http://127.0.0.1:8000/api/models',
    json={
        "name": "o1-preview",
        "provider": "openai",
        "model_identifier": "o1-preview",
        "model_type": "reasoning",
        "description": "OpenAI o1 Preview"
    }
)

print(response.json())
```

### 2. 기존 모델 타입 변경

```bash
curl -X PUT http://localhost:8000/api/models/15 \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "reasoning"
  }'
```

### 3. 백엔드 재시작 (필수!)

모델 등록 후 반드시 백엔드를 재시작해야 Predictor가 새 모델을 인식합니다:

```bash
pm2 restart azak-backend
```

### 4. 예측 생성 확인

```bash
# 로그 확인
pm2 logs azak-backend --lines 100

# 예측 데이터 조회
curl http://localhost:8000/api/predictions?news_id=6797
```

---

## 참고 사항

### 1. Reasoning 모델 목록

현재 지원 가능한 reasoning 모델:

| 모델명 | Provider | Model Identifier | 특징 |
|--------|----------|-----------------|------|
| gpt-5-mini | openrouter | openai/gpt-5-mini | GPT-5 Mini (경량 추론) |
| o1-preview | openai | o1-preview | OpenAI o1 Preview |
| o1-mini | openai | o1-mini | OpenAI o1 Mini |
| o3-mini | openai | o3-mini | OpenAI o3 Mini |

### 2. Reasoning vs Normal 모델 차이

| 구분 | Normal 모델 | Reasoning 모델 |
|------|------------|---------------|
| **response_format** | ✅ 지원 (`{"type": "json_object"}`) | ❌ 미지원 (오류 발생) |
| **max_tokens** | 1000 (충분) | 4000 (Chain of Thought 필요) |
| **응답 필드** | `content`만 사용 | `content` + `reasoning` + `reasoning_details` |
| **JSON 추출** | 직접 반환 | Chain of Thought에서 추출 필요 |
| **비용** | 상대적으로 저렴 | 상대적으로 비쌈 (토큰 많이 사용) |

### 3. 주의 사항

#### ⚠️ 백엔드 재시작 필수
- 모델 등록/수정 후 **반드시** 백엔드 재시작 필요
- Predictor는 초기화 시점에만 모델 목록 로드

#### ⚠️ 토큰 비용 증가
- Reasoning 모델은 4000 토큰까지 사용 (일반 모델의 4배)
- Chain of Thought 생성으로 추가 비용 발생
- 비용 모니터링 권장

#### ⚠️ 응답 시간 증가
- Reasoning 모델은 추론 과정이 길어 응답 시간 증가
- 평균 응답 시간: normal 3~5초, reasoning 10~20초

### 4. 트러블슈팅

#### 문제: "model_type 컬럼 없음" 오류
```bash
# 마이그레이션 스크립트 실행
uv run python /tmp/add_model_type_column.py
```

#### 문제: Reasoning 모델 예측 실패
```bash
# 1. 백엔드 재시작
pm2 restart azak-backend

# 2. 모델 목록 확인
curl http://localhost:8000/api/models

# 3. 로그 확인
pm2 logs azak-backend --lines 50
```

#### 문제: JSON 파싱 실패
- **원인**: max_tokens 부족으로 응답 잘림
- **해결**: 코드에서 이미 4000 토큰으로 설정됨 (확인 필요)

---

## 관련 파일

### 수정된 파일
- `backend/db/models/model.py` - Model 클래스에 model_type 컬럼 추가
- `backend/api/models.py` - API 스키마에 model_type 필드 추가
- `backend/llm/predictor.py` - Predictor 로직에 reasoning 모델 처리 추가

### 마이그레이션 스크립트
- `/tmp/add_model_type_column.py` - DB 마이그레이션
- `/tmp/register_gpt5mini_reasoning.py` - gpt-5-mini 재등록 스크립트

### 테스트 데이터
- 뉴스 ID: 6797
- 예측 ID: 7579 (GPT-4o), 7580 (DeepSeek), 7581 (Qwen3), 7582 (gpt-5-mini)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-21 | 1.0.0 | Reasoning 모델 지원 추가 (model_type enum, API 분기, 토큰 증가) |

---

**작성일**: 2025-11-21
**최종 수정일**: 2025-11-21
**작성자**: Development Team
