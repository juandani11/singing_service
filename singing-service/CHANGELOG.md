# Changelog

Todos los cambios notables de `singing-service` se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versionado [SemVer](https://semver.org/lang/es/).

## [0.3.0-dev] — 2026-11-15

### Añadido

- `GET /ready` (readiness: `warmup`, `shutting_down`, `ffmpeg_unavailable`).
- `GET /version` (version, git_sha, build_time, python, ffmpeg, fastapi, librosa).
- `app_state` + lifespan con self-test de arranque y flag `shutting_down`.
- Dockerfile `ARG/ENV GIT_SHA/BUILD_TIME`; compose `build.args`.
- Warm-up de `librosa.pyin` en lifespan (sine 440 Hz en memoria) para mitigar el JIT.
- `SKIP_WARMUP` (default `false`) para omitir el warm-up.
- `/health` `checks.warmup` (`{"ok": bool, "duration_ms": float|null}`), aditivo.
- `rhythm_eval` real: `beat_track` (tempo, hop 960 = 60 ms) +
  `onset_detect(wait=5)` (onsets) + filtro del onset artificial <50 ms.
  Downsamples a 8 kHz descartado: rompía ruido/tempo; MASTmelody ~1.5 s local /
  ~3.8 s Docker con hop 960 (documentado).
- `rhythm_accuracy` deja de ser siempre `null` (número si hay onsets).
- Warm-up extendido: `beat_track`/`onset_detect` + `SKIP_WARMUP_BEAT`; `/health`
  `checks.rhythm_warmup`; log `warmup_beat_track_completed`.
- Campos aditivos: `scores.ritmo`, `metrics.estimated_tempo_bpm`,
  `metrics.onset_count`, `metrics.onset_stability`, `metrics.tempo_deviation_bpm`,
  `timings.rhythm_ms`, `tempo_bpm` (form).
- FastDTW (`align_frames`) cableado en `mode=comparative`; fallback
  `align_by_time` si falla.
- `metrics.alignment_method` (`"fastdtw"` | `"time"`) y `timings.align_ms`
  (aditivos; `dtw_ms` se mantiene como alias).
- MASTmelody `pitch_accuracy` 20.7→44.4; `average_cent_deviation` 153.9→92.9;
  offset 200 ms alineado (>80). La calibración de umbrales es HU-S4-XX.
- Tests de integración (`@pytest.mark.integration`) para MASTmelody y worker 5xx;
  `pytest` por defecto 115; `pytest -m integration` 3 (local) / 1+2 skipped (Docker).
- `tests/test_hu_s1_02.py` (9), `tests/test_hu_s1_03.py` (8),
  `tests/test_hu_s1_01.py` (13) y `tests/test_hu_s1_04.py` (5);
  total 115 por defecto + 3 integración (118).

### Cambiado

- `settings.version` 0.2.0 → 0.3.0.
- `/health` ahora `async def` + `run_in_threadpool` (mismo shape + `checks.warmup`
  y `checks.rhythm_warmup`).

### Documentación

- `docs/celery-contract.md` §2 (`tempo_bpm`), §3 (JIT/startup y nota de latencia
  `rhythm_eval`), §4 (ritmo y alineación aditivos) y §4.1; `docs/USAGE.md`;
  `docs/ARCHITECTURE.md` §6.1, §6.2 y §7; `Docs/scoring.md` §Ritmo, §Feedback y
  FastDTW cableado; `docs/SPRINT1_BACKLOG.md` HU-S1-04 ✅ y HU-S2-XX;
  `CIERRE_HU_S1_01.md` §Limitaciones conocidas.

## [Unreleased]

### Documentación

- Nota C en `docs/celery-contract.md` §4: cardinalidad de `feedback` (1 por tipo, no por segmento).
- Deuda técnica B documentada en `docs/SPRINT1_BACKLOG.md`: recalibrar `scores.estabilidad` en Sprint 4 con datos reales.

## [0.2.2] — 2026-11-14

### Añadido

- Middleware `X-Request-ID`: header en todas las respuestas, `request_id` en body de
  errores y logs JSON.
- Código de error `UNHANDLED_ERROR` (500) con `logging.exception` y `request_id`.
- `/health` incluye `request_id`.
- 5 tests nuevos (`test_request_id.py`).
- 7 tests nuevos de handlers/cobertura (`test_exception_handlers.py`).
- Nota V-01 en contrato §5 (Content-Length inválido rechazado por uvicorn).
- `UNHANDLED_ERROR` en tabla de errores del contrato.

### Documentación

- `docs/USAGE.md`: sección de errores ampliada con V-01 y `UNHANDLED_ERROR`.
- `docs/celery-contract.md` §5: nota V-01 + `UNHANDLED_ERROR`.

### Verificación

- 83 tests, 97% cobertura, ruff OK.
- `verify_handoff.sh` 4/4 HANDOFF OK.
- Sin repo git: fingerprint de referencia `v0.2.2` =
  `821a796d9f6e27e49b1a22c35319ba0fe227600ed90c5defb4b05bece31e92ae` (árbol
  `singing-service/`, excluye `.venv`, caches, `integration/fixtures` y este
  `CHANGELOG.md`).

### Verificaciones de lectura

- V-01 (Content-Length falso): `400` text/plain de uvicorn antes del middleware; sin
  `X-Request-ID` → **P1 documentado**.
- V-02 (500 real): logs con traceback; body JSON sin stack → **OK**.
- V-03 (NaN): JSON válido con `mean_pitch_hz=null` y `scores.vocal=0` → **OK**.

## [0.2.1] — 2026-11-14 — Documentación

### Añadido

- `docs/USAGE.md`: manual de uso verificado (quick start, endpoints, curl, Python,
  Celery, formatos, modos, errores, Swagger, troubleshooting).
- `docs/SWAGGER_GUIDE.md`: guía de Swagger UI/ReDoc, exportación de OpenAPI y
  generación de clientes con `openapi-generator-cli`.
- OpenAPI enriquecido (solo metadata): tags `Análisis`/`Salud`/`Sistema`, contacto,
  licencia, descripciones, `responses` documentadas (202/400/413/422/429/500/503) y
  ejemplos de request/response.
- `AUDITORIA_v0.2.0.md` (raíz del workspace): auditoría empírica, 15 casos límite,
  concurrencia, logs y OpenAPI.

### Sin cambios

- Sin cambios de lógica de negocio. 71 tests verdes; contrato intacto.

## [0.2.0] — 2026-11-12 — Sprint 0 cierre

### Añadido

- Endpoint `POST /api/v1/analyze` con `mode=absolute|comparative`.
- Soporte de formatos WAV, M4A, AAC, MP3 y OGG vía FFmpeg (`ffmpeg-python` disponible
  para probing; la conversión usa subprocess directo).
- Límites de subida: **50 MB** y **600 s** (`AUDIO_TOO_LARGE` / `AUDIO_TOO_LONG`).
- `/health` con checks de `ffmpeg`, `librosa`, `models_loaded` y `disk_space_mb`;
  HTTP 503 si el servicio queda `degraded`.
- Métricas del contrato híbrido: `pitch_stability_cents`, `mean_pitch_hz`,
  `voiced_ratio`; en comparative además `pitch_accuracy` y `average_cent_deviation`.
- Feedback tipado con `code` estable (`OUT_OF_TUNE`, `NO_VOICE`, `UNSTABLE_PITCH`,
  `PITCH_OUT_OF_RANGE`); los `segments` llevan `severity` y tiempos (`start`/`end`).
- `integration/`: simulador de worker Celery, matriz de errores (9 checks), generador
  de fixtures y `verify_handoff.sh` (4/4 OK).
- `docs/celery-contract.md` con 7 secciones y tarea Celery real (guard para 5xx sin JSON).
- **71 tests**, 93 % de cobertura (`app/core` + `app/main`); `ruff` OK.

### Cambiado (BREAKING para Core)

- Campo multipart `file` → **`audio`** (corregido en `CONSISTENCY_FIX.md`).
- `mode=mock|real` → **`mode=absolute|comparative`**.
- `reference_file` → **`reference_audio`** (opcional; sólo comparative).
- `INVALID_MODE` 400 → **422**.
- `FILE_TOO_LARGE` / `DURATION_TOO_LONG` → **`AUDIO_TOO_LARGE` / `AUDIO_TOO_LONG`**.
- `UNSUPPORTED_FORMAT` / `NO_AUDIO_TRACK` 415 → **400**.
- `pitch.reference` ahora es **nullable** (null en absolute).

### Diferido a Sprint 1

- `rhythm_eval` real (stub explícito; `rhythm_accuracy=null`).
- `pitch_contour` con downsample (`include_contour` es futuro).
- Evaluación CREPE vs `librosa.pyin`.
- FastDTW / alineamiento temporal avanzado.

## [0.1.0] — 2026-10-06 — Sprint 0 inicial

- Versión inicial del microservicio: FastAPI, `/health`, `/docs`, Dockerfile
  multi-stage con FFmpeg y usuario no-root.
- Contrato OpenAPI v1 con respuesta mock y almacén TTL stateless.
- Preprocesamiento FFmpeg → WAV 16 kHz mono y pitch con `librosa.pyin`.
- Segmentos, scores 0–100 y feedback `OUT_OF_TUNE` / `NO_VOICE`.
