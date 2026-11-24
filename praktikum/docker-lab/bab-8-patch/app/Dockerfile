# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY app/requirements.txt ./requirements.txt

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --requirement requirements.txt \
    && /opt/venv/bin/pip uninstall -y pip setuptools wheel \
    && rm -rf /opt/venv/lib/python3.11/site-packages/pip* \
              /opt/venv/lib/python3.11/site-packages/setuptools* \
              /opt/venv/lib/python3.11/site-packages/wheel* \
              /opt/venv/lib/python3.11/site-packages/_distutils_hack \
              /opt/venv/lib/python3.11/site-packages/distutils-precedence.pth \
              /opt/venv/bin/pip* \
              /opt/venv/bin/wheel*


FROM python:3.11-slim AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y zlib1g \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/local/lib/python3.11/site-packages/* \
    && rm -rf /usr/local/bin/pip* /usr/local/bin/wheel* \
    && groupadd --gid "${APP_GID}" appgroup \
    && useradd \
        --uid "${APP_UID}" \
        --gid "${APP_GID}" \
        --no-create-home \
        --shell /usr/sbin/nologin \
        appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"]

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=2", "--worker-tmp-dir=/tmp", "--access-logfile=-", "--error-logfile=-", "app:app"]
