# CIERRE_FORMAL_v0.2.2 — git, tag y verificación

> Cierre formal del workspace `App-SyncDance` con repo git, tag `v0.2.2`, tests de
> handlers y verificación final. Fecha: 2026-11-14.

## 1. Git — inicialización, commit y tag

### 1.1 `git init`

```
Initialized empty Git repository in C:/Users/HP/Documents/PROYECTOS/App-SyncDance/.git/
```

### 1.2 `git add -A` + `git status` (antes del commit)

`git add -A` emitió avisos `LF will be replaced by CRLF` (esperado en Windows).
Estado staged (81 archivos):

```
On branch master

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
	new file:   .gitignore
	new file:   AUDITORIA_v0.2.0.md
	new file:   CIERRE_GAPS_SPRINT0.md
	new file:   CIERRE_v0.2.2.md
	new file:   CONSISTENCY_FIX.md
	new file:   DOCS_CONTINUATION.md
	new file:   Docs/SyncDance AI Requisitos y Alcance Propuesto.docx
	new file:   Docs/integracion-core.md
	new file:   Docs/plan-implementacion-singing-service.md
	new file:   Docs/prompt-agente-figma-canto.md
	new file:   Docs/prototipo.png
	new file:   Docs/scoring.md
	new file:   ESTADO_ACTUAL.md
	new file:   FIX_P0-01.md
	new file:   HANDOFF_CORE.md
	new file:   opencode.json
	new file:   singing-service/.dockerignore
	new file:   singing-service/.env.example
	new file:   singing-service/.gitignore
	new file:   singing-service/CHANGELOG.md
	new file:   singing-service/CONTRIBUTING.md
	new file:   singing-service/Dockerfile
	new file:   singing-service/README.md
	new file:   singing-service/app/__init__.py
	new file:   singing-service/app/api/__init__.py
	new file:   singing-service/app/api/routes/__init__.py
	new file:   singing-service/app/api/routes/analyze.py
	new file:   singing-service/app/core/__init__.py
	new file:   singing-service/app/core/config.py
	new file:   singing-service/app/core/log.py
	new file:   singing-service/app/core/store.py
	new file:   singing-service/app/main.py
	new file:   singing-service/app/middleware/__init__.py
	new file:   singing-service/app/middleware/request_id.py
	new file:   singing-service/app/mock/__init__.py
	new file:   singing-service/app/mock/data.py
	new file:   singing-service/app/schemas/__init__.py
	new file:   singing-service/app/schemas/analyze.py
	new file:   singing-service/app/services/__init__.py
	new file:   singing-service/app/services/align.py
	new file:   singing-service/app/services/compare.py
	new file:   singing-service/app/services/feedback.py
	new file:   singing-service/app/services/metrics.py
	new file:   singing-service/app/services/pitch.py
	new file:   singing-service/app/services/preprocess.py
	new file:   singing-service/app/services/rhythm_eval.py
	new file:   singing-service/app/services/scoring.py
	new file:   singing-service/docker-compose.yml
	new file:   singing-service/docs/ARCHITECTURE.md
	new file:   singing-service/docs/SPRINT1_BACKLOG.md
	new file:   singing-service/docs/SWAGGER_GUIDE.md
	new file:   singing-service/docs/TROUBLESHOOTING.md
	new file:   singing-service/docs/USAGE.md
	new file:   singing-service/docs/celery-contract.md
	new file:   singing-service/integration/README.md
	new file:   singing-service/integration/generate_fixtures.py
	new file:   singing-service/integration/requirements.txt
	new file:   singing-service/integration/simulate_celery_worker.py
	new file:   singing-service/integration/test_error_scenarios.py
	new file:   singing-service/integration/verify_handoff.sh
	new file:   singing-service/postman_collection.json
	new file:   singing-service/pyproject.toml
	new file:   singing-service/requirements-dev.txt
	new file:   singing-service/requirements.txt
	new file:   singing-service/scripts/demo_e2e.py
	new file:   singing-service/tests/__init__.py
	new file:   singing-service/tests/audio_utils.py
	new file:   singing-service/tests/fixtures/audios/README.md
	new file:   singing-service/tests/snapshots/openapi_v1.json
	new file:   singing-service/tests/test_absolute.py
	new file:   singing-service/tests/test_align.py
	new file:   singing-service/tests/test_busy.py
	new file:   singing-service/tests/test_comparative.py
	new file:   singing-service/tests/test_contract.py
	new file:   singing-service/tests/test_e2e.py
	new file:   singing-service/tests/test_health.py
	new file:   singing-service/tests/test_log.py
	new file:   singing-service/tests/test_pitch.py
	new file:   singing-service/tests/test_preprocess.py
	new file:   singing-service/tests/test_request_id.py
	new file:   singing-service/tests/test_store.py
```

### 1.3 Commit A (release inicial) + tag

```
[master (root-commit) 42eda5a] chore: singing-service v0.2.2 — cierre Sprint 0 + handoff Core
 81 files changed, 13226 insertions(+)
```

```
=== git rev-parse HEAD ===
42eda5af3fb76448ede84dc886936091d7955217
=== git rev-parse v0.2.2 (tag object) ===
2bfae4ad0a4ff174e7cba49e1e4736a4bc1af6e0
=== git rev-parse v0.2.2^{commit} ===
42eda5af3fb76448ede84dc886936091d7955217
=== git log --oneline -1 ===
42eda5a chore: singing-service v0.2.2 — cierre Sprint 0 + handoff Core
=== git log -1 --format=%cI ===
2026-11-14T16:14:26-04:00
=== git tag -l ===
v0.2.2
=== git status ===
On branch master
nothing to commit, working tree clean
```

### 1.4 Release final (B) — tests de handlers añadidos tras el commit A

Los tests de la Tarea 3 se añadieron **después** del commit A. Para que el tag apunte al
estado final (83 tests, 97 %), se re-taggeó:

```
=== git status --short (antes de B) ===
 M CIERRE_v0.2.2.md
 M HANDOFF_CORE.md
 M singing-service/docs/ARCHITECTURE.md
 M singing-service/docs/SPRINT1_BACKLOG.md
 M singing-service/integration/test_error_scenarios.py
?? singing-service/tests/test_exception_handlers.py
=== git commit B ===
[master 1b9271b] test/docs: exception handlers coverage (97%), V-01 integration check, Python note, HU-S1-08
 6 files changed, 229 insertions(+), 6 deletions(-)
 create mode 100644 singing-service/tests/test_exception_handlers.py
=== re-tag v0.2.2 ===
Updated tag 'v0.2.2' (was 2bfae4a)
=== git rev-parse HEAD (B) ===
1b9271bc22db876416772893afc48ca753600a05
=== git rev-parse v0.2.2 (tag object) ===
fdad4cc5dc5c9dd2576e375e2bfdbe431864e71c
=== git rev-parse v0.2.2^{commit} ===
1b9271bc22db876416772893afc48ca753600a05
=== git log --oneline -3 ===
1b9271b test/docs: exception handlers coverage (97%), V-01 integration check, Python note, HU-S1-08
42eda5a chore: singing-service v0.2.2 — cierre Sprint 0 + handoff Core
=== git log -1 --format=%cI ===
2026-11-14T16:20:37-04:00
```

**Tag final:** `v0.2.2` (annotated) → commit
`1b9271bc22db876416772893afc48ca753600a05`; tag object
`fdad4cc5dc5c9dd2576e375e2bfdbe431864e71c`.

> Nota de auto-referencia: un archivo no puede contener el SHA del commit que lo
> incluye. HANDOFF/CIERRE se actualizan en un commit de metadata posterior (C) con el
> SHA del release B. El tag `v0.2.2` apunta a B (release con 83 tests); C solo registra
> el SHA en los documentos.

## 2. Python real

```
=== python --version (global) ===
python : no se encontró Python; ejecutar sin argumentos para instalar desde el
Microsoft Store ... (alias de ejecución de Windows)
=== venv python --version ===
Python 3.14.6
=== venv imports ===
librosa 1.0.0
numba 0.68.0
scipy 1.18.1
numpy 2.5.3
```

El `python` global de Windows no está instalado (solo el alias de Microsoft Store). El
entorno real del servicio es el venv: **Python 3.14.6**, con librosa 1.0.0, numba 0.68.0,
scipy 1.18.1 y numpy 2.5.3. Documentado en `docs/ARCHITECTURE.md` §6.

## 3. Tests y cobertura

```
Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
app\core\__init__.py       0      0   100%
app\core\config.py        16      0   100%
app\core\log.py           10      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py               55      0   100%
----------------------------------------------------
TOTAL                    138      4    97%
======================= 83 passed, 1 warning in 21.39s ========================
```

- `app/main.py`: **100 %** (líneas 81, 112-113, 119-120 cubiertas por
  `tests/test_exception_handlers.py`).
- `app/core/store.py`: 93 % (ramas defensivas de expiración/eviction).
- Total: **83 tests, 97 %**.

Tests nuevos (`tests/test_exception_handlers.py`):

1. `HTTPException(418)` con `request_id` en header y body.
2. `RequestValidationError` (422) con `request_id` top-level y header.
3. `UNHANDLED_ERROR` (500) con `request_id`, body sin stack y log con `exc_info`
   (monkeypatch de `extract_pitch`; `librosa.pyin` se captura como
   `400 PITCH_EXTRACT_FAILED` por diseño).
4. `HTTPException` con `detail` no-dict (404) → `request_id` (cubre línea 81).
5. `/health` con `request_id` en header y body.
6. `/health` con fallo de import de librosa → 503 `degraded` (cubre 112-113).
7. `/health` con `disk_usage` fallando → `disk_space_mb=0` (cubre 119-120).

## 4. Handoff y matriz

```
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

Matriz de errores (10 checks, incluye V-01):

```
[PASS] mode_invalido: HTTP 422 code=INVALID_MODE
[PASS] comparative_sin_referencia: HTTP 400 code=MISSING_REFERENCE
[PASS] audio_mayor_50mb: HTTP 413 code=AUDIO_TOO_LARGE
[PASS] audio_mayor_600s: HTTP 413 code=AUDIO_TOO_LONG
[PASS] txt_renombrado_a_wav: HTTP 400 code=INVALID_AUDIO
[PASS] extension_txt_no_soportada: HTTP 400 code=UNSUPPORTED_FORMAT
[PASS] sin_campo_audio: HTTP 422 code=VALIDATION_ERROR
[PASS] servicio_caido: ConnectionError (sin respuesta 5xx)
[PASS] 5xx_sin_json: action=retry reason=Non-JSON response 500
[PASS] v01_content_length_service_alive: rejected=b'' health=200

RESUMEN: 10/10 checks OK
```

## 5. Diff de HANDOFF_CORE.md y CIERRE_v0.2.2.md

Bloque nuevo (SHA real):

```markdown
> **Versión:** v0.2.2
> **Tag git:** `v0.2.2` (annotated; tag object `fdad4cc5dc5c9dd2576e375e2bfdbe431864e71c`)
> **Commit SHA:** `1b9271bc22db876416772893afc48ca753600a05`
> **Fecha:** 2026-11-14T16:20:37-04:00
> **Fingerprint (respaldo):** `821a796d9f6e27e49b1a22c35319ba0fe227600ed90c5defb4b05bece31e92ae`
> **Estado:** ✅ LISTO PARA INTEGRACIÓN CON CORE
> **Tests:** 83 passed, 97% cobertura, ruff OK
> **Verificación:** `bash singing-service/integration/verify_handoff.sh` → 4/4 HANDOFF OK
> **Documentación vigente:** `singing-service/docs/celery-contract.md` (v0.2.2),
> `singing-service/docs/USAGE.md`, `singing-service/docs/SWAGGER_GUIDE.md`
```

En `CIERRE_v0.2.2.md` §Versión: tag/commit/fecha equivalentes y sección
**Cómo obtener esta versión** con `git checkout v0.2.2` y la verificación
`git rev-parse v0.2.2^{commit}` → `1b9271b...`.

## 6. Confirmaciones

- **Tag `v0.2.2` creado** (annotated) → commit
  `1b9271bc22db876416772893afc48ca753600a05`.
- **SHA capturado:** commit `1b9271b...`; tag object `fdad4cc...`.
- **`.gitignore` raíz** excluye `.venv/`, `__pycache__/`, `.pytest_cache/`,
  `.ruff_cache/`, `singing-service/integration/fixtures/`, `.env`, logs y secretos.
- **Commit inicial incluye todo el workspace** (81 archivos: `Docs/`, `singing-service/`,
  `opencode.json`, informes).
- **83 tests verdes**, 97 % cobertura, `ruff` OK, `verify_handoff.sh` **4/4 HANDOFF OK**,
  matriz **10/10**.
- **No se tocó lógica de análisis**; solo tests, docs y metadata.
- **`core-api/` intacto** (no existe).
- **Documentos históricos intactos** (`CIERRE_GAPS_SPRINT0.md`, `ESTADO_ACTUAL.md`,
  `CONSISTENCY_FIX.md`).
