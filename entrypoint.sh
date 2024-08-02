#!/bin/sh

# 데이터베이스 파일 소유권 및 권한 설정

if [ -f /app/db_data/db.sqlite3 ]; then
  chmod 777 /app/db_data/db.sqlite3
fi

# 마이그레이션 적용
python manage.py migrate --noinput

exec "$@"
