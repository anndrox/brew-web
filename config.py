import os

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
