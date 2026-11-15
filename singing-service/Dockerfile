# syntax=docker/dockerfile:1
# SyncDance AI — singing-service (plan §4 Sprint 0: multi-stage + FFmpeg)

FROM python:3.14.6-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
# build-essential: fastdtw se distribuye como sdist sin wheels (Sprint 4)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN python -m pip install --prefix=/install -r requirements.txt

FROM python:3.14.6-slim
# Metadatos de build (HU-S1-02): se exponen en GET /version.
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
ENV GIT_SHA=${GIT_SHA} \
    BUILD_TIME=${BUILD_TIME}
# FFmpeg: conversión/estándar de audio (m4a/mp3/video -> wav) — Sprint 2+
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY --from=builder /install /usr/local
WORKDIR /app
COPY app ./app
# Tests e integración dentro de la imagen para poder correr `pytest -v` en Docker.
COPY tests ./tests
COPY integration ./integration
COPY pyproject.toml ./
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health').status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

