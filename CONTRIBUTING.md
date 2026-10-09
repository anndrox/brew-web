# Contributing

Thank you for improving Brew-Web.

Brew-Web is maintained on a best-effort basis and does not have a guaranteed
review schedule or active feature roadmap. Focused fixes with clear reproduction
steps and tests are the easiest contributions to review. Please keep discussion
constructive and allow time for a response.

## Development setup

1. Fork and clone the repository.
2. Create `.env` from `.env.example` and replace both placeholder secrets.
3. Create a focused branch from `main`.
4. Install development dependencies with `python -m pip install -r requirements-dev.txt`.
5. Run `ruff check .` and `pytest` before opening a pull request.
6. Validate container changes with `docker compose config --quiet` and `docker compose build`.

Keep pull requests focused, link the issue they address, document user-visible
changes, and call out schema or upgrade impacts. Add a regression test for bug
fixes whenever practical. Never commit `.env`, database dumps, logs, credentials,
or personal brewing data.

Security reports belong in GitHub private vulnerability reporting, not public issues.
