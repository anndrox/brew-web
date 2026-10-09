import io
import hashlib
import re
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from app import db
from app.database import dump_statements
from app.models import AppSettings, Batch, Ingredient, Recipe, User
from app.routes_calculators import honey_pounds, hydrometer_correction
from app.utils import sanitize_instructions
from test_app import create_admin, login_as


@pytest.mark.parametrize('remaining', [(1, 2), (0, 2), (2,)])
def test_removed_first_or_middle_ingredient_does_not_truncate(app, client, remaining):
    login_as(client, create_admin(app))
    with app.app_context():
        recipe = Recipe(name='Original', content='Instructions')
        db.session.add(recipe)
        db.session.flush()
        db.session.add_all([Ingredient(recipe_id=recipe.id, name=f'Item {i}',
                                      amount_per_gallon=i + 1, unit='g') for i in range(3)])
        db.session.commit()
        recipe_id = recipe.id
    data = {'name': 'Changed', 'content': '<p>Stir</p>'}
    for i in remaining:
        data.update({f'ingredient_name_{i}': f'Item {i}', f'ingredient_amount_{i}': str(i + 1),
                     f'ingredient_unit_{i}': 'g'})
    assert client.post(f'/app/recipes/{recipe_id}/edit', data=data).status_code == 302
    with app.app_context():
        assert [i.name for i in Ingredient.query.order_by(Ingredient.id)] == [f'Item {i}' for i in remaining]


@pytest.mark.parametrize('amount', ['nan', 'inf', '-1', 'not a number', ''])
def test_invalid_recipe_edit_retains_all_original_data(app, client, amount):
    login_as(client, create_admin(app))
    with app.app_context():
        recipe = Recipe(name='Original', content='Original instructions')
        db.session.add(recipe)
        db.session.flush()
        db.session.add(Ingredient(recipe_id=recipe.id, name='Keep', amount_per_gallon=10, unit='g'))
        db.session.commit()
        recipe_id = recipe.id
    response = client.post(f'/app/recipes/{recipe_id}/edit', data={
        'name': 'Should not save', 'content': 'Should not save',
        'ingredient_name_1': 'Invalid', 'ingredient_amount_1': amount, 'ingredient_unit_1': 'g',
    })
    assert response.status_code == 400
    with app.app_context():
        recipe = db.session.get(Recipe, recipe_id)
        assert (recipe.name, recipe.content) == ('Original', 'Original instructions')
        assert Ingredient.query.one().name == 'Keep'


def test_instructions_sanitize_old_rows_without_rewriting_storage(app, client):
    login_as(client, create_admin(app))
    unsafe = '<p class="ql-align-center"><strong>Safe</strong></p><script>alert(1)</script><img src=x onerror=alert(1)><a href="javascript:alert(1)">bad</a>` ${alert(1)} </script>'
    with app.app_context():
        recipe = Recipe(name='Legacy', content=unsafe)
        db.session.add(recipe)
        db.session.commit()
        recipe_id = recipe.id
    detail = client.get(f'/app/recipes/{recipe_id}')
    assert b'<strong>Safe</strong>' in detail.data
    assert b'ql-align-center' in detail.data
    assert b'onerror=' not in detail.data and b'javascript:alert' not in detail.data
    edit = client.get(f'/app/recipes/{recipe_id}/edit')
    assert b'const existingInstructions = "' in edit.data
    assert b'\\u003c' in edit.data  # tojson prevents script-context breakout.
    with app.app_context():
        assert db.session.get(Recipe, recipe_id).content == unsafe
    assert sanitize_instructions(None) == ''


def test_delete_recipe_csrf_and_viewer_controls(app, client):
    login_as(client, create_admin(app))
    with app.app_context():
        recipe = Recipe(name='Delete test')
        db.session.add(recipe)
        db.session.commit()
        recipe_id = recipe.id
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(f'/app/recipes/{recipe_id}/delete').status_code == 400
    page = client.get(f'/app/recipes/{recipe_id}')
    token = re.search(rb'name="csrf_token" value="([^"]+)"', page.data).group(1).decode()
    assert client.post(f'/app/recipes/{recipe_id}/delete', data={'csrf_token': token}).status_code == 302


def test_viewer_alias_remains_read_only_and_categories_visible(app, client):
    login_as(client, create_admin(app))
    assert client.post('/app/settings/admin/create-user', data={
        'username': 'reader', 'password': 'Good1!Password', 'role': 'viewer',
    }).status_code == 302
    with app.app_context():
        user = User.query.filter_by(username='reader').one()
        assert user.role == 'user'
        user.font_size = '18px'
        reader_id = user.id
        db.session.add_all([Recipe(name='Cider Visible', alcohol_type='Hard Cider'),
                            Recipe(name='Custom Visible', alcohol_type='Historical category')])
        db.session.commit()
        recipe_id = Recipe.query.filter_by(name='Cider Visible').one().id
    login_as(client, reader_id)
    page = client.get('/app/')
    assert b'Cider Visible' in page.data and b'Custom Visible' in page.data
    assert b'font-size: 18px' in page.data
    assert client.get('/app/recipes/new').status_code == 403
    detail = client.get(f'/app/recipes/{recipe_id}')
    assert b'Edit Recipe' not in detail.data and b'Delete</button>' not in detail.data


def test_calculators_reference_values_and_unit_equivalence(app, client):
    login_as(client, create_admin(app))
    assert honey_pounds(5, 0.100) == pytest.approx(14.2857142857)
    assert hydrometer_correction(1.050, 100, 60) == pytest.approx(1.056137, abs=0.00001)
    assert hydrometer_correction(1.050, 68, 68) == 1.050
    for sample in (31, 101):
        with pytest.raises(ValueError):
            hydrometer_correction(1.050, sample, 68)
    dilution = client.post('/app/calculator/dilution', data={
        'original_volume': '5', 'original_gravity': '1.100', 'target_gravity': '1.050'})
    assert b'Add 5.0 gallons' in dilution.data
    honey = client.post('/app/calculator/honey-needed', data={'volume': '5', 'target_gravity': '1.100'})
    assert b'14.29 lb' in honey.data
    sweet = client.post('/app/calculator/sweetness', data={
        'batch_volume': '5', 'current_gravity': '1.000', 'target_gravity': '1.010'})
    assert b'1.43 lb' in sweet.data
    recovery = client.post('/app/calculator/volume-recovery', data={
        'current_volume': '4', 'target_volume': '5', 'original_gravity': '1.100'})
    assert b'2.86 lb' in recovery.data and b'0.76 gallons' in recovery.data
    with app.app_context():
        db.session.add(AppSettings(unit_preference='metric'))
        db.session.commit()
    dilution = client.post('/app/calculator/dilution', data={
        'original_volume': '18.92705', 'original_gravity': '1.100', 'target_gravity': '1.050'})
    assert b'Add 18.93 liters' in dilution.data


@pytest.mark.parametrize('volume', ['nan', 'inf', '-1', '0'])
def test_invalid_calculator_input_is_rejected(app, client, volume):
    login_as(client, create_admin(app))
    assert client.post('/app/calculator/honey-needed', data={
        'volume': volume, 'target_gravity': '1.100'}).status_code == 400


def test_update_check_uses_releases_and_caches_failures(monkeypatch):
    import app.utils as utils
    monkeypatch.setattr(utils, '_update_cache', None)
    getter = Mock(side_effect=requests.ConnectionError('offline'))
    monkeypatch.setattr(utils.requests, 'get', getter)
    assert utils.check_for_updates()['latest'] == 'unknown'
    utils.check_for_updates()
    assert getter.call_count == 1
    assert getter.call_args.args[0].endswith('/releases/latest')
    monkeypatch.setattr(utils, '_update_cache', None)
    getter.side_effect = None
    getter.return_value = Mock(status_code=200, json=lambda: {'tag_name': 'v1.10.0'})
    assert utils.check_for_updates()['update_available']


def test_sql_parser_keeps_quoted_semicolons_and_copy_data():
    source = "-- generated\nSET standard_conforming_strings = on;\nINSERT INTO recipe (content) VALUES ('Stir; don''t stop');\nCOPY public.recipe (id, content) FROM stdin;\n1\tCOMMIT; is text\n\\.\n\\restrict ABC123\n-- footer\n\\unrestrict ABC123\n"
    statements = list(dump_statements(source))
    assert len(statements) == 3
    assert statements[-1][2] == '1\tCOMMIT; is text\n'


@pytest.mark.parametrize('source', ['COMMIT;', 'BEGIN;', '\\! echo unsafe\n',
                                  'DROP DATABASE brewweb;', 'COPY recipe FROM PROGRAM \'echo x\';',
                                  'SELECT 1; SELECT 2', 'SELECT \'unterminated;'])
def test_sql_parser_rejects_unsafe_restore_controls(source):
    with pytest.raises(ValueError):
        list(dump_statements(source))


def test_import_failure_never_reports_success(app, monkeypatch, tmp_path):
    import app.database as database
    import app.routes_admin as admin
    source = tmp_path / 'temporary.sql'
    source.write_text('bad SQL')
    monkeypatch.setattr(database, 'restore_backup', Mock(side_effect=ValueError('bad backup')))
    class ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target
        def start(self):
            self.target()
    monkeypatch.setattr(admin.threading, 'Thread', ImmediateThread)
    with app.app_context():
        assert admin._import_lock.acquire(False)
        admin._start_background_import(str(source))
        assert admin._read_import_status()['status'] == 'error'
        assert not admin._import_lock.locked()
    assert not source.exists()


def test_upload_does_not_overwrite_existing_backup(app, client, monkeypatch, tmp_path):
    import app.routes_admin as admin
    login_as(client, create_admin(app))
    monkeypatch.setattr(admin, 'BACKUP_FOLDER', str(tmp_path))
    original = tmp_path / 'backup.sql'
    original.write_text('keep original')
    captured = []
    monkeypatch.setattr(admin, '_start_background_import', captured.append)
    try:
        response = client.post('/app/settings/admin/import-db', data={
            'backup_file': (io.BytesIO(b'new uploaded file'), 'backup.sql')})
        assert response.status_code == 302
        assert original.read_text() == 'keep original'
        assert Path(captured[0]).read_bytes() == b'new uploaded file'
    finally:
        if admin._import_lock.locked():
            admin._import_lock.release()


def test_stats_with_dates_and_static_assets_are_local(app, client):
    from datetime import datetime
    login_as(client, create_admin(app))
    with app.app_context():
        recipe = Recipe(name='Stats')
        db.session.add(recipe)
        db.session.flush()
        db.session.add(Batch(name='Batch', recipe_id=recipe.id, start_date=datetime(2026, 10, 9), abv=10))
        db.session.commit()
    for url in ('/app/', '/app/stats/', '/app/calendar', '/app/recipes/new'):
        page = client.get(url)
        assert page.status_code == 200
        assert b'cdn.jsdelivr.net' not in page.data and b'cdn.quilljs.com' not in page.data
        if url == '/app/':
            assert b'chart.umd' not in page.data
        for asset in re.findall(rb'(?:src|href)="(/static/vendor/[^"]+)"', page.data):
            assert client.get(asset.decode()).status_code == 200


def test_bundled_vendor_assets_match_documented_hashes():
    root = Path(__file__).resolve().parent.parent / 'app/static/vendor'
    expected = {
        'chartjs-4.5.1/chart.umd.min.js': '48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a',
        'fullcalendar-6.1.20/index.global.min.js': 'b101204ba23e14478e957e284d58bba96fc7311021d0eeaf89fa5e65720c46c8',
        'quill-2.0.3/quill.js': 'f6157c72ac9b3f51cdead426335688a027b12405d9d6a4daadd38a676b2d7ff2',
        'quill-2.0.3/quill.snow.css': '1c7948cd13aa92fac6390319bc1e5e461823da171519d3a768db56164f871636',
    }
    for filename, digest in expected.items():
        assert hashlib.sha256((root / filename).read_bytes()).hexdigest() == digest
