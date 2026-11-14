# ESTADO_ACTUAL.md — singing-service (SyncDance AI)

> Informe técnico de estado. **Solo lectura:** ningún archivo del proyecto fue modificado
> para generarlo. Todos los outputs de comandos son reales (2026-11-12, UTC).
> Servicio: microservicio de análisis de voz (EP-08, RF-37…RF-40, HU-43…HU-47).
> Sprints ejecutados: S0–S5 (plan `Docs/plan-implementacion-singing-service.md`).
>
> **Histórico:** este informe refleja el estado previo a `CONSISTENCY_FIX.md`. El campo
> multipart vigente es `audio` (antes `file`); ver `singing-service/docs/celery-contract.md`.

---

## 1. Estructura de archivos actual

Árbol de `singing-service/` (excluye `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`,
`node_modules`). Generado con script equivalente a `tree /F`:

```
singing-service\
  app\
    api\
      routes\
        __init__.py
        analyze.py
      __init__.py
    core\
      __init__.py
      config.py
      log.py
      store.py
    mock\
      __init__.py
      data.py
    schemas\
      __init__.py
      analyze.py
    services\
      __init__.py
      align.py
      feedback.py
      pitch.py
      preprocess.py
      scoring.py
    __init__.py
    main.py
  scripts\
    demo_e2e.py
  tests\
    fixtures\
      audios\
        README.md
    snapshots\
      openapi_v1.json
    __init__.py
    test_align.py
    test_busy.py
    test_contract.py
    test_e2e.py
    test_health.py
    test_log.py
    test_pitch.py
    test_preprocess.py
    test_store.py
  .dockerignore
  .gitignore
  docker-compose.yml
  Dockerfile
  postman_collection.json
  pyproject.toml
  README.md
  requirements.txt
```

**41 archivos.** No hay archivos vacíos (todos tienen ≥1 línea; todos los `__init__.py`
contienen docstring/import). **No existe** `core/` (el paquete es `app/`), ni `.env.example`,
ni `pyproject` de build (solo config de lint/tests), ni audios de prueba.

---

## 2. Estado por componente

| Ruta | Propósito | Estado | Líneas | Si PARCIAL/STUB: qué falta |
|---|---|---|---|---|
| `Dockerfile` | Multi-stage python:3.14-slim + FFmpeg + usuario no-root | **COMPLETO** | 30 | — (ver §6) |
| `requirements.txt` | Dependencias con rangos acotados (runtime+dev) | **COMPLETO** | 27 | — |
| `pyproject.toml` | Config pytest (`-q`) y ruff (E,F,I,UP,B; line 100) | **COMPLETO** | 14 | No es pyproject de paquete (sin `[project]`); no hay config de cobertura |
| `app/main.py` | App FastAPI: `/health`, `/docs`, `logging.basicConfig` | **COMPLETO** | 39 | — |
| `app/api/routes/analyze.py` | `POST /api/v1/analyze` (202, idempotente, semáforo) + `GET /{id}` | **COMPLETO** | 268 | — |
| `app/schemas/analyze.py` | Contrato Pydantic v1 (se congela en snapshot OpenAPI) | **COMPLETO** | 104 | — |
| `app/core/config.py` | Settings por env (MODE, TTL, hop, límites, concurrencia) | **COMPLETO** | 40 | — |
| `app/core/store.py` | Store en memoria con TTL 1 h + índice por `attempt_id` | **COMPLETO** | 80 | — |
| `app/core/log.py` | `log_event()` JSON una-línea (RNF-03) | **COMPLETO** | 23 | — |
| `app/mock/data.py` | Respuesta mock con valores congelados de Figma | **COMPLETO** | 178 | — |
| `app/services/preprocess.py` | FFmpeg subprocess: validación, conversión→WAV 16 kHz, duración | **COMPLETO** | 178 | — |
| `app/services/pitch.py` | `librosa.pyin` → curvas F0 + `silence_pct` | **COMPLETO** | 75 | — |
| `app/services/align.py` | FastDTW + cents + `hz_to_note` + `build_segments` | **COMPLETO** | 161 | — |
| `app/services/scoring.py` | Scores 0–100 (vocal/afinación/estabilidad/volumen) | **COMPLETO** | 73 | — |
| `app/services/feedback.py` | Feedback `OUT_OF_TUNE`/`NO_VOICE` (HU-46) | **COMPLETO** | 44 | — |
| `tests/` (9 archivos + fixtures/snapshot) | 54 tests: contract, store, preprocess, pitch, align, busy, log, e2e, health | **COMPLETO** | 944 (suma) | Sin `conftest.py`; sin cobertura |
| `README.md` | Docs: estado por sprint, API, ejecución, decisiones | **PARCIAL** | 123 | Falta curl `POST` de ejemplo; línea 105 dice "(51)" tests (reales: **54**); checklist "Estado por sprint" sólo lista S0–S2 arriba (S3–S5 están más abajo) |
| `.env.example` | — | **FALTA** | — | **NO EXISTE** (los settings están documentados en README/plan pero no hay plantilla `.env`) |
| `docker-compose.yml` (en `singing-service/`) | Compose local: build, puerto 5000, env MODE=mock | **COMPLETO** | 16 | — |
| `docker-compose.yml` (raíz del monorepo) | — | **FALTA** | — | **NO EXISTE**: `Test-Path .\docker-compose.yml` → `False` (no hay monorepo en este workspace) |
| `scripts/demo_e2e.py` | Tanda E2E + métricas §15.1 | **COMPLETO** | 178 | — |
| `postman_collection.json` | 6 requests (health, mock, real, GET, 404, errores) | **COMPLETO** | 252 | — |
| `tests/snapshots/openapi_v1.json` | Snapshot del contrato OpenAPI | **COMPLETO** | 560 | — |
| `tests/fixtures/audios/README.md` | Explica que los audios se autogeneran | **COMPLETO** | 15 | No hay `.wav`/`.mp3` en el repo |
| **`core/pitch_detector.py`** | — | **NO EXISTE** | — | Equivalente real: `app/services/pitch.py` (+ `hz_to_note` en `app/services/align.py`) |
| **`core/rhythm_eval.py`** | — | **NO EXISTE** | — | **No hay evaluación de ritmo en el servicio** (el brief S0 la mencionaba; fuera del alcance actual EP-08 vocal) |
| **`core/feedback_gen.py`** | — | **NO EXISTE** | — | Equivalente real: `app/services/feedback.py` |

---

## 3. Endpoints implementados

### 3.1 `GET /health`

- **Estado:** funcional (verificado por TestClient y por `curl` en contenedor).
- **Request:** sin parámetros.
- **Response (real, 200):**

```json
{
  "status": "ok",
  "service": "singing-service",
  "version": "1.0.0",
  "mode": "mock"
}
```

- `mode=absolute/comparative`: **NO aplica** (no es un endpoint de análisis).
- `pitch_contour`: **NO aplica**.

### 3.2 `POST /api/v1/analyze`

- **Estado:** funcional — probado en `mode=mock` y `mode=real` (tests + ejecución real de este informe).
- **Request (multipart/form-data) — implementado:**

| Campo | Tipo | Requerido | Notas |
|---|---|---|---|
| `file` | file | sí | Audio/video del intento |
| `reference_file` | file | sí | Audio de referencia (siempre; no es opcional) |
| `attempt_id` | string (min 1) | sí | Idempotencia |
| `routine_id` | string (min 1) | sí | Rutina |
| `mode` | string | no (default `mock`) | **`mock` \| `real`** — NO `absolute`/`comparative` |

- **Response (real, 202):**

```json
{
  "analysis_id": "0b690002174a40c79d1110679b6fe46d",
  "status": "completed"
}
```

  (En `mode=real`: `analysis_id: "5ec7d844e0ba42139f3379a020e7066d"`, `status: "completed"`.)

- **Errores reales verificados:**

```json
// 400 (mode inválido)
{ "detail": { "code": "INVALID_MODE", "message": "mode debe ser 'mock' o 'real'" } }
```

```json
// 422 (falta campo, Pydantic) — forma estándar FastAPI con `detail` array
// 413/415/429/500 — ver tabla de códigos en README §Errores
```

- `mode=absolute` / `mode=comparative`: **NO** (soporta `mock`/`real`; ver §8).
- `pitch_contour`: **NO** (la respuesta no incluye ese campo).

### 3.3 `GET /api/v1/analyze/{analysis_id}`

- **Estado:** funcional (mock y real).
- **Request:** path param `analysis_id`.
- **Response (real, 200 — curvas truncadas con `...[+N items]` por legibilidad):**

```json
{
  "analysis_id": "0b690002174a40c79d1110679b6fe46d",
  "attempt_id": "att-report-1",
  "routine_id": "rut-1",
  "status": "completed",
  "algorithm_version": "1.0.0-mock",
  "duration_sec": 45.0,
  "pitch": {
    "student": [
      { "t": 0.0, "f0": null, "voiced": false },
      { "t": 0.046, "f0": null, "voiced": false },
      "...[+973 items]"
    ],
    "reference": [
      { "t": 0.0, "f0": 220.0, "voiced": true },
      { "t": 0.046, "f0": 221.07, "voiced": true },
      "...[+973 items]"
    ],
    "hop_ms": 46
  },
  "segments": [
    { "start": 12.0, "end": 12.6, "type": "out_of_tune", "expected_note": "E4", "sung_note": "F#4", "delta_cents": 45, "severity": "medium" },
    { "start": 27.1, "end": 28.0, "type": "no_voice", "expected_note": null, "sung_note": null, "delta_cents": null, "severity": "info" },
    { "start": 41.0, "end": 41.6, "type": "out_of_tune", "expected_note": "A4", "sung_note": "G#4", "delta_cents": 72, "severity": "high" }
  ],
  "scores": { "vocal": 71, "afinacion": 71, "estabilidad": 66, "control_volumen": 80, "silence_pct": 4 },
  "feedback": [
    { "code": "SUSTAIN_2ND_BAR", "message": "Sostén la afinación en el segundo compás: hasta 72 cents de desviación." },
    { "code": "LOW_VOLUME_ENTRY", "message": "Detectamos 4% del tiempo sin voz; es distinto a una desafinación." }
  ],
  "timings": { "preprocess_ms": 180, "pitch_ms": 640, "dtw_ms": 210, "scoring_ms": 30 }
}
```

- **404 (real):**

```json
{
  "detail": {
    "code": "ANALYSIS_NOT_FOUND",
    "message": "Análisis inexistente o expirado; relanza el POST /analyze"
  }
}
```

- `mode=absolute/comparative`: **NO** (el GET no recibe `mode`).
- `pitch_contour`: **NO** como campo propio. Sí devuelve **curvas F0 completas** en
  `pitch.student` / `pitch.reference` **sin downsample** (mock: `hop_ms=46`;
  real: `hop_ms=32` → 31.25 Hz, no 10 Hz).

---

## 4. Librerías y versiones instaladas

### 4.1 `pip freeze` (venv local `.venv`, Python 3.14.6) — salida real

```
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
certifi==2026.7.22
cffi==2.1.1
charset-normalizer==3.5.2
click==8.5.0
cloudpickle==3.1.2
colorama==0.4.6
decorator==5.3.1
fastapi==0.142.2
fastdtw==0.3.4
h11==0.16.0
httpcore==1.0.9
httptools==0.8.0
httpx==0.28.1
idna==3.20
iniconfig==2.3.0
joblib==1.6.0
lazy-loader==0.6
librosa==1.0.0
llvmlite==0.50.0
msgpack==1.2.3
narwhals==2.26.0
numba==0.68.0
numpy==2.5.3
opentelemetry-api==1.45.1
packaging==26.3
platformdirs==4.12.3
pluggy==1.6.0
pooch==1.9.0
pycparser==3.0
pydantic==2.13.5
pydantic-settings==2.15.0
pydantic_core==2.46.5
Pygments==2.21.0
pytest==8.4.2
python-dotenv==1.2.4
python-multipart==0.0.32
PyYAML==6.0.3
requests==2.34.2
ruff==0.16.10
scikit-learn==1.9.1
scipy==1.18.1
soundfile==0.14.0
soxr==1.1.0
starlette==1.7.0
threadpoolctl==3.7.0
typing-inspection==0.4.4
typing_extensions==4.16.0
urllib3==2.8.0
uvicorn==0.54.0
watchfiles==1.3.0
websockets==17.2
```

### 4.2 `requirements.txt` (rangos, no pins exactos)

```
fastapi>=0.115,<1.0
uvicorn[standard]>=0.30,<1.0
pydantic>=2.10,<3.0
pydantic-settings>=2.5,<3.0
python-multipart>=0.0.19,<1.0
librosa>=1.0,<2.0
fastdtw>=0.3.4,<0.4
pytest>=8.0,<9.0
httpx>=0.27,<1.0
ruff>=0.8
```

(numpy/scipy comentados: llegan como dependencias de librosa; FFmpeg es binario del SO/Docker)

### 4.3 Paquetes críticos

| Paquete | Local | ¿Crítico? | Nota |
|---|---|---|---|
| `librosa` | 1.0.0 | **SÍ** | `pyin` (HU-43) |
| `numpy` | 2.5.3 | **SÍ** | arrays F0 |
| `scipy` | 1.18.1 | **SÍ** | señal (vía librosa) |
| `numba` / `llvmlite` | 0.68.0 / 0.50.0 | **SÍ** | JIT de pyin (ver §9, arranque fría) |
| `fastdtw` | 0.3.4 | **SÍ** | alineación DTW; sdist → `build-essential` en Docker |
| `fastapi` | 0.142.2 | **SÍ** | framework |
| `uvicorn` | 0.54.0 | **SÍ** | servidor |
| `soundfile` | 0.14.0 | **SÍ** | I/O de audio (wheel trae libsndfile) |
| `pydantic` / `pydantic-settings` | 2.13.5 / 2.15.0 | **SÍ** | contratos + config |
| `python-multipart` | 0.0.32 | **SÍ** | uploads multipart |
| `ffmpeg-python` | **NO INSTALADO** | no | Se usa **FFmpeg por subprocess directo** (decisión: una dependencia menos) |
| `pytest` / `httpx` / `ruff` | 8.4.2 / 0.28.1 / 0.16.10 | dev | tests + lint |
| FFmpeg (binario) | 9.0.1-full_build (local) / 7.1.5 (Debian, Docker) | **SÍ** | conversión de audio |

⚠️ Local y Docker no comparten pins exactos (requirements usa rangos; el build de Docker
de este informe instaló `fastapi-0.162.5`, `numpy-2.5.4`, `numba-0.68.1`, etc.).

---

## 5. Estado de pruebas

### 5.1 Tests existentes (54)

| Archivo | # | Tests (nombre real) y qué prueban |
|---|---|---|
| `test_health.py` | 3 | `test_health_returns_200` · `test_swagger_docs_available` · `test_openapi_schema_generated` — health/docs/schema |
| `test_contract.py` | 7 | `test_openapi_matches_v1_snapshot` (snapshot) · `test_mock_analyze_flow_validates_contract` · `test_analyze_is_idempotent_by_attempt_id` · `test_invalid_mode_returns_400` · `test_unknown_analysis_returns_404` · `test_analyze_requires_files` · `test_empty_attempt_id_rejected` |
| `test_store.py` | 4 | `test_get_by_index_returns_none_after_expiry` · `test_index_follows_value_expiry` · `test_purge_removes_stale_index_entries` · `test_max_entries_evicts_oldest` — TTL/índice |
| `test_preprocess.py` | 13 | `test_real_mode_preprocesses_and_reports_duration` · `test_real_mode_is_idempotent` · `test_unsupported_extension_returns_415` · `test_corrupt_audio_returns_400` · `test_corrupt_reference_returns_400` · `test_invalid_ffmpeg_binary_returns_500` · `test_empty_file_returns_400` · `test_file_too_large_returns_413` · `test_duration_too_long_returns_413` · `test_video_without_audio_track_returns_415` · `test_convert_produces_16k_mono_wav` · `test_wav_duration_on_non_wav_raises_typed_error` · `test_convert_keeps_files_inside_tmp_dir` |
| `test_pitch.py` | 3 | `test_extract_pitch_finds_tone_and_silence` · `test_real_mode_uses_pyin_pitch` · `test_pure_silence_reports_high_silence_pct` |
| `test_align.py` | 15 | `test_align_identical_curves_give_zero_cents` · `test_align_offset_gives_expected_cents` · `test_align_unvoiced_frames_are_not_judged` · `test_align_handles_different_lengths` · `test_hz_to_note` (**440→A4**) · `test_build_segments_out_of_tune_high_severity` · `test_build_segments_medium_below_threshold` · `test_build_segments_short_runs_are_ignored` · `test_build_segments_no_voice_run` · `test_build_segments_short_silence_ignored` · `test_scoring_perfect_match` · `test_scoring_all_mismatched` · `test_scoring_without_matched_frames` · `test_feedback_distinguishes_no_voice_from_out_of_tune` · `test_real_mode_reports_out_of_tune_segment` |
| `test_busy.py` | 3 | `test_busy_returns_429_when_queue_full` · `test_semaphore_released_after_error` · `test_mock_bypasses_semaphore` — semáforo S5 |
| `test_log.py` | 3 | `test_idempotent_hit_is_logged` · `test_not_found_is_logged` · `test_busy_env_bounds_fail_fast` — RNF-03 + `Field(ge=…)` |
| `test_e2e.py` | 3 | `test_e2e_known_deviation_full_contract` · `test_e2e_long_pause_produces_no_voice_feedback` · `test_e2e_pipeline_accepts_mp3` — contrato §11 |

### 5.2 `pytest -v` — output completo real

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\HP\Documents\PROYECTOS\App-SyncDance\singing-service
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1, platformdirs-4.12.3
collected 54 items

tests\test_align.py ...............                                      [ 27%]
tests\test_busy.py ...                                                   [ 33%]
tests\test_contract.py .......                                           [ 46%]
tests\test_e2e.py ...                                                    [ 51%]
tests\test_health.py ...                                                 [ 57%]
tests\test_log.py ...                                                    [ 62%]
tests\test_pitch.py ...                                                  [ 68%]
tests\test_preprocess.py .............                                   [ 92%]
tests\test_store.py ....                                                 [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\HP\Documents\PROYECTOS\App-SyncDance\singing-service\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 54 passed, 1 warning in 20.33s ========================
```

**54 passed** en 20.33 s.

### 5.3 Cobertura

**NO CONFIGURADO.** `pip show pytest-cov` → `WARNING: Package(s) not found: pytest-cov`.
En `pyproject.toml` sólo existe `addopts = "-q"` (sin `--cov`). `pytest --cov` no puede
ejecutarse: **NO VERIFICABLE** (plugin ausente).

### 5.4 Fixtures / audios de prueba

- `tests/fixtures/audios/` contiene **sólo** `README.md` (15 líneas): explica que los audios
  se **autogeneran** por test (sines, silencio, pausas largas, mp3 vía FFmpeg).
- **No hay ningún `.wav`/`.mp3`/`.m4a`/`.ogg`/`.flac` en el repo** (búsqueda recursiva: 0 resultados).
- Tests usan `tmp_path` (pytest) + `tempfile.TemporaryDirectory` en la ruta real.

---

## 6. Estado del Docker

### 6.1 `docker build` — primer intento: FALLÓ (error real, red/DNS transitoria)

> Docker Desktop estaba apagado al iniciar la sesión; se lanzó y el daemon quedó `DAEMON_READY`.
> El primer `docker compose build` falló (timeout de 900 s superado por reintentos de pip):

```
#13 231.6    ━━╸                                      4.0/59.7 MB 234.8 kB/s eta 0:03:58
#13 231.7 WARNING: Connection interrupted while downloading.
#13 231.7 WARNING: Attempting to resume incomplete download (4.0 MB/59.7 MB, attempt 1)
#13 231.9 WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NameResolutionError("HTTPSConnection(host='files.pythonhosted.org', port=443): Failed to resolve 'files.pythonhosted.org' ([Errno -2] Name or service not known)")': /packages/5c/ed/54107648386edf3da7def03d42721c72279f6bc2e17b5274c18955dc5833/llvmlite-0.50.0-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
#13 232.4 WARNING: Retrying (Retry(total=3, ...)) after connection broken by 'NameResolutionError(...)'
#13 640.8 WARNING: Retrying (Retry(total=2, ...)) after connection broken by 'NameResolutionError(...)'
#13 642.8 WARNING: Retrying (Retry(total=1, ...)) after connection broken by 'NameResolutionError(...)'

<shell tool terminated command after exceeding timeout 900000 ms>
EXIT_CODE=1   (timeout; build incompleto)
```

Diagnóstico posterior (real): DNS dentro de Docker respondía bien tras el fallo
(`docker run --rm python:3.14-slim getent hosts files.pythonhosted.org` → OK).

### 6.2 Segundo intento `docker compose build`: ÉXITO (exit 0)

Output final real (tail):

```
#13 64.55   Building wheel for fastdtw (pyproject.toml): finished with status 'done'
#13 64.56   Created wheel for fastdtw: filename=fastdtw-0.3.4-py3-none-any.whl size=3611 ...
#13 64.69 Installing collected packages: websockets, uvloop, urllib3, ... fastdtw, cffi, anyio, watchfiles, starlette, soundfile, scikit-learn, pydantic, pooch, httpx, pydantic-settings, librosa, fastapi
#13 89.55 Successfully installed annotated-doc-0.0.6 annotated-types-0.8.0 anyio-4.16.0 certifi-2026.10.23 cffi-2.1.1 charset-normalizer-3.5.2 click-8.5.1 cloudpickle-3.1.2 decorator-5.3.1 fastapi-0.162.5 fastdtw-0.3.4 h11-0.16.0 httpcore-1.0.9 httptools-0.9.0 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 joblib-1.6.0 lazy-loader-0.6 librosa-1.0.0 llvmlite-0.50.0 msgpack-1.2.4 narwhals-2.28.0 numba-0.68.1 numpy-2.5.4 opentelemetry-api-1.45.2 packaging-26.3 platformdirs-4.14.5 pluggy-1.7.0 pooch-1.9.0 pycparser-3.12 pydantic-2.14.3 pydantic-core-2.50.4 pydantic-settings-2.16.2 pygments-2.21.0 pytest-8.4.2 python-dotenv-1.2.4 python-multipart-0.0.33 pyyaml-6.0.3 requests-2.34.2 ruff-0.17.4 scikit-learn-1.9.1 scipy-1.18.1 soundfile-0.14.0 soxr-1.1.0 starlette-1.10.0 threadpoolctl-3.8.0 typing-extensions-4.16.0 typing-inspection-0.4.5 urllib3-2.8.0 uvicorn-0.54.0 uvloop-0.23.0 watchfiles-1.3.0 websockets-17.4
#13 DONE 90.4s
#14 [stage-1 3/6] COPY --from=builder /install /usr/local
#14 DONE 5.9s
#16 [stage-1 5/6] COPY app ./app
#16 DONE 0.1s
#17 [stage-1 6/6] RUN useradd --create-home --uid 10001 appuser     && chown -R appuser:appuser /app
#17 DONE 1.0s
#18 exporting layers 23.8s done
#18 naming to docker.io/library/singing-service-singing-service:latest 0.0s done
#18 unpacking to docker.io/library/singing-service-singing-service:latest 13.6s done
#18 DONE 37.7s
 Image singing-service-singing-service Built
EXIT_CODE=0
```

**Construye sin errores** (con red estable). Requiere acceso a PyPI (llvmlite ≈60 MB).

### 6.3 `docker compose up -d` — logs de inicio reales

```
 Network singing-service_default Created
 Container singing-service Creating
 Container singing-service Created
 Container singing-service Starting
 Container singing-service Started
UP_EXIT=0
```

```
singing-service  | INFO:     Started server process [1]
singing-service  | INFO:     Waiting for application startup.
singing-service  | INFO:     Application startup complete.
singing-service  | INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
singing-service  | INFO:     127.0.0.1:47890 - "GET /health HTTP/1.1" 200 OK
singing-service  | INFO:     172.21.0.1:45894 - "GET /health HTTP/1.1" 200 OK
```

### 6.4 `curl /health` — respuesta real

```
$ curl.exe -s -w "`nHTTP_STATUS=%{http_code}`n" http://localhost:5000/health
{"status":"ok","service":"singing-service","version":"1.0.0","mode":"mock"}
HTTP_STATUS=200
```

### 6.5 Tamaño de imagen (`docker images`)

```
singing-service-singing-service:latest  1.59GB
singing-service:latest                  1.59GB
singing-service:s0                      921MB
```

### 6.6 Usuario no-root

- **Sí.** `Dockerfile` línea 24-26: `useradd --create-home --uid 10001 appuser` + `USER appuser`.
- Verificado en contenedor en ejecución:

```
$ docker compose exec -T singing-service id
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
ID_EXIT=0
```

**Nota:** tras la verificación se ejecutó `docker compose down` (contenedor y red eliminados;
`DOWN_EXIT=0`) para dejar el entorno como estaba. Las imágenes permanecen.

---

## 7. Integración con Core API

**NO IMPLEMENTADO.** Evidencias:

| Pregunta | Resultado |
|---|---|
| ¿Existe `core-api/`? | `Test-Path .\core-api` → **`False`** (no existe en este workspace) |
| ¿Código con `SINGING_SERVICE_URL` o `singing-service:5000`? | **0 coincidencias** en `.py/.yml/.env/.json` fuera de `singing-service/` y `Docs/` (búsqueda recursiva del workspace) |
| ¿Tarea Celery que orqueste la llamada? | **NO EXISTE** en código. Hay **esqueleto documentado** en `Docs/integracion-core.md` §3: `@shared_task analyze_vocal` con `SINGING_URL = "http://singing-service:5000/api/v1/analyze"`, reintentos/backoff y manejo de 429 — pero **no está en ningún repo de código** |
| ¿Cola `audio_queue`? | **NO VERIFICABLE / NO EXISTE** en código; ni `audio_queue` ni otras colas aparecen en el workspace fuera de la guía (que tampoco nombra cola concreta) |
| ¿Variable de entorno en `docker-compose.yml`? | **NO**: `singing-service/docker-compose.yml` sólo define `MODE`, `ANALYSIS_TTL_SECONDS`, `HOP_LENGTH`, `CENT_THRESHOLD`, `MAX_FILE_MB`. No hay `SINGING_SERVICE_URL`/`SINGING_URL`. En la guía, la constante se llama **`SINGING_URL`** (no `SINGING_SERVICE_URL`) |
| ¿`docker-compose.yml` raíz del monorepo? | **NO EXISTE** en el workspace |

**Conclusión:** la integración está **documentada** (`Docs/integracion-core.md`, HU-47)
pero **no implementada**; además el workspace actual no contiene el monorepo (`core-api/`).

---

## 8. Contrato de API real vs esperado

### 8.1 Request

| Campo esperado | Implementado real | ¿Coincide? |
|---|---|---|
| `audio` (file, requerido) | **`file`** (file, requerido) | ❌ nombre distinto |
| `mode` default `"absolute"`, valores `absolute` \| `comparative` | **`mode`** default `"mock"`, valores **`mock` \| `real`** | ❌ semántica distinta (feature-flag de pipeline, no modo de análisis) |
| `reference_audio` (opcional, solo comparative) | **`reference_file`** (siempre requerido) | ❌ nombre + obligatoriedad |
| `reference_notes` (JSON, opcional) | **NO EXISTE** | ❌ falta |
| `tempo_bpm` (float, opcional) | **NO EXISTE** | ❌ falta |
| `include_contour` (bool, default false) | **NO EXISTE** (la curva siempre va en el GET) | ❌ falta |
| — (esperado: `attempt_id`/`routine_id` no listados) | **`attempt_id`** y **`routine_id`** requeridos | ➕ extra en el real |

### 8.2 Response

| Campo esperado | Implementado real | ¿Coincide? |
|---|---|---|
| `status` | `status` (`queued`/`completed`/`failed`; en la práctica `completed`) | ✅ nombre ✓ (estados `queued`/`failed` reservados al Core, RNF-07) |
| `request_id` | **`analysis_id`** | ❌ nombre distinto |
| `mode` | **NO está en la respuesta** | ❌ falta |
| `processing_time_ms` | **`timings`** = `{preprocess_ms, pitch_ms, dtw_ms, scoring_ms}` (sin total) | ❌ estructura distinta (no hay total único) |
| `audio`: `duration_seconds`, `sample_rate`, `voiced_ratio` | `duration_sec` ✓ ; `sample_rate` **NO** ; `voiced_ratio` ≈ `scores.silence_pct` (inverso, % sin voz) | ⚠️ parcial/nombres distintos |
| `metrics.overall_score` | `scores.vocal` | ⚠️ nombre distinto |
| `metrics.pitch_stability_cents` | `scores.estabilidad` (0–100, no cents) | ⚠️ unidad/distinto |
| `metrics.mean_pitch_hz` | **NO expuesto** (sólo curvas completas) | ❌ falta |
| comparative: `pitch_accuracy`, `rhythm_accuracy`, `average_cent_deviation` | **NO existen** (no hay rama comparative) | ❌ falta |
| `feedback[]`: `{code, type, severity, timestamp_start, timestamp_end, message}` | `feedback[]`: **sólo `{code, message}`** | ❌ faltan `type`, `severity`, `timestamp_start/end` |
| `pitch_contour`: null o array **downsampleado a 10 Hz** | **NO existe ese campo**; el GET devuelve `pitch.student`/`pitch.reference` **sin downsample** (real: 31.25 Hz / `hop_ms=32`; mock: `hop_ms=46`) | ❌ campo y muestreo distintos |
| — | **Extras reales**: `attempt_id`, `routine_id`, `algorithm_version`, `segments[]` (HU-45), `scores` sub-métricas | ➕ no previstas en el esperado |

**Resumen:** el servicio implementa el contrato congelado en `tests/snapshots/openapi_v1.json`
(plan §2.2), que **difiera sustancialmente** del "contrato esperado" de este informe
(nombres de campos, semántica de `mode`, feedback enriquecido, `pitch_contour` a 10 Hz,
métricas comparative). Requiere **negociación/alineación con el equipo** antes de integrar.

---

## 9. Problemas conocidos y TODOs

### 9.1 Marcadores `TODO`/`FIXME`/`HACK`/`XXX`

**Ninguno real.** Búsqueda en `*.py,*.yml,*.md,*.txt,*.toml,Dockerfile` → 3 coincidencias,
todas **falsos positivos** (texto español que contiene "todo"/"Método"):

```
app\mock\data.py:87:  - Mock puro (S1): todos los defaults  valores congelados de Figma.   ("todos")
tests\test_align.py:256: assert result.scores.afinacion <= 20  # todo el audio desafinado   ("todo")
README.md:22: | Método | Ruta | Descripción |                                               ("Método")
```

### 9.2 Problemas conocidos (sin marcador)

1. **Arranque frío de numba/pyin:** el primer `mode=real` paga JIT (~6–10 s extra).
   Medido en este informe: `pitch_ms: 10549` en el primer request vs ~640–1000 ms en
   siguientes (wall total 10965 ms). Documentado en el plan (E2E Docker: 2808 ms wall medio).
2. **Sin timeout duro sobre librosa/pyin ni FastDTW:** sólo FFmpeg tiene timeout (120 s →
   `CONVERT_TIMEOUT`). Un pyin extremadamente lento podría retener un slot del semáforo
   (acotado a 2 concurrentes; `BUSY_TIMEOUT_SEC=30` en espera).
3. **Límites por diseño:** audios >5 min → 413 `DURATION_TOO_LONG`; >20 MB → 413 `FILE_TOO_LARGE`.
4. **Sin validación de MIME/Content-Type:** se valida extensión (`ensure_supported_extension`,
   415) + decodificación FFmpeg (400); no se mira el header `Content-Type` del upload.
5. **Store en memoria con TTL 1 h:** reinicio del contenedor pierde resultados
   (stateless por decisión; fuente de verdad = Core). Límite de entradas con eviction LRU-ish.
6. **Deriva documental en README:** línea 105 dice "(51)" tests (reales: **54**); sin curl
   `POST` de ejemplo; checklist superior sólo muestra S0–S2 (S3–S5 documentados más abajo).
7. **`pyproject.toml`:** `ruff target-version = "py312"` mientras se ejecuta Python 3.14.
8. **Sin `.env.example`, sin cobertura (`pytest-cov`), sin CI configurado** en este workspace.
9. **Un solo worker uvicorn** (CMD sin `--workers`); concurrencia limitada por el semáforo
   interno (2) en `mode=real`.
10. **Sin autenticación** (decisión: red Docker interna) — documentado en `main.py`/README.
11. **Docker build necesita red a PyPI** (llvmlite ≈60 MB): build offline falla (falló en
    este informe por DNS transitorio; ver §6.1).
12. **`ffmpeg-python` no se usa** (subprocess directo): esperado por algunos revisores
    como dependencia; es decisión deliberada (comentario en `requirements.txt`).

---

## 10. Decisiones técnicas tomadas

| Tema | Decisión real | Detalle/evidencia |
|---|---|---|
| FastAPI sync/async | **Mixto** | `analyze()` es **`async def`** (recibe upload y orquesta); el CPU/FFmpeg/pyin/DTW corre con **`run_in_threadpool`** (no bloquea el event loop). `get_analysis()` y `health()` son **`def`** (lookup de dict en memoria). `asyncio.to_thread` para adquirir el semáforo |
| Uvicorn workers | **1 worker** | `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]` — sin `--workers`; compose tampoco lo define |
| Manejo de errores | **`HTTPException` + `detail` tipado `{code, message}`** | Códigos: `INVALID_MODE` 400 · `EMPTY_FILE`/`EMPTY_AUDIO` 400 · `INVALID_AUDIO` 400 · `CONVERT_TIMEOUT` 400 · `PITCH_EXTRACT_FAILED` 400 · `UNSUPPORTED_FORMAT` 415 · `NO_AUDIO_TRACK` 415 · `FILE_TOO_LARGE` 413 · `DURATION_TOO_LONG` 413 · `ANALYSIS_NOT_FOUND` 404 · `SERVICE_BUSY` 429 · `FFMPEG_NOT_FOUND` 500 · Pydantic 422 |
| Validación MIME/tamaño/duración | **Sin MIME; sí tamaño y duración** | Extensión en `analyze.py`/`preprocess.py` (`ensure_supported_extension` → 415); tamaño con `read_capped` (tope `MAX_FILE_MB=20` → 413); duración en preprocess (tope `MAX_DURATION_SEC=300` → 413); contenido validado por FFmpeg. **No** se inspecciona `Content-Type` |
| Timeout interno FFmpeg | **120 s** | `_FFMPEG_TIMEOUT_SEC = 120` en `preprocess.py` → `CONVERT_TIMEOUT` |
| Timeout pyin/DTW | **No hay timeout explícito** | Mitigado por semáforo (2) + espera acotada (30 s → 429) |
| Logging estructurado | **Sí — JSON una-línea, nivel INFO** | `logging.basicConfig(level=INFO, format="%(message)s")` + `log_event()` (`app/core/log.py`); eventos `analysis_accepted` (con timings/vocal), `analysis_failed` (code/http_status), `analysis_not_found`, `analysis_idempotent_hit`; sin PII (RNF-06) |
| Idempotencia | **Por `attempt_id`** | Chequeo **tras** validar `mode`, **antes** de leer archivos/trabajo pesado |
| Estado | **Stateless, store en memoria TTL 1 h** | Fuente de verdad = Core (PostgreSQL) |
| Concurrencia | **`threading.Semaphore(2)` vía `asyncio.to_thread`** | Sólo en `mode=real`; `finally` libera; `Field(ge=…)` evita 500 por env inválido |
| Feature-flag | **`MODE=mock\|real`** | `algorithm_version` delata el pipeline: `1.0.0-mock` / `0.4.0-align-scoring` |
| FFmpeg | **subprocess directo** (no pydub/ffmpeg-python) | `-ar 16000 -ac 1` + loudnorm; binario configurable `FFMPEG_BINARY` |

---

## 11. Lo que falta para cerrar Sprint 0

Checklist del Sprint 0, marcado con el estado **real** (no con el ideal):

- [x] **[HECHO]** Estructura del microservicio con FastAPI, Dockerfile, requirements
- [x] **[HECHO]** `docker compose up` levanta el servicio (verificado §6.3)
- [x] **[HECHO]** GET `/health` responde 200 (verificado §6.4)
- [~] **[PARCIAL]** POST `/api/v1/analyze` acepta audio, modo **absolute**
      → acepta audio ✓ pero **`mode` es `mock|real`, no `absolute`** (§8.1)
- [x] **[HECHO]** Pitch detector con `librosa.pyin` + conversión Hz→nota
      (`app/services/pitch.py` + `hz_to_note` en `align.py`)
- [x] **[HECHO]** Test con sine wave 440 Hz → A4
      (`test_hz_to_note`: `hz_to_note(440.0) == "A4"`; además tonos 440 en `test_pitch`/`test_e2e`)
- [~] **[PARCIAL]** Métricas básicas (voiced_ratio, pitch_stability, mean_pitch)
      → `silence_pct` ✓ (≈voiced_ratio), `estabilidad` ✓, **`mean_pitch_hz` NO expuesto**
- [x] **[HECHO]** Feedback básico (1-2 mensajes según umbrales)
      (`feedback.py`: `OUT_OF_TUNE`/`NO_VOICE`, con el fix "0% sin voz")
- [~] **[PARCIAL]** Dockerfile `python:3.12-slim` + ffmpeg + libsndfile, no-root
      → usa **`python:3.14-slim`** (3.12 no); ffmpeg ✓; libsndfile **implícito**
      (wheel de `soundfile` + paquete `libsndfile1` de ffmpeg en runtime); **no-root ✓**
- [ ] **[PENDIENTE]** Integración con Core vía Celery task en `audio_queue`
      → **NO IMPLEMENTADO** (§7; sólo guía en `Docs/integracion-core.md`)
- [~] **[PARCIAL]** Tests pytest con audio sintético y real
      → sintético ✓; "real" = archivos **generados en runtime**; **no hay audios reales en el repo**
- [~] **[PARCIAL]** README con curl de ejemplo
      → curl `GET /health` ✓; **falta curl `POST /api/v1/analyze`**

**Sprint 0 funcionalmente cerrado para el servicio en aislamiento; los ítems PENDIENTE/PARCIAL
dependen del monorepo del equipo o de decisiones de contrato (§8).**

---

## 12. Próximos pasos sugeridos

| # | Paso concreto | Esfuerzo | Por qué primero |
|---|---|---|---|
| 1 | **Cortes docs/derivación rápida:** corregir README (51→54 tests, añadir curl `POST` de ejemplo, unificar checklist S0–S5), crear `.env.example` con todas las env de `config.py`, fijar `ruff target-version="py314"` | **S** | Desbloquea revisión externa sin riesgo; 30–60 min |
| 2 | **Cobertura de tests:** añadir `pytest-cov` a dev-requirements + `addopts --cov=app --cov-report=term-missing` y techo mínimo (p. ej. ≥85%) | **S** | Visibilidad de regresiones para el agente Claude/CI |
| 3 | **Alinear contrato con el "esperado" (§8):** decisión de equipo sobre `mode=absolute\|comparative` (¿traducir a `mock/real`?, ¿rama comparative real?), `pitch_contour` a 10 Hz, feedback con `type/severity/timestamps`, `mean_pitch_hz`; actualizar snapshot OpenAPI + Postman + guía Core | **M** | Sin esto, cualquier integración con Core chocará con el shape real |
| 4 | **Integración real con Core (monorepo):** mover `singing-service/` al monorepo, rama `feature/singing-microservice`, compose raíz con `SINGING_URL`/`SINGING_SERVICE_URL`, task Celery `analyze_vocal` en la cola acordada (guía: reintentos + 429 backoff), smoke E2E Core↔singing | **L** | Es el único ítem PENDIENTE del Sprint 0 y está **bloqueado** por disponibilidad del monorepo |
| 5 | **Endurecimiento operativo:** timeout para pyin/DTW (o watchdog por request), `--workers`/uvicorn en compose según CPU del host, `HEALTHCHECK` extendido (ffmpeg presente + modo), reintento del build Docker con caché de wheels (mirror) para builds offline | **M** | Reduce riesgo en producción; tras la integración |

---

*Fin del informe. Para cualquier comando dudoso, reroducir con:
`singing-service/.venv/Scripts/python.exe -m pytest -v` · `docker compose build` ·
`curl http://localhost:5000/health`.*
