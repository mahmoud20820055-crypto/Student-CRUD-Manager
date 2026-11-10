# syntax=docker/dockerfile:1

# ---------- Stage 1: builder - install dependencies into a virtualenv ----------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
# Optional build secret "pip_ca": a CA bundle for builds behind a TLS-intercepting
# proxy. Never stored in an image layer; normal builds simply skip it.
RUN --mount=type=secret,id=pip_ca,required=false \
    if [ -f /run/secrets/pip_ca ]; then export PIP_CERT=/run/secrets/pip_ca; fi; \
    pip install -r requirements.txt

# ---------- Stage 2: test - run the test suite (docker build --target test .) ----------
FROM builder AS test
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN --mount=type=secret,id=pip_ca,required=false \
    if [ -f /run/secrets/pip_ca ]; then export PIP_CERT=/run/secrets/pip_ca; fi; \
    pip install -r requirements-dev.txt
COPY src/ ./src/
COPY tests/ ./tests/
RUN python -m pytest -q tests

# ---------- Stage 3: runtime - small final image, no build tools ----------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Student CRUD Manager" \
      org.opencontainers.image.description="Flask + SQLite app for managing student records" \
      org.opencontainers.image.source="https://github.com/mahmoud20820055-crypto/Student-CRUD-Manager"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    DATABASE_PATH=/app/data/students.db \
    GUNICORN_WORKERS=2

# Unprivileged user that owns the data directory
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app src/ ./src/
RUN mkdir -p /app/data && chown app:app /app/data

USER app
EXPOSE 8000
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=2).status == 200 else 1)"

# Shell form via sh -c so ${PORT}/${GUNICORN_WORKERS} are expanded; exec keeps gunicorn as PID 1
CMD ["sh", "-c", "exec gunicorn --chdir src --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS} --access-logfile - wsgi:app"]
