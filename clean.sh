#!/bin/sh
set -eu

# Project-scoped cleanup. Database volumes and backups are preserved.
docker compose down --remove-orphans

find ./app ./tests -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' \) -delete 2>/dev/null || true
find ./app ./tests -type d -name '__pycache__' -empty -delete 2>/dev/null || true

printf '%s\n' 'Brew-Web containers stopped and local Python caches removed.'
printf '%s\n' 'Database volumes, backups, logs, and unrelated Docker resources were preserved.'
