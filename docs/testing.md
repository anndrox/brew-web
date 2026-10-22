# Verification and release gates

Use GitHub hosted runners for all project container checks. Do not start Docker
Desktop on the maintainer's computer. Local checks are Python lint, unit tests
and dependency auditing; the PostgreSQL/Compose/image tests run on GitHub with
disposable data and test-only credentials.

## Changed behavior and coverage

| Behavior | Automated evidence |
| --- | --- |
| Sparse ingredient indices after deleting the first/middle row | `test_removed_first_or_middle_ingredient_does_not_truncate` |
| Invalid edits preserve original recipe and ingredients | `test_invalid_recipe_edit_retains_all_original_data` |
| Legacy recipe markup is safe without rewriting storage | `test_instructions_sanitize_old_rows_without_rewriting_storage` |
| Recipe deletion needs CSRF and read-only users see no edit controls | `test_delete_recipe_csrf_and_viewer_controls`, viewer/category test |
| Cider/custom-category visibility, viewer alias and font preference | `test_viewer_alias_remains_read_only_and_categories_visible` |
| Formula corrections and metric equivalence | Calculator reference/invalid-input tests and existing storage round-trip tests |
| Offline update failures are cached; notifications use published releases | `test_update_check_uses_releases_and_caches_failures` |
| Chart, editor and calendar assets are local and load only where needed | `test_stats_with_dates_and_static_assets_are_local`; browser smoke test |
| Legacy values, hashes, IDs, relations, null volume and serial sequence safety | PostgreSQL upgrade matrix and container upgrade script |
| Real inserts/COPY/custom pg_dump restore and invalid-restore rollback | PostgreSQL restore matrix, lock-conflict and original-revision assertions |
| Correct volume reuse, preservation by down, missing-volume refusal | `tests/upgrade/verify_compose_volume.sh` |
| Bounded connection wait refuses an unreachable database | Startup failure case in `verify_container_upgrade.sh` |
| Bundled browser files match their documented immutable hashes | `test_bundled_vendor_assets_match_documented_hashes` |
| Quill formula/video export payloads never render as executable markup | `test_quill_export_advisory_payloads_are_sanitized_on_save_and_display` and browser format/paste checks |

See [compatibility](compatibility.md) for the supported schema profiles and
[calculators](calculators.md) for formulas and operational limits.

## Local Python checks

```bash
python -m pip install -r requirements-dev.txt
ruff check .
python -m pytest
pip-audit -r requirements.txt
```

Without `BREWWEB_TEST_POSTGRES`, integration tests explicitly skip. That variable
is for a disposable runner service with permission to create/drop test databases;
never point it at an existing user database. The normal unit-test fixture uses
in-memory SQLite and temporary import status files. No local Docker is required.

## GitHub checks

The GitHub workflow-validation job verifies all `.github/workflows/*.yml` files
using actionlint 1.7.12's checksum-pinned Linux binary. This checks context
availability, expressions and workflow structure; Python lint/tests alone do
not cover these. Optional shellcheck/pyflakes integrations are disabled so this
gate is specifically the workflow validator, alongside the existing Ruff gate.

For the October 11 recovery, actionlint was intentionally run against the exact
old v1.4.1 publishing workflow: it exited 1 at line 63 with `context "runner" is
not allowed here`. It then exited 0 against all corrected GitHub workflows.
That deliberate validator regression check is separate from the original failed
publication, which was an unintended workflow defect. The CI job repeats the
all-workflow check and is part of the reusable tag-validation gate.

CI runs Python 3.11/3.13, Ruff, Pytest and the dependency audit; a PostgreSQL 15
service executes real backup/restore tests in uniquely named temporary databases.
The container job validates Compose, checks volume identity, builds the candidate
without publishing, and proves published-v1.4.0 and unversioned database upgrade
paths with a second candidate startup. Containers/networks/volumes are confined
to the GitHub runner and cleaned up. CodeQL analyzes application Python.

The PostgreSQL tests also preserve pooled connection settings across restore,
and verify that a renamed sequence containing quotes is handled safely and is
never moved backwards. The browser journey creates the first administrator,
logs out/in, creates and edits rich-text recipes with bullet formatting, removes
the first ingredient, adds a batch, renders charts and saves a calendar event
with remote browser requests blocked.

The publishing workflow now calls the same CI workflow and cannot access its
registry publishing token until validation succeeds. It verifies the tag matches
`VERSION` before pushing the image. Ordinary branch/PR checks do not publish
images, attach release artifacts or deploy any application.

Forgejo's safe Python preflight and its runner isolation boundary are unchanged.
Docker/Compose checks are not moved onto the Forgejo runner and remain deferred
there pending a separately approved isolated-builder design. No host socket,
privileged mode, host execution or runner infrastructure change is required.

## Candidate verification record

On October 9, 2026, implementation SHA
`56384bfc70f44cf9f9d35054428953d3ff988243` passed
[CI run 37927305398](https://github.com/anndrox/brew-web/actions/runs/37927305398)
and [CodeQL run 37927305476](https://github.com/anndrox/brew-web/actions/runs/37927305476).
Python 3.11 and 3.13 each passed 61 tests; their 15 integration skips were run
separately against PostgreSQL 15, where all 15 passed. Ruff, the production Python
dependency audit, the offline Chromium journey, Compose volume checks and image
upgrade checks passed. The Python audit reported no known vulnerabilities;
the separate browser audit still has the documented Quill advisory below.

Intentional negative tests included an unreachable database startup, invalid
restore input, incompatible schemas and concurrent restore refusal. They passed
by detecting the expected failure and preserving the disposable original data.
Earlier failed integration runs exposed real compatibility/test-environment
issues; they are not reclassified as deliberate failure tests.

The final candidate must also pass checks after documentation/release-gate edits.
Its exact SHA and final run links are recorded in
[PR #31](https://github.com/anndrox/brew-web/pull/31). The v1.4.1 publishing workflow
failed validation before any jobs ran; there is no published v1.4.1 image.
The v1.4.2 recovery workflow performs an
anonymous digest-pinned pull and isolated upgrade checks after pushing, and must
finish successfully before the GitHub release page is published.

## Release timing

The original publication window began Sunday October 11, 2026 at 09:00
America/New_York (13:00 UTC, EDT). After the v1.4.1 workflow failure, the owner
approved recovery on `codex/release-workflow-repair` and publication as v1.4.2.
Do not merge unrelated Dependabot branches, move the existing v1.4.1 tag, or
deploy users' installations. There is no additional scheduled delay for recovery.

Publication requires the exact candidate SHA's CI (including workflow validation)
and CodeQL checks to pass and
the completed documentation to be synchronized with the branch. After the
authorized squash merge, main's checks must pass before tagging the merge SHA.
Tag-triggered CI runs again before image publication. Publish the release page
only after that workflow succeeds; record its immutable digest and verification
result. A scheduler wake-up starts this process at 09:00; builds and checks take
additional time, so public image availability is later than the initial wake-up.

If checks fail, a tag already exists, or unrelated/conflicting changes would be
included, stop publication and report the owner decision needed. The local Codex
scheduled task needs the computer powered on, the app running, and GitHub access.
It is not a production deployment scheduler.

## Dependency audit scope

For v1.4.3, candidate and anonymous post-publish checks also execute
`tests/security/runtime_versions.py` inside the actual image. It asserts Python
3.13.17+, driver 2.9.13+, Debian libpq 15.19+, pip 26.2.2+ and both pip/requests
CA bundles at least 2026.10.19. It records mapped native-library paths and Debian
package versions, refuses private wheel libraries and checks that the build
compiler is absent. The PostgreSQL/browser job compiles the same driver against
the same base distribution, rather than testing only the prebuilt wheel.
These checks do not replace distribution-native vulnerability assessment.
CI first installs the hash-pinned PSF-recommended pip wheel, without weakening TLS.
Image upgrade checks run independently from immutable v1.4.0 and v1.4.2 sources;
both retain the unversioned-schema and repeated-startup cases. All such containers
and databases remain disposable GitHub-hosted runner resources.

PHP exposure checks are separate from Python dependency auditing. The manual/PR
`PHP exposure assessment` workflow checks the exact released v1.4.2 web image and
the pinned PostgreSQL image shared by `db`/`export`. Candidate builds and future
published images also run `tests/security/verify_no_php.sh`. The detector checks
commands, installed packages and known runtime filenames inside an ephemeral,
read-only, network-disabled, unprivileged container with no host data mounts.
Its deliberate failure test adds only a harmless temporary command marker in a
separate disposable container. No vulnerable PHP package or exploit is installed.
Results are recorded in job logs, not uploaded artifacts. See the
[PHP assessment](security/php-2026-10.md) for the scope and limitations.

pip-audit checks Python production requirements. A separate npm audit of the
three pinned browser packages reports Quill's known low-severity
CVE-2025-15056; the application's mitigations and their tests are documented in
[SECURITY.md](../SECURITY.md#bundled-editor-advisory). Do not silently suppress this
finding, claim Quill is patched, or interpret an unflagged older version as proof
of a fix. Review new browser advisories before publication and stop if a new
finding is not covered by a reviewed mitigation or a compatible patched version.
