#!/bin/sh
set -eu
project="brewweb-volume-check-$$"
volume="brewweb-existing-data-$$"
cleanup() {
  docker compose -p "$project" -f docker-compose.yml -f docker-compose.legacy-volume.yml down >/dev/null 2>&1 || true
  docker volume rm "$volume" >/dev/null 2>&1 || true
}
export SECRET_KEY=volume-validation-only POSTGRES_PASSWORD=volume-validation-only
export BREWWEB_DATA_VOLUME="$volume"
trap cleanup EXIT INT TERM
docker volume create "$volume" >/dev/null
config="$(docker compose -p "$project" -f docker-compose.yml -f docker-compose.legacy-volume.yml config --format json)"
printf '%s' "$config" | python -c 'import json,sys,os; v=json.load(sys.stdin)["volumes"]["pgdata"]; assert v["external"] is True; assert v["name"] == os.environ["BREWWEB_DATA_VOLUME"]'
docker compose -p "$project" -f docker-compose.yml -f docker-compose.legacy-volume.yml create db
container="$(docker compose -p "$project" -f docker-compose.yml -f docker-compose.legacy-volume.yml ps --all --quiet db)"
mounted="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$container")"
test "$mounted" = "$volume"
docker compose -p "$project" -f docker-compose.yml -f docker-compose.legacy-volume.yml down
docker volume inspect "$volume" >/dev/null
docker volume rm "$volume" >/dev/null
if docker compose -p "$project" -f docker-compose.yml -f docker-compose.legacy-volume.yml create db; then
  printf '%s\n' 'ERROR: missing external volume was accepted.' >&2
  exit 1
fi
printf '%s\n' 'Existing volume mounted exactly, preserved by down, and missing-volume startup refused.'
