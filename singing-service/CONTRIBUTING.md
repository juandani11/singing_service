# Contributing — singing-service

## Setup

1. Clonar el monorepo.
2. `cd singing-service`
3. `docker compose up -d --build singing-service`
4. `pip install -r requirements-dev.txt`
5. `pytest -v` → **111 passed** (2 de integración deseleccionados); `pytest -v -m integration` → **2** (local) / **1 passed + 1 skipped** (Docker).

> **Tests de integración.** Los marcados `@pytest.mark.integration` (MASTmelody y
> worker 5xx) se excluyen por defecto (`-m 'not integration'`); correr
> `pytest -m integration`. MASTmelody requiere `integration/fixtures/mastmelody_per.m4a`
> (ignorado por `.gitignore`; no se copia en Docker → `skip`). El worker 5xx
> corre en local y Docker; `verify_handoff.sh` también lo cubre vía el script.

## Flujo de cambio

1. Rama `feat/HU-S1-XX` desde `main`.
2. Si cambia el contrato: actualizar `docs/celery-contract.md` + snapshot OpenAPI +
   `integration/` + `CHANGELOG.md`.
3. Correr `pytest -v` (addopts ya incluye `--cov=app.core --cov=app.main`) y verificar
   **≥ 70 % en `app/core`**.
4. Correr `ruff check .`.
5. Correr `bash integration/verify_handoff.sh` → `HANDOFF OK`.
6. PR con el checklist de abajo.

### Regenerar el snapshot OpenAPI

Tras un cambio de contrato:

```bash
python -c "import json; from fastapi.testclient import TestClient; from app.main import app; open('tests/snapshots/openapi_v1.json','w',encoding='utf-8').write(json.dumps(TestClient(app).get('/openapi.json').json(), indent=2, ensure_ascii=False))"
```

## Checklist de PR

- [ ] Tests añadidos/actualizados.
- [ ] Cobertura ≥ 70 % en `app/core`.
- [ ] `ruff check .` OK.
- [ ] Contrato actualizado (si aplica).
- [ ] `CHANGELOG.md` actualizado.
- [ ] Snapshot OpenAPI regenerado (si aplica).
- [ ] `verify_handoff.sh` OK.
- [ ] No se tocó `core-api/`.

## Reglas

- **No bloquear el event loop:** el endpoint es `async def`; cualquier llamada a
  librosa/FFmpeg debe ir por `run_in_threadpool` (no llamadas síncronas pesadas en el
  cuerpo `async`).
- No añadir dependencias pesadas sin justificarlo en el PR.
- No romper el contrato sin marcarlo **BREAKING** y notificar al equipo de Core.
- Los documentos históricos (`ESTADO_ACTUAL.md`, `CIERRE_GAPS_SPRINT0.md`,
  `HANDOFF_CORE.md`, `CONSISTENCY_FIX.md`) no se reescriben; se enlazan desde el README.
- Usar `pathlib` y evitar rutas hardcodeadas (multiplataforma).
