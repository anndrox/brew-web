#!/bin/sh
# Entry script for the web container:
# 1) Ensure Alembic is initialized (if migrations/env.py is missing).
# 2) Run migrations/upgrade (best effort) to keep the DB schema current.
# 3) Seed default yeast data (best effort).
# 4) Start Gunicorn on port 4452 with access/error logging.

# Ensure psql commands can authenticate (can be overridden via PGPASSWORD env)
export PGPASSWORD="${PGPASSWORD:-brewpass}"

echo "⏳ Waiting for database..."
until psql -h db -U brewuser -d postgres -tAc "SELECT 1" >/dev/null 2>&1; do
  sleep 1
done

echo "📦 Running database migrations..."

if [ ! -f "/app/migrations/env.py" ]; then
  echo "🗂️ Initializing Alembic..."
  flask db init
fi

# Ensure database exists (handles fresh volumes)
echo "🗄️ Ensuring database brewweb exists..."
if ! psql -h db -U brewuser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='brewweb';" | grep -q 1; then
  createdb -h db -U brewuser -O brewuser -E UTF8 brewweb || true
fi

flask db migrate -m "Auto migration" || true
flask db upgrade || true

# Guard against missing new columns on restored backups (run after upgrade so table exists)
echo "🔧 Ensuring app_settings.unit_preference column exists..."
psql -h db -U brewuser -d brewweb -c "ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS unit_preference VARCHAR(10) DEFAULT 'imperial';" || true

echo "🌱 Seeding yeast types (if missing)..."
flask seed-yeasts || true

exec gunicorn -w 4 -b 0.0.0.0:4452 wsgi:app \
  --access-logfile logs/access.log \
  --error-logfile logs/brewweb.log
