# CIERRE_HU_S1_05 — Timeout interno + `/metrics` Prometheus

> Rama `sprint2` (desde `sprint1`/`v0.3.0`). Tag `v0.3.0` intacto en `0016e2e`.
> Fecha: 2026-11-16 · 123 tests por defecto + 3 integración (126) · 98 % · ruff OK · HANDOFF OK.

## 1. Diff resumido

```text
 singing-service/CHANGELOG.md                    |  23 ++
 singing-service/app/api/routes/analyze.py       | 517 +++++++++++++++---------
 singing-service/app/core/config.py              |   5 +
 singing-service/app/main.py                     |  20 +-
 singing-service/docs/ARCHITECTURE.md            |  39 +-
 singing-service/docs/SPRINT1_BACKLOG.md         |  10 +-
 singing-service/docs/USAGE.md                   |  21 +
 singing-service/docs/celery-contract.md         |  10 +
 singing-service/requirements.txt                |   1 +
 singing-service/tests/snapshots/openapi_v1.json |  34 ++
 10 files changed, 465 insertions(+), 215 deletions(-)

Nuevos:
  singing-service/app/metrics.py
  singing-service/docs/SPRINT2_BACKLOG.md
  singing-service/tests/test_hu_s1_05.py
```

El diff grande de `analyze.py` es en su mayoría indentación: el bloque de
procesamiento queda dentro del `try/finally` que mide `active_requests` y la
latencia total. La lógica de pitch/ritmo/scoring no cambia.

## 2. Implementación

### 2.1 Timeouts (`app/core/config.py`)

| Env var | Default | Validación | Fase |
|---|---|---|---|
| `PYIN_TIMEOUT_SECONDS` | `120.0` | `0 < x < 300` | `librosa.pyin` (alumno y referencia) |
| `ALIGN_TIMEOUT_SECONDS` | `30.0` | `0 < x < 120` | `align_frames` (FastDTW) |

`Field(gt=0, lt=...)`: un env inválido falla en el startup, no por request.

### 2.2 Timeout real (`app/api/routes/analyze.py`)

Se usa un `ThreadPoolExecutor` dedicado + `asyncio.wait_for`. **Motivo:** el
endpoint es async, pero `run_in_threadpool` (anyio) usa
`abandon_on_cancel=False`: cancelar el await **espera** a que el hilo termine, así
que no sirve para timeout. Un Future de `loop.run_in_executor` sí se abandona al
vencer `wait_for`.

Al vencer:

```json
{"detail":{"code":"ANALYSIS_TIMEOUT","message":"El análisis excedió el timeout en la fase 'pyin'","request_id":"..."}}
```

HTTP **504**, con `request_id` del middleware. `analysis_timeouts_total{phase}` se
incrementa. El timeout de alineación **no** cae al fallback `align_by_time`: se
relanza como 504 (`except HTTPException: raise` antes del `except Exception`).

**Limitación documentada:** librosa/FastDTW no son interrumpibles. El request
responde y libera el semáforo, pero el hilo huérfano sigue hasta terminar; el
executor (`max_workers=max(4, MAX_CONCURRENT_ANALYSES)`) acota cuántos se acumulan.

### 2.3 `/metrics` (`app/metrics.py` + `app/main.py`)

`prometheus-client==0.21.0` (instalado sin conflictos).

- `analysis_requests_total{mode,status}` — Counter.
- `analysis_duration_seconds{mode}` — Histogram (0.5, 1, 2, 5, 10, 30, 60, 120, 300).
- `pitch_duration_seconds` — Histogram.
- `align_duration_seconds{method}` — Histogram (`fastdtw`/`time`).
- `rhythm_duration_seconds` — Histogram.
- `active_requests` — Gauge.
- `analysis_timeouts_total{phase}` — Counter.

`GET /metrics` → `Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)`.
Sin auth (red interna, consistente con `/health`).

## 3. Evidencia

### 3.1 `pytest -v` (local)

```text
tests\test_hu_s1_05.py ........                                          [ 74%]
...
=============== 123 passed, 3 deselected, 2 warnings in 21.30s ================
```

### 3.2 `pytest -m integration -v` (local)

```text
================ 3 passed, 123 deselected, 1 warning in 5.72s =================
```

### 3.3 `ruff check .`

```text
All checks passed!
```

### 3.4 Docker (imagen reconstruida con prometheus-client)

```text
$ docker compose build singing-service
...
Successfully installed ... prometheus-client-0.21.0 ...
 Image singing-service-singing-service Built

$ docker compose exec -T singing-service python -m pytest --no-cov
123 passed, 3 deselected, 2 warnings in 17.02s

$ docker compose exec -T singing-service python -m pytest -m integration --no-cov
1 passed, 2 skipped, 123 deselected, 1 warning in 1.03s
# 2 skipped: fixtures MASTmelody no se copian a la imagen
```

### 3.5 HANDOFF

```text
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

### 3.6 `GET /metrics` — primeras 20 líneas (real, Docker)

```text
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 117294.0
python_gc_objects_collected_total{generation="1"} 135002.0
python_gc_objects_collected_total{generation="2"} 31493.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 340.0
python_gc_collections_total{generation="1"} 30.0
python_gc_collections_total{generation="2"} 2.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="14",patchlevel="6",version="3.14.6"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
```

### 3.7 Tras 1 `/analyze` — grep de counters (real, Docker)

```text
$ curl -s -X POST http://localhost:5000/api/v1/analyze \
    -F "audio=@hu105.wav" -F "attempt_id=hu105-docker-evidence" \
    -F "routine_id=r-hu105" -F "mode=absolute"
{"analysis_id":"30829c330a9d404f8d81ea1bcf2af251","status":"completed","mode":"absolute"}

$ curl -s http://localhost:5000/metrics | grep 'analysis_requests_total{mode="absolute",status="success"}'
analysis_requests_total{mode="absolute",status="success"} 1.0

$ curl -s http://localhost:5000/metrics | grep 'analysis_duration_seconds_count{mode="absolute"}'
analysis_duration_seconds_count{mode="absolute"} 1.0
```

### 3.8 Timeout simulado (real, local; `PYIN_TIMEOUT_SECONDS=0.5` + mock lento)

```text
{"ts": "2026-11-16T15:39:38+00:00", "request_id": "timeout-evidence", "event": "analysis_timeout", "attempt_id": "hu105-timeout-evidence", "phase": "pyin", "timeout_sec": 0.5}
{"ts": "2026-11-16T15:39:38+00:00", "request_id": "timeout-evidence", "event": "analysis_failed", "attempt_id": "hu105-timeout-evidence", "code": "ANALYSIS_TIMEOUT", "http_status": 504}
HTTP Request: POST http://testserver/api/v1/analyze "HTTP/1.1 504 Gateway Timeout"
status: 504
body: {"detail":{"code":"ANALYSIS_TIMEOUT","message":"El análisis excedió el timeout en la fase 'pyin'","request_id":"timeout-evidence"}}
x-request-id: timeout-evidence
semaphore_value: 2
```

## 4. Confirmaciones

- **Contrato no roto:** `POST /analyze` mantiene el mismo request/response
  (`202 {analysis_id,status,mode}`); solo se añade el código de error
  `ANALYSIS_TIMEOUT` (504) y el endpoint `/metrics`. Snapshot OpenAPI regenerado
  conscientemente (`+34` líneas: `/metrics` y `responses.504`).
- **`core-api/` intacto:** no existe en este workspace y no se tocó nada fuera de
  `singing-service/`.
- **Tag `v0.3.0` intacto:**

```text
$ git rev-parse v0.3.0^{commit}
0016e2e65266ea6086e8c50253932497668e5e8d
```

- **Sin tag ni merge:** no se creó `v0.4.0` ni se hizo merge a `master`.

## 5. Limitaciones y seguimiento

- El hilo huérfano de librosa/FastDTW sigue hasta terminar tras el 504; el
  executor lo acota. Si se observan acumulaciones, bajar `PYIN_TIMEOUT_SECONDS`
  o escalar réplicas.
- `test_metrics_*` usan deltas (antes/después) porque los counters son globales al
  proceso y otros tests ya generan análisis; el valor `1.0` se muestra en la
  evidencia de un contenedor recién arrancado.
- HU-S1-05 queda ✅ en `docs/SPRINT2_BACKLOG.md`; el tag `v0.4.0` se crea al final
  de Sprint 2 (HU-S1-07).
