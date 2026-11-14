# Changelog

Todos los cambios notables de `singing-service` se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versionado [SemVer](https://semver.org/lang/es/).

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
