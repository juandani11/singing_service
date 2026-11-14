"""Aplicación FastAPI del microservicio de voz.

Sprint 0: scaffold + /health extendido + /docs (contrato OpenAPI v1 híbrido).
"""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.analyze import router as analyze_router
from app.core.config import settings
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


@app.get(
    "/health",
    tags=["Salud"],
    summary="Health check con dependencias",
    description=(
        "Estado del servicio y de sus dependencias (ffmpeg, librosa, modelos y "
        "disco). Devuelve **503 `degraded`** si falta FFmpeg o librosa no carga."
    ),
    responses={
        200: {
            "description": "Servicio sano",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "service": "singing-service",
                        "version": "0.2.0",
                        "checks": {
                            "ffmpeg": {"ok": True, "version": "7.1.5"},
                            "librosa": {"ok": True, "version": "1.0.1"},
                            "models_loaded": {"ok": True},
                            "disk_space_mb": 952675,
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
                        "version": "0.2.0",
                        "checks": {
                            "ffmpeg": {"ok": False, "version": None},
                            "librosa": {"ok": True, "version": "1.0.1"},
                            "models_loaded": {"ok": True},
                            "disk_space_mb": 952675,
                        },
                        "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        "timestamp": "2026-11-14T19:12:15.713759+00:00",
                    }
                }
            },
        },
    },
)
def health() -> JSONResponse:
    """Estado del servicio y de sus dependencias (ffmpeg, librosa, disco).

    `degraded` (HTTP 503) si falta FFmpeg o librosa no carga.
    """
    ffmpeg = _check_ffmpeg()
    librosa = _check_librosa()
    checks = {
        "ffmpeg": ffmpeg,
        "librosa": librosa,
        # pyin es parte de librosa: no hay modelos externos que cargar.
        "models_loaded": {"ok": bool(librosa["ok"])},
        "disk_space_mb": _disk_space_mb(),
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
