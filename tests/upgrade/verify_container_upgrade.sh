#!/bin/sh
set -eu

image="${1:-brewweb:ci}"
published_image='ghcr.io/anndrox/brew-web@sha256:903a350b742d817885a62f6ca17d67afe99ff8a997aa3bc8bddd87095def7f73'
run_image="$image"
network="brewweb-upgrade-$$"
database_container="brewweb-upgrade-db-$$"
web_container="brewweb-upgrade-web-$$"
database_password="upgrade-test-only"

cleanup() {
  docker rm -fv "$web_container" "$database_container" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

docker network create "$network" >/dev/null
docker run --detach --name "$database_container" --network "$network" \
  --env POSTGRES_USER=brewuser \
  --env POSTGRES_PASSWORD="$database_password" \
  --env POSTGRES_DB=brewweb \
  postgres:15-alpine@sha256:fe0737ba566a2c5b2a28f34433c0a423261900ec17b9bf7ad115e1aae7e57f1b \
  >/dev/null

attempt=0
until docker exec "$database_container" pg_isready -U brewuser -d brewweb >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    docker logs "$database_container"
    exit 1
  fi
  sleep 1
done

docker exec --interactive "$database_container" psql \
  --set ON_ERROR_STOP=1 --username brewuser --dbname brewweb \
  < tests/upgrade/legacy_v1_4.sql

start_web() {
  docker run --detach --name "$web_container" --network "$network" \
    --read-only \
    --tmpfs /tmp:rw,uid=1000,gid=1000,mode=1777 \
    --tmpfs /app/instance:rw,uid=1000,gid=1000,mode=0755 \
    --tmpfs /app/logs:rw,uid=1000,gid=1000,mode=0755 \
    --tmpfs /app/backups:rw,uid=1000,gid=1000,mode=0755 \
    --security-opt no-new-privileges:true \
    --env SECRET_KEY=upgrade-validation-only \
    --env POSTGRES_HOST="$database_container" \
    --env POSTGRES_USER=brewuser \
    --env POSTGRES_PASSWORD="$database_password" \
    --env POSTGRES_DB=brewweb \
    "$run_image" >/dev/null

  attempt=0
  until [ "$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$web_container")" = healthy ]; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ] || [ "$(docker inspect --format '{{.State.Running}}' "$web_container")" != true ]; then
      docker logs "$web_container"
      exit 1
    fi
    sleep 1
  done
}

verify_data() {
  docker exec --interactive "$database_container" psql \
    --set ON_ERROR_STOP=1 --username brewuser --dbname brewweb \
    < tests/upgrade/verify_preserved_data.sql
}

# First prove the currently published v1.4.0 image's database can be opened by
# the candidate; same database, credentials, mounts, data and PostgreSQL major.
run_image="$published_image"
start_web
verify_data
docker rm -fv "$web_container" >/dev/null
run_image="$image"
start_web
verify_data
docker rm -fv "$web_container" >/dev/null

# Reset ONLY the disposable runner database, never a user volume, to exercise
# the unversioned schema separately from the published/versioned installation.
docker exec "$database_container" psql --set ON_ERROR_STOP=1 --username brewuser --dbname brewweb \
  -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
docker exec --interactive "$database_container" psql \
  --set ON_ERROR_STOP=1 --username brewuser --dbname brewweb \
  < tests/upgrade/legacy_v1_4.sql
start_web
verify_data

# A second startup proves that an already-upgraded database is handled idempotently.
docker rm -fv "$web_container" >/dev/null
start_web
verify_data

printf '%s\n' 'Published v1.4.0 upgrade, unversioned compatibility and second startup preserved representative data.'
