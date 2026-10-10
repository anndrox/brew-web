# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --requirement requirements.txt

RUN groupadd --gid 1000 brewweb \
    && useradd --uid 1000 --gid brewweb --create-home --shell /usr/sbin/nologin brewweb

COPY --chown=brewweb:brewweb . .

RUN mkdir -p /app/instance /app/logs /app/backups \
    && chmod +x /app/entrypoint.sh \
    && chown -R brewweb:brewweb /app

USER brewweb

EXPOSE 4452

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:4452/healthz', timeout=3)"]

ENTRYPOINT ["/app/entrypoint.sh"]
