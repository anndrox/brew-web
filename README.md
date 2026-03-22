# Brew-Web

[![Version](https://img.shields.io/badge/version-v1.4.0-blue)](#)
[![Docker](https://img.shields.io/badge/built%20with-Docker-blue)](#)
[![Flask](https://img.shields.io/badge/framework-Flask-yellow)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)](#)

Self-hosted web app for managing mead brewing recipes, batches, and calculators.

---

## Quick Start

[![Docker Compose](https://img.shields.io/badge/Setup-Docker%20Compose-informational)](#)

### Requirements
- Docker and Docker Compose
- `.env` in the project root (copy `.env.example`) with `SECRET_KEY` set
- **Before upgrading:** create a fresh SQL backup from `/settings/admin` (Export). The importer rewrites schemas and reseeds data to support old dumps, so keep a rollback handy.

### Installation
```bash
wget https://github.com/anndrox/brew-web/raw/main/brew-web.zip

unzip brew-web.zip -d .
cd brew-web

cp .env.example .env
$EDITOR .env   # set SECRET_KEY

docker compose up -d --build
```
Access at http://localhost:4452

> Imports from older backups now run schema repairs and yeast seeding automatically; no manual steps needed.

---

## Authentication & Security
- Run `/setup` on first start.
- Admin/user management via `/settings/admin`.
- Force password reset: create `/instance/force_reset.flag`.
- Keep behind TLS proxy; don’t expose 4452 directly.
- Store secrets only in `.env`; rotate `SECRET_KEY` for production.
- CSRF and login protection are enabled by default.

---

## Features
- ✓ Recipe scaling with structured ingredients
- ✓ Batch logging with gravities, honey, and notes
- ✓ Built-in brewing calculators:
  - ABV, **Target ABV**, TOSNA, dilution, sweetness, carbonation, temp correction, volume recovery, honey required
- ✓ Yeast reference guide
- ✓ Batch calendar tracker
- ✓ Role-based admin management
- ✓ Full PostgreSQL backup & restore
- ✓ Settings: theme, font, security
- ✓ Global unit preference (imperial/metric); recipes, forms, and calculators honor it

---

## Backup & Restore
[![Database](https://img.shields.io/badge/PostgreSQL-Export%2FImport-success)](#)

- **Export:** `/export-db` (admin) → saves to `/backups`
- **Import:** upload `.sql` via `/settings/admin`; runs in background with status page. Schema fixes and yeast reseed run automatically, even if Alembic revisions are missing.
- **Always export before upgrading** so you can roll back quickly.
- Safe for `docker compose down -v && up --build` cycles.

---

## Configuration
[![Configurable](https://img.shields.io/badge/Config-.env%20%2B%20docker--compose.yml-yellow)](#)

Key env:
```env
SECRET_KEY=changeme-in-production
```

---

## Project Structure
[![Structure](https://img.shields.io/badge/Folder%20Layout-Described-lightgrey)](#)
```
brew-web/
├─ app/
│  ├─ templates/
│  ├─ static/
│  ├─ routes/
│  └─ models.py
├─ backups/
├─ config.py
├─ docker-compose.yml
├─ Dockerfile
└─ README.md
```

---

## Dev Tips
- Reset environment:
  ```bash
  docker compose down -v && docker compose up --build
  ```
- Customize UI: edit `base.html`, `admin.html`, `static/style.css`
- Logs: `/logs/brewweb.log`

---

Recent maintenance and import hardening provided with assistance from Codex.
