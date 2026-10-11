# Container releases

GitHub Actions publishes the public image at `ghcr.io/anndrox/brew-web` when a
version tag matching `v*` is pushed. Ordinary CI builds images but does not publish
them. No application deployment is performed by the publishing workflow.

Every tag now runs the complete reusable CI workflow before the registry login
or image push. The tag must exactly match `v` plus the source `VERSION`. Candidate
v1.4.1 remains on a separate branch until the authorized October 11, 2026
09:00 Eastern publication window. See [release gates](testing.md#release-timing).

## Verified release: v1.4.0

- Source: `891daf0011082548cba5e188ed1b8c5177a267fa`.
- [Publishing run](https://github.com/anndrox/brew-web/actions/runs/34243674520): passed.
- [Release](https://github.com/anndrox/brew-web/releases/tag/v1.4.0).
- Tags: `1.4.0`, `1.4`, and `latest`.
- Platform: `linux/amd64`; native ARM64 images are not currently published.
- Immutable image reference:
  `ghcr.io/anndrox/brew-web@sha256:903a350b742d817885a62f6ca17d67afe99ff8a997aa3bc8bddd87095def7f73`.

On 2026-09-08, anonymous registry access returned HTTP 200 and Docker pulled the
image with an empty credential configuration. The repository Compose file started
the downloaded image with `--no-build` in a separate temporary project using fresh
PostgreSQL data and temporary localhost ports. Both containers became healthy.
Database migrations reached `eaf3a864a154` (head). CSRF-protected first-admin setup,
login, home, recipes, batches, calculators, and settings returned successful responses.
The web container ran as `brewweb` with a read-only root filesystem. The test
containers, network, database volume, and temporary files were removed afterward.
This verifies a fresh installation; it is not an exhaustive upgrade or feature test.

## Publishing future releases

1. Select a reviewed source commit with passing CI, CodeQL, PostgreSQL restore,
   published-image upgrade, volume reuse and browser checks. Keep `VERSION` and
   release notes consistent with the chosen version. Review the detailed
   [compatibility instructions](compatibility.md) for user data preservation.
2. Push a new semantic version tag, such as `v1.4.1`, at that exact commit.
   This triggers `.github/workflows/publish.yml`; a release page alone does not
   substitute for the tag-push trigger. Never move an already published version tag.
3. Wait for the publishing workflow to succeed, and record the resulting digest.
4. On a GitHub runner, verify anonymous image access and an isolated installation using `docker compose pull web db`
   followed by `docker compose up -d --no-build`. Check setup and migrations in an
   isolated test database before recommending an upgrade. Do not start local
   Docker Desktop or attach an existing user's volume for release validation.
   The publishing workflow automatically checks anonymous pull of its exact
   output digest and runs isolated startup/data-preserving upgrade tests with
   that published image. A failed post-push check blocks release-page publication;
   it cannot undo an already pushed image, so do not move the version tag or
   describe that release as verified until the failure is resolved.
5. Publish the matching GitHub release page with notes, supported platforms, image
   reference, and backup guidance. If GHCR creates a new package as private, its
   owner must make the package public before advertising anonymous installation.

The workflow uses GitHub's job-scoped `GITHUB_TOKEN` with `packages: write`, rather
than a stored personal access token. It emits image provenance and an SBOM. It
runs on GitHub's hosted runner; this does not grant Docker socket access or image
publishing authority to the separate Forgejo runner.

Ordinary pull-request CI builds the candidate image and runs
`tests/upgrade/verify_container_upgrade.sh` against ephemeral PostgreSQL. The test
seeds representative v1.4 data, exercises both the one-time compatibility path and
the actual published v1.4.0 image's database followed by an idempotent candidate
startup, and fails if data, relationships, compatibility
columns, or the expected Alembic revision are missing. The containers, network,
and database volume are runner-local and removed after the job.

Thanks to [jrhedman](https://github.com/jrhedman) for proposing release image
publishing and identifying the missing user-facing release in
[PR #5](https://github.com/anndrox/brew-web/pull/5).
