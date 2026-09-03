# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e

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
