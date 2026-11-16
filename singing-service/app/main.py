"""Aplicación FastAPI del microservicio de voz.

Sprint 0: scaffold + /health extendido + /docs.
Sprint 1 (HU-S1-02): /ready (readiness) + /version (metadatos de build).
Sprint 2 (HU-S1-05): /metrics Prometheus.
"""

import importlib.metadata
import logging
import os
import shutil
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.analyze import router as analyze_router
from app.core.config import settings
from app.core.log import log_event
from app.middleware.request_id import (
    RequestIDLogFilter,
    RequestIDMiddleware,
    get_request_id,
)
from app.services.preprocess import ffmpeg_version

# RNF-03: eventos estructurados de `singing.*` en stdout (una línea JSON)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("singing").addFilter(RequestIDLogFilter())

tags_metadata = [
    {
        "name": "Análisis",
        "description": "Análisis de canto: pitch, métricas, segmentos y feedback.",
    },
    {
        "name": "Salud",
        "description": "Estado del servicio y de sus dependencias (ffmpeg, librosa, disco).",
    },
    {
        "name": "Sistema",
        "description": "Metadatos y documentación del servicio.",
    },
]


@dataclass
class AppState:
    """Flags de ciclo de vida (HU-S1-02/HU-S1-03; `shutting_down` para H-04)."""

    ready: bool = False
    shutting_down: bool = False
    warmup_completed: bool = False
    warmup_duration_ms: float | None = None
    warmup_beat_track_completed: bool = False
    warmup_beat_track_duration_ms: float | None = None


app_state = AppState()


def _check_ffmpeg() -> dict:
    version = ffmpeg_version()
    return {"ok": version is not None, "version": version}


def _check_librosa() -> dict:
    try:
        import librosa

        return {"ok": True, "version": librosa.__version__}
    except Exception as exc:  # import roto o binarios incompatibles
        return {"ok": False, "version": None, "error": type(exc).__name__}


def _disk_space_mb() -> int:
    try:
        return int(shutil.disk_usage(Path.cwd()).free // (1024 * 1024))
    except OSError:
        return 0


def _pkg_version(name: str) -> str:
    """Versión instalada de un paquete; `unknown` si no está disponible."""
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def _self_test() -> bool:
    """Comprueba dependencias críticas antes de marcar `ready`."""
    return bool(_check_ffmpeg()["ok"]) and bool(_check_librosa()["ok"])


def _skip_warmup() -> bool:
    """`SKIP_WARMUP=true|1|yes|on` evita el warm-up (tests/entornos rápidos)."""
    return os.environ.get("SKIP_WARMUP", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _skip_warmup_beat() -> bool:
    """`SKIP_WARMUP_BEAT=true|1|yes|on` omite solo el warm-up de ritmo."""
    return os.environ.get("SKIP_WARMUP_BEAT", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _warmup() -> None:
    """Fuerza el JIT de `librosa.pyin` con un sine 440 Hz en memoria (HU-S1-03)."""
    started = time.perf_counter()
    try:
        import librosa
        import numpy as np

        sr = settings.sample_rate
        t = np.arange(int(0.5 * sr)) / sr
        y = (0.3 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
        f0, _voiced, _prob = librosa.pyin(
            y,
            fmin=65.0,
            fmax=1600.0,
            sr=sr,
            hop_length=settings.hop_length,
            frame_length=2048,
        )
        values = f0[np.isfinite(f0)]
        detected = float(np.median(values)) if values.size else 0.0
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        app_state.warmup_duration_ms = duration_ms
        if abs(detected - 440.0) <= 5.0:
            app_state.warmup_completed = True
            log_event(
                logging.INFO,
                "warmup_completed",
                duration_ms=duration_ms,
                detected_hz=round(detected, 2),
            )
        else:
            app_state.warmup_completed = False
            log_event(
                logging.WARNING,
                "warmup_failed",
                error=f"unexpected_hz:{detected:.2f}",
            )
    except Exception as exc:  # el servicio puede atender sin warm-up
        app_state.warmup_completed = False
        app_state.warmup_duration_ms = round(
            (time.perf_counter() - started) * 1000, 2
        )
        log_event(
            logging.WARNING,
            "warmup_failed",
            error=f"{type(exc).__name__}: {exc}",
        )


def _warmup_beat_track() -> None:
    """Fuerza el JIT de `beat_track`/`onset_detect` (HU-S1-01).

    `beat_track` compila numba en el primer uso (~10 s); sin este warm-up el
    primer `/analyze` pagaría ese coste aunque el pyin ya esté caliente.
    """
    started = time.perf_counter()
    try:
        import librosa
        import numpy as np

        sr = settings.sample_rate
        t = np.arange(int(0.5 * sr)) / sr
        y = (0.3 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
        librosa.beat.beat_track(y=y, sr=sr, hop_length=settings.hop_length)
        librosa.onset.onset_detect(
            y=y,
            sr=sr,
            hop_length=settings.hop_length,
            units="time",
            wait=5,
        )
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        app_state.warmup_beat_track_duration_ms = duration_ms
        app_state.warmup_beat_track_completed = True
        log_event(
            logging.INFO,
            "warmup_beat_track_completed",
            duration_ms=duration_ms,
        )
    except Exception as exc:  # el servicio puede atender sin este warm-up
        app_state.warmup_beat_track_completed = False
        app_state.warmup_beat_track_duration_ms = round(
            (time.perf_counter() - started) * 1000, 2
        )
        log_event(
            logging.WARNING,
            "warmup_beat_track_failed",
            error=f"{type(exc).__name__}: {exc}",
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: self-test + warm-up + ready; shutdown: flag `shutting_down` (H-04)."""
    app_state.ready = False
    app_state.shutting_down = False
    app_state.warmup_completed = False
    app_state.warmup_duration_ms = None
    app_state.warmup_beat_track_completed = False
    app_state.warmup_beat_track_duration_ms = None
    if not await run_in_threadpool(_self_test):
        log_event(logging.ERROR, "startup_self_test_failed")
        sys.exit(1)
    if _skip_warmup():
        log_event(logging.INFO, "warmup_skipped")
    else:
        await run_in_threadpool(_warmup)
        if _skip_warmup_beat():
            log_event(logging.INFO, "warmup_beat_track_skipped")
        else:
            await run_in_threadpool(_warmup_beat_track)
    app_state.ready = True
    try:
        yield
    finally:
        app_state.shutting_down = True
        app_state.ready = False


app = FastAPI(
    title="SyncDance AI — singing-service",
    description=(
        "Microservicio **stateless** de análisis de canto de SyncDance AI. "
        "Recibe un audio (`absolute`) o un audio + referencia (`comparative`) y "
        "devuelve pitch, métricas, segmentos y feedback. "
        "Sin autenticación: solo red interna de Docker (decisión del equipo). "
        "Contrato detallado para el Core: `docs/celery-contract.md`."
    ),
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    contact={"name": "SyncDance AI — Equipo 7"},
    license_info={"name": "Uso interno — SyncDance AI"},
    lifespan=lifespan,
)

app.include_router(analyze_router)
app.add_middleware(RequestIDMiddleware)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Errores HTTP tipados con `request_id` en el body y en el header."""
    rid = _request_id(request)
    detail = exc.detail
    if isinstance(detail, dict):
        content: dict = {"detail": {**detail, "request_id": rid}}
    else:
        content = {"detail": detail, "request_id": rid}
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={"X-Request-ID": rid},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 de FastAPI (validación) con `request_id` en el body."""
    rid = _request_id(request)
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors()), "request_id": rid},
        headers={"X-Request-ID": rid},
    )


@app.get(
    "/health",
    tags=["Salud"],
    summary="Liveness check con dependencias",
    description=(
        "Liveness: estado del servicio y de sus dependencias (ffmpeg, librosa, "
        "modelos y disco). Devuelve **503 `degraded`** si falta FFmpeg o librosa "
        "no carga. Para readiness usa `/ready`."
    ),
    responses={
        200: {
            "description": "Servicio sano",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "service": "singing-service",
                        "version": "0.3.0",
                        "checks": {
                            "ffmpeg": {"ok": True, "version": "7.1.5"},
                            "librosa": {"ok": True, "version": "1.0.0"},
                            "models_loaded": {"ok": True},
                            "disk_space_mb": 952675,
                            "warmup": {"ok": True, "duration_ms": 2710.5},
                            "rhythm_warmup": {"ok": True, "duration_ms": 10050.2},
                        },
                        "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        "timestamp": "2026-11-14T19:07:53.272048+00:00",
                    }
                }
            },
        },
        503: {
            "description": "Servicio degradado (falta FFmpeg o librosa no carga)",
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "singing-service",
                        "version": "0.3.0",
                        "checks": {
                            "ffmpeg": {"ok": False, "version": None},
                            "librosa": {"ok": True, "version": "1.0.0"},
                            "models_loaded": {"ok": True},
                            "disk_space_mb": 952675,
                            "warmup": {"ok": False, "duration_ms": None},
                            "rhythm_warmup": {"ok": False, "duration_ms": None},
                        },
                        "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        "timestamp": "2026-11-14T19:12:15.713759+00:00",
                    }
                }
            },
        },
    },
)
async def health() -> JSONResponse:
    """Estado del servicio y de sus dependencias (ffmpeg, librosa, disco).

    `degraded` (HTTP 503) si falta FFmpeg o librosa no carga.
    """
    ffmpeg = await run_in_threadpool(_check_ffmpeg)
    librosa = await run_in_threadpool(_check_librosa)
    checks = {
        "ffmpeg": ffmpeg,
        "librosa": librosa,
        # pyin es parte de librosa: no hay modelos externos que cargar.
        "models_loaded": {"ok": bool(librosa["ok"])},
        "disk_space_mb": await run_in_threadpool(_disk_space_mb),
        "warmup": {
            "ok": app_state.warmup_completed,
            "duration_ms": app_state.warmup_duration_ms,
        },
        "rhythm_warmup": {
            "ok": app_state.warmup_beat_track_completed,
            "duration_ms": app_state.warmup_beat_track_duration_ms,
        },
    }
    healthy = bool(ffmpeg["ok"]) and bool(librosa["ok"])
    payload = {
        "status": "ok" if healthy else "degraded",
        "service": settings.service_name,
        "version": settings.version,
        "checks": checks,
        "request_id": get_request_id(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return JSONResponse(payload, status_code=200 if healthy else 503)


@app.get(
    "/ready",
    tags=["Salud"],
    summary="Readiness probe (K8s/Docker)",
    description=(
        "Readiness: indica si el servicio puede atender tráfico. **200** cuando "
        "está listo; **503** durante `warmup`, tras `shutting_down` o si "
        "`ffmpeg_unavailable`. Diferente de `/health` (liveness)."
    ),
    responses={
        200: {
            "description": "Listo para atender",
            "content": {
                "application/json": {
                    "example": {
                        "ready": True,
                        "reason": None,
                        "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                    }
                }
            },
        },
        503: {
            "description": "No listo (warmup, shutting_down o ffmpeg_unavailable)",
            "content": {
                "application/json": {
                    "example": {
                        "ready": False,
                        "reason": "warmup",
                        "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                    }
                }
            },
        },
    },
)
async def ready() -> JSONResponse:
    """Readiness probe con `request_id` (middleware `X-Request-ID`)."""
    rid = get_request_id()
    if app_state.shutting_down:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "shutting_down", "request_id": rid},
        )
    if not app_state.ready:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "warmup", "request_id": rid},
        )
    ffmpeg = await run_in_threadpool(_check_ffmpeg)
    if not ffmpeg["ok"]:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "reason": "ffmpeg_unavailable",
                "request_id": rid,
            },
        )
    return JSONResponse(
        status_code=200,
        content={"ready": True, "reason": None, "request_id": rid},
    )


@app.get(
    "/version",
    tags=["Sistema"],
    summary="Metadatos de versión y build",
    description=(
        "Versión del servicio, commit/build inyectados en la imagen "
        "(`GIT_SHA`, `BUILD_TIME`) y versiones de runtime (debug)."
    ),
    responses={
        200: {
            "description": "Metadatos de versión",
            "content": {
                "application/json": {
                    "example": {
                        "version": "0.3.0",
                        "git_sha": "abc1234",
                        "build_time": "2026-11-15T12:00:00Z",
                        "python": "3.14.6",
                        "ffmpeg": "7.1.5",
                        "fastapi": "0.142.2",
                        "librosa": "1.0.0",
                        "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                    }
                }
            },
        }
    },
)
async def version() -> dict:
    """Metadatos de versión/build/runtime (sin crashear si falta algo)."""
    ffmpeg = await run_in_threadpool(ffmpeg_version)
    return {
        "version": settings.version,
        "git_sha": os.environ.get("GIT_SHA") or "unknown",
        "build_time": os.environ.get("BUILD_TIME") or "unknown",
        "python": sys.version.split()[0] if sys.version else "unknown",
        "ffmpeg": ffmpeg or "unknown",
        "fastapi": _pkg_version("fastapi"),
        "librosa": _pkg_version("librosa"),
        "request_id": get_request_id(),
    }


@app.get(
    "/metrics",
    tags=["Sistema"],
    summary="Métricas Prometheus",
    description=(
        "Métricas del servicio en formato Prometheus (`text/plain; version=0.0.4`). "
        "Sin autenticación: red interna, consistente con `/health`. Incluye "
        "contadores de análisis, histogramas de latencia (total, pitch, alineación "
        "y ritmo), requests activos y timeouts internos."
    ),
    response_class=Response,
    responses={
        200: {
            "description": "Métricas en formato Prometheus",
            "content": {
                "text/plain": {
                    "example": (
                        "# HELP analysis_requests_total Análisis finalizados por modo y resultado\n"
                        "# TYPE analysis_requests_total counter\n"
                        'analysis_requests_total{mode="absolute",status="success"} 1.0\n'
                    )
                }
            },
        }
    },
)
def metrics() -> Response:
    """Expone el registry Prometheus por defecto (HU-S1-05)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
