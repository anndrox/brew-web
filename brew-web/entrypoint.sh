#!/bin/sh
echo "📦 Running database migrations..."

# ✅ Only init Alembic if env.py is missing (not just the folder)
if [ ! -f "/app/migrations/env.py" ]; then
  echo "📁 Initializing Alembic..."
  flask db init
fi

flask db migrate -m "Auto migration" || true
flask db upgrade || true

echo "🌱 Seeding yeast types (if missing)..."
flask seed-yeasts || true

exec gunicorn -w 4 -b 0.0.0.0:4452 wsgi:app \
  --access-logfile logs/access.log \
  --error-logfile logs/brewweb.log
