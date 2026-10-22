# Dependency security review

Reviewed October 22, 2026. GitHub's Dependabot API reported **zero open security
alerts** and six open version-update PRs. These are different signals: a version
PR is not automatically a vulnerability alert, and zero alerts does not cover
the interpreter, OS packages, libraries inside binary wheels or manually bundled
browser assets. No alerts were dismissed to produce that result.

## Decisions

| Proposal or finding | Decision |
| --- | --- |
| PR23, build-push-action 7.4.0 | Apply its documented workflow-command-injection fix; retain the exact upstream SHA pin |
| PR26, Python image digest | Supersede the stale proposal: both old/proposed images contain Python 3.13.15. Use the verified current Python 3.13.17 Bookworm security image instead, without a Python minor/distro change |
| PR36, grouped pip updates | Apply driver 2.9.13 for parser/native-library maintenance; leave unrelated Ruff 0.17.1 and Playwright 1.64.0 updates separate |
| PR22, setup-buildx 4.4.1 | Defer this routine tooling update; no specific applicable security fix was established in this review |
| PR35/37, CodeQL 4.39.0 | Defer routine analyzer updates; existing CodeQL continues to run, but this is not a claim newer queries are unnecessary |
| Quill CVE-2025-15056 | No upstream patched release listed; retain documented format restrictions, server sanitization and targeted tests. Do not downgrade merely to hide the advisory |

## Runtime and build changes

- Python base: `python:3.13-slim-bookworm@sha256:e32be0e55814a08977501ca863271d9bd02443710db8f2afaf8372e2c4508530`.
  Official registry metadata identifies Linux/amd64 Python 3.13.17. The previous
  `ed86c8…` image and Dependabot's `2325bb…` proposal both identify Python 3.13.15.
- The [PSF's Python 3.13.17 security release](https://www.python.org/downloads/release/python-31317/)
  updates pip's CA bundle for the eMudhra/emSign incident. The intermediate
  [3.13.16 release](https://www.python.org/downloads/release/python-31316/)
  also contains security fixes. Updating installed code is defense in depth;
  this review does not claim every affected stdlib function is exposed by Brew-Web.
- Requests' CA dependency is explicitly pinned to certifi 2026.10.19. CI installs
  the PSF-recommended pip 26.2.2 wheel with SHA-256 verification before dependency
  downloads; certificate validation is never disabled and no root is added.
- psycopg2-binary 2.9.13 retains the existing driver API. Its upstream
  [changes](https://github.com/psycopg/psycopg2/releases/tag/2.9.13) fix malformed
  bytea/int64-array parsing; its build configuration refreshes native libraries.
  These maintenance fixes are not represented as a demonstrated Brew-Web exploit
  or a newly assigned psycopg2 CVE.
- [build-push-action 7.4.0](https://github.com/docker/build-push-action/releases/tag/v7.4.0)
  changes metadata logging to use the untrusted-output helper. The patch is in
  the project's actual publishing path; it does not grant extra token permissions.

## Verification and limits

The GitHub-only image inventory prints interpreter, pip, both CA bundles,
driver/libpq and system/bundled OpenSSL versions and asserts the reviewed minimums.
Do not assume binary wheels use the operating system's OpenSSL: updating the base
alone does not replace their private libraries. Native-library version reporting
is not a complete CVE scan, and the inventory does not promise the wheel contains
the newest OpenSSL branch/patch. Upstream OpenSSL advisories may concern features
not used by this application; custom external TLS/database deployments need their
own assessment. The separate [editor advisory](../../SECURITY.md#bundled-editor-advisory)
remains disclosed rather than called fixed.

Required release evidence: CI, CodeQL, runtime/CA checks, PHP absence checks,
browser journeys, 15 PostgreSQL restore/legacy cases, and data-preserving container
upgrades from both immutable published v1.4.0 and v1.4.2 images. The tag workflow
repeats CI and anonymously verifies the exact published digest before announcing
the release. The release page and linked review PR record final source/run/digest
evidence; no candidate is described as published before those checks succeed.

No PostgreSQL major upgrade, schema migration, volume/credential change or
application behavior change is intended. Keep a verified pre-upgrade backup and
retain the existing volume and credentials as described in the
[compatibility guide](../compatibility.md). Test databases and containers live
only on GitHub's disposable runner; no local Docker Desktop or user database is
used. Earlier release tags and digests must never be moved.
