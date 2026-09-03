# Security policy

## Supported versions

Security fixes are made against the latest release and the `main` branch.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's
[private vulnerability reporting](https://github.com/anndrox/brew-web/security/advisories/new)
and include the affected version, reproduction steps, impact, and any suggested mitigation.

Please allow a reasonable period for investigation and remediation before public disclosure.

## Deployment expectations

Brew-Web is intended to run behind an HTTPS reverse proxy. Keep the application and database
bound to trusted interfaces, use unique secrets, and take a verified database backup before upgrades.
