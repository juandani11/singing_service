# CONSISTENCY_FIX — campo multipart `file` → `audio`

> Cierre de la inconsistencia de contrato detectada en el handoff a Core.
> Fecha: 2026-11-12 (UTC). Servicio: `singing-service` (70 tests, 93 % cobertura).
> No se tocó `core-api/` (no existe).

## 1. Auditoría (estado ANTES del cambio)

Búsqueda recursiva en `app/`, `tests/`, `integration/`, `docs/`, `scripts/`, `README.md`,
`Docs/integracion-core.md`, `CIERRE_GAPS_SPRINT0.md`, `HANDOFF_CORE.md` y
`ESTADO_ACTUAL.md`.

### 1.1 Campo `file` (multipart) — ❌ incorrecto

| Archivo | Línea | Texto encontrado | ¿Es campo multipart? | ¿Correcto? |
|---|---|---|---|---|
| `app/api/routes/analyze.py` | 112 | `file: UploadFile = File(...)` | Sí (definición) | ❌ |
| `app/api/routes/analyze.py` | 176 | `ensure_supported_extension(file.filename)` | Sí (uso) | ❌ |
| `app/api/routes/analyze.py` | 177 | `read_capped(file, max_bytes)` | Sí (uso) | ❌ |
| `app/api/routes/analyze.py` | 187 | `preprocess_bytes(..., file.filename, ...)` | Sí (uso) | ❌ |
| `tests/test_absolute.py` | 18 | `files={"file": (name, ...)}` | Sí | ❌ |
| `tests/test_align.py` | 233 | `"file": ("alumno.wav", ...)` | Sí | ❌ |
| `tests/test_busy.py` | 16 | `{"file": (name, ...)}` | Sí | ❌ |
| `tests/test_comparative.py` | 22, 105, 122 | `{"file": (...)}` | Sí | ❌ |
| `tests/test_contract.py` | 22 | `{"file": (name, ...)}` | Sí | ❌ |
| `tests/test_e2e.py` | 26 | `"file": (name, data, ...)` | Sí | ❌ |
| `tests/test_log.py` | 22 | `{"file": ("a.wav", ...)}` | Sí | ❌ |
| `tests/test_pitch.py` | 20 | `{"file": (filename, ...)}` | Sí | ❌ |
| `tests/test_preprocess.py` | 36, 87 | `{"file": (...)}` | Sí | ❌ |
| `tests/test_contract.py` | 99 | `def test_analyze_requires_file` | No (nombre de test) | ⚠️ renombrado |
| `tests/snapshots/openapi_v1.json` | 239, 242, 291 | `"file"`, `"title": "File"`, `"file"` | Sí (schema) | ❌ |
| `integration/simulate_celery_worker.py` | 92 | `files = {"file": (...)}` | Sí | ❌ |
| `integration/simulate_celery_worker.py` | 126 | `files["file"][1].close()` | Sí | ❌ |
| `integration/test_error_scenarios.py` | 99 | `field: str = "file"` | Sí (default) | ❌ |
| `integration/test_error_scenarios.py` | 146 | `"sin_campo_file"` | Etiqueta del check | ⚠️ renombrada |
| `scripts/demo_e2e.py` | 52 | `"file": ("alumno.wav", ...)` | Sí | ❌ |
| `docs/celery-contract.md` | 28 | tabla `\| \`file\` \| archivo \|` | Sí | ❌ |
| `docs/celery-contract.md` | 53 | `"file": ("intento.m4a", ...)` | Sí | ❌ |
| `docs/celery-contract.md` | 64 | `-F "file=@intento.m4a"` | Sí | ❌ |
| `docs/celery-contract.md` | 134 | `falta \`file\`/...` | Sí | ❌ |
| `docs/celery-contract.md` | 213 | `"file": (` (tarea Celery) | Sí | ❌ |
| `docs/celery-contract.md` | 254 | `files["file"][1].close()` | Sí | ❌ |
| `docs/celery-contract.md` | 285 | checklist `POST` envía `file` | Sí | ❌ |
| `integration/README.md` | 35 | «el servicio espera `file` (no `audio`)» | Sí | ❌ |
| `integration/README.md` | 46 | «sin `file` → 422» | Sí | ❌ |
| `README.md` | 67 | `multipart: \`file\`, ...` | Sí | ❌ |
| `README.md` | 74, 87, 177 | `-F "file=@..."` | Sí | ❌ |
| `Docs/integracion-core.md` | 36 | tabla `\| \`file\` \| archivo \|` | Sí | ❌ |
| `Docs/integracion-core.md` | 102 | `files = {"file": (...)}` | Sí | ❌ |
| `CIERRE_GAPS_SPRINT0.md` | 159, 204, 261 | `-F "file=@..."` | Sí (histórico) | ⚠️ histórico |
| `HANDOFF_CORE.md` | 21 | «el campo real es `file`, no `audio`» | Sí | ❌ |
| `HANDOFF_CORE.md` | 2568 | salida matriz: `body.file` | Sí (output) | ❌ |
| `HANDOFF_CORE.md` | 2652 | `falta \`file\`/...` | Sí | ❌ |
| `HANDOFF_CORE.md` | 2731 | `"file": (` (tarea Celery) | Sí | ❌ |
| `HANDOFF_CORE.md` | 2772 | `files["file"][1].close()` | Sí | ❌ |
| `HANDOFF_CORE.md` | 2786 | checklist `POST` con `file` | Sí | ❌ |
| `HANDOFF_CORE.md` | 2813 | nota «Campo `file`» | Sí | ❌ |
| `ESTADO_ACTUAL.md` | 138, 141, 518, 521 | tabla/§8 con `file` | Sí (histórico) | ⚠️ histórico |

### 1.2 `reference_audio` — ✅ correcto (consistente)

| Archivo(s) | Líneas (muestra) | ¿Campo multipart? | ¿Correcto? |
|---|---|---|---|
| `app/api/routes/analyze.py` | 4, 113, 135, 139, 180-182, 197 | Sí | ✅ |
| `tests/test_align.py`, `test_comparative.py`, `test_e2e.py`, `test_preprocess.py` | 234; 24, 123; 27; 88 | Sí | ✅ |
| `integration/simulate_celery_worker.py` | 100 | Sí | ✅ |
| `scripts/demo_e2e.py` | 53 | Sí | ✅ |
| `docs/celery-contract.md` | 32, 54, 65, 222, 238, 270 | Sí | ✅ |
| `integration/README.md`, `README.md`, `Docs/integracion-core.md` | varias | Sí | ✅ |
| `CIERRE_GAPS_SPRINT0.md`, `HANDOFF_CORE.md` | 51, 58, 204, 244; 2740, 2789 | Sí | ✅ |

No se encontró ninguna variante incorrecta de `reference_audio`.

### 1.3 `reference_file` — ❌ obsoleto (sólo en informes históricos)

| Archivo | Línea | Texto | ¿Campo? | ¿Correcto? |
|---|---|---|---|---|
| `CIERRE_GAPS_SPRINT0.md` | 78 | `reference_file` (columna «Antes») | Sí (histórico) | ⚠️ histórico |
| `ESTADO_ACTUAL.md` | 139, 520 | `reference_file` | Sí (histórico) | ⚠️ histórico |

El contrato vigente ya usaba `reference_audio`; no hay `reference_file` en código ni docs
vivos.

---

## 2. Decisión: renombrar a `audio`

**Aplicada: `file` → `audio`.**

Justificación:

1. `audio` es semánticamente correcto para el intento del alumno.
2. Simetría con `reference_audio` (ambos son pistas de audio).
3. Coincide con el contrato original (`ESTADO_ACTUAL.md` §8 y `CIERRE_GAPS_SPRINT0.md` §2).
4. El cambio es de una línea en FastAPI (`file: UploadFile` → `audio: UploadFile`) más
   las referencias internas.
5. **No existe ninguna razón técnica documentada para mantener `file`**: era simplemente
   el nombre inicial de la implementación; no hay dependencia, middleware ni cliente
   productivo que lo justifique.

**Impacto:** BREAKING para clientes que enviaban `file`. El handoff a Core se actualizó
completo; no queda a medias.

---

## 3. Diff resumido por archivo

| Archivo | Cambio |
|---|---|
| `app/api/routes/analyze.py` | `file: UploadFile` → `audio: UploadFile`; `file.filename`/`read_capped(file)`/`preprocess_bytes(..., file.filename)` → `audio.*` (4 referencias) |
| `tests/test_absolute.py` | clave multipart `"file"` → `"audio"` |
| `tests/test_align.py` | idem |
| `tests/test_busy.py` | idem |
| `tests/test_comparative.py` | idem (3 usos) |
| `tests/test_contract.py` | idem; `test_analyze_requires_file` → `test_analyze_requires_audio` |
| `tests/test_e2e.py` | idem |
| `tests/test_log.py` | idem |
| `tests/test_pitch.py` | idem |
| `tests/test_preprocess.py` | idem (2 usos) |
| `tests/snapshots/openapi_v1.json` | regenerado: requestBody `audio` (title `Audio`), required `audio` |
| `integration/simulate_celery_worker.py` | `files={"audio": ...}`; `files["audio"]`; docstring actualizado |
| `integration/test_error_scenarios.py` | `field="audio"`; check `sin_campo_file` → `sin_campo_audio` |
| `integration/README.md` | nota de campo, «sin `audio` → 422», tabla de errores, sección «Limitaciones de plataforma» |
| `scripts/demo_e2e.py` | clave `"file"` → `"audio"` |
| `docs/celery-contract.md` | §2 tabla/código/curl, §5 matriz de errores (Tarea 4), §6 código Celery, §7 checklist |
| `README.md` | tabla de API y 3 curls |
| `Docs/integracion-core.md` | tabla de contrato y código Celery |
| `CIERRE_GAPS_SPRINT0.md` | banner histórico + fila BREAKING «campo `file` → `audio`» |
| `HANDOFF_CORE.md` | nota de desviación, §5, §6, checklist, nota final y salida de matriz |
| `ESTADO_ACTUAL.md` | banner histórico (no se reescribe el cuerpo) |

**No se cambió comportamiento**: mismo pipeline, mismos modos, mismas métricas, mismos
códigos de error. Sólo el nombre del campo.

---

## 4. `pytest -v` (output real)

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
======================= 70 passed, 1 warning in 25.86s ========================
```

---

## 5. `python integration/test_error_scenarios.py` (output real)

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

RESUMEN: 8/8 checks OK
```

---

## 6. `bash integration/verify_handoff.sh` (output real)

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

> Nota: el contenedor se reconstruyó (`docker compose build`) antes de esta corrida para
> descartar la imagen previa con `file`.

---

## 7. Tabla de errores final (tal como quedó en `docs/celery-contract.md` §5)

| Código HTTP | Code | Causa | Acción recomendada para Core |
|---|---|---|---|
| 400 | `UNSUPPORTED_FORMAT` | Extensión no permitida (`.txt`, `.pdf`) | No reintentar; error del cliente |
| 400 | `INVALID_AUDIO` | Contenido corrupto o no decodificable | No reintentar; error del cliente |
| 400 | `MISSING_REFERENCE` | `comparative` sin referencia | No reintentar; bug del cliente |
| 413 | `AUDIO_TOO_LARGE` | > 50 MB | No reintentar |
| 413 | `AUDIO_TOO_LONG` | > 600 s | No reintentar |
| 422 | `INVALID_MODE` | `mode` no válido | No reintentar |
| 422 | `VALIDATION_ERROR` | Campo faltante (p. ej. `audio`) | No reintentar; bug del cliente |
| 500 | `INTERNAL_ERROR` | Fallo del servicio | Reintentar con backoff |
| 503 | `SERVICE_DEGRADED` | FFmpeg o dependencias no disponibles | Reintentar con backoff; alertar |

**Códigos adicionales** (también en el contrato): `INVALID_REFERENCE_NOTES`,
`NO_AUDIO_TRACK`, `EMPTY_FILE`, `EMPTY_AUDIO`, `CONVERT_TIMEOUT`, `PITCH_EXTRACT_FAILED`
(400, no reintentar), `SERVICE_BUSY` (429, backoff), `FFMPEG_NOT_FOUND` (500, reintentar
1-2 veces) y `ConnectionError` (backoff).

**Nota de wire real:**

- `VALIDATION_ERROR` es la etiqueta para la lista de validación de FastAPI (`detail` es
  un array, no un objeto con `code`).
- `INTERNAL_ERROR` no es un `detail.code` emitido hoy: el único 500 tipado es
  `FFMPEG_NOT_FOUND`; otros 500 no traen `code`.
- `SERVICE_DEGRADED` no lo emite `/api/v1/analyze`; el 503 sólo lo devuelve `/health`
  (sin `detail.code`). El worker debe tratar cualquier 503 como degradado.

---

## 8. Confirmación: sin referencias vivas a `file` como campo multipart

**No queda ninguna referencia a `file` como campo multipart en código ni en documentos
vivos.** Evidencia:

- Búsqueda de `"file"` (comilla doble literal) en `app/`, `tests/`, `integration/`,
  `docs/`, `scripts/`, `README.md`, `Docs/integracion-core.md`: **0 resultados**.
- Búsqueda de `-F "file=` : sólo 3 coincidencias en `CIERRE_GAPS_SPRINT0.md`
  (evidencia histórica pre-rename, con banner explícito).
- Búsqueda de `` `file` `` : sólo notas explicativas del rename en `CIERRE_GAPS_SPRINT0.md`,
  `HANDOFF_CORE.md` y el banner de `ESTADO_ACTUAL.md`.
- `tests/snapshots/openapi_v1.json` usa `audio` (título `Audio`) y `audio` en `required`.

**Excepción justificada:** `CIERRE_GAPS_SPRINT0.md` y `ESTADO_ACTUAL.md` son informes
históricos; conservan `file`/`reference_file` en su cuerpo y llevan un banner que apunta
al contrato vigente. No se reescribieron para no falsear la evidencia de las corridas
originales.

---

## 9. Confirmación: alcance del cambio en `app/` y `tests/`

- `app/`: **sólo** `app/api/routes/analyze.py` cambió (parámetro `file` → `audio` y sus
  3 usos internos). `app/main.py`, `app/core/`, `app/services/` y `app/schemas/` no se
  tocaron.
- `tests/`: **sólo** cambió la clave multipart `"file"` → `"audio"` en 9 archivos y el
  nombre de `test_analyze_requires_file` → `test_analyze_requires_audio`. Ninguna
  aserción, umbral ni lógica de test cambió.
- El snapshot OpenAPI se regeneró (consecuencia esperada del rename).
- `ruff` OK; `pytest` 70/70; matriz 8/8; `verify_handoff.sh` 4/4.

**Por qué se tocaron tests:** todos enviaban el campo `file`; tras el rename habrían
devuelto 422. El cambio es exclusivamente la clave del multipart, no la lógica.
