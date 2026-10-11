import requests
from functools import wraps
from flask import abort, current_app, g, has_request_context
import nh3
from flask_login import current_user
from config import Config
import re
import json
import os
import time

_update_cache = None
_update_cache_at = 0.0
_UPDATE_CACHE_SECONDS = 3600

def is_strong_password(password):
    return (
        bool(password) and
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[\W_]', password)
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
    global _update_cache, _update_cache_at

    now = time.monotonic()
    if _update_cache is not None and now - _update_cache_at < _UPDATE_CACHE_SECONDS:
        return _update_cache

    _update_cache = {"update_available": False, "current": Config.VERSION, "latest": "unknown"}
    _update_cache_at = now  # Cache failures too, avoiding repeated offline delays.
    try:
        latest_url = "https://api.github.com/repos/anndrox/brew-web/releases/latest"
        resp = requests.get(latest_url, timeout=2)

        if resp.status_code == 200:
            latest_version = resp.json()['tag_name'].removeprefix('v')
            current_parts = tuple(int(part) for part in Config.VERSION.split('.'))
            latest_parts = tuple(int(part) for part in latest_version.split('.'))
            if len(latest_parts) != 3:
                return _update_cache
            _update_cache = {
                "update_available": latest_parts > current_parts,
                "current": Config.VERSION,
                "latest": latest_version
            }
            _update_cache_at = now
            return _update_cache
    except (requests.RequestException, KeyError, ValueError, TypeError):
        pass
    return _update_cache

def get_unit_preference():
    """One settings query per request; schema repairs belong to startup, not page rendering."""
    if has_request_context() and hasattr(g, 'unit_preference'):
        return g.unit_preference
    from app.models import AppSettings
    settings = AppSettings.query.first()
    preference = settings.unit_preference if settings else 'imperial'
    if preference not in ('imperial', 'metric'):
        preference = 'imperial'
    if has_request_context():
        g.unit_preference = preference
    return preference


def sanitize_instructions(content):
    """Keep Quill formatting, never executable markup; old rows are sanitized on display."""
    tags = {'p', 'br', 'div', 'span', 'b', 'strong', 'i', 'em', 'u', 's',
            'ol', 'ul', 'li', 'a', 'blockquote', 'pre', 'code', 'h1', 'h2', 'h3'}
    classes = {'ql-align-center', 'ql-align-right', 'ql-align-justify', 'ql-direction-rtl'}
    return nh3.clean(content or '', tags=tags, attributes={'a': {'href', 'title', 'target'}},
                     allowed_classes={tag: classes for tag in tags},
                     url_schemes={'http', 'https', 'mailto'})

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
GALLON_TO_LITER = 3.78541

def gallons_to_liters(gallons):
    return gallons * GALLON_TO_LITER if gallons is not None else None

def liters_to_gallons(liters):
    return liters / GALLON_TO_LITER if liters is not None else None

def per_liter_to_per_gallon(amount_per_liter):
    """Convert an ingredient rate for one liter to the equivalent rate for one gallon."""
    return amount_per_liter * GALLON_TO_LITER if amount_per_liter is not None else None

def per_gallon_to_per_liter(amount_per_gallon):
    """Convert an ingredient rate for one gallon to the equivalent rate for one liter."""
    return amount_per_gallon / GALLON_TO_LITER if amount_per_gallon is not None else None

def f_to_c(fahrenheit):
    return (fahrenheit - 32) * 5 / 9 if fahrenheit is not None else None

def c_to_f(celsius):
    return (celsius * 9 / 5) + 32 if celsius is not None else None
