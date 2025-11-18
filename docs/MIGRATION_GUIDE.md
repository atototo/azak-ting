# 리포트 마이그레이션 가이드

## 개요

레거시 리포트 시스템을 모델별 리포트 시스템으로 마이그레이션하는 가이드입니다.

- **작성일**: 2025-11-16
- **상태**: ✅ 완료 (2025-11-16 22:44)

---

## 마이그레이션 결과

### 완료된 작업

1. ✅ **코드 구현 완료**
   - 모든 활성 모델에 대해 리포트 생성 (`stock_analysis_service.py:188-252`)
   - A/B 테스트 설정에 맞춰 모델별 최신 조회 (`stock_analysis_service.py:260-338`)
   - 뉴스 저장 시 리포트 생성 로직 제거 (`news_saver.py:250-253`)

2. ✅ **데이터 마이그레이션 완료**
   - 42개 레거시 리포트 → 84개 모델별 리포트
   - Model A (Qwen3 Max, ID=5): 42개
   - Model B (DeepSeek V3.2, ID=2): 42개
   - 성공률: 100%

3. ✅ **성능 최적화 완료**
   - 3개 인덱스 추가
   - 백업 파일 생성 (284K)

---

## 스크립트 사용법

### 1. 백업 스크립트

```bash
# 기본 백업 (자동으로 타임스탬프 추가)
./scripts/backup_reports.sh

# 커스텀 백업 파일명
./scripts/backup_reports.sh my_backup_name

# 백업 후 압축 여부 선택 가능
```

**생성되는 파일**:
- `./data/backups/[백업명].sql`
- `./data/backups/[백업명].sql.gz` (압축 선택 시)

### 2. 마이그레이션 스크립트

```bash
# Dry-run (실제 변경 없이 테스트)
source .venv/bin/activate
python scripts/migrate_legacy_reports.py --dry-run --verbose

# 실제 마이그레이션
source .venv/bin/activate
python scripts/migrate_legacy_reports.py --verbose
```

**옵션**:
- `--dry-run`: 실제 변경 없이 시뮬레이션만 수행
- `--verbose`: 상세 로그 출력

### 3. 복구 스크립트

```bash
# 백업에서 복구
./scripts/restore_reports.sh data/backups/migration_before_20251116.sql

# 압축된 백업에서 복구
./scripts/restore_reports.sh data/backups/migration_before_20251116.sql.gz
```

---

## 마이그레이션 절차 (상세)

### 사전 준비

1. **스케줄러 중지**
   ```bash
   # 스케줄러 프로세스 확인
   ps aux | grep scheduler

   # 중지 (필요한 경우)
   docker-compose stop scheduler
   ```

2. **DB 백업**
   ```bash
   ./scripts/backup_reports.sh migration_before_$(date +%Y%m%d)
   ```

3. **현재 데이터 상태 확인**
   ```sql
   SELECT
       COUNT(*) as total_reports,
       COUNT(CASE WHEN model_id IS NULL THEN 1 END) as legacy_reports,
       COUNT(CASE WHEN model_id IS NOT NULL THEN 1 END) as new_reports
   FROM stock_analysis_summaries;
   ```

### 마이그레이션 실행

1. **Dry-run 테스트**
   ```bash
   source .venv/bin/activate
   python scripts/migrate_legacy_reports.py --dry-run --verbose
   ```

2. **결과 검토**
   - 변환될 리포트 개수 확인
   - 에러 메시지 확인
   - 모델별 생성 개수 확인

3. **실제 마이그레이션**
   ```bash
   python scripts/migrate_legacy_reports.py --verbose
   # 확인 프롬프트에서 'yes' 입력
   ```

4. **검증**
   ```sql
   -- 전체 현황
   SELECT
       COUNT(*) as total_reports,
       COUNT(CASE WHEN model_id IS NULL THEN 1 END) as legacy_reports,
       COUNT(CASE WHEN model_id IS NOT NULL THEN 1 END) as new_reports,
       COUNT(DISTINCT stock_code) as unique_stocks,
       COUNT(DISTINCT model_id) as unique_models
   FROM stock_analysis_summaries;

   -- 모델별 개수
   SELECT model_id, COUNT(*) as report_count
   FROM stock_analysis_summaries
   WHERE model_id IS NOT NULL
   GROUP BY model_id
   ORDER BY model_id;

   -- 샘플 데이터 확인
   SELECT stock_code, model_id, last_updated
   FROM stock_analysis_summaries
   WHERE model_id IS NOT NULL
   ORDER BY last_updated DESC
   LIMIT 10;
   ```

### 인덱스 추가

```sql
-- 모델별 최신 리포트 조회용
CREATE INDEX IF NOT EXISTS idx_summary_stock_model_updated
ON stock_analysis_summaries(stock_code, model_id, last_updated DESC);

-- 스케줄러용 (오래된 리포트 찾기)
CREATE INDEX IF NOT EXISTS idx_summary_updated_stock
ON stock_analysis_summaries(last_updated DESC, stock_code)
WHERE model_id IS NOT NULL;

-- 평가 시스템용 (목표가 있는 리포트)
CREATE INDEX IF NOT EXISTS idx_summary_evaluation
ON stock_analysis_summaries(last_updated DESC)
WHERE short_term_target_price IS NOT NULL;
```

### 사후 작업

1. **새 리포트 동작 확인**
   - 프론트엔드에서 종목 상세 페이지 확인
   - A/B 테스트 리포트 표시 확인
   - 리포트 업데이트 버튼 테스트

2. **스케줄러 재시작**
   ```bash
   docker-compose start scheduler
   ```

3. **레거시 데이터 삭제** (선택사항, 충분한 검증 후)
   ```sql
   -- 삭제 전 재확인
   SELECT COUNT(*) as will_be_deleted
   FROM stock_analysis_summaries
   WHERE model_id IS NULL;

   -- 실제 삭제
   DELETE FROM stock_analysis_summaries WHERE model_id IS NULL;
   ```

---

## 트러블슈팅

### 문제: 마이그레이션 중 에러 발생

**증상**:
```
종목 XXX 마이그레이션 실패: ...
```

**원인**:
- custom_data가 NULL이거나 형식이 잘못됨
- JSON 파싱 오류

**해결**:
```bash
# 해당 종목의 데이터 확인
docker exec azak-postgres psql -U postgres -d azak -c \
  "SELECT stock_code, custom_data FROM stock_analysis_summaries WHERE stock_code = 'XXX';"

# 스크립트는 에러가 있어도 계속 진행하므로
# 최종 통계에서 에러 개수 확인
```

### 문제: 롤백이 필요한 경우

**해결**:
```bash
# 백업에서 복구
./scripts/restore_reports.sh data/backups/migration_before_20251116.sql

# 인덱스 재생성 (필요한 경우)
docker exec azak-postgres psql -U postgres -d azak -c \
  "REINDEX TABLE stock_analysis_summaries;"
```

### 문제: 인덱스 생성 실패

**증상**:
```
ERROR: could not create unique index
```

**원인**: 중복 데이터 존재

**해결**:
```sql
-- 중복 데이터 확인
SELECT stock_code, model_id, last_updated, COUNT(*)
FROM stock_analysis_summaries
WHERE model_id IS NOT NULL
GROUP BY stock_code, model_id, last_updated
HAVING COUNT(*) > 1;

-- 중복 제거 (최신 데이터만 유지)
-- 주의: 실행 전 반드시 백업 확인
```

---

## 마이그레이션 체크리스트

### 실행 전
- [ ] DB 백업 완료
- [ ] 스케줄러 중지
- [ ] 현재 데이터 상태 기록
- [ ] Dry-run 테스트 성공
- [ ] 백업 파일 크기 확인 (정상 범위)

### 실행 중
- [ ] 마이그레이션 스크립트 성공 완료
- [ ] 에러 개수 = 0 확인
- [ ] 생성된 리포트 개수 확인

### 실행 후
- [ ] 데이터 검증 쿼리 실행
- [ ] 인덱스 생성 완료
- [ ] 프론트엔드 동작 확인
- [ ] 스케줄러 재시작
- [ ] 새 리포트 생성 확인 (스케줄러)

---

## 참고 파일

- **마이그레이션 스크립트**: `scripts/migrate_legacy_reports.py`
- **백업 스크립트**: `scripts/backup_reports.sh`
- **복구 스크립트**: `scripts/restore_reports.sh`
- **프로세스 분석 문서**: `docs/REPORT_PROCESS_ANALYSIS.md`
- **백업 디렉토리**: `./data/backups/`

---

## 마이그레이션 히스토리

### 2025-11-16 22:44 - 초기 마이그레이션
- **대상**: 42개 레거시 리포트
- **결과**: 84개 모델별 리포트 생성 (100% 성공)
- **소요 시간**: ~1초
- **백업**: `./data/backups/migration_before_20251116.sql` (284K)
- **인덱스**: 3개 추가 완료
