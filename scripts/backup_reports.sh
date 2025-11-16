#!/bin/bash
#
# 리포트 테이블 백업 스크립트
#
# 사용법:
#   ./scripts/backup_reports.sh [백업파일명]
#
# 예시:
#   ./scripts/backup_reports.sh reports_backup_20251116

set -e  # 에러 발생 시 즉시 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정
CONTAINER_NAME="craveny-postgres"
DB_NAME="craveny"
DB_USER="postgres"
BACKUP_DIR="./data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 백업 파일명 (인자로 받거나 기본값 사용)
BACKUP_NAME="${1:-reports_backup_${TIMESTAMP}}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}리포트 테이블 백업 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# Docker 컨테이너 확인
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ PostgreSQL 컨테이너를 찾을 수 없습니다: ${CONTAINER_NAME}${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 컨테이너: ${CONTAINER_NAME}${NC}"
echo -e "${YELLOW}🗄️  데이터베이스: ${DB_NAME}${NC}"
echo -e "${YELLOW}💾 백업 파일: ${BACKUP_FILE}${NC}"
echo ""

# 백업 전 현황 확인
echo -e "${YELLOW}📊 백업 전 데이터 현황:${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\
    SELECT
        COUNT(*) as total_reports,
        COUNT(CASE WHEN model_id IS NULL THEN 1 END) as legacy_reports,
        COUNT(CASE WHEN model_id IS NOT NULL THEN 1 END) as new_reports
    FROM stock_analysis_summaries;"

echo ""

# 테이블 백업 실행
echo -e "${YELLOW}⏳ 백업 중...${NC}"
docker exec $CONTAINER_NAME pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    --table=stock_analysis_summaries \
    --clean \
    --if-exists \
    --create \
    > "$BACKUP_FILE"

# 백업 성공 확인
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ 백업 완료!${NC}"
    echo -e "${GREEN}   파일: ${BACKUP_FILE}${NC}"
    echo -e "${GREEN}   크기: ${BACKUP_SIZE}${NC}"

    # 압축 (선택사항)
    echo ""
    read -p "백업 파일을 압축하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⏳ 압축 중...${NC}"
        gzip "$BACKUP_FILE"
        COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
        echo -e "${GREEN}✅ 압축 완료: ${BACKUP_FILE}.gz (${COMPRESSED_SIZE})${NC}"
    fi
else
    echo -e "${RED}❌ 백업 실패${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}백업 완료${NC}"
echo -e "${GREEN}========================================${NC}"
