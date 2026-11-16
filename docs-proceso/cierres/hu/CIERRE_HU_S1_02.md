# CIERRE_HU_S1_02 — `/ready` + `/version`

> HU-S1-02 implementada en la rama `sprint1`. Base `v0.2.3` (`f744a8e`).
> Versión de trabajo: **0.3.0-dev**. Fecha: 2026-11-15.
> **92 tests**, **97 % cobertura**, `ruff` OK, **HANDOFF OK**.

## 1. Diff resumido

| Archivo | Cambio |
|---|---|
| `app/main.py` | `AppState` (`ready`/`shutting_down`), lifespan con self-test, `GET /ready`, `GET /version`; `/health` pasa a `async def` + `run_in_threadpool` (mismo shape). |
| `app/core/config.py` | `settings.version` 0.2.0 → **0.3.0**. |
| `Dockerfile` | `ARG GIT_SHA=unknown` / `ARG BUILD_TIME=unknown` + `ENV` en la etapa final. |
| `docker-compose.yml` | `build.args` con `GIT_SHA`/`BUILD_TIME` (`${VAR:-unknown}`). |
| `tests/test_hu_s1_02.py` | **Nuevo**: 9 tests (`/ready` 200/warmup/shutting_down/ffmpeg_unavailable, `/version` env/unknown/campos/header, `_pkg_version` unknown, lifespan). |
| `tests/test_health.py` | Aserciones de versión 0.3.0. |
| `tests/snapshots/openapi_v1.json` | Regenerado (nuevos endpoints + 0.3.0). |
| `docs/celery-contract.md` | §4.1 endpoints de sistema (`/ready`, `/version`), liveness vs readiness. |
| `docs/USAGE.md` | `/ready` y `/version` con curl y respuestas reales; `/health` 0.3.0. |
| `docs/ARCHITECTURE.md` | §6.1 build metadata (`GIT_SHA`/`BUILD_TIME`); contador de tests. |
| `CHANGELOG.md` | `[0.3.0-dev]`. |
| `README.md` / `CONTRIBUTING.md` | Estado v0.3.0-dev y 92 tests. |

## 2. Tests y cobertura

```
Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
app\core\__init__.py       0      0   100%
app\core\config.py        16      0   100%
app\core\log.py           10      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py              101      2    98%   105-106
----------------------------------------------------
TOTAL                    184      6    97%
======================== 92 passed, 1 warning in 9.94s ========================
```

- 83 previos + 9 nuevos = **92**.
- Las 2 líneas no cubiertas de `app/main.py` son la rama de fallo del self-test
  (`log_event` + `sys.exit(1)`); el resto del lifespan está cubierto.
- `ruff check .` → `All checks passed!`.

## 3. Handoff

```
-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 4. Evidencia de endpoints (servicio real)

`GET /ready` → **200**:

```json
{"ready":true,"reason":null,"request_id":"bbad70aa396342e18d128fc66c36b64e"}
```

`GET /version` → **200**:

```json
{"version":"0.3.0","git_sha":"abc1234","build_time":"2026-11-15T12:00:00Z","python":"3.14.6","ffmpeg":"7.1.5-0+deb13u1","fastapi":"0.142.2","librosa":"1.0.0","request_id":"5ec99b15ffe14d359cefd91c6b2ba045"}
```

`GET /version` con `X-Request-ID: test-123`:

```
HTTP/1.1 200 OK
x-request-id: test-123
{"version":"0.3.0","git_sha":"abc1234","build_time":"2026-11-15T12:00:00Z","python":"3.14.6","ffmpeg":"7.1.5-0+deb13u1","fastapi":"0.142.2","librosa":"1.0.0","request_id":"test-123"}
```

`/health` (mismo shape, versión 0.3.0):

```json
{"status":"ok","service":"singing-service","version":"0.3.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.0"},"models_loaded":{"ok":true},"disk_space_mb":945681},"request_id":"1179d2d633aa4d15a6ec751ef01f2c2c","timestamp":"2026-11-15T19:40:29.222900+00:00"}
```

## 5. Build con `GIT_SHA`/`BUILD_TIME`

```
$env:GIT_SHA="abc1234"; $env:BUILD_TIME="2026-11-15T12:00:00Z"; docker compose build --no-cache singing-service
...
 Image singing-service-singing-service Built
BUILD_EXIT=0
```

`/version` mostró `git_sha=abc1234` y `build_time=2026-11-15T12:00:00Z` (sección 4).
El paso por env funciona en Windows PowerShell; en Linux/macOS:

```bash
GIT_SHA=$(git rev-parse --short HEAD) BUILD_TIME=$(date -Iseconds) docker compose build
```

## 6. Confirmaciones

- **83 tests previos verdes** + **9 nuevos** = **92 passed**; cobertura **97 %**.
- **`/analyze` intacto**: no se tocó `app/api/routes/analyze.py`, `app/services/` ni
  `app/core/store.py`; el contrato de análisis no cambió.
- **`/health` no cambió de shape** (mismo JSON; solo versión 0.3.0 y `async` +
  `run_in_threadpool`).
- **`core-api/` intacto** (no existe).
- **Tag `v0.2.3` intacto** (`f744a8e`); el trabajo está **solo en `sprint1`**, sin
  merge ni tag nuevo.
- **Docker/local**: Python 3.14.6, deps pinned, 92/92 en ambos entornos.
