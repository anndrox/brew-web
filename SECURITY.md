# Security policy

## Supported versions

Security fixes are made against the latest release and the `main` branch.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's
[private vulnerability reporting](https://github.com/anndrox/brew-web/security/advisories/new)
and include the affected version, reproduction steps, impact, and any suggested mitigation.

Please allow a reasonable period for investigation and remediation before public disclosure.

## Deployment expectations

Brew-Web is intended for local self-hosted use, not an externally exposed service.
Keep application/database ports on localhost or trusted interfaces, use unique
secrets, and take a verified database backup before upgrades. If enabling LAN or
remote browser access, use HTTPS and secure cookies; this does not make the
application an audited public multi-tenant service.

Administrators may replace the database using trusted pg_dump backups. SQL dumps
are executable; do not import backups from untrusted parties. The transactional
restore protects against supported restore failures, not malicious database code.
Recipe HTML is sanitized on display and save; browser dependencies are bundled
with pinned versions. Existing inline scripts require CSP `unsafe-inline`, so a
strict nonce-based CSP remains future work. No penetration-test or zero-risk claim
is implied by passing automated checks.

## Bundled editor advisory

Quill 2.0.3 has the upstream HTML-export advisory
[CVE-2025-15056](https://github.com/advisories/GHSA-v3m3-f69x-jf25), with no upstream
patched release listed as of October 9, 2026. npm audit therefore reports a known
low-severity advisory for the bundled package; Python dependency audit results
do not cover JavaScript. Do not represent this as a clean all-language audit.

The [researcher's report](https://fluidattacks.com/advisories/diomedes) identifies
formula/video export interpolating unchecked values into HTML. Brew-Web disables
both formats using an explicit editor format allowlist. Every saved HTML fragment
and every old fragment rendered into a page/editor passes through the server's
tag/attribute/URL sanitizer, independently of client checks. Regression tests cover
the identified export payload shapes and browser rejection of video embeds.
No raw export HTML is rendered as trusted content. These are application-level
mitigations, not an upstream library patch; retain them during future updates and
revisit the dependency when a fixed release is available. Images/video/formulas
are not supported recipe instruction formats.
