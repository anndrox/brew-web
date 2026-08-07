#!/bin/sh
# Entry script for the web container:
# 1) Ensure Alembic is initialized (if migrations/env.py is missing).
# 2) Run migrations/upgrade (best effort) to keep the DB schema current.
# 3) Seed default yeast data (best effort).
# 4) Start Gunicorn on port 4452 with access/error logging.

# Load environment variables with fallbacks to the original defaults
DB_USER="${POSTGRES_USER:-brewuser}"
DB_NAME="${POSTGRES_DB:-brewweb}"
DB_HOST="${POSTGRES_HOST:-db}"
export PGPASSWORD="${POSTGRES_PASSWORD:-brewpass}"

echo "⏳ Waiting for database..."
until psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1" >/dev/null 2>&1; do
  sleep 1
done

echo "📦 Running database migrations..."

if [ ! -f "/app/migrations/env.py" ]; then
  echo "🗂️ Initializing Alembic..."
  flask db init
fi

# Ensure database exists (handles fresh volumes)
echo "🗄️ Ensuring database $DB_NAME exists..."
if ! psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | grep -q 1; then
  createdb -h "$DB_HOST" -U "$DB_USER" -O "$DB_USER" -E UTF8 "$DB_NAME" || true
fi

flask db migrate -m "Auto migration" || true
flask db upgrade || true

# Guard against missing new columns on restored backups (run after upgrade so table exists)
echo "🔧 Ensuring app_settings.unit_preference column exists..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS unit_preference VARCHAR(10) DEFAULT 'imperial';" || true

echo "🌱 Seeding yeast types (if missing)..."
flask seed-yeasts || true

exec gunicorn -w 4 -b 0.0.0.0:4452 wsgi:app \
  --access-logfile logs/access.log \
  --error-logfile logs/brewweb.log
