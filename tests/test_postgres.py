"""Runner-only integration tests. Never use a user's existing database here."""

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import BASELINE, prepare_schema, restore_backup, validate_schema

ROOT = Path(__file__).resolve().parent.parent
TEST_URL = os.environ.get('BREWWEB_TEST_POSTGRES')
pytestmark = pytest.mark.skipif(not TEST_URL, reason='Requires isolated runner PostgreSQL service')


@pytest.fixture()
def engine():
    url = make_url(TEST_URL)
    database = 'brewweb_test_' + uuid.uuid4().hex
    admin = create_engine(url, isolation_level='AUTOCOMMIT')
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE {database}')
    instance = create_engine(url.set(database=database))
    try:
        yield instance
    finally:
        instance.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE {database} WITH (FORCE)')
        admin.dispose()


def seed_legacy(engine, layout='v1.4-unversioned'):
    with engine.begin() as connection:
        connection.execute(text((ROOT / 'tests/upgrade/legacy_v1_4.sql').read_text()))
        password_hash = generate_password_hash('Preserved1!Password')
        connection.execute(text('UPDATE "user" SET password_hash=:hash'), {'hash': password_hash})
        if layout.startswith('v1.3.1'):
            # Matches archived release/brew-web-1.3.1.zip models: no yeast table,
            # no batch volume, no unit preference; free-text yeast and TOSNA exist.
            connection.exec_driver_sql('DROP TABLE yeast')
            connection.exec_driver_sql('ALTER TABLE batch DROP COLUMN batch_size')
            connection.exec_driver_sql('ALTER TABLE app_settings DROP COLUMN unit_preference')
            connection.exec_driver_sql("ALTER TABLE \"user\" ADD theme VARCHAR(20); ALTER TABLE \"user\" ADD font_size VARCHAR(10)")
            connection.exec_driver_sql("UPDATE \"user\" SET theme='light', font_size='18px'")
            connection.exec_driver_sql("ALTER TABLE calendar_event ADD note TEXT; UPDATE calendar_event SET note='Old calendar note'")
            connection.exec_driver_sql('ALTER TABLE batch ADD tosna_total FLOAT; ALTER TABLE batch ADD tosna_per_day FLOAT; ALTER TABLE batch ADD tosna_enabled BOOLEAN')
            connection.exec_driver_sql('UPDATE batch SET tosna_total=15.14, tosna_per_day=3.79, tosna_enabled=true')
        if layout.endswith('generated') or layout.endswith('baseline'):
            connection.exec_driver_sql('CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)')
            connection.execute(text('INSERT INTO alembic_version VALUES (:revision)'), {
                'revision': 'legacy_generated_id' if layout.endswith('generated') else BASELINE})
    return password_hash


def snapshot(engine):
    with engine.connect() as connection:
        return {name: [dict(row) for row in connection.execute(text(f'SELECT * FROM "{name}" ORDER BY id')).mappings()]
                for name in inspect(connection).get_table_names(schema='public') if name != 'alembic_version'}


@pytest.mark.parametrize('layout', ['v1.3.1-generated', 'v1.4-unversioned', 'v1.4-generated', 'v1.4-baseline'])
def test_upgrade_preserves_every_existing_value_and_is_idempotent(engine, layout):
    password_hash = seed_legacy(engine, layout)
    before = snapshot(engine)
    for _ in range(2):
        with engine.begin() as connection:
            prepare_schema(connection)
            validate_schema(connection)
            assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == BASELINE
        after = snapshot(engine)
        for name, rows in before.items():
            for original, updated in zip(rows, after[name], strict=True):
                assert {key: updated[key] for key in original} == original
        assert check_password_hash(after['user'][0]['password_hash'], 'Preserved1!Password')
        assert after['user'][0]['password_hash'] == password_hash
        if layout.startswith('v1.3.1'):
            assert after['batch'][0]['batch_size'] is None  # No invented historical volume.
            assert after['app_settings'][0]['unit_preference'] == 'imperial'
    # New records must not collide with preserved explicit IDs.
    with engine.begin() as connection:
        assert connection.execute(text("INSERT INTO recipe (name) VALUES ('After upgrade') RETURNING id")).scalar_one() > 1


def test_unknown_schema_fails_without_stamping_or_mutating_data(engine):
    seed_legacy(engine, 'v1.4-generated')
    with engine.begin() as connection:
        connection.exec_driver_sql('ALTER TABLE recipe ADD unfamiliar_column TEXT')
    before = snapshot(engine)
    with pytest.raises(ValueError, match='Unsupported columns'):
        with engine.begin() as connection:
            prepare_schema(connection)
    assert snapshot(engine) == before
    with engine.connect() as connection:
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == 'legacy_generated_id'


def dump_database(engine, path, custom=False, inserts=True):
    url = engine.url
    env = {**os.environ, 'PGPASSWORD': url.password}
    command = ['pg_dump', '-h', url.host, '-p', str(url.port or 5432), '-U', url.username,
               '-d', url.database, '--no-owner', '--no-privileges', '--file', str(path)]
    if custom:
        command.append('--format=custom')
    elif inserts:
        command.append('--inserts')
    subprocess.run(command, env=env, check=True, capture_output=True)


@pytest.mark.parametrize('custom,inserts', [(False, True), (False, False), (True, False)])
def test_real_pg_dump_restores_all_data_relationships_and_login(engine, tmp_path, custom, inserts):
    seed_legacy(engine, 'v1.4-generated')
    with engine.begin() as connection:
        prepare_schema(connection)
        connection.execute(text('UPDATE recipe SET content=:content'),
                           {'content': "Unicode 🍯, quotes ' and semicolons;\nsecond line"})
    original = snapshot(engine)
    path = tmp_path / ('backup.dump' if custom else 'backup.sql')
    dump_database(engine, path, custom, inserts)
    with engine.begin() as connection:
        connection.exec_driver_sql("UPDATE recipe SET name='Changed after backup'")
    restore_backup(path, engine)
    assert snapshot(engine) == original
    assert check_password_hash(snapshot(engine)['user'][0]['password_hash'], 'Preserved1!Password')
    restore_backup(path, engine)  # Same file can be restored twice.
    assert snapshot(engine) == original


@pytest.mark.parametrize('failure', ['sql-error', 'invalid-schema', 'no-admin', 'commit-control'])
def test_failed_restore_keeps_original_database_and_revision(engine, tmp_path, failure):
    seed_legacy(engine)
    with engine.begin() as connection:
        prepare_schema(connection)
    original = snapshot(engine)
    path = tmp_path / 'bad.sql'
    dump_database(engine, path)
    source = path.read_text()
    source += {
        'sql-error': "\nINSERT INTO nonexistent_table VALUES (1);\n",
        'invalid-schema': '\nALTER TABLE recipe ADD unexpected_column TEXT;\n',
        'no-admin': "\nUPDATE \"user\" SET role='user';\n",
        'commit-control': '\nCOMMIT;\n',
    }[failure]
    # UPDATE is deliberately outside supported pg_dump statements, so test the
    # no-admin case by changing its existing INSERT rather than expanding the allowlist.
    if failure == 'no-admin':
        source = path.read_text().replace("'admin'", "'user'")
    path.write_text(source)
    with pytest.raises(Exception):
        restore_backup(path, engine)
    assert snapshot(engine) == original
    with engine.connect() as connection:
        assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == BASELINE


def test_restore_legacy_missing_columns_uses_same_reviewed_bridge(engine, tmp_path):
    seed_legacy(engine, 'v1.3.1-generated')
    original = snapshot(engine)
    path = tmp_path / 'legacy.sql'
    dump_database(engine, path)
    with engine.begin() as connection:
        prepare_schema(connection)
    restore_backup(path, engine)
    restored = snapshot(engine)
    for name, rows in original.items():
        assert [{key: row[key] for key in rows[0]} for row in restored[name]] == rows


def test_restore_concurrency_is_refused_before_destructive_sql(engine, tmp_path):
    seed_legacy(engine)
    path = tmp_path / 'backup.sql'
    dump_database(engine, path)
    original = snapshot(engine)
    with engine.begin() as blocker:
        blocker.execute(text('SELECT pg_advisory_xact_lock(4452, 1)'))
        with pytest.raises(ValueError, match='already running'):
            restore_backup(path, engine)
    assert snapshot(engine) == original
