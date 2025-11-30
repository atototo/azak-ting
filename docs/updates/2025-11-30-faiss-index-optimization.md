# FAISS 인덱스 최적화: IndexIVFFlat + Inner Product

**작업 일자**: 2025-11-30
**작업자**: young
**관련 이슈**: #19
**커밋**: a672d97

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

FAISS 벡터 검색 인덱스를 브루트포스 방식(`IndexFlatL2`)에서 클러스터 기반 방식(`IndexIVFFlat + Inner Product`)으로 최적화하여 검색 성능을 개선했습니다.

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 인덱스 타입 | `IndexFlatL2` | `IndexIVFFlat + IP` |
| 검색 복잡도 | O(N) | O(√N) |
| 유사도 계산 | `1/(1+L2)` 근사 | Inner Product (정확) |
| 벡터 수 | 10,140개 | 10,140개 |

---

## AS-IS (기존 상태)

### 문제점

1. **브루트포스 검색**: 모든 벡터와 비교하여 유사도 계산
   - 10,000개 벡터 → 10,000번 비교 필요
   - 데이터 증가 시 선형적 성능 저하

2. **부정확한 유사도 계산**: L2 distance를 cosine similarity로 근사 변환
   ```python
   # 기존 방식 - 근사치
   similarity = 1 / (1 + L2_distance)
   ```

3. **확장성 한계**: 100,000건 이상 시 심각한 성능 저하 예상

### 관련 코드

```python
# backend/llm/vector_search.py:86
self._index = faiss.IndexFlatL2(settings.EMBEDDING_DIM)
```

### 영향도

| 항목 | 내용 |
|------|------|
| **심각도** | Medium |
| **영향 범위** | 벡터 검색 API, 뉴스 유사도 분석 |
| **발생 빈도** | 모든 검색 요청 |
| **영향받는 사용자** | 전체 |

---

## 변경 필요 사유

### 1. 데이터 규모 증가

- 현재 벡터 수: **10,140개** (이미 10,000건 초과)
- 일일 뉴스 수집량: ~100건
- 예상 증가: 월 3,000건 → 연말 50,000건 예상

### 2. 성능 최적화 필요

FAISS 공식 가이드라인에 따른 인덱스 선택:

| 데이터 규모 | 권장 인덱스 | 특징 |
|------------|-----------|------|
| ~10,000건 | `IndexFlatL2` | 현재 (OK) |
| 10,000~100,000건 | `IndexIVFFlat` | 클러스터 기반, 빠름 |
| 100,000건+ | `IndexHNSWFlat` | 그래프 기반, 매우 빠름 |

### 3. 정확도 개선

- Inner Product 사용 시 정규화된 벡터는 정확한 Cosine Similarity
- 현재 임베딩 모델(KoSimCSE)은 이미 L2 정규화된 벡터 출력

---

## TO-BE (변경 후 상태)

### 핵심 개선사항

1. **IndexIVFFlat 적용**: 클러스터 기반 검색
   - 100개 클러스터로 데이터 분할
   - nprobe=10으로 상위 10개 클러스터만 검색
   - 실제 비교 대상: ~1,000개 (10% 수준)

2. **Inner Product 사용**: 정확한 cosine similarity
   ```python
   # 변경 후 - 정확한 값
   similarity = float(inner_product)  # 바로 cosine similarity
   ```

3. **자동 인덱스 감지**: 기존 L2 인덱스와 새 IVF 인덱스 모두 지원

### Before/After 비교

| 항목 | 이전 (AS-IS) | 이후 (TO-BE) | 변화 |
|------|-------------|------------|------|
| 인덱스 타입 | IndexFlatL2 | IndexIVFFlat+IP | 클러스터 기반 |
| 검색 시간 | O(N) | O(√N) | ~90% 감소 |
| 유사도 정확도 | 근사치 | 정확 | 개선 |
| 메모리 | 동일 | 약간 증가 | 클러스터 정보 |

---

## 변경 사항 상세

### 1. 주요 파일 변경

| 파일 | 변경 내용 |
|------|----------|
| `backend/llm/vector_search.py` | IVF 인덱스 지원, 유사도 계산 개선 |
| `scripts/migrate_faiss_index.py` | 마이그레이션 스크립트 신규 |

### 2. 코드 비교

#### 변경 파일: `backend/llm/vector_search.py`

**Before (AS-IS)**:
```python
class NewsVectorSearch:
    # 기존: 단순 초기화
    def __init__(self):
        self._index: Optional[faiss.Index] = None

    # 기존: FlatL2만 지원
    def _create_empty_index(self):
        return faiss.IndexFlatL2(settings.EMBEDDING_DIM)

    # 기존: 근사 유사도
    similarity = 1 / (1 + dist)
```

**After (TO-BE)**:
```python
class NewsVectorSearch:
    # IVF 설정 추가
    IVF_NLIST = 100   # 클러스터 수
    IVF_NPROBE = 10   # 검색 시 탐색할 클러스터 수

    def __init__(self):
        self._index: Optional[faiss.Index] = None
        self._is_ivf: bool = False  # IVF 인덱스 여부

    # Inner Product 인덱스 생성
    def _create_empty_index(self):
        return faiss.IndexFlatIP(settings.EMBEDDING_DIM)

    # IVF 인덱스 감지
    def _is_index_ivf(self, index):
        try:
            _ = index.nprobe
            return True
        except AttributeError:
            return False

    # 정확한 유사도 계산
    if self._is_ivf:
        similarity = float(dist)  # IP = cosine similarity
    else:
        similarity = 1 / (1 + dist)  # L2 호환성
```

**변경 이유**:
- 10,000건 이상 데이터에서 성능 저하 방지
- 정확한 cosine similarity 계산
- 기존 인덱스와의 호환성 유지

#### 신규 파일: `scripts/migrate_faiss_index.py`

마이그레이션 스크립트 주요 기능:

```python
def migrate_index():
    # 1. 기존 인덱스에서 벡터 추출
    vectors = extract_vectors(old_index)

    # 2. L2 정규화
    vectors_normalized = normalize_vectors(vectors)

    # 3. IVF 인덱스 생성 및 학습
    quantizer = faiss.IndexFlatIP(dim)
    new_index = faiss.IndexIVFFlat(quantizer, dim, nlist)
    new_index.train(vectors_normalized)

    # 4. 벡터 추가 및 저장
    new_index.add(vectors_normalized)
    faiss.write_index(new_index, index_path)
```

---

## 테스트 결과

### 1. 마이그레이션 검증

```
📊 기존 인덱스 정보:
   - 벡터 수: 10,140개
   - 타입: FlatL2 (마이그레이션 필요)

🏗️  IVF 인덱스 생성 중...
   - 클러스터 수: 100

📚 인덱스 학습 중...
   - 학습 완료 (is_trained=True)

✅ 검증:
   - 벡터 수: 10,140개
   - IVF 인덱스: True

🔍 검색 테스트:
   - 상위 5개 결과: indices=[0, 4328, 449, 984, 5616]
   - 유사도: [1.0, 0.5834, 0.5712, 0.5519, 0.5495]
```

### 2. 서버 로드 테스트

```
2025-11-30 14:21:05 - INFO - 📊 IVF 인덱스 로드됨 (nprobe=10)
2025-11-30 14:21:05 - INFO - ✅ FAISS 인덱스 로드 완료: 10140개 벡터 (IVFFlat+IP)
```

### 3. 검증 항목

- [x] 기존 벡터 수 보존 (10,140개)
- [x] IVF 인덱스 정상 로드
- [x] nprobe 설정 적용 (10)
- [x] 검색 결과 유사도 범위 정상 (0.0~1.0)
- [x] 기존 L2 인덱스 호환성 유지

---

## 사용 방법

### 1. 마이그레이션 실행

기존 L2 인덱스를 IVF 인덱스로 변환:

```bash
cd /Users/young/ai-work/craveny

# PM2 서비스 중지
pm2 stop azak-api azak-scheduler

# 마이그레이션 실행
.venv/bin/python scripts/migrate_faiss_index.py

# PM2 서비스 재시작
pm2 start azak-api azak-scheduler
```

### 2. 롤백 방법

마이그레이션 실패 시 백업에서 복구:

```bash
# 백업 파일 확인
ls data/faiss/backup_*.index

# 복구
cp data/faiss/backup_20251130_141553.index data/faiss/news_embeddings.index
```

### 3. 설정 조정

성능과 정확도 균형 조정:

```python
# backend/llm/vector_search.py
class NewsVectorSearch:
    IVF_NLIST = 100   # 클러스터 수 (↑ 정확도, ↓ 속도)
    IVF_NPROBE = 10   # 탐색 클러스터 (↑ 정확도, ↓ 속도)
```

---

## 참고 사항

### 1. 변경 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 인덱스 타입 | IndexFlatL2 | IndexIVFFlat+IP |
| 검색 복잡도 | O(N) | O(√N) |
| 클러스터 수 | - | 100 |
| nprobe | - | 10 |
| 유사도 계산 | 근사치 | 정확 |

### 2. 주의 사항

1. **IVF 인덱스는 학습 필요**: 새로운 인덱스 생성 시 `train()` 호출 필수
2. **최소 벡터 수**: IVF 학습에 최소 1,000개 벡터 권장
3. **백업 보관**: 마이그레이션 전 자동 백업 생성됨

### 3. 향후 계획

- 100,000건 도달 시 `IndexHNSWFlat` 검토
- GPU 가속 (`faiss-gpu`) 도입 검토

### 4. 관련 파일

| 파일 | 역할 |
|------|------|
| `backend/llm/vector_search.py` | 벡터 검색 클래스 |
| `backend/config.py` | FAISS 설정 (경로, 차원) |
| `scripts/migrate_faiss_index.py` | 마이그레이션 스크립트 |
| `data/faiss/news_embeddings.index` | FAISS 인덱스 파일 |
| `data/faiss/news_metadata.pkl` | 메타데이터 파일 |

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-30 | 1.0.0 | IndexIVFFlat + Inner Product 마이그레이션 |

---

**작성일**: 2025-11-30
**최종 수정일**: 2025-11-30
**작성자**: young
