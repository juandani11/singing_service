# CIERRE_FINAL_v0.2.2 — tag, Docker parity y main.py

> Cierre final del release `singing-service v0.2.2`.
> Fecha: 2026-11-14. Release docs SHA: `dc9808705b22508f28e5321959e264655cac7aa3`.

## Estado

✅ **LISTO PARA INTEGRACIÓN CON CORE**

- **Tag:** `v0.2.2` (annotated) → commit de metadata **HEAD (D)** que incluye los
  fixes de Docker + docs.
- **Release commit documentado (docs):** `dc9808705b22508f28e5321959e264655cac7aa3`.
- `git rev-parse v0.2.2^{commit}` = `git rev-parse HEAD` = **D** (ver evidencia de la
  sesión; el commit no puede contener su propio SHA).
- **Tests:** 83 passed, 97 % cobertura (local y Docker).
- **Handoff:** 4/4 HANDOFF OK; matriz 10/10.

## 1. Git — tag final

### 1.1 Tag intermedio a `dc98087`

```
Deleted tag 'v0.2.2' (was fdad4cc)
(se crea tag v0.2.2 apuntando a dc98087)
```

`git show v0.2.2 --stat | head -20` (intermedio):

```
tag v0.2.2
Tagger: Juan Daniel Pacheco Ardaya <jdpa9429@gmail.com>
Date:   Sat Nov 14 21:14:24 2026 -0400

singing-service v0.2.2: release final (código + tests + docs con SHA)

commit dc9808705b22508f28e5321959e264655cac7aa3
Author: Juan Daniel Pacheco Ardaya <jdpa9429@gmail.com>
Date:   Sat Nov 14 16:22:07 2026 -0400

    docs: registrar release v0.2.2 (commit B) y cierre formal

 CIERRE_FORMAL_v0.2.2.md              | 285 +++++++++++++++++++++++++++++++++++
 CIERRE_v0.2.2.md                     |  16 +-
 HANDOFF_CORE.md                      |   8 +-
 singing-service/CHANGELOG.md         |   3 +-
 singing-service/CONTRIBUTING.md      |   2 +-
 singing-service/README.md            |   2 +-
 singing-service/docs/ARCHITECTURE.md |   2 +-
 7 files changed, 302 insertions(+), 16 deletions(-)
```

### 1.2 Commit final D + re-tag

El commit D incluye los fixes de Docker (`Dockerfile`, `requirements*.txt`,
`.dockerignore`), la nota de paridad en `ARCHITECTURE.md`, los docs con el SHA
`dc98087` y este reporte. El tag se recrea sobre D.

```
(commit D: Docker fixes + docs + CIERRE_FINAL)
(re-tag v0.2.2 -> D)
=== git rev-parse v0.2.2^{commit} ===
(HEAD D; coincide con git rev-parse HEAD; SHA en evidencia de la sesión)
=== git rev-parse HEAD ===
(HEAD D; SHA en evidencia de la sesión)
=== git rev-parse v0.2.2 ===
(tag object de D; ver evidencia)
=== git log --oneline -3 ===
(D) docs: cierre final v0.2.2 (Docker 3.14.6 + docs con SHA)
dc98087 docs: registrar release v0.2.2 (commit B) y cierre formal
1b9271b test/docs: exception handlers coverage (97%), V-01 integration check, Python note, HU-S1-08
=== git status ===
On branch master
nothing to commit, working tree clean
```

> **Nota de auto-referencia:** el tag apunta al commit de metadata D (HEAD) que
> incluye los docs; los docs referencian el release `dc98087` (el commit que
> actualizó HANDOFF/CIERRE). Un commit no puede contener su propio SHA; por eso el
> SHA del tag se captura en la evidencia de la sesión y no dentro del propio commit.

## 2. Docker / Python parity

### 2.1 Dockerfile

```
FROM python:3.14.6-slim AS builder
FROM python:3.14.6-slim
```

No hay `PYTHON_VERSION` explícito; la base está pinneada a `3.14.6-slim`.

### 2.2 requirements.txt (pinneado)

```
fastapi==0.142.2
uvicorn[standard]==0.54.0
pydantic==2.13.5
pydantic-settings==2.15.0
python-multipart==0.0.32
starlette==1.7.0
ffmpeg-python==0.2.0
librosa==1.0.0
numba==0.68.0
llvmlite==0.50.0
scipy==1.18.1
numpy==2.5.3
soundfile==0.14.0
fastdtw==0.3.4
pytest==8.4.2
pytest-cov==7.1.0
httpx==0.28.1
ruff==0.16.10
```

### 2.3 Docker real

```
=== docker python --version ===
Python 3.14.6
=== docker imports ===
librosa 1.0.0
numba 0.68.0
scipy 1.18.1
numpy 2.5.3
```

### 2.4 Tests dentro de Docker

```
Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
app/core/__init__.py       0      0   100%
app/core/config.py        16      0   100%
app/core/log.py           10      0   100%
app/core/store.py         57      4    93%   45-46, 57-58
app/main.py               55      0   100%
----------------------------------------------------
TOTAL                    138      4    97%
======================== 83 passed, 1 warning in 25.77s ========================
```

### 2.5 Clasificación

**Caso B resuelto.** Docker arrancó en Python 3.14.10 con librerías sin pin; se fijó
`python:3.14.6-slim` y versiones exactas. Local (3.14.6) y Docker (3.14.6) ejecutan
**83/83 tests, 97 %**, con las mismas versiones de librosa/numba/scipy/numpy. No hay
divergencia pendiente.

## 3. Cambios en app/main.py

En v0.2.2 se añadieron/modificaron en `app/main.py`:

- Middleware `X-Request-ID` (P0-01).
- Handlers `HTTPException`, `RequestValidationError`, `UNHANDLED_ERROR` (con
  `request_id`).
- `/health` incluye `request_id`.

**NO** se modificó la lógica de análisis (`app/core/`, `app/services/`,
`app/api/routes/analyze.py`). La cobertura de `app/main.py` pasó de 91 % a 100 % por
los tests de handlers (v0.2.2), no por cambios de lógica de negocio.

## 4. Confirmaciones

- **Tag `v0.2.2` apunta a HEAD (D)**: `git rev-parse v0.2.2^{commit}` ==
  `git rev-parse HEAD`.
- **Docs con SHA de release:** `dc98087` (HANDOFF/CIERRE).
- **Docker tests verdes:** 83 passed, 97 %.
- **Local tests verdes:** 83 passed, 97 %.
- **`ruff` OK**, **HANDOFF OK (4/4)**, matriz **10/10**.
- **No se tocó lógica de análisis**; solo Docker/build/test setup, docs y metadata.
- **`core-api/` intacto** (no existe).
- **Documentos históricos intactos** (`CIERRE_GAPS_SPRINT0.md`, `ESTADO_ACTUAL.md`,
  `CONSISTENCY_FIX.md`).
