import os

import pytest

os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('DATABASE_URL', 'sqlite://')

import app as app_package
from app import create_app, db


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(
        app_package,
        'check_for_updates',
        lambda: {'update_available': False, 'current': '1.4.0', 'latest': '1.4.0'},
    )

    application = create_app()
    application.instance_path = str(tmp_path / 'instance')
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    os.makedirs(application.instance_path, exist_ok=True)

    with application.app_context():
        db.create_all()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
