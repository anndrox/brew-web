import os

from sqlalchemy.engine import URL


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    VERSION = "1.4.0"
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY or SECRET_KEY in {'changeme-in-production', 'replace-with-a-random-secret'}:
        raise RuntimeError("SECRET_KEY must be set in environment (see .env.example).")

    _DATABASE_URL = os.environ.get('DATABASE_URL')
    if _DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = _DATABASE_URL
    else:
        _DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
        if not _DB_PASSWORD or _DB_PASSWORD == 'replace-with-a-random-database-password':
            raise RuntimeError("POSTGRES_PASSWORD must be set in environment (see .env.example).")
        SQLALCHEMY_DATABASE_URI = URL.create(
            'postgresql+psycopg2',
            username=os.environ.get('POSTGRES_USER', 'brewuser'),
            password=_DB_PASSWORD,
            host=os.environ.get('POSTGRES_HOST', 'db'),
            port=5432,
            database=os.environ.get('POSTGRES_DB', 'brewweb'),
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE')
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
