# FIX P0-01 — `X-Request-ID` + verificaciones V-01/V-02/V-03

> Fix autorizado de P0-01 (`X-Request-ID`) y verificaciones de lectura.
> Fecha: 2026-11-14. 76 tests, 93 % cobertura. No se tocó lógica de análisis.

## 1. Resumen y decisión

| Ítem | Resultado |
|---|---|
| P0-01 (`X-Request-ID`) | **CORREGIDO** (middleware + logs + errores + `/health`) |
| Tests | **76 passed** (71 + 5 de `test_request_id.py`) |
| `verify_handoff.sh` | **4/4 checks OK — HANDOFF OK** |
| V-01 (Content-Length falso) | **P1** (400 text/plain de uvicorn, sin JSON; servicio vivo) |
| V-02 (500 real) | **OK** (logs con traceback; body sin stack) |
| V-03 (NaN) | **OK** (JSON válido; `mean_pitch_hz=null`) |
| **¿Listo para Core?** | **SÍ** (P0-01 resuelto; V-01 es P1 documentado) |

## 2. Diff resumido

| Archivo | Cambio |
|---|---|
| `app/middleware/__init__.py` | **Nuevo** (paquete). |
| `app/middleware/request_id.py` | **Nuevo**: `RequestIDMiddleware`, `RequestIDLogFilter`, `get_request_id()` (ContextVar). Valida `^[A-Za-z0-9_-]{1,128}$`, reutiliza o genera `uuid4().hex`, añade header a todas las respuestas y convierte excepciones no capturadas en `500 UNHANDLED_ERROR` con `request_id` + `logger.error(..., exc_info=True)`. |
| `app/main.py` | `app.add_middleware(RequestIDMiddleware)`; filtro en logger `singing`; handlers `StarletteHTTPException` y `RequestValidationError` con `request_id`; `/health` incluye `request_id`; ejemplos OpenAPI actualizados. |
| `app/core/log.py` | `log_event` incluye `"request_id": get_request_id()` en cada línea JSON. |
| `app/api/routes/analyze.py` | **Solo metadata**: ejemplos de error OpenAPI con `request_id` (sin cambios de lógica). |
| `tests/test_request_id.py` | **Nuevo**: 5 tests (generado, eco, inválido, 400, 422). |
| `tests/snapshots/openapi_v1.json` | Regenerado por los ejemplos con `request_id`. |
| `docs/celery-contract.md` | §2 header `X-Request-ID`; §5 nota de request_id/`UNHANDLED_ERROR`. |
| `docs/USAGE.md` | Sección "Request ID"; health/404 actualizados con `request_id`. |
| `docs/TROUBLESHOOTING.md` | Fila de cliente malformado (V-01). |
| `CHANGELOG.md` | `[0.2.2] — Fix P0-01`. |

**Sin cambios en el pipeline de análisis** (`preprocess`, `pitch`, `compare`, `metrics`,
`scoring`, `feedback`).

## 3. Evidencia P0-01

### 3.1 POST sin `X-Request-ID` (header generado)

```powershell
curl.exe -s -D - -o NUL -X POST http://localhost:5000/api/v1/analyze `
  -F "audio=@integration/fixtures/sine_440hz_5s.wav" `
  -F "attempt_id=rid-noheader" -F "routine_id=rid" -F "mode=absolute"
```

```
HTTP/1.1 202 Accepted
x-request-id: 4c8f1a0c24b84c53a8cd545fddf8b757
```

### 3.2 POST con `X-Request-ID: abc-123` (eco)

```
HTTP/1.1 202 Accepted
x-request-id: abc-123
```

### 3.3 Error 400 (header + body con `request_id`)

```
HTTP/1.1 400 Bad Request
x-request-id: rid-400
{"detail":{"code":"INVALID_AUDIO","message":"No se pudo decodificar el audio","request_id":"rid-400"}}
```

### 3.4 Error 422 de FastAPI (header + body top-level)

```
HTTP/1.1 422 Unprocessable Content
x-request-id: rid-422
{"detail":[{"type":"missing","loc":["body","audio"],"msg":"Field required","input":null}],"request_id":"rid-422"}
```

### 3.5 `/health` con `request_id`

```json
{"status":"ok","service":"singing-service","version":"0.2.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.1"},"models_loaded":{"ok":true},"disk_space_mb":952673},"request_id":"f126e66412cd4ad9aeea35ee425129a8","timestamp":"2026-11-14T19:33:49.158075+00:00"}
```

### 3.6 Log real con `request_id`

```
singing-service  | {"ts": "2026-11-14T19:34:10+00:00", "request_id": "4c8f1a0c24b84c53a8cd545fddf8b757", "event": "analysis_accepted", "analysis_id": "3cdd3911c74245be8ccf31a6a51c45bc", "attempt_id": "rid-noheader", "routine_id": "rid", "mode": "absolute", "algorithm_version": "0.5.0-hybrid-modes", "duration_sec": 5.0, "vocal": 99, "timings": {"preprocess_ms": 597, "pitch_ms": 20721, "dtw_ms": 0, "scoring_ms": 33}}
```

## 4. Tests y handoff

### `pytest -v` (76 passed)

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\HP\Documents\PROYECTOS\App-SyncDance\singing-service
configfile: pyproject.toml
testpaths: tests, integration
plugins: anyio-4.15.1, platformdirs-4.12.3, cov-7.1.0
collected 76 items

tests\test_absolute.py .....                                             [  6%]
tests\test_align.py ...............                                      [ 26%]
tests\test_busy.py ...                                                   [ 30%]
tests\test_comparative.py ......                                         [ 38%]
tests\test_contract.py ........                                          [ 48%]
tests\test_e2e.py ...                                                    [ 52%]
tests\test_health.py ....                                                [ 57%]
tests\test_log.py ...                                                    [ 61%]
tests\test_pitch.py ...                                                  [ 65%]
tests\test_preprocess.py ................                                [ 86%]
tests\test_request_id.py .....                                           [ 93%]
tests\test_store.py ....                                                 [ 98%]
integration\test_error_scenarios.py .                                    [100%]

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
app\core\log.py           10      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py               55      5    91%   81, 112-113, 119-120
----------------------------------------------------
TOTAL                    138      9    93%
======================= 76 passed, 1 warning in 29.49s ========================
```

### `verify_handoff.sh`

```
=== singing-service :: verify_handoff ===
service_dir : /c/Users/HP/Documents/PROYECTOS/App-SyncDance/singing-service
python      : /c/Users/HP/Documents/PROYECTOS/App-SyncDance/singing-service/.venv/Scripts/python.exe
analyze_url : http://localhost:5000/api/v1/analyze

-- 1/4 docker compose up + health --
docker compose up: OK
[PASS] health 200 (http://localhost:5000/health)

-- 2/4 fixtures --
fixtures: OK (9 archivos)

-- 3/4 simulacion de worker (absolute + comparative) --
[PASS] simulate absolute
[PASS] simulate comparative

-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

> El fixture `nan.wav` de V-03 queda en `integration/fixtures/` (gitignored); por eso
> el generador reporta 9 archivos.

## 5. V-01 — Content-Length falso (solo verificación)

Comando (con `-v`):

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -H "Content-Length: 10000" \
  -F "audio=@integration/fixtures/sine_440hz_5s.wav" \
  -F "mode=absolute" -v
```

Salida real relevante:

```
Invalid HTTP request received.
...
< HTTP/1.1 400 Bad Request
< content-type: text/plain; charset=utf-8
< content-length: 30
```

- **Código HTTP:** `400 Bad Request`.
- **Body:** `Invalid HTTP request received.` (texto plano, 30 bytes; **no JSON**).
- **Servicio vivo:** `/health` → `200`.
- **Log con request_id:** **no** (uvicorn rechaza la petición en el parser HTTP antes
  de que corra el middleware; el log es `Invalid HTTP request received.`).
- **Clasificación:** 🟠 **P1** — 400 sin JSON; documentado en
  `docs/TROUBLESHOOTING.md`. No es 200 vacío ni 5xx, y el contenedor sigue sano.

**No se aplicó fix** (solo verificación, según instrucciones).

## 6. V-02 — 500 real (solo verificación)

Se forzó con un harness de test (no se modificó el servicio): se añadió una ruta
temporal `/__boom` que lanza `RuntimeError` y se llamó con `TestClient`.

Código del handler (middleware):

```python
try:
    response = await call_next(request)
except Exception as exc:
    logger.error(
        json.dumps({
            "ts": datetime.now(UTC).isoformat(),
            "request_id": request_id,
            "event": "unhandled_exception",
            "error": type(exc).__name__,
        }, ensure_ascii=False),
        exc_info=True,
    )
    response = JSONResponse(
        status_code=500,
        content={"detail": {
            "code": "UNHANDLED_ERROR",
            "message": "Error interno no controlado",
            "request_id": request_id,
        }},
    )
```

Salida real:

```
STATUS: 500
HEADER: v02-abc
BODY: {"detail":{"code":"UNHANDLED_ERROR","message":"Error interno no controlado","request_id":"v02-abc"}}
```

Log real (JSON + traceback):

```
{"ts": "2026-11-14T19:34:54.891095+00:00", "request_id": "v02-abc", "event": "unhandled_exception", "error": ...
File "C:\...\app\middleware\request_id.py", line 52, in ...
RuntimeError: boom-v02
```

- **Logs con stack:** **SÍ** (`exc_info=True`).
- **Body con stack:** **NO** (solo `code`/`message`/`request_id`).
- **Clasificación:** ✅ **OK**.

## 7. V-03 — NaN en JSON (solo verificación)

Generación:

```python
import numpy as np, soundfile as sf
sf.write("integration/fixtures/nan.wav", np.array([np.nan] * 44100), 44100)
```

> El comando del enunciado no incluía `attempt_id`/`routine_id` (obligatorios); se
> añadieron para que el análisis se ejecutara.

POST → `202`, GET del resultado → `1980 bytes`. `jq` no está instalado en el entorno;
se usó un parser JSON estricto (rechaza `NaN`/`Infinity`):

```
JSON_STRICT=OK
contains_NaN_literal= False
mean_pitch_hz= None
scores.vocal= 0
voiced_ratio= 0.0
status= completed mode= absolute
```

- **JSON válido:** **SÍ** (`JSON_STRICT=OK`, sin `NaN` literal).
- **`mean_pitch_hz`:** `null`.
- **`scores.vocal`:** `0` (válido; el contrato usa `scores.vocal`, no `overall_score`).
- **Clasificación:** ✅ **OK**; documentado como comportamiento aceptable.

## 8. Cierre

```
pytest -v: 76 passed, 1 warning in 29.49s (cobertura 93%)
bash integration/verify_handoff.sh: 4/4 checks OK — HANDOFF OK
ruff check .: All checks passed!
```

- **Contrato:** no se rompió; el header `X-Request-ID` es aditivo y los bodies de error
  añaden `request_id`. El snapshot OpenAPI se regeneró por los ejemplos.
- **Lógica de análisis:** intacta (`preprocess`, `pitch`, `compare`, `metrics`,
  `scoring`, `feedback` sin cambios).
- **`core-api/`:** intacto (no existe).
- **Documentos históricos:** `ESTADO_ACTUAL.md`, `CIERRE_GAPS_SPRINT0.md`,
  `HANDOFF_CORE.md`, `CONSISTENCY_FIX.md`, `AUDITORIA_v0.2.0.md` no se modificaron.
- **Decisión final:** **SÍ para Core.** P0-01 resuelto; V-01 queda como P1 documentado
  (cliente HTTP malformado), V-02 y V-03 en OK.
