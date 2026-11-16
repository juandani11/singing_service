"""Endpoints del análisis vocal (contrato v1 híbrido — Sprint 0, gaps O1/O2).

`mode=absolute` (default): sin referencia; estabilidad interna, pitch medio y
voiced_ratio. `mode=comparative`: referencia por audio (`reference_audio`) o
notas JSON (`reference_notes`); comparación temporal simple (sin DTW).
"""

import asyncio
import functools
import logging
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

import librosa
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.log import log_event
from app.core.store import analysis_store
from app.metrics import (
    active_requests,
    align_duration_seconds,
    analysis_duration_seconds,
    analysis_requests_total,
    analysis_timeouts_total,
    pitch_duration_seconds,
    rhythm_duration_seconds,
)
from app.schemas.analyze import (
    AcceptedResponse,
    AnalysisMode,
    AnalysisResult,
    PitchCurves,
    Segment,
    Timings,
)
from app.services.align import align_frames, build_segments
from app.services.compare import ComparedFrame, align_by_time, parse_reference_notes
from app.services.contour import build_pitch_contour
from app.services.feedback import build_absolute_feedback, build_feedback
from app.services.metrics import absolute_metrics, comparative_metrics
from app.services.pitch import extract_pitch
from app.services.preprocess import (
    PreprocessError,
    ensure_supported_extension,
    preprocess_bytes,
    read_capped,
)
from app.services.rhythm_eval import analyze_rhythm
from app.services.scoring import compute_absolute_scores, compute_scores

router = APIRouter(prefix="/api/v1", tags=["Análisis"])

_ALLOWED_MODES = frozenset({"absolute", "comparative"})
_ALGORITHM_VERSION = "0.5.0-hybrid-modes"

# Concurrencia (Sprint 5, hardening): acota FFmpeg/pyin simultáneos.
# threading.Semaphore vía to_thread: no bloquea el event loop mientras espera
# y es seguro entre loops (uvicorn vs TestClient).
_analysis_semaphore = threading.Semaphore(settings.max_concurrent_analyses)

# HU-S1-05: executor dedicado para aplicar timeout real. `run_in_threadpool`
# (anyio) ignora la cancelación hasta que el hilo termina; un Future de
# `run_in_executor` sí se abandona al vencer `asyncio.wait_for`.
_timeout_executor = ThreadPoolExecutor(
    max_workers=max(4, settings.max_concurrent_analyses),
    thread_name_prefix="analysis-timeout",
)


def _accepted(result: AnalysisResult) -> AcceptedResponse:
    analysis_store.save(
        result.analysis_id,
        result,
        index_key=result.attempt_id,
    )
    log_event(
        logging.INFO,
        "analysis_accepted",
        analysis_id=result.analysis_id,
        attempt_id=result.attempt_id,
        routine_id=result.routine_id,
        mode=result.mode,
        algorithm_version=result.algorithm_version,
        duration_sec=result.duration_sec,
        vocal=result.scores.vocal,
        timings={
            "preprocess_ms": result.timings.preprocess_ms,
            "pitch_ms": result.timings.pitch_ms,
            "rhythm_ms": result.timings.rhythm_ms,
            "align_ms": result.timings.align_ms,
            "dtw_ms": result.timings.dtw_ms,
            "scoring_ms": result.timings.scoring_ms,
        },
    )
    return AcceptedResponse(
        analysis_id=result.analysis_id,
        status=result.status,
        mode=result.mode,
    )


def _http_error(exc: PreprocessError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _fail(attempt_id: str, code: str, message: str, status_code: int) -> HTTPException:
    log_event(
        logging.WARNING,
        "analysis_failed",
        attempt_id=attempt_id,
        code=code,
        http_status=status_code,
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


async def _run_with_timeout(
    func,
    *args,
    timeout: float,
    phase: str,
    attempt_id: str,
    **kwargs,
):
    """Ejecuta `func` en un hilo y responde 504 `ANALYSIS_TIMEOUT` al vencer.

    Limitación documentada: librosa/fastdtw no son interrumpibles. Al vencer el
    timeout el request responde y el semáforo se libera, pero el hilo huérfano
    sigue ejecutándose hasta terminar (el executor acota cuántos se acumulan).
    """
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(
        _timeout_executor, functools.partial(func, *args, **kwargs)
    )
    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except TimeoutError:
        future.cancel()
        analysis_timeouts_total.labels(phase=phase).inc()
        log_event(
            logging.WARNING,
            "analysis_timeout",
            attempt_id=attempt_id,
            phase=phase,
            timeout_sec=timeout,
        )
        raise HTTPException(
            status_code=504,
            detail={
                "code": "ANALYSIS_TIMEOUT",
                "message": f"El análisis excedió el timeout en la fase '{phase}'",
            },
        ) from None


@router.post(
    "/analyze",
    response_model=AcceptedResponse,
    status_code=202,
    summary="Analizar audio de canto",
    description="""Analiza un audio de canto y devuelve métricas de pitch, segmentos y feedback.

**Modos:**
- `absolute` (default): análisis sin referencia; `pitch_accuracy` y
  `average_cent_deviation` son `null`.
- `comparative`: compara contra `reference_audio` (o `reference_notes`); requiere
  referencia.

**Formatos:** wav, m4a, mp3, aac, ogg. **Límites:** 50 MB, 600 s.

**Ritmo (HU-S1-01):** `tempo_bpm` opcional (BPM esperado); si se envía,
`metrics.tempo_deviation_bpm` mide la desviación y `rhythm_accuracy` la incorpora.
`include_contour` sigue siendo futuro (Sprint 1).

**Respuesta:** `202 Accepted` (no 200) con `{analysis_id, status, mode}`; el
resultado completo se consulta en `GET /api/v1/analyze/{analysis_id}`.

**Ejemplo curl:**
```bash
curl -X POST http://localhost:5000/api/v1/analyze \\
  -F "audio=@test.wav" \\
  -F "attempt_id=attempt-123" \\
  -F "routine_id=routine-9" \\
  -F "mode=absolute"
```
""",
    responses={
        202: {
            "description": "Análisis aceptado; consultar el GET del resultado",
            "content": {
                "application/json": {
                    "example": {
                        "analysis_id": "8386a02e0cc8495a8d63523b3fc86b19",
                        "status": "completed",
                        "mode": "absolute",
                    }
                }
            },
        },
        400: {
            "description": "Audio o referencia inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "INVALID_AUDIO",
                            "message": "No se pudo decodificar el audio",
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
        413: {
            "description": "Excede los límites de tamaño o duración",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "AUDIO_TOO_LARGE",
                            "message": "Archivo mayor al límite de 50 MB",
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
        422: {
            "description": "`mode` inválido o campo obligatorio faltante",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "INVALID_MODE",
                            "message": "mode debe ser 'absolute' o 'comparative'",
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
        429: {
            "description": "Servicio saturado (semáforo de análisis)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "SERVICE_BUSY",
                            "message": "Servicio saturado de análisis; reintenta en unos segundos",
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
        500: {
            "description": "Falta FFmpeg en el entorno",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "FFMPEG_NOT_FOUND",
                            "message": "FFmpeg no está disponible en el entorno",
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
        503: {
            "description": (
                "No aplica a este endpoint: el 503 lo devuelve `/health` cuando el "
                "servicio está degradado."
            )
        },
        504: {
            "description": "Timeout interno de pyin o de la alineación (HU-S1-05)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "ANALYSIS_TIMEOUT",
                            "message": (
                                "El análisis excedió el timeout en la fase 'pyin'"
                            ),
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
    },
)
async def analyze(
    audio: UploadFile = File(..., description="Audio o video del intento"),
    reference_audio: UploadFile | None = File(
        default=None, description="Audio de referencia (requerido en comparative)"
    ),
    reference_notes: str | None = Form(
        default=None,
        description='Notas JSON de referencia: [{"t":0.0,"f0":440.0}, ...]',
    ),
    attempt_id: str = Form(..., min_length=1, description="Intento en el Core (idempotencia)"),
    routine_id: str = Form(..., min_length=1, description="Rutina a la que pertenece el intento"),
    mode: str = Form(
        "absolute",
        description="absolute (sin referencia) | comparative (requiere referencia)",
    ),
    tempo_bpm: float | None = Form(
        default=None,
        description="Tempo esperado en BPM (opcional); habilita tempo_deviation_bpm",
    ),
    include_contour: bool = Form(
        default=False,
        description="Incluir pitch_contour downsampleado a ~10 Hz (HU-S1-09)",
    ),
) -> AcceptedResponse:
    if mode not in _ALLOWED_MODES:
        raise _fail(
            attempt_id,
            "INVALID_MODE",
            "mode debe ser 'absolute' o 'comparative'",
            422,
        )

    if mode == "comparative" and reference_audio is None and not reference_notes:
        raise _fail(
            attempt_id,
            "MISSING_REFERENCE",
            "mode=comparative requiere 'reference_audio' o 'reference_notes'",
            400,
        )

    # Idempotencia: reintento del Core con el mismo attempt_id no duplica trabajo
    existing_id = analysis_store.get_by_index(attempt_id)
    if existing_id is not None:
        existing = analysis_store.get(existing_id)
        if existing is not None:
            log_event(
                logging.INFO,
                "analysis_idempotent_hit",
                attempt_id=attempt_id,
                analysis_id=existing_id,
                status=existing.status,
            )
            return AcceptedResponse(
                analysis_id=existing_id,
                status=existing.status,
                mode=existing.mode,
            )

    hop_ms = round(settings.hop_length / settings.sample_rate * 1000)
    max_bytes = settings.max_file_mb * 1024 * 1024
    is_comparative = mode == "comparative"

    started = time.perf_counter()
    status = "error"
    active_requests.inc()
    try:
        acquired = await asyncio.to_thread(
            _analysis_semaphore.acquire, True, settings.busy_timeout_sec
        )
        if not acquired:
            raise _fail(
                attempt_id,
                "SERVICE_BUSY",
                "Servicio saturado de análisis; reintenta en unos segundos",
                429,
            )
        try:
            ensure_supported_extension(audio.filename)
            data = await read_capped(audio, max_bytes)

            reference_data = None
            if is_comparative and reference_audio is not None:
                ensure_supported_extension(reference_audio.filename)
                reference_data = await read_capped(reference_audio, max_bytes)

            preprocess_start = time.perf_counter()
            with tempfile.TemporaryDirectory(prefix="syncdance-") as tmp:
                tmp_dir = Path(tmp)
                student = await run_in_threadpool(
                    preprocess_bytes, data, audio.filename, tmp_dir=tmp_dir, name="student"
                )

                reference = None
                reference_notes_points = None
                if reference_data is not None:
                    reference = await run_in_threadpool(
                        preprocess_bytes,
                        reference_data,
                        reference_audio.filename,
                        tmp_dir=tmp_dir,
                        name="reference",
                    )
                elif is_comparative and reference_notes:
                    try:
                        reference_notes_points = parse_reference_notes(reference_notes)
                    except ValueError as exc:
                        raise PreprocessError(
                            "INVALID_REFERENCE_NOTES", str(exc), 400
                        ) from exc
                preprocess_ms = int((time.perf_counter() - preprocess_start) * 1000)

                pitch_start = time.perf_counter()
                student_pitch = await _run_with_timeout(
                    extract_pitch,
                    student.path,
                    timeout=settings.pyin_timeout_seconds,
                    phase="pyin",
                    attempt_id=attempt_id,
                    hop_length=settings.hop_length,
                )
                reference_pitch = None
                if reference is not None:
                    reference_pitch = await _run_with_timeout(
                        extract_pitch,
                        reference.path,
                        timeout=settings.pyin_timeout_seconds,
                        phase="pyin",
                        attempt_id=attempt_id,
                        hop_length=settings.hop_length,
                    )
                pitch_ms = int((time.perf_counter() - pitch_start) * 1000)
                pitch_duration_seconds.observe(pitch_ms / 1000.0)

                compare_start = time.perf_counter()
                reference_points = (
                    reference_pitch.points
                    if reference_pitch is not None
                    else reference_notes_points
                )
                alignment_method = "time"
                if is_comparative and reference_points:
                    try:
                        aligned = await _run_with_timeout(
                            align_frames,
                            student_pitch.points,
                            reference_points,
                            timeout=settings.align_timeout_seconds,
                            phase="align",
                            attempt_id=attempt_id,
                        )
                        alignment_method = "fastdtw"
                    except HTTPException:
                        # Timeout de alineación: 504, no fallback silencioso.
                        raise
                    except Exception as exc:
                        log_event(
                            logging.WARNING,
                            "align_fastdtw_failed",
                            error=f"{type(exc).__name__}: {exc}",
                        )
                        tolerance = max(hop_ms / 1000.0 * 2.0, 0.1)
                        aligned = align_by_time(
                            student_pitch.points,
                            reference_points,
                            tolerance_sec=tolerance,
                        )
                else:
                    aligned = [
                        ComparedFrame(cents=None, ref_f0=None)
                        for _ in student_pitch.points
                    ]
                align_ms = int((time.perf_counter() - compare_start) * 1000)
                dtw_ms = align_ms
                align_duration_seconds.labels(method=alignment_method).observe(
                    align_ms / 1000.0
                )

                rhythm_start = time.perf_counter()
                rhythm_y, _ = await run_in_threadpool(
                    librosa.load,
                    str(student.path),
                    sr=settings.sample_rate,
                    mono=True,
                )
                rhythm = await run_in_threadpool(
                    analyze_rhythm,
                    rhythm_y,
                    settings.sample_rate,
                    tempo_bpm_hint=tempo_bpm,
                )
                rhythm_ms = int((time.perf_counter() - rhythm_start) * 1000)
                rhythm_duration_seconds.observe(rhythm_ms / 1000.0)

                scoring_start = time.perf_counter()
                segments = build_segments(
                    student_pitch.points,
                    aligned,
                    hop_ms=hop_ms,
                    duration_sec=student.duration_sec,
                    cent_threshold=settings.cent_threshold,
                )
                if rhythm.feedback_items:
                    segments = sorted(
                        [
                            *segments,
                            *(Segment(**item) for item in rhythm.feedback_items),
                        ],
                        key=lambda segment: segment.start,
                    )
                if is_comparative:
                    metrics = comparative_metrics(
                        student_pitch.points,
                        aligned,
                        cent_threshold=settings.cent_threshold,
                    )
                    scores = await run_in_threadpool(
                        compute_scores,
                        cents=[f.cents for f in aligned],
                        points=student_pitch.points,
                        silence_pct=student_pitch.silence_pct,
                        student_wav=student.path,
                        hop_length=settings.hop_length,
                        sample_rate=settings.sample_rate,
                        cent_threshold=settings.cent_threshold,
                    )
                    feedback = build_feedback(
                        segments, duration_sec=student.duration_sec
                    )
                else:
                    metrics = absolute_metrics(student_pitch.points)
                    scores = await run_in_threadpool(
                        compute_absolute_scores,
                        points=student_pitch.points,
                        silence_pct=student_pitch.silence_pct,
                        student_wav=student.path,
                        hop_length=settings.hop_length,
                        sample_rate=settings.sample_rate,
                        cent_threshold=settings.cent_threshold,
                    )
                    feedback = build_absolute_feedback(
                        student_pitch.points,
                        segments=segments,
                        stability_cents=metrics.pitch_stability_cents,
                        duration_sec=student.duration_sec,
                    )
                metrics = metrics.model_copy(
                    update={
                        "rhythm_accuracy": rhythm.rhythm_accuracy,
                        "estimated_tempo_bpm": rhythm.estimated_tempo_bpm,
                        "onset_count": rhythm.onset_count,
                        "onset_stability": rhythm.onset_stability,
                        "tempo_deviation_bpm": rhythm.tempo_deviation_bpm,
                        "alignment_method": alignment_method,
                    }
                )
                scores = scores.model_copy(
                    update={
                        "ritmo": (
                            int(round(rhythm.rhythm_accuracy))
                            if rhythm.rhythm_accuracy is not None
                            else None
                        )
                    }
                )
                scoring_ms = int((time.perf_counter() - scoring_start) * 1000)

                pitch_contour = None
                if include_contour:
                    pitch_contour = build_pitch_contour(
                        student_pitch.points,
                        reference_points,
                        hop_ms=hop_ms,
                    )
        except PreprocessError as exc:
            raise _http_error(exc) from exc
        except HTTPException as exc:
            # Errores tipados que no dependen de FFmpeg (p. ej. AUDIO_TOO_LARGE)
            code = exc.detail.get("code") if isinstance(exc.detail, dict) else None
            log_event(
                logging.WARNING,
                "analysis_failed",
                attempt_id=attempt_id,
                code=code,
                http_status=exc.status_code,
            )
            raise
        finally:
            _analysis_semaphore.release()

        reference_curve = (
            reference_pitch.points
            if reference_pitch is not None
            else reference_notes_points
        )
        response = _accepted(
            AnalysisResult(
                analysis_id=uuid.uuid4().hex,
                attempt_id=attempt_id,
                routine_id=routine_id,
                status="completed",
                mode=cast(AnalysisMode, mode),
                algorithm_version=_ALGORITHM_VERSION,
                duration_sec=student.duration_sec,
                pitch=PitchCurves(
                    student=student_pitch.points,
                    reference=reference_curve if is_comparative else None,
                    hop_ms=hop_ms,
                ),
                pitch_contour=pitch_contour,
                segments=segments,
                scores=scores,
                metrics=metrics,
                feedback=feedback,
                timings=Timings(
                    preprocess_ms=preprocess_ms,
                    pitch_ms=pitch_ms,
                    rhythm_ms=rhythm_ms,
                    align_ms=align_ms,
                    dtw_ms=dtw_ms,
                    scoring_ms=scoring_ms,
                ),
            )
        )
        status = "success"
        return response
    finally:
        active_requests.dec()
        analysis_duration_seconds.labels(mode=mode).observe(
            time.perf_counter() - started
        )
        analysis_requests_total.labels(mode=mode, status=status).inc()


@router.get(
    "/analyze/{analysis_id}",
    response_model=AnalysisResult,
    summary="Obtener el resultado de un análisis",
    description="""Devuelve el `AnalysisResult` completo de un análisis previo.

Incluye `pitch` (curvas F0), `segments`, `scores`, `metrics`, `feedback` y
`timings`. En `mode=absolute`, `pitch.reference`, `pitch_accuracy` y
`average_cent_deviation` son `null`; `rhythm_accuracy` puede ser número si hay
onsets (HU-S1-01).

El resultado vive en memoria con TTL de 1 h; si expiró, relanzar el `POST` con el
mismo `attempt_id`.
""",
    responses={
        200: {
            "description": "Resultado del análisis",
            "content": {
                "application/json": {
                    "example": {
                        "analysis_id": "8386a02e0cc8495a8d63523b3fc86b19",
                        "attempt_id": "attempt-123",
                        "routine_id": "routine-9",
                        "status": "completed",
                        "mode": "absolute",
                        "algorithm_version": "0.5.0-hybrid-modes",
                        "duration_sec": 5.0,
                        "pitch": {
                            "student": [{"t": 0.0, "f0": 439.8, "voiced": True}],
                            "reference": None,
                            "hop_ms": 32,
                        },
                        "segments": [],
                        "scores": {
                            "vocal": 99,
                            "afinacion": 100,
                            "estabilidad": 100,
                            "control_volumen": 97,
                            "ritmo": 94,
                            "silence_pct": 0,
                        },
                        "metrics": {
                            "pitch_stability_cents": 0.0,
                            "mean_pitch_hz": 439.8,
                            "voiced_ratio": 1.0,
                            "pitch_accuracy": None,
                            "rhythm_accuracy": 93.9,
                            "estimated_tempo_bpm": 117.2,
                            "onset_count": 10,
                            "onset_stability": 93.9,
                            "tempo_deviation_bpm": None,
                            "average_cent_deviation": None,
                        },
                        "feedback": [],
                        "timings": {
                            "preprocess_ms": 762,
                            "pitch_ms": 289,
                            "rhythm_ms": 31,
                            "dtw_ms": 0,
                            "scoring_ms": 8,
                        },
                    }
                }
            },
        },
        404: {
            "description": "Análisis inexistente o expirado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": "ANALYSIS_NOT_FOUND",
                            "message": (
                                "Análisis inexistente o expirado; relanza el "
                                "POST /analyze"
                            ),
                            "request_id": "7c1f0b2e9a4d4f6b8c3e5a1d2f4b6c8e",
                        }
                    }
                }
            },
        },
        422: {"description": "Parámetro inválido"},
    },
)
def get_analysis(analysis_id: str) -> AnalysisResult:
    result = analysis_store.get(analysis_id)
    if result is None:
        log_event(
            logging.INFO,
            "analysis_not_found",
            analysis_id=analysis_id,
            http_status=404,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "code": "ANALYSIS_NOT_FOUND",
                "message": "Análisis inexistente o expirado; relanza el POST /analyze",
            },
        )
    return result
