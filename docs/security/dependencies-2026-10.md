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
| PR36, grouped pip updates | Apply driver 2.9.13, source-built against Debian native libraries in Linux containers; leave unrelated Ruff 0.17.1 and Playwright 1.64.0 updates separate |
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
  bytea/int64-array parsing. The first candidate's actual inventory still showed
  a private OpenSSL 3.5.8 library in its wheel. Following the
  [maintainer's production installation guidance](https://www.psycopg.org/docs/install.html),
  the Linux image instead uses `--no-binary=psycopg2-binary`, compiling against
  Debian's libpq 15/OpenSSL packages. Build headers/compiler are removed in the
  same image layer; runtime package dependencies remain. The import/API and
  requirement name stay unchanged, so ordinary local development can still use
  its platform's wheel. No PostgreSQL server-major migration is involved.
  These maintenance fixes are not represented as a demonstrated Brew-Web exploit
  or a newly assigned psycopg2 CVE.
- [build-push-action 7.4.0](https://github.com/docker/build-push-action/releases/tag/v7.4.0)
  changes metadata logging to use the untrusted-output helper. The patch is in
  the project's actual publishing path; it does not grant extra token permissions.

## Verification and limits

The GitHub-only image inventory prints interpreter, pip, both CA bundles,
driver/libpq, loaded native-library paths and Debian package versions. It refuses
private wheel library directories and a compiler remaining in the final image.
Upgrading a base alone does not replace a wheel's private native libraries;
source compilation avoids that separate update channel here. Native-library
version reporting is not a complete CVE scan: Debian backports require vendor
package-version assessment, not just comparison with upstream version strings.
Custom external TLS/database deployments need their own assessment. The separate
[editor advisory](../../SECURITY.md#bundled-editor-advisory)
remains disclosed rather than called fixed.

### Remaining Debian OpenSSL findings

The [Debian tracker](https://security-tracker.debian.org/tracker/source-package/openssl)
still lists six open issues for Bookworm's security package
`3.0.22-1~deb12u1`. Source-linking the driver does **not** fix these issues.
The [upstream advisory](https://openssl-library.org/news/secadv/20260929.txt)
and the stock deployment were reviewed separately:

| Findings | Stock Brew-Web exposure assessment |
| --- | --- |
| CVE-2026-84782 / CVE-2026-75806 | Require DTLS; the app/database use TCP, not DTLS |
| CVE-2026-77696 / CVE-2026-54872 | Require SM2 or affected generic-curve signing; Brew-Web implements neither |
| CVE-2026-75805 | Requires a particular CMP revocation operation; no CMP client is used |
| CVE-2026-35189 | Malicious TLS certificates can cause memory pressure. The app's update lookup targets a fixed GitHub HTTPS URL with certificate verification, not a user-selected server. This limits attacker access but does not patch the library or eliminate malicious-peer risk |

These are applicability assessments from source/configuration review, not exploit
tests or a clean OS audit. The default Gunicorn listener is HTTP; a custom TLS
proxy is outside this image. Custom database TLS peers, signing code, outbound
endpoints or trust stores require reassessment. Keep certificate verification
enabled and do not add untrusted roots; use trusted database endpoints. Follow
Debian's package fixes rather than replacing system crypto with an unreviewed
hand-built library. The residual certificate-memory risk remains disclosed until
a vendor fix is available for this supported distro.

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
