from app import db
from app.models import User


def create_admin(app):
    with app.app_context():
        user = User(username='admin', role='admin', is_admin=True)
        user.set_password('Strong1!Password')
        db.session.add(user)
        db.session.commit()


def test_healthcheck_is_available_before_setup(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_first_visit_redirects_to_setup(client):
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/setup')


def test_setup_rejects_weak_password(client):
    response = client.post(
        '/setup',
        data={'username': 'admin', 'password': 'weak', 'confirm_password': 'weak'},
        follow_redirects=True,
    )
    assert b'Use at least 8 characters' in response.data


def test_reset_requires_login_without_recovery_flag(app, client):
    create_admin(app)

    response = client.get('/reset', follow_redirects=False)

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')


def test_login_is_rate_limited(app, client):
    create_admin(app)

    for _ in range(5):
        response = client.post('/login', data={'username': 'admin', 'password': 'wrong'})
        assert response.status_code == 200

    response = client.post('/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code == 429
