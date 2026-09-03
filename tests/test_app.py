import re
from datetime import datetime

from app import db
from app.models import Batch, CalendarEvent, Recipe, User, Yeast


def create_admin(app):
    with app.app_context():
        user = User(username='admin', role='admin', is_admin=True)
        user.set_password('Strong1!Password')
        db.session.add(user)
        db.session.commit()
        return user.id


def login_as(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_healthcheck_is_available_before_setup(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert "default-src 'self'" in response.headers['Content-Security-Policy']


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


def test_settings_landing_page_renders(app, client):
    admin_id = create_admin(app)
    login_as(client, admin_id)

    response = client.get('/app/settings/')

    assert response.status_code == 200
    assert b'/app/settings/admin/' in response.data
    assert b'/app/settings/customize' in response.data
    assert b'/app/settings/password' in response.data


def test_calculator_routes_are_only_registered_under_app(app, client):
    admin_id = create_admin(app)
    login_as(client, admin_id)

    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert '/calculator/' not in rules
    assert '/app/calculator/' in rules
    assert sum(rule.rule == '/app/' for rule in app.url_map.iter_rules()) == 1

    response = client.get('/app/calculator/')
    assert response.status_code == 200
    assert b'/app/calculator/abv' in response.data


def test_batch_edit_parses_dates_on_sqlite(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        recipe = Recipe(name='Date Test Recipe', alcohol_type='Mead')
        db.session.add(recipe)
        db.session.flush()
        batch = Batch(
            recipe_id=recipe.id,
            name='Date Test Batch',
            start_date=datetime(2026, 9, 1),
        )
        db.session.add(batch)
        db.session.commit()
        recipe_id = recipe.id
        batch_id = batch.id
    login_as(client, admin_id)

    response = client.post(
        f'/app/batches/{batch_id}/edit',
        data={
            'name': 'Date Test Batch Updated',
            'recipe_id': recipe_id,
            'start_date': '2026-09-02',
            'end_date': '2026-09-12',
            'batch_size': '5',
            'initial_gravity': '1.100',
            'final_gravity': '1.010',
            'fermentation_temp': '68',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        updated = db.session.get(Batch, batch_id)
        assert updated.start_date == datetime(2026, 9, 2)
        assert updated.end_date == datetime(2026, 9, 12)


def test_tosna_calendar_creation_uses_calendar_start_field(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        recipe = Recipe(name='TOSNA Test Recipe', alcohol_type='Mead')
        db.session.add(recipe)
        db.session.flush()
        batch = Batch(
            recipe_id=recipe.id,
            name='TOSNA Test Batch',
            start_date=datetime(2026, 9, 1),
            batch_size=5,
            initial_gravity=1.100,
        )
        db.session.add(batch)
        db.session.commit()
        batch_id = batch.id
    login_as(client, admin_id)

    response = client.post(
        f'/app/batches/batch/{batch_id}/tosna',
        data={'add_to_calendar': 'on'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        events = CalendarEvent.query.order_by(CalendarEvent.start).all()
        assert [event.title for event in events] == [
            'TOSNA Day 1',
            'TOSNA Day 2',
            'TOSNA Day 3',
            'TOSNA Day 4',
        ]
        assert events[0].start.isoformat() == '2026-09-01'


def test_calendar_mutations_require_csrf_token(app, client):
    admin_id = create_admin(app)
    login_as(client, admin_id)
    app.config['WTF_CSRF_ENABLED'] = True

    rejected = client.post(
        '/app/calendar-event',
        json={'title': 'Rejected', 'start': '2026-09-03'},
    )
    assert rejected.status_code == 400

    calendar_page = client.get('/app/calendar')
    token_match = re.search(rb"X-CSRFToken': '([^']+)'", calendar_page.data)
    assert token_match is not None
    accepted = client.post(
        '/app/calendar-event',
        json={'title': 'Protected event', 'start': '2026-09-03'},
        headers={'X-CSRFToken': token_match.group(1).decode()},
    )
    assert accepted.status_code == 200


def test_restore_yeasts_keeps_same_name_in_multiple_categories(app, client):
    admin_id = create_admin(app)
    login_as(client, admin_id)

    response = client.post('/app/yeasts/restore', follow_redirects=False)

    assert response.status_code == 302
    with app.app_context():
        ec_1118 = Yeast.query.filter_by(name='Lalvin EC-1118').all()
        assert {yeast.alcohol_type for yeast in ec_1118} == {'Mead', 'Wine', 'Hard Cider'}
        assert all(yeast.is_default for yeast in ec_1118)
