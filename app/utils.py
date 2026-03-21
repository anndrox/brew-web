import requests
from functools import wraps
from flask import abort, current_app
from flask_login import current_user
from config import Config
import re
import json
import os
from sqlalchemy.exc import ProgrammingError

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'[\W_]', password)  # requires a symbol
    )

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def check_for_updates():
    try:
        latest_url = "https://raw.githubusercontent.com/anndrox/brew-web/main/VERSION"
        resp = requests.get(latest_url, timeout=5)

        if resp.status_code == 200:
            latest_version = resp.text.strip()
            return {
                "update_available": latest_version != Config.VERSION,
                "current": Config.VERSION,
                "latest": latest_version
            }
    except Exception as e:
        return {
            "update_available": False,
            "error": str(e),
            "current": Config.VERSION,
            "latest": "unknown"
        }

    return {
        "update_available": False,
        "current": Config.VERSION,
        "latest": "unknown"
    }

def get_unit_preference():
    """Return 'imperial' or 'metric' based on AppSettings; defaults to imperial on errors."""
    try:
        from app.models import AppSettings  # local import to avoid circular dependency
        settings = AppSettings.query.first()
        if settings and settings.unit_preference in ('imperial', 'metric'):
            return settings.unit_preference
    except ProgrammingError:
        try:
            from app import db
            db.session.execute("ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS unit_preference VARCHAR(10) DEFAULT 'imperial';")
            db.session.commit()
            settings = AppSettings.query.first()
            if settings and settings.unit_preference in ('imperial', 'metric'):
                return settings.unit_preference
        except Exception:
            return 'imperial'
    except Exception:
        pass
    return 'imperial'

def is_metric():
    return get_unit_preference() == 'metric'

def read_import_status_file():
    try:
        path = os.path.join(current_app.instance_path, "import_status.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
# --- Unit helpers ---
def gallons_to_liters(gallons):
    return gallons * 3.78541 if gallons is not None else None

def liters_to_gallons(liters):
    return liters / 3.78541 if liters is not None else None

def f_to_c(fahrenheit):
    return (fahrenheit - 32) * 5 / 9 if fahrenheit is not None else None

def c_to_f(celsius):
    return (celsius * 9 / 5) + 32 if celsius is not None else None
