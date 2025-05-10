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
wget https://github.com/anndrox/brew-web/raw/main/brew-web-1.3.0.zip

unzip brew-web-1.3.0.zip -d .

cd brew-web

docker compose up -d --build
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

[![Configurable](https://img.shields.io/badge/Customizable-.env%20%7C%20docker-compose.yml-yellow)](#)

Key environment variables:

```env
environment:
  SECRET_KEY: changeme-in-production  # <-- CHANGE THIS 
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

![2025-05-10 11_19_52-Brew Log](https://github.com/user-attachments/assets/f31efcbd-fc3a-460a-b28d-fc97d219fe2b)
![2025-05-10 11_20_06-Brew Log](https://github.com/user-attachments/assets/852049ba-f0d2-4f56-a42a-014f2755ff12)
![2025-05-10 11_20_53-Brew Log](https://github.com/user-attachments/assets/cb4d8620-dc28-4577-b56f-8710662ad770)
![2025-05-10 11_21_05-Brew Log](https://github.com/user-attachments/assets/e1bc6fc8-35dd-4929-ab87-74314be23f1e)
![2025-05-10 11_21_22-Brew Log](https://github.com/user-attachments/assets/77b513a0-a965-4c65-9064-ad0755befc0b)
![2025-05-10 11_21_34-Brew Log](https://github.com/user-attachments/assets/a6cf1218-d004-42dd-b83d-40aab4b24e34)

