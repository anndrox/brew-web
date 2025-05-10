import requests
from functools import wraps
from flask import abort
from flask_login import current_user
from config import Config
import re

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
    
    