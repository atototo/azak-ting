# Supabase 마이그레이션 - 로컬 Docker 인프라 클라우드 전환

**작업 일자**: 2025-11-23
**작업자**: young
**관련 이슈**: #6
**Pull Request**: (작업 후 업데이트 예정)

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

로컬 Docker 환경(PostgreSQL + Redis)을 Supabase 클라우드로 마이그레이션하여 인프라 관리 부담을 감소시키고, 데이터 증가에 대비한 보관 정책을 수립합니다.

**핵심 변경사항**:
- PostgreSQL (Docker) → Supabase (클라우드)
- Redis 캐시 → PostgreSQL 테이블로 통합
- 1분봉 데이터 30일 보관 정책 도입
- FAISS 로컬 유지 + Supabase Storage 백업

**예상 효과**:
- 완전 무료 운영 ($0/월)
- 인프라 관리 포인트 최소화
- 자동 백업 및 데이터 안정성 향상
- 월간 데이터 증가량: 133MB → 38MB로 감소

---

## AS-IS (기존 상태)

### 문제점

**1. 현재 인프라 구성**

#### PostgreSQL (Docker)
- **DB 크기**: 71 MB
- **주요 테이블**:
  - `stock_prices_minute`: 25 MB (104,715건) - 35%
  - `predictions`: 7 MB (3,350건)
  - `news_articles`: 4.5 MB (7,051건)
  - 기타 19개 테이블: 26.8 MB
- **총 테이블 수**: 23개

#### Redis (Docker)
- **메모리 사용량**: 1.19 MB
- **키 개수**: 2개
- **일일 명령어**: ~72,000 commands/day
- **용도**:
  - 예측 결과 캐싱 (24시간 TTL)
  - KIS API 토큰 관리
  - ~~세션 관리~~ (JWT 사용으로 불필요)

#### FAISS (로컬 파일)
- **크기**: 21 MB
- **벡터 수**: 7,040개
- **저장 방식**: 로컬 파일 시스템

**2. 데이터 증가 추이**

| 구분 | 일일 증가량 | 월간 증가량 |
|------|------------|------------|
| 뉴스 | 423건/일 | ~8.2 MB/월 |
| 예측 | 481건/일 | ~30 MB/월 |
| 1분봉 | 19,800건/일 | **~95 MB/월** 🔥 |
| **총합** | - | **~133 MB/월** |

**3. 용량 예측**

```
현재:     71 MB
1개월:   204 MB
2개월:   337 MB
3개월:   470 MB
4개월:   603 MB ← Supabase 무료 티어 초과 (500MB)
```

### 에러 로그

현재 에러는 없으나, 데이터 증가로 인한 용량 한계 도달이 예상됨.

### 영향도

| 항목 | 내용 |
|------|------|
| **심각도** | Medium (3개월 여유) |
| **영향 범위** | 전체 시스템 (DB, 캐시, 백업) |
| **발생 빈도** | 지속적 (매일 데이터 증가) |
| **영향받는 사용자** | 시스템 관리자 (인프라 관리 부담) |

---

## 변경 필요 사유

### 1. 인프라 관리 부담

**현재 문제점**:
- 로컬 Docker 컨테이너 관리 필요
- 백업 수동 관리
- 서버 재시작 시 컨테이너 재기동 필요
- 확장성 제약

**개선 필요성**:
- 클라우드 마이그레이션으로 관리 자동화
- Supabase의 자동 백업 활용
- 서비스 안정성 향상

### 2. 용량 증가 대응

**문제점**:
- 1분봉 데이터가 월 95MB씩 무한 증가
- 3-4개월 후 Supabase 무료 티어(500MB) 초과
- 유료 전환 시 비용 발생

**해결책**:
- 1분봉 데이터 30일 보관 정책 도입
- 일봉 데이터는 별도 테이블에 영구 보관
- 월간 증가량: 133MB → 38MB로 감소

### 3. 비용 최적화

**현재 상황**:
- 로컬 Docker: 무료 (하지만 관리 필요)
- 잠재적 비용: Redis 클라우드 사용 시 $5/월

**목표**:
- Redis 제거하고 PostgreSQL로 통합
- 완전 무료 운영 유지 ($0/월)

---

## TO-BE (변경 후 상태)

### 핵심 개선사항

**1. PostgreSQL → Supabase 마이그레이션**
- 모든 테이블 및 데이터 완전 이전
- 스키마 동일하게 유지
- 연결 URL만 변경

**2. Redis 제거 및 PostgreSQL 통합**

새로운 테이블 추가:

```sql
-- 예측 캐시 테이블
CREATE TABLE prediction_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_prediction_cache_expires ON prediction_cache(expires_at);

-- KIS 토큰 테이블
CREATE TABLE kis_tokens (
    id SERIAL PRIMARY KEY,
    token_type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**3. 1분봉 보관 정책**

```python
def _cleanup_old_minute_data(self):
    """30일 이상 된 1분봉 데이터 삭제"""
    db.execute("""
        DELETE FROM stock_prices_minute
        WHERE datetime < NOW() - INTERVAL '30 days'
    """)
```

- 매월 1일 새벽 3시 자동 실행
- 일봉 데이터는 영구 보관 (별도 테이블)

**4. FAISS 백업**
- 서버 로컬 파일 유지
- Supabase Storage에 백업
- 서버 재시작 시 자동 복원

### Before/After 비교

| 항목 | 이전 (AS-IS) | 이후 (TO-BE) | 변화 |
|------|-------------|------------|------|
| **PostgreSQL** | Docker (로컬) | Supabase (클라우드) | ✅ 관리 자동화 |
| **Redis** | Docker (1.19MB) | 제거 → PostgreSQL 통합 | ✅ 인프라 단순화 |
| **FAISS** | 로컬만 | 로컬 + Supabase Storage | ✅ 백업 추가 |
| **월간 증가량** | 133MB | 38MB | ✅ 71% 감소 |
| **관리 포인트** | 3개 (DB, Redis, FAISS) | 1개 (Supabase) | ✅ 67% 감소 |
| **비용** | $0 | $0 | ✅ 무료 유지 |
| **백업** | 수동 | 자동 | ✅ 안정성 향상 |

---

## 변경 사항 상세

### 1. 주요 파일 변경

(작업 후 업데이트 예정)

### 2. 코드 비교

(작업 후 업데이트 예정)

### 3. 아키텍처 변경

**AS-IS 아키텍처**:
```
Backend API
    ↓
PostgreSQL (Docker)  Redis (Docker)  FAISS (로컬)
    ↓                    ↓               ↓
로컬 디스크         로컬 메모리      로컬 파일
```

**TO-BE 아키텍처**:
```
Backend API
    ↓
Supabase PostgreSQL (클라우드)  FAISS (로컬)
    ↓                              ↓
- 기존 테이블 (23개)          로컬 파일
- prediction_cache (신규)          ↓
- kis_tokens (신규)        Supabase Storage (백업)
```

---

## 테스트 결과

(작업 후 업데이트 예정)

### 1. 자동 테스트

(작업 후 업데이트 예정)

### 2. 수동 테스트

(작업 후 업데이트 예정)

### 3. 검증 항목

- [ ] 모든 데이터 마이그레이션 완료 (23개 테이블, 모든 레코드)
- [ ] 예측 캐시 기능 정상 동작
- [ ] KIS API 토큰 관리 정상 동작
- [ ] 뉴스/주가 데이터 조회 정상
- [ ] 예측 결과 저장/조회 정상
- [ ] 1분봉 보관 정책 스케줄러 동작 확인
- [ ] FAISS 백업/복원 테스트

---

## 사용 방법

(작업 후 업데이트 예정)

### 1. 로컬 환경 적용

(작업 후 업데이트 예정)

### 2. 기능 사용법

(작업 후 업데이트 예정)

### 3. 예제

(작업 후 업데이트 예정)

---

## 참고 사항

### 1. 변경 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| PostgreSQL | Docker (로컬) | Supabase (클라우드) |
| Redis | Docker (1.19MB, 2 keys) | 제거 (PostgreSQL 통합) |
| FAISS | 로컬 파일 | 로컬 + Supabase Storage 백업 |
| 1분봉 보관 | 무제한 | 30일 |
| 월간 증가량 | 133MB | 38MB |
| 비용 | $0 | $0 |

### 2. 주의 사항

**마이그레이션 중**:
- 서비스 다운타임 발생 가능
- 데이터 백업 필수
- 롤백 계획 수립 필요

**성능 관련**:
- Redis → PostgreSQL 캐시 전환으로 약간의 성능 저하 가능
- 하지만 현재 사용량(72K commands/day)에서는 영향 미미

**데이터 보관 정책**:
- 1분봉 데이터는 30일 후 자동 삭제됨
- 필요 시 일봉 데이터로 변환 후 영구 보관 필요

### 3. 트러블슈팅

**문제: Supabase 연결 실패**
- 해결: 연결 URL 및 환경 변수 확인
- 확인: `.env` 파일의 `DATABASE_URL` 설정

**문제: 캐시 미스율 증가**
- 원인: Redis → PostgreSQL 전환으로 인한 성능 차이
- 해결: `prediction_cache` 테이블 인덱스 최적화

**문제: KIS API 토큰 갱신 실패**
- 해결: `kis_tokens` 테이블 로직 검증
- 확인: 토큰 만료 시간 및 갱신 주기

### 4. 관련 파일

**변경 예정 파일**:
- `backend/llm/prediction_cache.py` - 캐시 로직
- `backend/crawlers/kis_client.py` - 토큰 관리
- `.env` - DB 연결 설정
- `backend/config/database.py` - DB 설정
- `backend/schedulers/` - 1분봉 cleanup 스케줄러 추가

**신규 생성 파일**:
- `migrations/supabase_migration.sql` - 마이그레이션 스크립트
- `scripts/backup_faiss_to_supabase.py` - FAISS 백업 스크립트

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-11-23 | 1.0 | 문서 초안 작성 (AS-IS 분석 완료) |

---

**작성일**: 2025-11-23
**최종 수정일**: 2025-11-23
**작성자**: young
