#!/bin/sh
set -eu

db_host="${POSTGRES_HOST:-db}"
db_user="${POSTGRES_USER:-brewuser}"
db_name="${POSTGRES_DB:-brewweb}"
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

printf '%s\n' 'Waiting for PostgreSQL...'
until psql -h "$db_host" -U "$db_user" -d "$db_name" -tAc 'SELECT 1' >/dev/null 2>&1; do
  sleep 1
done

# v1.4.0 and earlier generated migrations at startup. If an existing database
# has application tables but no Alembic metadata, mark it at this reviewed
# baseline before applying future committed migrations.
has_alembic="$(psql -h "$db_host" -U "$db_user" -d "$db_name" -tAc "SELECT to_regclass('public.alembic_version') IS NOT NULL")"
has_users="$(psql -h "$db_host" -U "$db_user" -d "$db_name" -tAc "SELECT to_regclass('public.user') IS NOT NULL")"

if [ "$has_alembic" != 't' ] && [ "$has_users" = 't' ]; then
  printf '%s\n' 'Applying legacy v1.4 compatibility fixes...'
  psql -v ON_ERROR_STOP=1 -h "$db_host" -U "$db_user" -d "$db_name" \
    -f migrations/legacy_v1_4_compat.sql
  printf '%s\n' 'Stamping existing v1.4 schema at the migration baseline...'
  flask db stamp head
fi

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
