# Brew-Web

[![CI](https://github.com/anndrox/brew-web/actions/workflows/ci.yml/badge.svg)](https://github.com/anndrox/brew-web/actions/workflows/ci.yml)
[![CodeQL](https://github.com/anndrox/brew-web/actions/workflows/codeql.yml/badge.svg)](https://github.com/anndrox/brew-web/actions/workflows/codeql.yml)
[![GitHub release](https://img.shields.io/github/v/release/anndrox/brew-web)](https://github.com/anndrox/brew-web/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Brew-Web is a self-hosted Flask application for managing brewing recipes, batches,
measurements, yeast references, calendars, and calculators. It runs as a non-root
container with PostgreSQL and is designed to sit behind an HTTPS reverse proxy.

## Features

- Recipe and ingredient scaling with imperial or metric units
- Batch tracking, gravity measurements, ABV, TOSNA, and calendar events
- Mead, wine, beer, and cider calculators
- Role-based accounts for administrators, editors, and users
- PostgreSQL backup and restore from the administration page
- Versioned database migrations and automatic startup upgrades
- CSRF-protected calendar changes and browser security headers

## Maintenance and support

Brew-Web is maintained on a best-effort basis rather than an active feature
roadmap. Reproducible defects and security issues are prioritized as maintainer
time permits, but response, review, and release times are not guaranteed. Feature
requests are welcome for discussion and may remain open until a contributor is
available to implement them.

For a stable installation, pin a numbered release instead of `latest`, keep a
verified PostgreSQL backup outside the container host, read release notes before
upgrading, and validate the upgrade in a non-production copy when practical. Use
the issue forms for reproducible bugs, and report suspected vulnerabilities
privately as described in [SECURITY.md](SECURITY.md).

## Quick start

Requirements: Git, Docker Engine or Docker Desktop, and Docker Compose v2.

The public prebuilt image is available from
[GitHub Container Registry](https://github.com/anndrox/brew-web/pkgs/container/brew-web).
No registry login or local image build is required. The current image supports
`linux/amd64` (x86-64); ARM64 users should build from source.

```bash
git clone https://github.com/anndrox/brew-web.git
cd brew-web
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put two different generated values into `SECRET_KEY` and `POSTGRES_PASSWORD` in
`.env`, then start the application:

```bash
docker compose pull web db
docker compose up -d --no-build
docker compose ps
```

Open <http://localhost:4452/setup> and create the first administrator. The default
configuration binds Brew-Web and PostgreSQL to localhost only.

Application responses include content-type, framing, referrer, permissions, and
content-security protections. When publishing through HTTPS, configure HSTS at
the reverse proxy and set `SESSION_COOKIE_SECURE=true`.

To pin the verified v1.4.0 release, set `BREWWEB_IMAGE=ghcr.io/anndrox/brew-web:1.4.0`
in `.env`. The default `latest` tag follows published releases. See
[release validation and maintainer instructions](docs/releases.md) for the immutable digest.

To build the current source instead of using the published image, set
`BREWWEB_IMAGE=brewweb:local` in `.env`, then run:

```bash
docker compose up -d --build
```

## Configuration

Copy `.env.example` to `.env`; `.env` is intentionally ignored by Git.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | required | Flask session and CSRF signing secret |
| `POSTGRES_PASSWORD` | required | PostgreSQL password |
| `POSTGRES_USER` | `brewuser` | PostgreSQL user |
| `POSTGRES_DB` | `brewweb` | PostgreSQL database |
| `BREWWEB_BIND` | `127.0.0.1` | Host interface for the web port |
| `BREWWEB_PORT` | `4452` | Host web port |
| `POSTGRES_PORT` | `5544` | Local PostgreSQL port |
| `SESSION_COOKIE_SECURE` | `false` | Set to `true` when served exclusively over HTTPS |
| `BREWWEB_IMAGE` | `ghcr.io/anndrox/brew-web:latest` | Container image or local tag |
| `RATELIMIT_STORAGE_URI` | `memory://` | Shared Flask-Limiter storage when using multiple workers |

Runtime data is stored in the `pgdata` Docker volume and the local `instance/`,
`logs/`, and `backups/` directories. Do not commit any of those contents.

The administrator's unit preference controls data entry and display. Brew-Web
stores batch volume in gallons, temperature in degrees Fahrenheit, and recipe
ingredient rates per gallon, then converts those canonical values at the user
interface boundary. Switching between imperial and metric therefore changes the
display without rewriting or compounding stored measurements.

## Upgrading and backups

Create and download a backup from **Settings → Administration** before every
upgrade. A manual custom-format backup can also be created with:

```bash
docker compose --profile tools run --rm export
```

Then update and restart:

```bash
git pull --ff-only
docker compose pull web db
docker compose up -d --no-build
```

Committed Alembic migrations are applied automatically. Existing unversioned v1.4
databases receive a one-time compatibility repair before being marked at the
baseline. `docker compose down` preserves data; do not add `--volumes` unless you
intentionally want to erase the database.

CI also exercises this upgrade path against an isolated PostgreSQL database. It
seeds representative account, settings, yeast, recipe, batch, ingredient,
measurement, and calendar data, starts the current image twice, and verifies the
rows and relationships remain intact after the compatibility repair and Alembic
migration. This guards the supported upgrade path; creating a backup before an
upgrade remains required operational practice.

## Development

```bash
python -m venv .venv
# Activate .venv using the command for your shell
python -m pip install -r requirements-dev.txt
ruff check .
python -m pytest
pip-audit -r requirements.txt
docker compose config --quiet
docker build -t brewweb:dev .
```

Changes should be made on a branch and submitted through a pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and [SECURITY.md](SECURITY.md)
for private vulnerability reporting.

## Recovery password reset

Create `instance/force_reset.flag`, restart the web container, and visit `/reset`.
Remove the flag after the administrator password has been changed. Keep filesystem
access to `instance/` restricted because this flow grants account recovery.

## License

Brew-Web is available under the [MIT License](LICENSE).
