# DOCS_CONTINUATION — cierre de contrato + documentación Sprint 1

> Continuación de documentación de `singing-service` tras el Sprint 0.
> Fecha: 2026-11-12 (UTC). Servicio: v0.2.0, **71 tests**, 93 % cobertura.
> No se tocó `app/` (salvo documentación) ni `core-api/` (no existe).

## 1. Árbol de documentación y archivos nuevos

```
singing-service/
├── README.md                     # NUEVO: índice (punto de entrada)
├── CHANGELOG.md                  # NUEVO: Keep a Changelog + SemVer
├── CONTRIBUTING.md               # NUEVO: guía de contribución
├── docs/
│   ├── celery-contract.md        # ACTUALIZADO: nota §5 + guard §6
│   ├── ARCHITECTURE.md           # NUEVO: arquitectura interna + Mermaid
│   ├── SPRINT1_BACKLOG.md        # NUEVO: backlog Sprint 1
│   └── TROUBLESHOOTING.md        # NUEVO: problemas comunes + debug audio
├── integration/
│   ├── simulate_celery_worker.py # ACTUALIZADO: classify_response (guard)
│   ├── test_error_scenarios.py   # ACTUALIZADO: 9º check 5xx sin JSON + pytest
│   └── README.md                 # ACTUALIZADO: tabla de errores alineada con §5
├── pyproject.toml                # ACTUALIZADO: testpaths tests+integration
└── ../DOCS_CONTINUATION.md       # NUEVO: este reporte (raíz del workspace)
```

Fechas usadas en `CHANGELOG.md` (no hay git en el workspace):

- **0.1.0 — 2026-10-06:** registro de S0 en `Docs/plan-implementacion-singing-service.md`.
- **0.2.0 — 2026-11-12:** cierre de gaps y handoff (informes del workspace).

## 2. Diff resumido por archivo

| Archivo | Qué se añadió / cambió | Por qué |
|---|---|---|
| `docs/celery-contract.md` | §5: tabla sólo con códigos emitidos + **nota de wire real**; §6: guard de 5xx sin JSON y distinción 2xx/4xx/5xx/timeout | Cerrar el matiz `INTERNAL_ERROR`/`SERVICE_DEGRADED` y evitar `KeyError` en 5xx no-JSON |
| `integration/simulate_celery_worker.py` | `classify_response()` (ok/fail/retry) y uso en el simulador | Compartir la misma lógica que la tarea Celery; testeable |
| `integration/test_error_scenarios.py` | 9º check `5xx_sin_json` (mini servidor `http.server` 500 sin JSON) + `test_5xx_without_json_is_recoverable` | Verificar que el guard trata el caso como recuperable, sin `KeyError` |
| `integration/README.md` | Tabla de errores sólo con códigos emitidos + nota de wire real | Evitar contradicción con el contrato §5 |
| `pyproject.toml` | `testpaths = ["tests", "integration"]` | Que pytest recoja el test de guard → 71 passed |
| `CHANGELOG.md` | Historia real 0.1.0/0.2.0, BREAKING y diferidos | Trazabilidad de versiones |
| `docs/SPRINT1_BACKLOG.md` | HU-S1-01…07 + fuera de alcance | Planificación del siguiente sprint |
| `docs/ARCHITECTURE.md` | Componentes reales, flujo Mermaid, decisiones y riesgos | Dejar el repo autoexplicativo |
| `docs/TROUBLESHOOTING.md` | Tabla de síntomas + debug de audio (ffprobe/ffmpeg/sox) | Soporte operativo |
| `CONTRIBUTING.md` | Setup, flujo, cobertura real, checklist y reglas | Onboarding sin romper contrato |
| `README.md` | Reescrito como índice con links verificados | Punto de entrada único |

**Correcciones de exactitud respecto al borrador:**

- `ARCHITECTURE.md` documenta la estructura real (`app/services/pitch.py`, `feedback.py`,
  `compare.py`; `app/core/` es config/log/store) en vez de `core/pitch_detector.py`.
- El endpoint es **`async def` + `run_in_threadpool`**, no `def` sync.
- Uvicorn corre con **1 worker** (el escalado es horizontal), no “N workers configurable”.
- `CONTRIBUTING.md` usa `pytest -v` (addopts `--cov=app.core --cov=app.main`), no
  `--cov=core` (el paquete real es `app.core`).
- `CHANGELOG.md` no atribuye `severity`/timestamps a `feedback` (van en `segments`).

## 3. `pytest -v` (output real, 71 passed)

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\HP\Documents\PROYECTOS\App-SyncDance\singing-service
configfile: pyproject.toml
testpaths: tests, integration
plugins: anyio-4.15.1, platformdirs-4.12.3, cov-7.1.0
collected 71 items

tests\test_absolute.py .....                                             [  7%]
tests\test_align.py ...............                                      [ 28%]
tests\test_busy.py ...                                                   [ 32%]
tests\test_comparative.py ......                                         [ 40%]
tests\test_contract.py ........                                          [ 52%]
tests\test_e2e.py ...                                                    [ 56%]
tests\test_health.py ....                                                [ 61%]
tests\test_log.py ...                                                    [ 66%]
tests\test_pitch.py ...                                                  [ 70%]
tests\test_preprocess.py ................                                [ 92%]
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
app\core\log.py            9      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py               34      4    88%   47-48, 54-55
----------------------------------------------------
TOTAL                    116      8    93%
======================= 71 passed, 1 warning in 13.30s ========================
```

## 4. `python integration/test_error_scenarios.py` (output real, 9/9)

```
Servicio OK: http://localhost:5000/health -> 200

[PASS] mode_invalido: HTTP 422 code=INVALID_MODE (esperado 422/INVALID_MODE)
[PASS] comparative_sin_referencia: HTTP 400 code=MISSING_REFERENCE (esperado 400/MISSING_REFERENCE)
[PASS] audio_mayor_50mb: HTTP 413 code=AUDIO_TOO_LARGE (esperado 413/AUDIO_TOO_LARGE)
[PASS] audio_mayor_600s: HTTP 413 code=AUDIO_TOO_LONG (esperado 413/AUDIO_TOO_LONG)
[PASS] txt_renombrado_a_wav: HTTP 400 code=INVALID_AUDIO (esperado 400/INVALID_AUDIO)  NOTE: el servicio clasifica datos corruptos como INVALID_AUDIO (no UNSUPPORTED_FORMAT)
[PASS] extension_txt_no_soportada: HTTP 400 code=UNSUPPORTED_FORMAT (esperado 400/UNSUPPORTED_FORMAT)
[PASS] sin_campo_audio: HTTP 422 code=VALIDATION_ERROR (body.audio: Field required) (esperado 422/None)
[PASS] servicio_caido: ConnectionError (sin respuesta 5xx)
[PASS] 5xx_sin_json: action=retry reason=Non-JSON response 500

RESUMEN: 9/9 checks OK
```

## 5. `bash integration/verify_handoff.sh` (output real)

```
=== singing-service :: verify_handoff ===
service_dir : /c/Users/HP/Documents/PROYECTOS/App-SyncDance/singing-service
python      : /c/Users/HP/Documents/PROYECTOS/App-SyncDance/singing-service/.venv/Scripts/python.exe
analyze_url : http://localhost:5000/api/v1/analyze

-- 1/4 docker compose up + health --
docker compose up: OK
[PASS] health 200 (http://localhost:5000/health)

-- 2/4 fixtures --
fixtures: OK (8 archivos)

-- 3/4 simulacion de worker (absolute + comparative) --
[PASS] simulate absolute
[PASS] simulate comparative

-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 6. Contenido de la nota §5 y del guard §6

### Nota de wire real (`docs/celery-contract.md` §5)

> **Nota de wire real.** El `singing-service` **no** emite `INTERNAL_ERROR` ni
> `SERVICE_DEGRADED`. Esos códigos son responsabilidad del Core al envolver la
> respuesta. Los únicos códigos que el servicio emite son los listados en la tabla. Si
> el worker de Core recibe un **5xx sin body JSON parseable** (crash no capturado,
> timeout del proxy, respuesta truncada), debe tratarlo como error recuperable:
> reintentar con backoff exponencial (máx. 3) y, si persiste, marcar el `Attempt` como
> `fallido` y alertar. El Core es quien mapea ese caso a su propio `INTERNAL_ERROR`
> antes de persistir.
>
> `VALIDATION_ERROR` es la etiqueta del Core para la **lista** de validación de FastAPI
> (`detail` es un array, no un objeto con `code`).

### Guard de §6 (tarea Celery de ejemplo)

```python
def _code(body: object) -> str:
    """Extrae detail.code del body JSON del servicio."""
    if not isinstance(body, dict):
        return "UNKNOWN"
    detail = body.get("detail")
    if isinstance(detail, dict):
        return detail.get("code", "UNKNOWN")
    return "VALIDATION_ERROR"


@shared_task(
    bind=True,
    autoretry_for=(httpx.TransportError,),   # timeout / conexión rechazada
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=330,
    time_limit=360,
)
def analyze_vocal(self, attempt_id, routine_id, audio_path, reference_path=None):
    # ... construccion de data/files (audio + reference_audio) ...

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(ANALYZE_URL, data=data, files=files)

            # 429: saturado -> recuperable
            if response.status_code == 429:
                raise self.retry(countdown=15)

            # 5xx: recuperable. Guard: un 5xx sin JSON no debe lanzar KeyError.
            if response.status_code >= 500:
                try:
                    body = response.json()
                except ValueError:
                    # 5xx sin JSON parseable -> error recuperable
                    raise self.retry(
                        exc=RuntimeError(
                            f"Non-JSON response {response.status_code}"
                        ),
                        countdown=2 ** self.request.retries,
                    )
                raise self.retry(
                    exc=RuntimeError(
                        f"Service error {response.status_code} code={_code(body)}"
                    ),
                    countdown=30,
                )

            # 4xx: error del cliente -> NO reintentar
            if 400 <= response.status_code < 500:
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                code = _code(body)
                _persist_failure(attempt_id, code)
                return {"status": "failed", "code": code}

            # 2xx: éxito
            response.raise_for_status()
            analysis_id = response.json()["analysis_id"]

            result = client.get(f"{ANALYZE_URL}/{analysis_id}", timeout=10.0)
            result.raise_for_status()
            payload = result.json()
            _persist_result(attempt_id, payload)
            return {"status": "completed", "analysis_id": analysis_id}
    except SoftTimeLimitExceeded:
        _persist_failure(attempt_id, "WORKER_TIMEOUT")
        raise
    finally:
        files["audio"][1].close()
        if reference_handle is not None:
            reference_handle.close()
```

> El ejemplo usa `_code(body)` en vez de `body.get("code")` porque el servicio
> devuelve `detail.code`; el snippet del enunciado con `body.get("code")` devolvería
> `None`. La estructura del guard (try/except ValueError → retry) es la pedida.

## 7. Links del README (verificación real)

Comando (Python, relativo a `singing-service/`):

```bash
python - <<'PY'
import re
from pathlib import Path
files = [Path("README.md"), Path("CONTRIBUTING.md"), Path("CHANGELOG.md")]
files += sorted(Path("docs").glob("*.md"))
files += [Path("integration/README.md")]
missing = 0
for f in files:
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", f.read_text(encoding="utf-8")):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (f.parent / link.split("#")[0]).resolve()
        if not target.exists():
            missing += 1
            print(f"MISSING {f}: {link}")
print(f"MISSING_TOTAL={missing}")
PY
```

Resultado real (tabla del README):

| Link del README | Destino | Existe |
|---|---|---|
| `docs/celery-contract.md` | `singing-service/docs/celery-contract.md` | OK |
| `docs/ARCHITECTURE.md` | `singing-service/docs/ARCHITECTURE.md` | OK |
| `docs/SPRINT1_BACKLOG.md` | `singing-service/docs/SPRINT1_BACKLOG.md` | OK |
| `docs/TROUBLESHOOTING.md` | `singing-service/docs/TROUBLESHOOTING.md` | OK |
| `integration/README.md` | `singing-service/integration/README.md` | OK |
| `CHANGELOG.md` | `singing-service/CHANGELOG.md` | OK |
| `CONTRIBUTING.md` | `singing-service/CONTRIBUTING.md` | OK |
| `../HANDOFF_CORE.md` | `App-SyncDance/HANDOFF_CORE.md` | OK |
| `../CONSISTENCY_FIX.md` | `App-SyncDance/CONSISTENCY_FIX.md` | OK |
| `../Docs/plan-implementacion-singing-service.md` | `App-SyncDance/Docs/plan-implementacion-singing-service.md` | OK |

`MISSING_TOTAL=0` (también se comprobaron los links internos de `docs/` y
`integration/README.md`: 0 rotos).

## 8. Confirmaciones

- **No se tocó `app/`.** La Tarea 0.2 es documentación (ejemplo Celery en
  `docs/celery-contract.md`); la Tarea 0.3 es código de `integration/`. No hubo cambios
  de lógica del endpoint ni de `app/`.
- **No se tocó `core-api/`** (no existe en el workspace).
- **No se implementó** `rhythm_eval` real, `pitch_contour` ni FastDTW; el backlog los
  describe como Sprint 1.
- **Contrato:** sólo se añadió la nota de wire real y el guard de 5xx; el resto del
  contrato (campos, modos, códigos emitidos) no cambió.
- **Documentos históricos** (`ESTADO_ACTUAL.md`, `CIERRE_GAPS_SPRINT0.md`,
  `HANDOFF_CORE.md`, `CONSISTENCY_FIX.md`) no se reescribieron; el README los enlaza.
