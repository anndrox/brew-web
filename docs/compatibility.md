# Upgrade compatibility and restore safety

Brew-Web 1.4.1 preserves the existing PostgreSQL 15 database, account password
hashes, IDs, brewing values and relationships. Upgrades add known missing columns;
they do not recalculate historical measurements, infer a missing batch size, or
change ingredient units. Make and verify a backup before upgrading. Unknown or
partially constructed schemas stop startup instead of being stamped as current.

## Supported source layouts

| Source | Upgrade behavior | Regression coverage |
| --- | --- | --- |
| Archived v1.3.1 model layout | Add yeast table, optional yeast references, nullable batch size and imperial unit preference; preserve free-text yeast, TOSNA, theme and calendar fields | `test_upgrade_preserves_every_existing_value_and_is_idempotent[v1.3.1-generated]` |
| Early v1.4 without Alembic metadata | Validate all existing tables, columns, types, primary keys and relationships; add reviewed optional columns; mark baseline `eaf3a864a154` | Same test, `v1.4-unversioned` |
| Known legacy model layout with an old generated migration ID | Validate the schema first; replace only migration metadata with the committed baseline in the same transaction | Same test, `v1.4-generated` |
| Committed v1.4 baseline and published v1.4.0 image | Preserve migration metadata and data; run committed migrations normally | Same test, `v1.4-baseline`, and container upgrade script |
| Unknown tables, columns, types, relationships or partial schema | Refuse automatic repair; original schema/version remain unchanged | `test_unknown_schema_fails_without_stamping_or_mutating_data` |

The v1.3.1 case follows the model declarations in the repository's archived
`release` tag at `6445885ab1d9362e3b8115c27f6417191e62748f`,
`brew-web-1.3.1.zip`; the early v1.4 case follows the historical
models and `tests/upgrade/legacy_v1_4.sql`. These are representative schema/data
fixtures, not a promise to support every hand-edited database or historical fork.
The container test additionally opens the actual published v1.4.0 image's
database using its immutable digest from [releases](releases.md).

The bridge stamps the fixed baseline, never `head`, so a future migration cannot
be skipped merely because an old schema was imported. Existing serial sequences
are advanced to at least their highest stored ID without moving them backwards.
Existing rows and password hashes are compared before and after two startups;
the PostgreSQL tests also prove that the preserved password still authenticates
and a new recipe receives an unused ID. No schema upgrade changes PostgreSQL's
major version.

## Keep the existing Docker volume

Older Compose installations often named their data volume from the directory or
the `-p` project name. The current default project is `brewweb-docker`. Changing
that identity without selecting the old volume can produce a new, empty database
that looks like lost information. Do not initialize a new administrator to repair
this situation, delete a volume, or copy files from a running PostgreSQL volume.

Before changing the checkout, use the old installation's Compose command:

```bash
docker compose ps -q db
docker inspect EXISTING_DB_CONTAINER_ID --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}'
docker volume inspect VERIFIED_EXISTING_VOLUME_NAME
```

Use the actual container ID and volume name returned above. Confirm PostgreSQL
major version 15, download a verified backup, and stop the old installation
without `--volumes` before a different Compose project mounts the same volume.
Never run two PostgreSQL containers against one data directory.

Put `BREWWEB_DATA_VOLUME=VERIFIED_EXISTING_VOLUME_NAME` in `.env`, retaining the
original `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD` and `SECRET_KEY`.
Then include the external-volume override on **every** Compose command:

```bash
docker compose -f docker-compose.yml -f docker-compose.legacy-volume.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.legacy-volume.yml pull web db
docker compose -f docker-compose.yml -f docker-compose.legacy-volume.yml up -d --no-build
docker compose -f docker-compose.yml -f docker-compose.legacy-volume.yml ps
docker compose -f docker-compose.yml -f docker-compose.legacy-volume.yml logs --tail=100 web
```

The override requires an existing named volume. A typo fails instead of silently
creating a replacement. `verify_compose_volume.sh` checks the exact mount name,
survival after `down`, and refusal when that external volume is missing.
Bind-mounted PostgreSQL data needs its own reviewed override; do not substitute
the named-volume instructions blindly.

PostgreSQL initialization environment variables only initialize an empty data
directory. Editing `.env` does **not** reset the password inside an existing
database. Keep the old values unless intentionally changing the database role
through PostgreSQL and updating the app together. Do not expose credentials in
issues or logs. Preserve any existing non-default project/port settings.

## Verify the upgrade before normal use

1. Pin the intended numbered application image rather than `latest`. Keep the
   existing PostgreSQL 15 image/data and environment values.
2. Start the stack and confirm health, schema compatibility and successful
   migration in the web log. PostgreSQL connection waiting now stops after
   `DB_WAIT_TIMEOUT` seconds (default 60), rather than waiting indefinitely.
3. Sign in with the existing account. Check recipes and ingredients, batches,
   measurements and temperatures, calendars, custom yeasts and unit preferences.
4. Create a disposable recipe and confirm its ID does not conflict with old
   records. Delete only that disposable record after testing.
5. Create another backup and keep the pre-upgrade backup off the container host.

If startup refuses the schema or old data is absent, stop and inspect the volume,
credentials and log first. Do not use `flask db stamp head`, run generated
migrations, delete `alembic_version`, or use `docker compose down --volumes` as a
repair. Obtain project-specific assistance using schema-only details, not a
public upload of your brewing database.

## Restore a trusted backup

The administration page accepts PostgreSQL plain `.sql` and custom `.dump`
backups. Existing Brew-Web SQL backups use inserts; ordinary pg_dump COPY dumps
are also supported. Custom files are converted by `pg_restore` before touching
the database. Use PostgreSQL 15 backup tools for the supported PostgreSQL 15
database. SQL backups are executable programs: import only your own trusted
Brew-Web backups, never files received from an untrusted source.

1. Download a current backup before importing. Keep both it and the restore file
   outside the container host. Ensure sufficient disk space and maintenance time.
2. Choose the trusted file under Settings → Administration. Uploaded files use
   unique temporary names; they never overwrite an existing local backup.
3. Do not edit records while restore is running. Schema replacement, data load,
   compatibility repair and validation share one database transaction. SQL errors,
   unsupported layouts and missing administrator accounts cause rollback. A
   failed restore must report **error**, not success; existing data stays intact.
4. After success, sign out and sign in using an administrator account/password
   from the restored backup. A restore intentionally replaces newer records
   with the backed-up records; it does not merge two databases.

A transaction-scoped PostgreSQL advisory lock prevents concurrent restores or
compatibility repairs. The default deployment remains one Gunicorn worker;
local progress status is not a distributed maintenance coordinator. Keep imports
in a maintenance window and do not scale this operation across replicas.
The parser refuses transaction-control statements, arbitrary psql commands,
server-side COPY files/programs, incomplete SQL and non-pg_dump commands. Dumps
containing custom routines, extensions, database creation or hand-written repair
scripts require separate manual review; this parser is not a security sandbox.

`test_real_pg_dump_restores_all_data_relationships_and_login` covers inserts,
COPY and custom archives, Unicode/quoted content, password verification and
repeat restores. `test_failed_restore_keeps_original_database_and_revision`
covers a SQL error after destructive statements, an invalid schema, loss of the
administrator and an attempted COMMIT. A separate case covers legacy v1.3.1
restore; a lock-conflict case proves refusal before destructive SQL.

## Rollback and compatibility limits

An image downgrade is not a database rollback. Keep the old checkout/image
reference and a verified pre-upgrade backup. For rollback, stop writes, restore
that backup into a separate PostgreSQL 15 database/volume, verify it with the old
image, and switch only after checks pass. Never delete the current volume until
recovery is independently confirmed. No automatic downgrade or PostgreSQL major
upgrade is provided.

Calculator corrections change future answers only. Stored gravity, temperatures,
ABV, ingredient rates, passwords and notes are not recalculated. Recipe HTML is
sanitized when displayed and newly saved; opening an old record does not rewrite
its stored content. Existing plain text and allowed Quill formatting survive;
scripts, event handlers and unsafe links do not render. Ingredient quantity units
remain as entered even when the per-volume denominator changes to liters.

Sources: [Compose project names](https://docs.docker.com/compose/how-tos/project-name/),
[PostgreSQL image initialization](https://github.com/docker-library/docs/blob/master/postgres/README.md),
[PostgreSQL backup and restore](https://www.postgresql.org/docs/15/backup-dump.html),
and [Alembic stamp](https://alembic.sqlalchemy.org/en/latest/api/commands.html#alembic.command.stamp).
