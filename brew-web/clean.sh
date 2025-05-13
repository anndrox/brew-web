#!/bin/bash

echo "🛑 Stopping and removing Docker containers..."
docker-compose down --volumes --remove-orphans

echo "🧹 Pruning unused Docker objects..."
docker system prune -f

echo "🧹 Removing stale build cache and volumes..."
docker builder prune --all --force
docker volume prune --force

echo "🧼 Removing Python cache files and directories..."
find ./app -name "*.pyc" -delete
find ./app -name "__pycache__" -type d -exec rm -rf {} +

echo "📁 Forcibly removing backups/, logs/, migrations/..."
rm -rf ./backups ./logs ./migrations

echo "🧼 Removing Jinja template cache if any..."
find ./app -name "*.pyo" -delete
find ./app -name "*.pyd" -delete

echo "🔧 Ready for clean rebuild."
