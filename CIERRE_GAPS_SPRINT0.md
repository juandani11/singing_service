# CIERRE_GAPS_SPRINT0 — singing-service

> Cierre de los 8 gaps detectados en `ESTADO_ACTUAL.md`. Fecha: 2026-11-12 (UTC).
> Alcance: sólo `singing-service/` (+ `Docs/integracion-core.md`, actualizado por O3).
> `core-api/` no existe en el workspace y **no se tocó**.
>
> **Actualización posterior (`CONSISTENCY_FIX.md`):** el campo multipart pasó de
> `file` a `audio`. Los curls y outputs de este informe son históricos (pre-rename);
> el contrato vigente está en `singing-service/docs/celery-contract.md`.

## Resumen ejecutivo

| # | Gap | Estado | Evidencia |
|---|---|---|---|
| 1 | Contrato híbrido `absolute`/`comparative` | **CERRADO** | §5/§6 + `test_absolute.py`/`test_comparative.py` |
| 2 | Formatos mobile (M4A/AAC) + `ffmpeg-python` | **CERRADO** | §7 + `test_m4a_is_decoded_and_analyzed` |
| 3 | Naming `SINGING_SERVICE_URL` | **CERRADO** | `.env.example`, README, `docs/celery-contract.md`, `Docs/integracion-core.md` |
| 4 | `rhythm_eval.py` | **CERRADO (O4-B)** | stub explícito + `rhythm_accuracy=null` + README "Ritmo: diferido a Sprint 1" |
| 5 | `pitch_contour` documentado como futuro | **CERRADO** | README §Modos (`include_contour=false` no implementado) |
| 6 | `pytest-cov` + cobertura | **CERRADO** | §3: 93 % (`app/core` + `app/main`; core: 100/100/93) |
| 7 | `/health` con dependencias | **CERRADO** | §4 + test degraded 503 |
| 8 | README (51→70 tests, curl POST) | **CERRADO** | README reescrito |

**Resultado:** `70 passed`, `ruff` OK, cobertura 93 %, Docker build OK, 3 modos/flujos
probados con curl real, imagen **1.6 GB** (< 2 GB) y contenedor no-root (`uid=10001`).

---

## 1. Diff resumido por archivo

### Creados

| Archivo | Qué | Por qué |
|---|---|---|
| `app/services/compare.py` | `align_by_time()` (remuestreo temporal simple) + `parse_reference_notes()` | O1: comparación **sin FastDTW** y notas JSON |
| `app/services/metrics.py` | `absolute_metrics()`, `comparative_metrics()`, rango humano 80–1100 Hz | O1: métricas del contrato híbrido |
| `app/services/rhythm_eval.py` | Stub `{"status":"not_implemented","reason":"deferred to Sprint 1"}` | O4-B: decisión explícita, sin métricas falsas |
| `requirements-dev.txt` | `-r requirements.txt` + `pytest-cov>=5.0,<8.0` | O6 |
| `.env.example` | Variables + `SINGING_SERVICE_URL` canónica | O3 |
| `docs/celery-contract.md` | URL, multipart, timeouts 5/300, códigos, pseudocódigo Celery | O8 |
| `tests/audio_utils.py` | Tonos WAV + transcodificación FFmpeg (M4A/MP3/OGG) | O2/O6 |
| `tests/test_absolute.py` | 5 tests de `mode=absolute` | O6 |
| `tests/test_comparative.py` | 6 tests de `mode=comparative` | O6 |

### Modificados

| Archivo | Qué cambió | Por qué |
|---|---|---|
| `app/schemas/analyze.py` | `AnalysisMode`, `Metrics`, `AnalysisResult.mode/metrics`, `PitchCurves.reference` nullable, `AcceptedResponse.mode` | O1 (contrato híbrido) |
| `app/core/config.py` | versión `0.2.0`; `MAX_FILE_MB` 20→**50**; `MAX_DURATION_SEC` 300→**600**; `ffmpeg_binary` (env/.env); eliminado `MODE` (feature-flag mock retirado) | O2/O5 |
| `app/services/preprocess.py` | `AUDIO_TOO_LARGE`/`AUDIO_TOO_LONG`; `UNSUPPORTED_FORMAT`/`NO_AUDIO_TRACK` → **400**; `ffmpeg_version()` | O2/O5 |
| `app/services/pitch.py` | `fmax` 1047→**1600** (detección de notas agudas fuera de rango); `fmin=65` para no detectar ruido de silencio | O1 |
| `app/services/scoring.py` | `compute_absolute_scores()` (consistencia vs mediana) | O1 |
| `app/services/feedback.py` | `build_absolute_feedback()` (`UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE`) | O1 |
| `app/api/routes/analyze.py` | Modos híbridos, `reference_audio`/`reference_notes`, `MISSING_REFERENCE` (400), `INVALID_MODE` (422), métricas, `algorithm_version=0.5.0-hybrid-modes` | O1/O2 |
| `app/main.py` | `/health` con `checks` + 503 `degraded` | O5 |
| `app/mock/data.py` | Fixture adaptado al schema (no expuesto por la API) | consistencia |
| `requirements.txt` | `ffmpeg-python==0.2.0` | O2 |
| `pyproject.toml` | `--cov=app.core --cov=app.main`, `target-version=py314` | O6 |
| `docker-compose.yml` | `MAX_FILE_MB=50`, `MAX_DURATION_SEC=600`, sin `MODE` | O2 |
| `README.md` | Contrato real, formatos, modos, curls, checklist, integración Core, 70 tests | O7 |
| `scripts/demo_e2e.py` | `mode=comparative` + `reference_audio` | consistencia |
| `tests/test_health.py` | Nuevo shape + degraded 503 | O6 |
| `tests/test_contract.py` | Flujo absolute, 422 `INVALID_MODE`, 400 `MISSING_REFERENCE` | O1/O6 |
| `tests/test_preprocess.py` | Nuevos códigos/límites + M4A + MP3 | O2/O6 |
| `tests/test_pitch.py`, `test_busy.py`, `test_e2e.py`, `test_align.py`, `test_log.py` | Adaptados a absolute/comparative | O1 |
| `tests/snapshots/openapi_v1.json` | Regenerado | contrato |
| `Docs/integracion-core.md` | `SINGING_SERVICE_URL`, modos, códigos, timeouts 5/300 | O3 (**excepción autorizada por O3**) |

### Sin cambios

`Dockerfile` (ya traía `ffmpeg` y usuario no-root), `app/core/store.py`, `app/core/log.py`,
`tests/test_store.py`.

---

## 2. BREAKING changes e impacto en Core

| Cambio | Antes | Ahora | Impacto |
|---|---|---|---|
| **`mode`** | `mock` \| `real` | **`absolute` (default) \| `comparative`** | El worker debe enviar el modo nuevo. `mock` ya no se expone por API |
| **Referencia** | `reference_file` (siempre requerido) | **`reference_audio`** (sólo comparative) o `reference_notes` | Renombrar campo; absolute no envía referencia |
| **Campo de audio** | `file` | **`audio`** | Corregido en el handoff (`CONSISTENCY_FIX.md`); simétrico con `reference_audio` |
| **202 body** | `{analysis_id,status}` | `{analysis_id,status,mode}` | Campo nuevo (aditivo) |
| **GET body** | sin `mode`/`metrics`; `pitch.reference` lista | `mode`, `metrics`, `pitch.reference` **nullable** | Consumidores deben tolerar `null` en absolute |
| **Códigos** | `FILE_TOO_LARGE`/`DURATION_TOO_LONG` | `AUDIO_TOO_LARGE`/`AUDIO_TOO_LONG` | Renombrar mapeo en Core |
| **HTTP** | `INVALID_MODE` 400; formato 415 | `INVALID_MODE` **422**; `UNSUPPORTED_FORMAT` **400**; `NO_AUDIO_TRACK` **400** | Ajustar tabla de errores |
| **Límites** | 20 MB / 300 s | **50 MB / 600 s** | Sin acción si el Core ya limita |
| **`/health`** | `{status,service,version,mode}` | `{status,service,version,checks,timestamp}`; **503** si degraded | Healthcheck de compose sigue funcionando (200/503) |
| **Versiones** | `1.0.0` / `0.4.0-align-scoring` | **`0.2.0`** / **`0.5.0-hybrid-modes`** | Trazabilidad |

---

## 3. `pytest -v` + cobertura (output completo real)

> Nota: el layout del proyecto es `app/core` y `app/main` (no `core/`/`main.py` en raíz),
> por eso la config usa `--cov=app.core --cov=app.main` (adaptación del O6).

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\HP\Documents\PROYECTOS\App-SyncDance\singing-service
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1, platformdirs-4.12.3, cov-7.1.0
collected 70 items

tests\test_absolute.py .....                                             [  7%]
tests\test_align.py ...............                                      [ 28%]
tests\test_busy.py ...                                                   [ 32%]
tests\test_comparative.py ......                                         [ 41%]
tests\test_contract.py ........                                          [ 52%]
tests\test_e2e.py ...                                                    [ 57%]
tests\test_health.py ....                                                [ 62%]
tests\test_log.py ...                                                    [ 67%]
tests\test_pitch.py ...                                                  [ 71%]
tests\test_preprocess.py ................                                [ 94%]
tests\test_store.py ....                                                 [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\HP\Documents\PROYECTOS\App-SyncDance\singing-service\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.6-final-0 _______________

Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
app\core\__init__.py       0      0   100%
app\core\config.py        16      0   100%
app\core\log.py            9      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py               34      4    88%   47-48, 54-55
----------------------------------------------------
TOTAL                    116      8    93%
======================= 70 passed, 1 warning in 23.39s ========================
```

**Objetivo ≥70 % en `core/`:** cumplido (`config` 100 %, `log` 100 %, `store` 93 %;
`main` 88 %). No falta cobertura crítica; las 8 líneas sin cubrir son ramas defensivas
(`store` expiración/eviction y `main` errores de import/disco).

---

## 4. curl real a `/health`

```powershell
curl.exe -s -w "`nHTTP_STATUS=%{http_code}`n" http://localhost:5000/health
```

```json
{"status":"ok","service":"singing-service","version":"0.2.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.0"},"models_loaded":{"ok":true},"disk_space_mb":954931},"timestamp":"2026-11-12T14:44:43.351337+00:00"}
HTTP_STATUS=200
```

---

## 5. curl real `mode=absolute` (WAV)

```powershell
curl.exe -s -w "`nHTTP_STATUS=%{http_code}" -X POST http://localhost:5000/api/v1/analyze `
  -F "file=@...\student_440.wav" -F "attempt_id=gap-abs-1" `
  -F "routine_id=rut-gap" -F "mode=absolute"
```

```json
{"analysis_id":"f574b2688dd9437b9ce0a9853d5a6b9f","status":"completed","mode":"absolute"}
HTTP_STATUS=202
```

`GET /api/v1/analyze/f574b2688dd9437b9ce0a9853d5a6b9f` (resumen real; `pitch.student`
tiene **94 frames** reales, recortado aquí; `pitch.reference` es `null`):

```json
{
  "mode": "absolute",
  "status": "completed",
  "algorithm_version": "0.5.0-hybrid-modes",
  "duration_sec": 3.0,
  "scores": {"vocal": 99, "afinacion": 100, "estabilidad": 100, "control_volumen": 96, "silence_pct": 0},
  "metrics": {
    "pitch_stability_cents": 0.0,
    "mean_pitch_hz": 439.8,
    "voiced_ratio": 1.0,
    "pitch_accuracy": null,
    "rhythm_accuracy": null,
    "average_cent_deviation": null
  },
  "segments": [],
  "feedback": [],
  "timings": {"preprocess_ms": 1090, "pitch_ms": 17428, "dtw_ms": 0, "scoring_ms": 286},
  "pitch_student_frames": 94,
  "pitch_reference_is_null": true,
  "first_student_frame": {"t": 0.0, "f0": 439.8, "voiced": true}
}
```

> `pitch_ms=17428` es el **primer** request real en el contenedor (JIT de numba/librosa frío).
> El siguiente request bajó a `pitch_ms=134` (§6). Ver próximo paso 5.

---

## 6. curl real `mode=comparative` (WAV + referencia)

```powershell
curl.exe -s -w "`nHTTP_STATUS=%{http_code}" -X POST http://localhost:5000/api/v1/analyze `
  -F "file=@...\student_460.wav" -F "reference_audio=@...\ref_440.wav" `
  -F "attempt_id=gap-cmp-1" -F "routine_id=rut-gap" -F "mode=comparative"
```

```json
{"analysis_id":"50dfedcd6f254ea4bf97f2a9378159ec","status":"completed","mode":"comparative"}
HTTP_STATUS=202
```

`GET /api/v1/analyze/50dfedcd6f254ea4bf97f2a9378159ec` (resumen real; curvas de 94 frames):

```json
{
  "mode": "comparative",
  "status": "completed",
  "duration_sec": 3.0,
  "scores": {"vocal": 49, "afinacion": 0, "estabilidad": 100, "control_volumen": 96, "silence_pct": 0},
  "metrics": {
    "pitch_stability_cents": 0.0,
    "mean_pitch_hz": 460.6,
    "voiced_ratio": 1.0,
    "pitch_accuracy": 0.0,
    "rhythm_accuracy": null,
    "average_cent_deviation": 80.0
  },
  "segments": [
    {"start": 0.0, "end": 3.0, "type": "out_of_tune", "expected_note": "A4", "sung_note": "A#4", "delta_cents": 80, "severity": "high"}
  ],
  "feedback": [
    {"code": "OUT_OF_TUNE", "message": "Desviación de hasta 80 cents (esperado A4, cantado A#4)."}
  ],
  "timings": {"preprocess_ms": 1008, "pitch_ms": 134, "dtw_ms": 9, "scoring_ms": 3},
  "pitch_student_frames": 94,
  "pitch_reference_frames": 94
}
```

**400 `MISSING_REFERENCE`** (comparative sin referencia):

```json
{"detail":{"code":"MISSING_REFERENCE","message":"mode=comparative requiere 'reference_audio' o 'reference_notes'"}}
HTTP_STATUS=400
```

**422 `INVALID_MODE`** (`mode=turbo`):

```json
{"detail":{"code":"INVALID_MODE","message":"mode debe ser 'absolute' o 'comparative'"}}
HTTP_STATUS=422
```

---

## 7. curl real con M4A (AAC)

```powershell
curl.exe -s -w "`nHTTP_STATUS=%{http_code}" -X POST http://localhost:5000/api/v1/analyze `
  -F "file=@...\intento.m4a" -F "attempt_id=gap-m4a-1" `
  -F "routine_id=rut-gap" -F "mode=absolute"
```

```json
{"analysis_id":"070d0254823341bf87d3e61b21d45ddb","status":"completed","mode":"absolute"}
HTTP_STATUS=202
```

`GET` (resumen real):

```json
{
  "mode": "absolute",
  "status": "completed",
  "duration_sec": 3.008,
  "scores": {"vocal": 99, "afinacion": 100, "estabilidad": 100, "control_volumen": 95, "silence_pct": 0},
  "metrics": {
    "pitch_stability_cents": 0.0,
    "mean_pitch_hz": 439.8,
    "voiced_ratio": 1.0,
    "pitch_accuracy": null,
    "rhythm_accuracy": null,
    "average_cent_deviation": null
  },
  "feedback": [],
  "timings": {"preprocess_ms": 359, "pitch_ms": 85, "dtw_ms": 0, "scoring_ms": 1}
}
```

---

## 8. Docker build + imágenes (tamaño final)

```
#12 [builder 5/5] RUN python -m pip install --prefix=/install -r requirements.txt
#12 4.434 Collecting ffmpeg-python==0.2.0 (from -r requirements.txt (line 15))
#12 4.489   Downloading ffmpeg_python-0.2.0-py3-none-any.whl.metadata (1.7 kB)
#12 89.72 Successfully installed ... fastapi-0.162.5 fastdtw-0.3.4 ffmpeg-python-0.2.0 future-1.0.0 ... librosa-1.0.0 llvmlite-0.50.0 numba-0.68.1 numpy-2.5.4 ...
#13 CACHED
#14 [stage-1 3/6] COPY --from=builder /install /usr/local
#14 DONE 24.5s
#17 [stage-1 6/6] RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
#17 DONE 4.6s
#18 exporting layers 57.1s done
#18 naming to docker.io/library/singing-service-singing-service:latest 0.0s done
#18 DONE 71.2s
 Image singing-service-singing-service Built
BUILD_EXIT=0
```

```
$ docker images --format "{{.Repository}}:{{.Tag}}  {{.Size}}"
singing-service-singing-service:latest  1.6GB
singing-service:latest                  1.59GB
singing-service:s0                      921MB
```

- **Tamaño final: 1.6 GB** (< 2 GB). Delta vs build anterior (1.59 GB): **≈ +10 MB**
  (`ffmpeg-python` + `future`); FFmpeg ya estaba en la imagen.
- Usuario: `docker compose exec -T singing-service id` → `uid=10001(appuser)`.
- `docker compose ps` → `Up (healthy)`.
- Tras la verificación se ejecutó `docker compose down` (entorno limpio).

---

## 9. Checklist Sprint 0 actualizado

| Ítem | Estado | Detalle |
|---|---|---|
| Estructura FastAPI/Dockerfile/requirements | **HECHO** | + `requirements-dev.txt`, `.env.example` |
| `docker compose up` | **HECHO** | `Up (healthy)` |
| `GET /health` 200 | **HECHO** | + checks y 503 degraded |
| `POST /api/v1/analyze` con `mode=absolute` | **HECHO** | §5 |
| `POST /api/v1/analyze` con `mode=comparative` | **HECHO** | §6 |
| Pitch `librosa.pyin` + Hz→nota | **HECHO** | `pitch.py`, `hz_to_note` |
| Test sine 440 → A4 | **HECHO** | `test_hz_to_note` + `mean_pitch_hz=439.8` |
| Métricas básicas | **HECHO** | `pitch_stability_cents`, `mean_pitch_hz`, `voiced_ratio` |
| Feedback (desafinación/sin voz/inestable/rango) | **HECHO** | `OUT_OF_TUNE`, `NO_VOICE`, `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE` |
| Dockerfile slim + ffmpeg + no-root | **HECHO*** | usa `python:3.14-slim` (no 3.12; decisión previa), ffmpeg ✓, no-root ✓ |
| Tests sintéticos + M4A/MP3 | **HECHO*** | sintéticos y transcodificados; **no hay audios reales en el repo** (pendiente §10) |
| README con curl de ejemplo | **HECHO** | curls POST absolute/comparative + integración Core |
| Formatos `.wav/.m4a/.mp3/.aac/.ogg` | **HECHO** | + flac/video; M4A probado end-to-end |
| Naming `SINGING_SERVICE_URL` | **HECHO** | docs + `.env.example` |
| `/health` con dependencias | **HECHO** | ffmpeg/librosa/models/disk |
| Cobertura ≥70 % en core | **HECHO** | 93 % (core: 100/100/93) |
| Ritmo | **DIFERIDO (O4-B)** | stub + `rhythm_accuracy=null` |
| `pitch_contour` | **DIFERIDO** | documentado; no expuesto |
| Celery `audio_queue` | **PENDIENTE (Core)** | contrato en `docs/celery-contract.md`; no se implementa aquí |

\* Desviaciones conscientes y documentadas.

---

## 10. Próximos pasos (5, con esfuerzo y responsable)

| # | Paso | Esfuerzo | Responsable |
|---|---|---|---|
| 1 | Implementar la task Celery del Core con `docs/celery-contract.md` (modo, referencia, timeouts 5/300, backoff 429/503) y smoke E2E Core↔servicio | **M** | **Equipo de Core** (yo apoyo con dudas del contrato) |
| 2 | Mover `singing-service/` al monorepo, compose raíz con `SINGING_SERVICE_URL`, rama `feature/singing-microservice` | **M** | **Equipo + yo** (bloqueado por acceso al monorepo) |
| 3 | Sprint 1: alineamiento avanzado (FastDTW) para comparative y ritmo real (O4-A: `beat_track`, tempo, onsets) | **L** | **Yo** |
| 4 | Audios reales de prueba en `tests/fixtures/audios/` (WAV/M4A con consentimiento) + CI que corra `pytest --cov` y `ruff` | **S** | **Yo** |
| 5 | Hardening de rendimiento: pre-calentar pyin/numba en startup (el primer request real tardó 17.4 s por JIT) y timeout/watchdog para pyin | **S** | **Yo** |

---

## 11. Decisiones y notas

- **O4 = Opción B (diferido a Sprint 1).** Justificación: `beat_track` es fiable con
  percusión/onsets, no con voz sostenida sin acompañamiento; sin alineamiento avanzado
  (Sprint 1) no hay base sólida para tempo/onsets. Se deja el stub explícito y
  `rhythm_accuracy=null` en ambos modos.
- **Comparación simple, no DTW:** `align_by_time()` remuestrea la referencia sobre los
  tiempos del alumno (tolerancia = 2 hops). `app/services/align.py` (FastDTW) se conserva
  con sus tests para Sprint 1, pero **no se usa en la ruta**.
- **`ffmpeg-python==0.2.0` instalado** (requisito O2) pero la conversión sigue por
  `subprocess` directo (ruta ya probada); queda disponible para probing/estandarización.
- **Mock retirado de la API:** `app/mock/data.py` se conserva como fixture de los valores
  de Figma, pero `mode=mock` ya no es válido (BREAKING documentado).
- **Cobertura:** el comando del O6 (`--cov=core --cov=main`) se adaptó a
  `--cov=app.core --cov=app.main` por el layout real (`app/`).
- **`Docs/integracion-core.md`** se actualizó por instrucción explícita O3, pese a la
  restricción general de no tocar fuera de `singing-service/`.
- **`pitch_contour`**: no se añadió al response; `include_contour=false` queda documentado
  como flag futuro.
