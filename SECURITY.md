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
