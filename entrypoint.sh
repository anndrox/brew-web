#!/bin/sh
set -eu

db_host="${POSTGRES_HOST:-db}"
db_user="${POSTGRES_USER:-brewuser}"
db_name="${POSTGRES_DB:-brewweb}"
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
export PGCONNECT_TIMEOUT=5
wait_seconds="${DB_WAIT_TIMEOUT:-60}"
case "$wait_seconds" in ''|*[!0-9]*|0) printf '%s\n' 'DB_WAIT_TIMEOUT must be a positive integer.' >&2; exit 1;; esac
deadline=$(( $(date +%s) + wait_seconds ))

printf '%s\n' 'Waiting for PostgreSQL...'
until psql -h "$db_host" -U "$db_user" -d "$db_name" -tAc 'SELECT 1' >/dev/null 2>&1; do
  if [ "$(date +%s)" -ge "$deadline" ]; then
    printf '%s\n' 'PostgreSQL connection timed out. Check hostname and existing database credentials; no data was modified.' >&2
    exit 1
  fi
  sleep 1
done

printf '%s\n' 'Validating database compatibility...'
flask prepare-schema

printf '%s\n' 'Applying database migrations...'
flask db upgrade

printf '%s\n' 'Seeding default yeast data...'
flask seed-yeasts

exec gunicorn \
  --workers "${GUNICORN_WORKERS:-1}" \
  --bind 0.0.0.0:4452 \
  --no-control-socket \
  --access-logfile - \
  --error-logfile - \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  wsgi:app
