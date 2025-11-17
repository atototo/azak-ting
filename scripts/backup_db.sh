#!/bin/bash
# DB 백업 스크립트
# Usage: ./scripts/backup_db.sh

set -e

# 설정
BACKUP_DIR="data/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/craveny_backup_${TIMESTAMP}.sql"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# .env 파일에서 DB 설정 읽기
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# PostgreSQL 백업 실행
echo "🔄 Starting database backup..."
echo "Database: $POSTGRES_DB"
echo "Backup file: $BACKUP_FILE"

PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
    -h ${POSTGRES_HOST:-localhost} \
    -p ${POSTGRES_PORT:-5432} \
    -U $POSTGRES_USER \
    -d $POSTGRES_DB \
    -F p \
    -f "$BACKUP_FILE"

# 백업 파일 압축
echo "📦 Compressing backup..."
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_FILE"
echo "📊 Backup size: $(du -h $BACKUP_FILE | cut -f1)"

# 7일 이상 된 백업 파일 삭제
echo "🧹 Cleaning up old backups (older than 7 days)..."
find "$BACKUP_DIR" -name "craveny_backup_*.sql.gz" -type f -mtime +7 -delete
echo "✅ Cleanup completed!"

# 백업 파일 목록 표시
echo ""
echo "📋 Recent backups:"
ls -lh "$BACKUP_DIR"/craveny_backup_*.sql.gz 2>/dev/null | tail -5 || echo "No backups found"
