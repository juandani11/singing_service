# Arquitectura — singing-service

## 1. Rol en SyncDance

Microservicio **stateless** de análisis de canto. Recibe un audio (intento del alumno y,
opcionalmente, referencia), devuelve métricas y feedback. No gestiona auth, no persiste
y no conoce usuarios: la fuente de verdad es el Core (PostgreSQL).

- Puerto: `5000` (red interna Docker; sin publicar en producción).
- API: `POST /api/v1/analyze` (202) + `GET /api/v1/analyze/{id}` + `GET /health`.
- Contrato: [`celery-contract.md`](celery-contract.md).

## 2. Vista de componentes internos

```
singing-service/
├── app/
│   ├── main.py                  # FastAPI app, /health (checks), /docs
│   ├── api/routes/analyze.py    # POST/GET /analyze, semáforo, idempotencia
│   ├── core/
│   │   ├── config.py            # settings por env (límites, TTL, concurrencia)
│   │   ├── log.py               # eventos JSON una-línea (RNF-03)
│   │   └── store.py             # almacén TTL en memoria + índice attempt_id
│   ├── schemas/analyze.py       # contrato Pydantic (request/response)
│   ├── services/
│   │   ├── preprocess.py        # FFmpeg → WAV 16 kHz mono, validaciones
│   │   ├── pitch.py             # librosa.pyin → F0 + silence_pct
│   │   ├── compare.py           # align_by_time (comparación simple) + notas JSON
│   │   ├── metrics.py           # métricas absolute/comparative
│   │   ├── scoring.py           # scores 0–100
│   │   ├── feedback.py          # códigos y mensajes (HU-46)
│   │   ├── rhythm_eval.py       # stub (diferido a Sprint 1)
│   │   └── align.py             # FastDTW cableado en comparative (HU-S1-04); fallback align_by_time
│   └── mock/data.py             # fixture con valores de Figma (no expuesto por API)
├── tests/                       # 115 tests por defecto + 3 de integración
├── integration/                 # simulador Celery, matriz de errores, fixtures, verify
└── docs/                        # contrato, arquitectura, backlog, troubleshooting
```

> Nota: el diseño inicial hablaba de `pitch_detector.py`, `feedback_gen.py` y
> `rhythm_eval.py` dentro de `core/`. La implementación real los ubica en
> `app/services/` como `pitch.py`, `feedback.py` y `rhythm_eval.py`; `app/core/` quedó
> para configuración, logging y store.

## 3. Contrato de API

Ver [`celery-contract.md`](celery-contract.md) para el detalle completo.

- **Request** (`multipart/form-data`): `audio` (archivo, obligatorio), `attempt_id`,
  `routine_id`, `mode=absolute|comparative`; en comparative, `reference_audio`
  (archivo) o `reference_notes` (JSON).
- **Response**: `analysis_id`, `attempt_id`, `routine_id`, `status`, `mode`,
  `algorithm_version`, `duration_sec`, `pitch`, `segments`, `scores`, `metrics`,
  `feedback`, `timings`.
- **Futuro**: `pitch_contour` (flag `include_contour`, Sprint 1) y `rhythm_accuracy`
  real (Sprint 1).

## 4. Flujo interno de `/analyze`

```mermaid
flowchart TD
    A[POST /api/v1/analyze] --> B{mode valido?}
    B -- no --> E422[422 INVALID_MODE]
    B -- si --> C{comparative sin referencia?}
    C -- si --> E400[400 MISSING_REFERENCE]
    C -- no --> D[Leer audio + limites 50 MB / 600 s]
    D --> F[FFmpeg -> WAV 16 kHz mono]
    F --> G[librosa.pyin -> F0]
    G --> H{mode}
    H -- absolute --> I[Metricas internas]
    H -- comparative --> J[align_frames (FastDTW) + fallback align_by_time + metricas]
    I --> K[Scores + segments + feedback]
    J --> K
    K --> L[202 + GET /analyze/id]
```

Pasos:

1. Validar `mode` (422 `INVALID_MODE` si es inválido).
2. Validar referencia (400 `MISSING_REFERENCE` en comparative sin referencia).
3. Idempotencia por `attempt_id` (devuelve el mismo `analysis_id` si ya existe).
4. Adquirir semáforo (2 análisis simultáneos; 429 `SERVICE_BUSY` si se llena).
5. Validar extensión y tamaño (400 / 413).
6. Decodificar con FFmpeg a WAV 16 kHz mono (400 si falla; 413 si dura > 600 s).
7. `librosa.pyin` → F0 (fmin 65, fmax 1600) y `silence_pct`.
8. Si comparative: `compare.align_by_time` (nearest-neighbor temporal) + métricas.
9. Scores 0–100, segmentos y feedback.
10. Guardar en el store TTL y devolver 202; el Core hace `GET` del resultado.

## 5. Decisiones técnicas

- **`async def` + `run_in_threadpool`:** el endpoint es `async def` (recibe uploads y
  orquesta), pero FFmpeg, pyin y scoring corren en `run_in_threadpool` para no bloquear
  el event loop. No se usa `def` sync para el endpoint.
- **Uvicorn con 1 worker** (CMD actual). La concurrencia interna se limita con
  `threading.Semaphore(MAX_CONCURRENT_ANALYSES=2)`; el escalado es horizontal (réplicas).
- **Sin auth interna:** confianza en la red Docker; el servicio no se publica fuera.
- **Sin persistencia:** store en memoria con TTL de 1 h; la fuente de verdad es el Core.
- **FFmpeg por subprocess** (no pydub). `ffmpeg-python==0.2.0` queda instalado para
  probing/estandarización, pero la ruta usa `subprocess` directo.
- **`rhythm_eval` diferido a Sprint 1:** stub explícito; `rhythm_accuracy=null`.
- **FastDTW cableado (HU-S1-04):** `analyze.py` usa `align_frames` en
  `mode=comparative`; si falla, cae a `align_by_time` (`metrics.alignment_method`
  = `"fastdtw"` | `"time"`). `timings.align_ms` es aditivo; `dtw_ms` es alias.

## 6. Dependencias externas

- **Python 3.14.6** — local venv y Docker (`python:3.14.6-slim`). Librerías
  pinneadas: librosa 1.0.0, numba 0.68.0, scipy 1.18.1, numpy 2.5.3.
  Ambas suites: **118 tests (115 por defecto + 3 integración), 98 %**; Docker
  115 + 1 passed + 2 skipped (fixtures MASTmelody).
- **FFmpeg** (sistema/Docker): decodificación y normalización de audio.
- **librosa**, **soundfile**, **numpy**, **scipy**: pitch y análisis.
- **numba/llvmlite**: JIT de pyin (causa el arranque frío).
- **FastAPI**, **Uvicorn**, **Pydantic**, **python-multipart**.

## 6.1 Configuración de build (`GIT_SHA`, `BUILD_TIME`)

El Dockerfile final declara `ARG GIT_SHA=unknown` / `ARG BUILD_TIME=unknown` y los
exporta como `ENV`; `docker-compose.yml` los pasa como `build.args`. Se exponen en
`GET /version` para debug.

```bash
# Linux/macOS
GIT_SHA=$(git rev-parse --short HEAD) BUILD_TIME=$(date -Iseconds) docker compose build

# Windows PowerShell
$env:GIT_SHA = (git rev-parse --short HEAD); $env:BUILD_TIME = (Get-Date -Format o); docker compose build
```

Si no se pasan, `/version` muestra `"unknown"` (no falla).

## 6.2 Configuración de warm-up (`SKIP_WARMUP` / `SKIP_WARMUP_BEAT`)

El lifespan ejecuta dos warm-ups (sine 440 Hz, 0.5 s, en memoria):

1. `librosa.pyin` (HU-S1-03) → `checks.warmup`.
2. `librosa.beat.beat_track` + `librosa.onset.onset_detect` (HU-S1-01) →
   `checks.rhythm_warmup`; el JIT de `beat_track` cuesta ~1.8 s en Docker en frío
   (el prototipo local aislado midió ~10 s; el warm-up de pyin ya calienta parte
   de numba).

`SKIP_WARMUP=true|1|yes|on` omite ambos (tests/entornos rápidos).
`SKIP_WARMUP_BEAT=true|1|yes|on` omite solo el de ritmo (tests que mockean librosa).
Por defecto se ejecutan; el startup completo queda en ~14 s (Docker: pyin ~9.4 s
+ ritmo ~1.3 s; `/ready` a los ~14 s) y el primer `/analyze` no paga el JIT. Los logs son
`warmup_completed`/`warmup_failed` y
`warmup_beat_track_completed`/`warmup_beat_track_failed`.

## 7. Riesgos conocidos

- **JIT frío de numba/llvmlite:** mitigado con warm-up extendido en lifespan
  (pyin + `beat_track`/`onset_detect`; HU-S1-01/HU-S1-03). Sine primer/segundo:
  10 s → <2 s (ver `CIERRE_HU_S1_01.md`/`CIERRE_HU_S1_03.md`); el startup paga ~14 s.
- **`beat_track` lento en audios reales:** con `hop=960` (60 ms) MASTmelody baja de
  5.7 s a ~1.5 s en local; en Docker mide ~3.8 s (documentado). El downsample a 8 kHz
  se probó y se descartó (rompía ruido/tempo).
- **CPU-bound:** pyin/FFmpeg consumen CPU; escalar horizontalmente (réplicas/HPA) y
  mantener el semáforo para no saturar.
- **Imagen Docker ~1.6 GB** (aceptable; revisar si crece con CREPE/GPU).
- **Sin timeout interno de pyin** (sólo FFmpeg 120 s); mitigación en HU-S1-05.

## 8. Links

- [`celery-contract.md`](celery-contract.md) — contrato con Core.
- [`SPRINT1_BACKLOG.md`](SPRINT1_BACKLOG.md) — siguiente sprint.
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — problemas comunes.
- [`../integration/README.md`](../integration/README.md) — kit de integración.
