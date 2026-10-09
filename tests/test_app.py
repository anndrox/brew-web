import re
from datetime import datetime

import pytest

from app import db
from app.models import (
    AppSettings,
    Batch,
    CalendarEvent,
    Ingredient,
    Measurement,
    Recipe,
    User,
    Yeast,
)
from app.utils import (
    c_to_f,
    f_to_c,
    gallons_to_liters,
    liters_to_gallons,
    per_gallon_to_per_liter,
    per_liter_to_per_gallon,
)


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


def test_metric_recipe_ingredient_amount_round_trips_on_create(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        db.session.add(AppSettings(unit_preference='metric'))
        db.session.commit()
    login_as(client, admin_id)

    response = client.post(
        '/app/recipes/new',
        data={
            'name': 'Metric Recipe',
            'content': 'Mix well',
            'alcohol_type': 'Mead',
            'ingredient_name_0': 'Honey',
            'ingredient_amount_0': '100',
            'ingredient_unit_0': 'g',
            'ingredient_note_0': '',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        recipe = Recipe.query.filter_by(name='Metric Recipe').one()
        ingredient = Ingredient.query.filter_by(recipe_id=recipe.id).one()
        assert ingredient.amount_per_gallon == pytest.approx(378.541)
        recipe_id = recipe.id

    detail = client.get(f'/app/recipes/{recipe_id}')
    assert detail.status_code == 200
    assert b'100.0 g Honey' in detail.data


def test_metric_recipe_ingredient_amount_round_trips_on_edit(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        db.session.add(AppSettings(unit_preference='metric'))
        recipe = Recipe(name='Metric Edit Recipe', content='Mix well', alcohol_type='Mead')
        db.session.add(recipe)
        db.session.flush()
        db.session.add(
            Ingredient(
                recipe_id=recipe.id,
                name='Honey',
                amount_per_gallon=378.541,
                unit='g',
                note='',
            )
        )
        db.session.commit()
        recipe_id = recipe.id
    login_as(client, admin_id)

    edit_page = client.get(f'/app/recipes/{recipe_id}/edit')
    assert edit_page.status_code == 200
    assert b'name="ingredient_amount_0"' in edit_page.data
    assert b'value="100.0"' in edit_page.data

    response = client.post(
        f'/app/recipes/{recipe_id}/edit',
        data={
            'name': 'Metric Edit Recipe',
            'content': 'Mix well',
            'alcohol_type': 'Mead',
            'ingredient_name_0': 'Honey',
            'ingredient_amount_0': '100',
            'ingredient_unit_0': 'g',
            'ingredient_note_0': '',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        ingredient = Ingredient.query.filter_by(recipe_id=recipe_id).one()
        assert ingredient.amount_per_gallon == pytest.approx(378.541)

    detail = client.get(f'/app/recipes/{recipe_id}')
    assert b'100.0 g Honey' in detail.data


@pytest.mark.parametrize('gallons', [0, 1, 5, 12.5])
def test_volume_conversion_round_trips(gallons):
    assert liters_to_gallons(gallons_to_liters(gallons)) == pytest.approx(gallons)


@pytest.mark.parametrize('amount_per_gallon', [0, 1, 100, 378.541])
def test_ingredient_rate_conversion_round_trips(amount_per_gallon):
    metric_rate = per_gallon_to_per_liter(amount_per_gallon)
    assert per_liter_to_per_gallon(metric_rate) == pytest.approx(amount_per_gallon)


@pytest.mark.parametrize('fahrenheit', [-40, 32, 68, 212])
def test_temperature_conversion_round_trips(fahrenheit):
    assert c_to_f(f_to_c(fahrenheit)) == pytest.approx(fahrenheit)


def test_metric_batch_values_and_labels_round_trip(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        db.session.add(AppSettings(unit_preference='metric'))
        recipe = Recipe(name='Metric Batch Recipe', alcohol_type='Mead')
        db.session.add(recipe)
        db.session.commit()
        recipe_id = recipe.id
    login_as(client, admin_id)

    new_page = client.get('/app/batches/new')
    assert b'Batch Size (liters)' in new_page.data
    assert 'Fermentation Temp (°C)'.encode() in new_page.data

    response = client.post(
        '/app/batches/new',
        data={
            'name': 'Metric Batch',
            'recipe_id': recipe_id,
            'start_date': '2026-10-09',
            'batch_size': '18.92705',
            'initial_gravity': '1.100',
            'final_gravity': '1.010',
            'fermentation_temp': '20',
            'enable_tosna': 'on',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        batch = Batch.query.filter_by(name='Metric Batch').one()
        assert batch.batch_size == pytest.approx(5)
        assert float(batch.fermentation_temp) == pytest.approx(68)
        assert batch.tosna_total == pytest.approx(15.14)
        batch_id = batch.id

    edit_page = client.get(f'/app/batches/{batch_id}/edit')
    assert b'Batch Size (liters)' in edit_page.data
    assert 'Fermentation Temp (°C)'.encode() in edit_page.data
    assert b'value="18.93"' in edit_page.data
    assert b'value="20.0"' in edit_page.data


def test_metric_measurement_temperature_and_label_round_trip(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        db.session.add(AppSettings(unit_preference='metric'))
        recipe = Recipe(name='Measurement Recipe', alcohol_type='Mead')
        db.session.add(recipe)
        db.session.flush()
        batch = Batch(
            recipe_id=recipe.id,
            name='Measurement Batch',
            start_date=datetime(2026, 10, 9),
        )
        db.session.add(batch)
        db.session.commit()
        batch_id = batch.id
    login_as(client, admin_id)

    form = client.get(f'/app/measurements/new?batch_id={batch_id}')
    assert 'Temperature (°C)'.encode() in form.data

    response = client.post(
        f'/app/measurements/new?batch_id={batch_id}',
        data={
            'batch_id': batch_id,
            'date': '2026-10-09',
            'gravity': '1.050',
            'ph': '3.5',
            'temperature': '20',
            'notes': 'Metric reading',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        measurement = Measurement.query.one()
        assert measurement.temperature == pytest.approx(68)

    detail = client.get(f'/app/batches/{batch_id}')
    assert '20.0 °C (68.0 °F)'.encode() in detail.data


def test_metric_calculators_apply_volume_and_mass_conversions(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        db.session.add(AppSettings(unit_preference='metric'))
        db.session.commit()
    login_as(client, admin_id)

    honey = client.post(
        '/app/calculator/honey-needed',
        data={'volume': '18.92705', 'target_gravity': '1.100'},
    )
    assert b'0.61 kg' in honey.data

    carbonation = client.post(
        '/app/calculator/carbonation',
        data={'volume': '18.92705', 'target_co2': '2.5'},
    )
    assert b'116.8 grams' in carbonation.data

    tosna = client.post(
        '/app/calculator/tosna',
        data={'batch_size': '18.92705', 'starting_gravity': '1.100'},
    )
    assert b'<strong>15.14</strong> g' in tosna.data


def test_temperature_correction_uses_matching_units_and_form_fields(app, client):
    admin_id = create_admin(app)
    with app.app_context():
        settings = AppSettings(unit_preference='metric')
        db.session.add(settings)
        db.session.commit()
        settings_id = settings.id
    login_as(client, admin_id)

    metric_form = client.get('/app/calculator/temp-correction')
    assert 'Sample Temperature (°C)'.encode() in metric_form.data
    metric = client.post(
        '/app/calculator/temp-correction',
        data={'reading': '1.050', 'sample_temp': '25', 'calibration_temp': '20'},
    )
    assert b'<strong>1.059</strong>' in metric.data

    with app.app_context():
        settings = db.session.get(AppSettings, settings_id)
        settings.unit_preference = 'imperial'
        db.session.commit()

    imperial_form = client.get('/app/calculator/temp-correction')
    assert 'Sample Temperature (°F)'.encode() in imperial_form.data
    imperial = client.post(
        '/app/calculator/temp-correction',
        data={'reading': '1.050', 'sample_temp': '77', 'calibration_temp': '68'},
    )
    assert b'<strong>1.059</strong>' in imperial.data


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
