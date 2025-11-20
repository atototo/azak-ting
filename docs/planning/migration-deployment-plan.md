# DB 마이그레이션 배포 계획

**작성일**: 2025-11-17
**대상 마이그레이션**: US-001 - 재무비율 및 상품정보 테이블 추가

---

## 📋 배포 체크리스트

### 배포 전 (Pre-deployment)

- [ ] 배포 시간 공지 (서비스 점검 필요 시)
- [ ] DB 백업 실행: `bash scripts/backup_db.sh`
- [ ] 백업 파일 생성 확인: `ls -lh data/backups/`
- [ ] 마이그레이션 파일 검토 완료
- [ ] 롤백 스크립트 동작 확인 완료

### 배포 (Deployment)

**실행 순서:**

```bash
# 1. product_info 테이블 생성
uv run python backend/db/migrations/add_product_info_table.py

# 2. financial_ratios 테이블 생성
uv run python backend/db/migrations/add_financial_ratios_table.py

# 3. priority 컬럼 deprecated 처리
uv run python backend/db/migrations/deprecate_priority_column.py
```

### 배포 후 검증 (Post-deployment Validation)

```bash
# 테이블 생성 확인
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt product_info"
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt financial_ratios"

# 인덱스 확인
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "\d product_info"
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "\d financial_ratios"

# priority 값 확인
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT DISTINCT priority FROM stocks;"
```

- [ ] 테이블 생성 확인
- [ ] 인덱스 생성 확인
- [ ] Foreign Key 제약조건 확인
- [ ] UNIQUE 제약조건 테스트
- [ ] priority 값이 모두 1인지 확인
- [ ] 애플리케이션 정상 작동 확인
- [ ] 로그 확인 (에러 없음)

---

## 🔄 롤백 계획

### 롤백이 필요한 경우

1. 마이그레이션 실행 중 오류 발생
2. 배포 후 애플리케이션 장애 발생
3. 데이터 무결성 문제 발견

### 롤백 실행 방법

**Option 1: 마이그레이션 스크립트로 롤백**

```bash
# 역순으로 실행
uv run python -c "from backend.db.migrations.deprecate_priority_column import downgrade; downgrade()"
uv run python -c "from backend.db.migrations.add_financial_ratios_table import downgrade; downgrade()"
uv run python -c "from backend.db.migrations.add_product_info_table import downgrade; downgrade()"
```

**Option 2: 백업에서 복원**

```bash
# 백업 파일 압축 해제
gunzip data/backups/azak_backup_YYYYMMDD_HHMMSS.sql.gz

# DB 복원
PGPASSWORD=$POSTGRES_PASSWORD psql \
    -h ${POSTGRES_HOST:-localhost} \
    -p ${POSTGRES_PORT:-5432} \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    -f data/backups/azak_backup_YYYYMMDD_HHMMSS.sql
```

### 롤백 후 확인사항

- [ ] 테이블 삭제 확인
- [ ] 애플리케이션 정상 작동 확인
- [ ] 롤백 사유 문서화

---

## 📊 예상 영향도

### 다운타임

- **예상 다운타임**: 없음 (신규 테이블 추가만 수행)
- **서비스 영향**: 없음 (기존 기능에 영향 없음)

### 성능 영향

- **디스크 사용량**: 신규 테이블로 인한 소량 증가
- **쿼리 성능**: 영향 없음 (인덱스 적절히 설정됨)

### 호환성

- **기존 코드 호환성**: 100% (신규 테이블만 추가, 기존 테이블 변경 없음)
- **API 호환성**: 유지됨
- **priority 컬럼**: Deprecated이지만 컬럼 유지로 하위 호환성 보장

---

## 🔧 트러블슈팅

### 문제: Foreign Key 제약조건 오류

```
ERROR: foreign key constraint fails
```

**해결방법**: stocks 테이블에 해당 stock_code가 존재하는지 확인

```sql
SELECT code FROM stocks WHERE code = '종목코드';
```

### 문제: UNIQUE 제약조건 위반

```
ERROR: duplicate key value violates unique constraint
```

**해결방법**: 중복 데이터 확인 및 제거 후 재시도

```sql
-- product_info
SELECT stock_code, COUNT(*) FROM product_info GROUP BY stock_code HAVING COUNT(*) > 1;

-- financial_ratios
SELECT stock_code, stac_yymm, div_cls_code, COUNT(*)
FROM financial_ratios
GROUP BY stock_code, stac_yymm, div_cls_code
HAVING COUNT(*) > 1;
```

### 문제: Migration 실행 중 타임아웃

**해결방법**: DB 연결 확인, 트랜잭션 격리 수준 확인

---

## 📝 배포 기록

| 날짜 | 환경 | 실행자 | 결과 | 비고 |
|------|------|--------|------|------|
| 2025-11-17 | Development | James | ✅ 성공 | 개발 환경 테스트 완료 |
| TBD | Production | TBD | - | - |

---

## 📚 관련 문서

- [US-001 스토리](../stories/stock-analysis-redesign/US-001-db-migrations.md)
- [PRD - Phase 1](../stock-analysis-redesign-prd.md#phase-1-데이터베이스-마이그레이션-1주차)
- [백업 스크립트](../../scripts/backup_db.sh)

---

## 📞 긴급 연락처

배포 중 문제 발생 시:
1. 즉시 롤백 실행
2. 로그 수집 및 보고
3. 문제 해결 후 재배포 계획 수립
