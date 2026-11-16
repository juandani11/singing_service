# CIERRE_HU_S1_03 — warm-up de librosa/numba

> HU-S1-03 en `sprint1`. Base `v0.2.3` (`f744a8e`). Versión de trabajo **0.3.0-dev**.
> Fecha: 2026-11-15. **100 tests, 98 % cobertura, ruff OK, HANDOFF OK.**

## 1. Diff resumido

| Archivo | Cambio |
|---|---|
| `app/main.py` | `_warmup()` (sine 440 Hz 0.5 s en memoria → `librosa.pyin`), `_skip_warmup()`, `AppState.warmup_completed/duration_ms`, lifespan ejecuta warm-up tras self-test; `/health` añade `checks.warmup`. |
| `tests/test_hu_s1_03.py` | **Nuevo**: 8 tests (éxito, fallo, skip, ready 503, duración <5 s, `/health` warmup, Hz inesperado, self-test falla → `SystemExit`). |
| `tests/test_hu_s1_02.py` | El test de lifespan usa `SKIP_WARMUP=true` (evita JIT real). |
| `tests/snapshots/openapi_v1.json` | Regenerado (health examples con `warmup`). |
| `docs/celery-contract.md` | §3 timeout (JIT mitigado; mantener 300 s) y §4.1 (`/health.checks.warmup` aditivo, no-BREAKING). |
| `docs/USAGE.md` | `/health` real con `warmup`; troubleshooting JIT mitigado. |
| `docs/ARCHITECTURE.md` | §6.2 `SKIP_WARMUP`; §7 JIT mitigado; contadores 100 tests/98 %. |
| `CHANGELOG.md` | `[0.3.0-dev]`: warm-up, `SKIP_WARMUP`, `/health.checks.warmup`, 8 tests. |
| `README.md` / `CONTRIBUTING.md` | 100 tests / 98 %. |

## 2. Tests y cobertura

```
Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
app\core\__init__.py       0      0   100%
app\core\config.py        16      0   100%
app\core\log.py           10      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py              133      0   100%
----------------------------------------------------
TOTAL                    216      4    98%
======================= 100 passed, 1 warning in 11.20s ========================
```

- **92 previos + 8 nuevos = 100**; `app/main.py` **100 %**.
- `ruff check .` → `All checks passed!`.

## 3. Handoff

```
-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 4. Medición de latencia real (Docker, tras warm-up)

Primer y segundo `POST /analyze` (`mode=absolute`, sine 440 Hz 5 s) tras arrancar:

```
request=1 wall_ms=345 pitch_ms=77 preprocess_ms=220 dtw_ms=0 scoring_ms=4 vocal=99
request=2 wall_ms=238 pitch_ms=73 preprocess_ms=146 dtw_ms=0 scoring_ms=1 vocal=99
```

Comparación con baseline v0.2.3:

| Medición | v0.2.3 (sin warm-up) | v0.2.3 + HU-S1-03 (con warm-up) |
|---|---|---|
| `pitch_ms` primer request | **10266 ms** | **77 ms** |
| `pitch_ms` segundo request | 238 ms | 73 ms |
| `wall_ms` primer request | ~10.3 s | **345 ms** |

**Objetivo <2 s: cumplido** (primer request real 345 ms de wall, 77 ms de pitch).

## 5. Warm-up en startup

Log real del contenedor:

```
{"ts": "2026-11-15T20:34:24+00:00", "request_id": "-", "event": "warmup_completed", "duration_ms": 6090.6, "detected_hz": 439.8}
```

`/health` real:

```json
{"status":"ok","service":"singing-service","version":"0.3.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.0"},"models_loaded":{"ok":true},"disk_space_mb":943399,"warmup":{"ok":true,"duration_ms":6090.6}},"request_id":"0a2e3487cd38468890e455be4d4a5d5f","timestamp":"2026-11-15T20:34:25.762105+00:00"}
```

`/ready` tras warm-up:

```json
{"ready":true,"reason":null,"request_id":"bea87961cdc943cda21aa6634b9dc849"}
HTTP=200
```

**Coste de startup:** warm-up **6090.6 ms en Docker** (JIT frío real) y **2701.9 ms
en local** (medido en proceso limpio). Es >1 s, pero evita 10.3 s en el primer request.
Se documenta como coste asumido de la mitigación.

## 6. Docker

```
$env:GIT_SHA="abc1234"; $env:BUILD_TIME="2026-11-15T12:00:00Z"; docker compose build --no-cache singing-service
 Image singing-service-singing-service Built
BUILD_EXIT=0
```

Tras `up -d`: `/ready` → **200**; `/health.checks.warmup.ok=true`; suite Docker:

```
======================== 100 passed, 1 warning in 9.06s ========================
TOTAL                    216      4    98%
```

## 7. Confirmaciones

- **92 tests previos verdes + 8 nuevos = 100** (local y Docker); cobertura **98 %**.
- **`/analyze` intacto** (no se tocó `app/api/routes/analyze.py`, `app/services/` ni
  `app/core/store.py`); contrato de análisis sin cambios.
- **`/health` cambia solo de forma aditiva** (`checks.warmup`), marcado no-BREAKING.
- **`core-api/` intacto** (no existe).
- **Tag `v0.2.3` intacto** (`f744a8e`); trabajo solo en `sprint1`, sin merge ni tag nuevo.
- **Warm-up exitoso en local y Docker**; no hubo divergencia de comportamiento.
- `SKIP_WARMUP=true` omite el warm-up (tests/entornos rápidos); `false` por defecto.
