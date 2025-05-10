import os

class Config:
    VERSION = "1.3.1"
    # 🔐 REQUIRED: Change this to a secure random string before deployment
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'changeme-in-production'  # <-- CHANGE THIS

    # 🛢️ PostgreSQL connection string for Docker Compose environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://brewuser:brewpass@db:5432/brewweb'
    # <-- If using Docker Compose, make sure your service is named `db`, or change `@db` to match

    # 🚫 Disable SQLAlchemy event system overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Enable CSRF protection for forms
    WTF_CSRF_ENABLED = True
