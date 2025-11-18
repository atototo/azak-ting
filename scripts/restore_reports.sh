#!/bin/bash
#
# 리포트 테이블 복구 스크립트
#
# 사용법:
#   ./scripts/restore_reports.sh <백업파일>
#
# 예시:
#   ./scripts/restore_reports.sh data/backups/reports_backup_20251116.sql

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 설정
CONTAINER_NAME="azak-postgres"
DB_NAME="azak"
DB_USER="postgres"

# 백업 파일 확인
if [ -z "$1" ]; then
    echo -e "${RED}❌ 백업 파일을 지정해주세요${NC}"
    echo "사용법: $0 <백업파일>"
    echo ""
    echo "사용 가능한 백업 파일:"
    ls -lh ./data/backups/reports_backup_*.sql* 2>/dev/null || echo "  (없음)"
    exit 1
fi

BACKUP_FILE="$1"

# .gz 파일인 경우 압축 해제
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${YELLOW}⏳ 압축 해제 중...${NC}"
    gunzip -k "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE%.gz}"
fi

# 파일 존재 확인
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ 백업 파일을 찾을 수 없습니다: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}리포트 테이블 복구${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}📦 컨테이너: ${CONTAINER_NAME}${NC}"
echo -e "${YELLOW}🗄️  데이터베이스: ${DB_NAME}${NC}"
echo -e "${YELLOW}📂 백업 파일: ${BACKUP_FILE}${NC}"
echo ""

# 경고
echo -e "${RED}⚠️  경고: 현재 데이터가 모두 삭제되고 백업으로 대체됩니다!${NC}"
echo ""
read -p "계속하시겠습니까? (yes/no): " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo -e "${YELLOW}복구가 취소되었습니다.${NC}"
    exit 0
fi

# 복구 전 현황
echo ""
echo -e "${YELLOW}📊 복구 전 데이터 현황:${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\
    SELECT
        COUNT(*) as total_reports,
        COUNT(CASE WHEN model_id IS NULL THEN 1 END) as legacy_reports,
        COUNT(CASE WHEN model_id IS NOT NULL THEN 1 END) as new_reports
    FROM stock_analysis_summaries;" 2>/dev/null || echo "  (테이블 없음)"

# 복구 실행
echo ""
echo -e "${YELLOW}⏳ 복구 중...${NC}"
cat "$BACKUP_FILE" | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

# 복구 후 현황
echo ""
echo -e "${YELLOW}📊 복구 후 데이터 현황:${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\
    SELECT
        COUNT(*) as total_reports,
        COUNT(CASE WHEN model_id IS NULL THEN 1 END) as legacy_reports,
        COUNT(CASE WHEN model_id IS NOT NULL THEN 1 END) as new_reports
    FROM stock_analysis_summaries;"

echo ""
echo -e "${GREEN}✅ 복구 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
