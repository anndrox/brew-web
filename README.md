# Brew-Web 🍯

[![Version](https://img.shields.io/badge/version-v1.3.0-blue)](#)
[![Docker](https://img.shields.io/badge/built%20with-Docker-blue)](#)
[![Flask](https://img.shields.io/badge/framework-Flask-yellow)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)](#)

A self-hosted web app to manage mead brewing recipes, batches, and calculators — complete with stats, backups, and admin tools.

---

## 🚀 Quick Start

[![Docker Compose](https://img.shields.io/badge/Setup-Docker%20Compose-informational)](#)

### Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

### Installation

```bash
wget https://github.com/anndrox/brew-web/releases/latest/download/brew-web-1.3.0.zip

unzip brew-web-1.3.0.zip -d .

cd brew-web

docker compose up -d
```

Access the app at: [http://localhost:4452](http://localhost:4452)

---

## 🔐 Authentication & Security

[![Flask Login](https://img.shields.io/badge/Security-Login%20Required-red)](#)

- Setup is required via `/setup` on first run
- Admin controls and user management via `/settings/admin`
- Force password reset by placing a file:
  ```
  /instance/force_reset.flag
  ```
- For public deployments, use a reverse proxy with SSL (e.g. NGINX + Let's Encrypt)

---

## 📋 Features

[![Feature Rich](https://img.shields.io/badge/Brew%20Tracking-Recipes%2C%20Batches%2C%20ABV-lightgrey)](#)

- ✅ Recipe scaling with structured ingredients
- ✅ Batch logging with gravities, honey, and notes
- ✅ Built-in brewing calculators:
  - ABV, TOSNA, dilution, sweetness, carbonation, temp correction, volume recovery
- ✅ Yeast reference guide with visuals and ratings
- ✅ Batch calendar tracker
- ✅ Role-based admin management
- ✅ Full PostgreSQL backup & restore
- ✅ Settings: theme, font, security

---

## 💾 Backup & Restore

[![Database](https://img.shields.io/badge/PostgreSQL-Export%2FImport-success)](#)

- **Export:**  
  Visit `/export-db` (admin only) — saves to `/backups`

- **Import:**  
  Upload `.sql` via `/admin`  
  ⏳ Import runs in the background with countdown and refresh

- Safe for `docker compose down -v && up --build` cycles

---

## ⚙️ Configuration

[![Configurable](https://img.shields.io/badge/Customizable-.env%20%7C%20config.py-yellow)](#)

Key environment variables:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://brewuser:brewpass@db:5432/brewweb
```

---

## 🗂 Project Structure

[![Structure](https://img.shields.io/badge/Folder%20Layout-Described-lightgrey)](#)

```
brew-web/
├── app/                  # Flask app
│   ├── templates/        # Jinja2 templates
│   ├── static/           # CSS & JS
│   ├── routes/           # Feature blueprints
│   └── models.py         # SQLAlchemy models
├── backups/              # SQL dumps
├── config.py             # App config
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 🧪 Dev Tips

[![For Developers](https://img.shields.io/badge/Usage-Dev%20Friendly-orange)](#)

- Reset environment:  
  ```bash
  docker compose down -v && docker compose up --build
  ```

- Customize UI:  
  Modify `base.html`, `admin.html`, or `static/style.css`

- Logs saved to:  
  `/logs/brewweb.log`

---

## 📌 Notes

- Your `pg_dump`/`psql` commands must use the same credentials as `docker-compose.yml`
- Tables are automatically dropped and reloaded on import via `subprocess.Popen()`
- Alembic is automatically skipped after full restores
- Countdown refresh prevents white screen crash during restore

---

## 📜 License

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

MIT © 2025 Scott Jones
