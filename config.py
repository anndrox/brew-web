import os


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(name):
    raw = os.environ.get(name, '')
    return [item.strip() for item in raw.split(',') if item.strip()]

class Config:
    VERSION = "1.4.0"
    # 🔐 REQUIRED: Change this to a secure random string before deployment
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY or SECRET_KEY == 'changeme-in-production':
        raise RuntimeError("SECRET_KEY must be set in environment (see .env.example).")

    # 🛢️ PostgreSQL connection string for Docker Compose environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://brewuser:brewpass@db:5432/brewweb'
    # <-- If using Docker Compose, make sure your service is named `db`, or change `@db` to match

    # 🚫 Disable SQLAlchemy event system overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enable CSRF protection for forms
    WTF_CSRF_ENABLED = True

    OIDC_ENABLED = env_bool('OIDC_ENABLED', False)
    OIDC_DISCOVERY_URL = os.environ.get('OIDC_DISCOVERY_URL')
    OIDC_CLIENT_ID = os.environ.get('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = os.environ.get('OIDC_CLIENT_SECRET')
    OIDC_SCOPES = os.environ.get('OIDC_SCOPES', 'openid profile email groups')
    OIDC_USERNAME_CLAIM = os.environ.get('OIDC_USERNAME_CLAIM', 'preferred_username')
    OIDC_EMAIL_CLAIM = os.environ.get('OIDC_EMAIL_CLAIM', 'email')
    OIDC_NAME_CLAIM = os.environ.get('OIDC_NAME_CLAIM', 'name')
    OIDC_GROUPS_CLAIM = os.environ.get('OIDC_GROUPS_CLAIM', 'groups')
    OIDC_ADMIN_GROUPS = env_list('OIDC_ADMIN_GROUPS')
    OIDC_EDITOR_GROUPS = env_list('OIDC_EDITOR_GROUPS')
    DISABLE_LOCAL_LOGIN = env_bool('DISABLE_LOCAL_LOGIN', OIDC_ENABLED)

    BREW_DB_HOST = os.environ.get('BREW_DB_HOST', 'db')
    BREW_DB_PORT = os.environ.get('BREW_DB_PORT', '5432')
    BREW_DB_NAME = os.environ.get('BREW_DB_NAME', 'brewweb')
    BREW_DB_USER = os.environ.get('BREW_DB_USER', 'brewuser')
    BREW_DB_PASSWORD = os.environ.get('BREW_DB_PASSWORD', 'brewpass')
