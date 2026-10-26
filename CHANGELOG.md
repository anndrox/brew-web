# Brew-Web Changelog

## [Unreleased]

- Update certifi to 2026.10.23, removing emSign C1/C3 trust roots; verify their
  fingerprints are absent from the actual container's requests CA store.
- Update runner-only Playwright to 1.64.1 (including its bundled Node CA security
  update) and Ruff to 0.17.2. Playwright is not installed in the application image.
- Update both CodeQL steps to the same SHA-pinned 4.39.1 release, group future
  CodeQL Dependabot updates, and test rejection of split versions/mutable pins.
- Add data-preserving upgrades from the current published v1.4.3 digest to
  candidate and future post-push checks, retaining older upgrade coverage.
- Hold merge and publication pending an official Python 3.13.18 Bookworm image
  for interpreter-level CVE-2026-115557 protection. certifi changes alone do not
  provide that protection. VERSION, released tags and images remain unchanged.

## [v1.4.3] - 2026-10-22

### Security maintenance

- Refresh the pinned Python 3.13 Bookworm image to the verified 3.13.17 security
  release; pin certifi 2026.10.19 and verify pip's bundled CA update. CI uses the
  PSF-recommended hash-pinned pip 26.2.2 wheel before dependency downloads.
- Update psycopg2-binary 2.9.12 to 2.9.13 for parser fixes. Compile the Linux
  container driver against Debian's maintained libpq/OpenSSL instead of private
  wheel libraries; remove the build compiler from the final image. No PostgreSQL
  server or schema change.
- Update SHA-pinned docker/build-push-action to 7.4.0, including its fix for
  workflow-command injection when printing build metadata.
- Review all six open Dependabot version PRs separately from security alerts;
  do not describe routine lint/browser/CodeQL updates as vulnerability fixes.
- Verify actual runtime/CA/native-library versions on GitHub and upgrade from
  both published v1.4.0 and v1.4.2 images, retaining data and repeated-startup checks.

### Security assessment

- Assess PHP CVE-2026-109618/CVE-2026-109619 against the stock v1.4.2 image and
  shared PostgreSQL/export image, with GitHub-only runtime inventory and a
  controlled detector test. No PHP patch, image replacement or data migration is
  implied: the stock application does not use PHP.
- Add PHP absence checks to candidate CI and future post-publish verification;
  publish the scoped findings and host/custom-image limitations.

## [v1.4.2] - 2026-10-11

### Release recovery

- Move the anonymous verification Docker configuration path to step-level
  environment variables, where GitHub supports the runner context.
- Add checksum-pinned actionlint 1.7.12 validation of every GitHub workflow to
  ordinary and tag-triggered CI, before publishing credentials are available.
- Publish the compatibility/reliability work below under a new version; retain
  the immutable v1.4.1 source tag. Its workflow was rejected before any jobs ran,
  so no v1.4.1 image or release page was published.

## [v1.4.1] - Unpublished source tag, 2026-10-11

### Fixed

- Validate recognized v1.3.1/v1.4 schemas before replacing old generated Alembic
  metadata, add missing batch size, retain historical values and advance serial
  sequences safely. Unknown layouts stop startup instead of being stamped as head.
- Restore trusted SQL/COPY/custom-format pg_dump backups in one transaction,
  validate schema/admin before commit, roll back on failure, coordinate restores
  with a database lock and avoid overwriting existing backup files on upload.
- Preserve remaining ingredients when first/middle rows are removed; reject
  invalid rows before replacing the original recipe/ingredients.
- Sanitize stored recipe HTML and JSON-encode editor initialization; restore
  recipe-delete CSRF protection and role-aware controls.
- Show cider and historical categories, support the viewer role label and apply
  font-size preferences. Preserve ingredient numerator units when changing rates.
- Correct gravity-point dilution, honey/sweetness/recovery estimates, hydrometer
  density correction and temperature-dependent corn-sugar estimates; document
  formula assumptions and the simplified legacy nutrient schedule.
- Cache offline update failures and notify only for newer published releases.

### Changed

- Bundle pinned Quill 2.0.3, Chart.js 4.5.1 and FullCalendar 6.1.20 with licenses;
  no runtime CDN dependency. Save semantic recipe HTML to retain list formatting.
- Add a required-existing-volume upgrade override, bounded database connection
  wait and Docker log rotation without changing PostgreSQL major or worker count.
- Gate image publishing on the full reusable GitHub CI workflow, verify version
  tags and document changed instructions alongside their regression tests.

### Verification

- Added GitHub-only PostgreSQL upgrade/restore, published-image upgrade, explicit
  volume reuse and offline browser checks. No local Docker Desktop is required.
- The 09:00 Eastern publication attempt failed workflow validation before any
  jobs started. Main CI/CodeQL passed, but that did not validate the release
  workflow. Version 1.4.2 carries the repair and the same application changes.

### Previously integrated maintenance

### Added

- CI across Python 3.11 and 3.13, dependency auditing, CodeQL analysis, and GHCR publishing.
- Dependabot configuration, issue forms, pull request template, CODEOWNERS, contribution guide,
  code of conduct, and security policy.
- A committed Alembic baseline and a compatibility path for existing v1.4 databases.
- Health check and regression tests for setup, recovery, password policy, and login throttling.

### Changed

- Pinned production and development dependencies for reproducible builds.
- Hardened the Docker image and Compose stack with a non-root user, read-only filesystem,
  localhost-only ports, required secrets, and project-scoped cleanup.
- Parameterized all PostgreSQL commands and replaced dynamic startup migrations with reviewed,
  committed migrations.
- Reworked installation, upgrade, backup, security, and development documentation.
- Clarified the project's best-effort maintenance model and recommended operational
  practices for stable installations, issue reports, and contributions.

### Fixed

- Corrected metric recipe ingredient-rate conversion so create, edit, and detail views
  round-trip without applying the gallon/liter factor twice.
- Corrected metric unit labels on batch and measurement forms and centralized volume and
  temperature conversions used by batch TOSNA and calculator paths.
- Repaired the hydrometer temperature-correction form and made its sample and calibration
  temperatures honor the selected unit system.
- Added container-upgrade regression coverage that verifies representative legacy user data
  and relationships survive compatibility repair, migration, and a second startup.
- Protected password recovery and import status endpoints from unauthenticated access.
- Restored the CSRF token in the recovery form and enabled login rate limiting.
- Fixed metric recipe conversion and persisted calculated ABV for new batches.
- Validated backup filenames and corrected legacy foreign-key repair SQL.
- Repaired the settings landing page and nested settings navigation endpoints.
- Fixed TOSNA calendar creation, day numbering, and cross-database batch date parsing.
- Removed duplicate calculator route registration and repaired calculator index links.
- Restored multi-category default yeasts without name-only deduplication.
- Protected calendar mutations with CSRF tokens and added browser security headers.

## [v1.4.0] - 2026-03-21
### Added
- Added flocculation and attenuation fields to yeast model
- Added Target ABV calculator with imperial/metric outputs.

### Maintenance (2026-03-21)
- Added global unit preference (imperial/metric) with admin setting; converted batch/forms/calculators to honor it.
- Updated calculators (honey required, volume recovery, sweetness, carbonation) to display results in the selected unit system.
- Improved ingredient row layout on New Recipe to keep spacing consistent when adding multiple rows.
- Hardened imports: background import now runs schema repairs (tables/columns), seed, and status polling page.
- Added import status page with auto-refresh and clear button.
- Entry startup now waits for DB, auto-creates database, and guards required columns.
- Updated README for `.env`/SECRET_KEY requirements and private deploy notes.
- `.gitignore` expanded (backups, logs, env, caches) and packaged zip excludes ignored files.
- Fixed password-reset redirect loop (force_reset handling) so first-time setup lands correctly.
- Expanded default yeast seed list (multi-type support)
- Locked default yeasts from deletion/editing
- Updated new/edit batch forms to reflect full yeast and recipe data
- Improved yeast selection consistency and validation

## [v1.3.1] - 2025-05-10
### Added
- TONSA additions to current batches and suggested feeding schedule and the ability to add it to the calendar
- Dynamic ingredient editing
 -Users can now:
   -See existing ingredients per gallon (looped from recipe.ingredients).
   -Add new ingredient rows dynamically with JavaScript.
   -Remove ingredients via a "❌" button.
- Ingredient indexing logic
  -JavaScript variable ingredientIndex is initialized from recipe.ingredients|length.
  -Keeps new fields indexed properly when dynamically added.
- Dropdown enhancements
  -Both alcohol_type and water_type now:
    -Show current value.
    -Pre-select the appropriate option on load.
    -Are built to be extensible if more types are added later.
### Changed
- Updated edit_recipe.html structure

### Fixed
- Calculator pages and routes
- (/) routes

## [v1.3.0] - 2025-05-09

### Added
- Full brewing calculator system:
  - ABV calculator
  - Sweetness targeting calculator
  - Dilution calculator
  - Honey required calculator
  - Carbonation calculator
  - TOSNA nutrient schedule calculator
  - Temperature correction calculator
  - Volume recovery calculator
- New `/stats` page with batch statistics
- Edit and delete functionality for recipes
- Edit batch functionality with gravity readings and honey used
- Ingredient scaling by batch size in recipe details
- Structured ingredient model and form updates
- Yeast reference page with icons and filtering
- Calendar page for alcohol-related batch events
- Settings sidebar with "Customize" and "Change Password"
- Admin-only `/setup` redirect handling
- Role-based access control (RBAC) system
- Administration page for user management
- Backup/export and import support for PostgreSQL database
- URL storage fields for to support sharing (work in progress)
- Docker Compose support with port 4452 routing and SSL proxy guidance
- `/instance/force_reset.flag` trigger for password reset/admin flow
- `settings/` template folder for modular settings UI

### Changed
- Converted unstructured recipe ingredients to structured format for scaling
- Adjusted CSS for dark/light mode readability across all views
- Reworked all calculator templates and forms for consistent UI
- Streamlined batch creation to allow optional initial gravity
- Improved layout consistency for `base.html` and all feature tabs
- Switched static routes to blueprint-aware routing
- Added flash message support to more forms
- Enforced user login and role checks on critical admin views

### Fixed
- Sidebar and navigation inconsistencies in dark/light mode
- Duplicate batch creation messages and display issues
- Visual bugs in yeast listing and batch views
- Missing calculator templates after regeneration
- Issues with batch creation when no recipes were available

## [1.2.0] - 2025-05-07

### Added
- Stats page displaying batch ABVs and frequency over time.
- Flash message when trying to create a batch without any recipes.
- Custom error pages: 403, 404, and 500 with friendly styling.
- Custom `utils.py` with `@role_required` decorator for per-role route control.
- Automatic admin role assignment on first user setup with fallback detection.
- Conditional display of top menu and navigation items based on user role.
- Flash messaging block added to `new_recipe.html` to show redirect notices.
- Brew Web logo added to top-left of UI with proper scaling and transparency.
- Admin settings page scaffolded and integrated into settings sidebar.
- User management via Administration page:
  - List current users with username, role, and admin status.
  - Create new users with selected role (`admin`, `editor`, `user`).
  - Reset user passwords.
  - Delete user accounts (with protection against deleting self).
- Role-based access control (RBAC) system:
  - New `role` field added to `User` model.
  - Decorator `@role_required(*roles)` added to enforce per-route role access.
  - Viewer access restricted from editing or creating recipes, batches, and measurements.
- First user created during `/setup` is automatically promoted to admin.
- User role shown in admin table for clarity.
- Dynamic sidebar hides "Administration" link from non-admin users.

### Fixed
- Removed hardcoded duplicate warning from `new_batch.html`.
- Improved flash message styling and visibility.
- Fixed improper route fallback causing setup logic to fail silently.
- Corrected error handling to catch batch creation issues and log them clearly.
- Brew Web logo size corrected and now responsive.
- Sidebar layout restored on `admin.html` to match other settings pages.
- CSS properly loaded by fixing static path to `/static/...`
- 403 errors correctly raised for restricted pages using `@role_required`.

### Changed
- `new_batch.html` now redirects instead of displaying a fallback block when no recipes exist.
- Sidebar logic refined to hide Administration unless role is explicitly `admin`.
- Consolidated flash message handling into layout base to avoid redundancy.
- `/recipes/new`, `/edit`, and `/delete` routes now limited to `admin` and `editor`.
- `/batches` and `/measurements` edit/delete routes restricted similarly.
- Deprecated `is_admin` use in favor of `role`, but preserved for backward compatibility.

---

## [1.1.0] - 2025-05-06

- Initial deployment of Dockerized Brew-Web app using GitHub ZIP release
- Added customizable theme (light/dark) and font size settings
- Integrated brewing calculators (ABV, sweetness, dilution, TOSNA, etc.)
- Fixed favicon appearance and reverse proxy path resolution for static assets
