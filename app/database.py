"""Reviewed legacy-schema bridge and transactional restores for trusted pg_dump files.

Backups contain executable SQL: this is not a sandbox for untrusted uploads.
Only an administrator's own Brew-Web PostgreSQL backups are supported.
"""

import io
import re
import subprocess
import tempfile
from pathlib import Path

from alembic.script import ScriptDirectory
from psycopg2 import sql
from sqlalchemy import inspect, text

BASELINE = 'eaf3a864a154'
ROOT = Path(__file__).resolve().parent.parent
LEGACY_ADDITIONS = {
    'user': {'theme', 'font_size'},
    'recipe': {'yeast_id'},
    'batch': {'batch_size', 'yeast_id', 'tosna_total', 'tosna_per_day', 'tosna_enabled'},
    'calendar_event': {'note'},
    'app_settings': {'unit_preference'},
}


def validate_schema(connection, *, legacy=False):
    """Refuse unknown/malformed layouts instead of silently blessing them as head."""
    from app.models import db

    inspector = inspect(connection)
    actual_tables = set(inspector.get_table_names(schema='public')) - {'alembic_version'}
    expected = set(db.metadata.tables)
    allowed_missing = {'yeast'} if legacy else set()
    if actual_tables - expected or expected - actual_tables - allowed_missing:
        raise ValueError('Unsupported database tables; restore a verified backup in a test copy first.')
    for name in sorted(actual_tables):
        table = db.metadata.tables[name]
        actual = {column['name']: column for column in inspector.get_columns(name, schema='public')}
        missing = set(table.columns.keys()) - set(actual)
        allowed = LEGACY_ADDITIONS.get(name, set()) if legacy else set()
        if missing - allowed or set(actual) - set(table.columns.keys()):
            raise ValueError(f'Unsupported columns in {name}; no schema version was changed.')
        if inspector.get_pk_constraint(name, schema='public')['constrained_columns'] != ['id']:
            raise ValueError(f'Unsupported primary key in {name}.')
        for column_name, column in actual.items():
            if column['type']._type_affinity is not table.columns[column_name].type._type_affinity:
                raise ValueError(f'Unsupported type in {name}.{column_name}.')
        expected_keys = {(tuple(key.parent.name for key in constraint.elements),
                          constraint.elements[0].column.table.name,
                          tuple(key.column.name for key in constraint.elements))
                         for constraint in table.foreign_key_constraints}
        actual_keys = {(tuple(key['constrained_columns']), key['referred_table'],
                        tuple(key['referred_columns']))
                       for key in inspector.get_foreign_keys(name, schema='public')}
        optional_keys = {key for key in expected_keys if key[0] == ('yeast_id',)} if legacy else set()
        if actual_keys - expected_keys or expected_keys - actual_keys - optional_keys:
            raise ValueError(f'Unsupported relationships in {name}.')


def prepare_schema(connection):
    """Bridge only structurally recognized legacy databases, in the caller's transaction."""
    inspector = inspect(connection)
    tables = inspector.get_table_names(schema='public')
    if 'user' not in tables:
        if set(tables) - {'alembic_version'}:
            raise ValueError('Partial database detected; refusing to initialize over existing tables.')
        return
    revision = None
    if 'alembic_version' in tables:
        revisions = connection.execute(text('SELECT version_num FROM alembic_version')).scalars().all()
        if len(revisions) > 1:
            raise ValueError('Multiple migration heads require manual review.')
        revision = revisions[0] if revisions else None
    known = {rev.revision for rev in ScriptDirectory(str(ROOT / 'migrations')).walk_revisions()}
    # v1.3.1 and early v1.4 created migration IDs dynamically. Accept their
    # schema shape, not an arbitrary claimed revision number or a partial schema.
    validate_schema(connection, legacy=True)
    connection.exec_driver_sql((ROOT / 'migrations/legacy_v1_4_compat.sql').read_text())
    validate_schema(connection)
    if revision not in known:
        connection.execute(text('CREATE TABLE IF NOT EXISTS alembic_version '
                                '(version_num VARCHAR(32) PRIMARY KEY)'))
        connection.execute(text('DELETE FROM alembic_version'))
        connection.execute(text('INSERT INTO alembic_version VALUES (:baseline)'), {'baseline': BASELINE})
    # Legacy hand-written inserts can leave serial sequences behind their IDs.
    for name in sorted(set(tables) | {'yeast'}):
        if name == 'alembic_version':
            continue
        sequence = connection.execute(text('SELECT pg_get_serial_sequence(:table, :column)'),
                                      {'table': f'public."{name}"', 'column': 'id'}).scalar()
        if sequence:
            sequence_schema, sequence_name = connection.execute(text(
                'SELECT n.nspname, c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace '
                'WHERE c.oid=CAST(:sequence AS regclass)'), {'sequence': sequence}).one()
            cursor = connection.connection.driver_connection.cursor()
            try:
                cursor.execute(sql.SQL('SELECT last_value, is_called FROM {}').format(
                    sql.Identifier(sequence_schema, sequence_name)))
                last_value, is_called = cursor.fetchone()
            finally:
                cursor.close()
            # Table name is from the verified allowlist; sequence names/values
            # are safely quoted/bound even when an old sequence was renamed.
            connection.execute(text(
                f'SELECT setval(CAST(:sequence AS regclass), '
                f'GREATEST(COALESCE((SELECT MAX(id) FROM "{name}"), 1), :last_value), '
                f':is_called OR EXISTS (SELECT 1 FROM "{name}"))'
            ), {'sequence': sequence, 'last_value': last_value, 'is_called': is_called})


# Lexical splitting preserves quoted semicolons, dollar strings and nested
# comments. COPY data is read separately, never interpreted as SQL or psql commands.
_TOKEN = re.compile(r"--[^\n]*(?:\n|$)|/\*|\$[A-Za-z_0-9]*\$|'|\"|;|\\")


def dump_statements(source):
    pos = start = 0
    length = len(source)
    while pos < length:
        match = _TOKEN.search(source, pos)
        if not match:
            break
        token = match.group()
        pos = match.end()
        if token.startswith('--'):
            continue
        if token == '/*':
            depth = 1
            while depth:
                nested = re.search(r'/\*|\*/', source[pos:])
                if not nested:
                    raise ValueError('Unterminated backup comment.')
                depth += 1 if nested.group() == '/*' else -1
                pos += nested.end()
        elif token in {"'", '"'}:
            while True:
                end = source.find(token, pos)
                if end < 0:
                    raise ValueError('Unterminated backup string.')
                if end + 1 < length and source[end + 1] == token:
                    pos = end + 2
                    continue
                # pg_dump uses standard_conforming_strings; E strings may escape.
                if token == "'" and end > 0 and source[end - 1] == '\\':
                    escaped = len(source[:end]) - len(source[:end].rstrip('\\'))
                    if escaped % 2 and re.search(r"\bE$", source[:match.start()], re.I):
                        pos = end + 1
                        continue
                pos = end + 1
                break
        elif token.startswith('$'):
            end = source.find(token, pos)
            if end < 0:
                raise ValueError('Unterminated backup dollar string.')
            pos = end + len(token)
        elif token == '\\':
            # New pg_dump versions wrap SQL in psql's restrict mode. Never
            # execute arbitrary psql commands (connect, shell, include, etc.).
            end = source.find('\n', pos)
            end = length if end < 0 else end + 1
            directive = source[match.start():end].strip()
            if not re.fullmatch(r'\\(?:un)?restrict [A-Za-z0-9]+', directive):
                raise ValueError('Unsupported psql command in backup.')
            source = source[:match.start()] + ' ' * (end - match.start()) + source[end:]
            pos = end
        elif token == ';':
            statement = source[start:pos]
            # Remove comments only for deciding the command, not for execution.
            command = re.sub(r'--[^\n]*|/\*.*?\*/', ' ', statement, flags=re.S).strip()
            if not re.match(r'^(SET\b|SELECT\b|INSERT\s+INTO\b|COPY\b|'
                            r'CREATE\s+(?:TABLE|SEQUENCE|SCHEMA)\b|'
                            r'ALTER\s+(?:TABLE|SEQUENCE)\b|COMMENT\s+ON\b)', command, re.I):
                raise ValueError('Unsupported SQL command; only Brew-Web pg_dump backups are supported.')
            copy_data = None
            if re.match(r'^COPY\b', command, re.I):
                if not re.search(r'\bFROM\s+stdin\s*;$', command, re.I):
                    raise ValueError('Only COPY FROM stdin is supported.')
                if source[pos:pos + 1] != '\n':
                    raise ValueError('Invalid COPY data boundary.')
                data_end = re.search(r'^\\\.\r?$', source[pos + 1:], re.M)
                if not data_end:
                    raise ValueError('Missing COPY terminator.')
                copy_data = source[pos + 1:pos + 1 + data_end.start()]
                pos += 1 + data_end.end()
            yield statement, command, copy_data
            start = pos
    tail = re.sub(r'--[^\n]*|/\*.*?\*/', ' ', source[start:], flags=re.S).strip()
    if tail:
        raise ValueError('Incomplete SQL backup.')


def restore_backup(path, engine):
    """All destructive SQL, data loads and schema validation commit together."""
    path = Path(path)
    with tempfile.TemporaryDirectory(prefix='brewweb-restore-') as folder:
        if path.suffix == '.dump':
            sql_path = Path(folder) / 'restore.sql'
            subprocess.run(['pg_restore', '--no-owner', '--no-privileges',
                            '--file', str(sql_path), str(path)], check=True, timeout=300,
                           capture_output=True)
        else:
            sql_path = path
        source = sql_path.read_text(encoding='utf-8').replace('\r\n', '\n')
        statements = list(dump_statements(source))  # Reject invalid controls before touching DB.
        if not statements:
            raise ValueError('Empty backup.')
        with engine.begin() as connection:
            # Transaction-scoped lock coordinates restore and startup, including
            # multiple workers, without giving workflow code any host authority.
            locked = connection.execute(text('SELECT pg_try_advisory_xact_lock(4452, 1)')).scalar()
            if not locked:
                raise ValueError('A database restore or upgrade is already running.')
            connection.exec_driver_sql("SET LOCAL lock_timeout = '10s'")
            connection.exec_driver_sql('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
            cursor = connection.connection.driver_connection.cursor()
            try:
                for statement, command, data in statements:
                    if re.fullmatch(r'CREATE\s+SCHEMA\s+"?public"?\s*;', command, re.I):
                        continue  # public was created above in the same transaction.
                    if data is not None:
                        cursor.copy_expert(statement, io.StringIO(data))
                    else:
                        # pg_dump SET and set_config(..., false) affect a whole
                        # session by default. Keep them in this transaction so
                        # pooled application connections retain their settings.
                        if re.match(r'^SET\b', command, re.I):
                            statement = re.sub(r'^SET\s+(?:(?:SESSION|LOCAL)\s+)?',
                                               'SET LOCAL ', command, count=1, flags=re.I)
                        elif re.match(r'^SELECT\s+pg_catalog\.set_config\(', command, re.I):
                            statement = re.sub(r',\s*false\s*\)\s*;$', ', true);',
                                               command, flags=re.I)
                        cursor.execute(statement)
            finally:
                cursor.close()
            connection.exec_driver_sql('SET LOCAL search_path = public, pg_catalog')
            prepare_schema(connection)
            validate_schema(connection)
            # A restored database must include an administrator, not strand its owner.
            if not connection.execute(text('SELECT 1 FROM "user" WHERE role = \'admin\' LIMIT 1')).scalar():
                raise ValueError('Backup has no administrator account.')
