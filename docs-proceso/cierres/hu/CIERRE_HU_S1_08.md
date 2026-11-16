# CIERRE_HU_S1_08 — Migrar `TestClient` de `httpx` a `httpx2`

> Rama `sprint2` (HEAD previo `4343068`). Tag `v0.3.0` intacto en `0016e2e`.
> Fecha: 2026-11-16 · 138 tests por defecto + 3 integración (141) · ruff OK · HANDOFF OK.

## 1. Diff resumido

```text
 singing-service/requirements.txt       | 2 +-
 singing-service/tests/test_preprocess.py | 2 +-
 singing-service/CHANGELOG.md           | 8 ++++++++
 singing-service/docs/SPRINT2_BACKLOG.md | 10 +++++-----
 4 files changed, 13 insertions(+), 9 deletions(-)

Nuevo:
  CIERRE_HU_S1_08.md
```

- `requirements.txt`: `httpx==0.28.1` → **`httpx2==2.16.2`**.
- `tests/test_preprocess.py`: `from httpx import Response` →
  **`from httpx2 import Response`** (único import directo en tests).
- Sin cambios en `app/` ni en lógica de negocio.

## 2. Verificación de la dependencia

`httpx2` estable disponible (2.16.2). Starlette 1.7.0 ya lo prefiere:

```python
try:
    import httpx2 as httpx
except ModuleNotFoundError:
    import httpx  # deprecated
```

```text
$ pip show httpx2
Name: httpx2
Version: 2.16.2
Requires: anyio, httpcore2, idna, truststore

$ pip check
No broken requirements found.
```

## 3. Evidencia

### `pytest -v` (local)

```text
=============================== warnings summary ===============================
tests/test_hu_s1_01.py::test_rhythm_eval_failure_returns_empty
  ...librosa/core/spectrum.py:3004: UserWarning: n_fft=2048 is too large ...
...
================ 138 passed, 3 deselected, 1 warning in 36.04s ================
```

**No aparece `StarletteDeprecationWarning`.** El único warning restante es el de
librosa (`n_fft`), ajeno a esta HU.

### Docker

```text
$ docker compose exec -T singing-service python -m pytest --no-cov
138 passed, 3 deselected, 1 warning in 29.90s

$ docker compose exec -T singing-service python -m pytest -m integration --no-cov
1 passed, 2 skipped, 138 deselected in 1.34s
```

La imagen reconstruida instala `httpx2==2.16.2`; no queda `httpx` en
`requirements.txt`.

### `ruff check .`

```text
All checks passed!
```

### HANDOFF

```text
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 4. Confirmaciones

- **Cero cambios de lógica:** solo dependencia y un import de tipo en un test.
- **`core-api/` intacto:** no existe en este workspace y no se tocó nada fuera de
  `singing-service/`.
- **Tag `v0.3.0` intacto:**

```text
$ git rev-parse v0.3.0^{commit}
0016e2e65266ea6086e8c50253932497668e5e8d
```

- **Sin tag ni merge:** no se creó `v0.4.0` ni se hizo merge a `master`.

## 5. Notas

- `httpx` puede seguir instalado en el venv local de forma residual, pero ya no es
  una dependencia declarada ni la usa Starlette (prefiere `httpx2`). En la imagen
  Docker limpia no se instala `httpx`.
- `httpx2` arrastra `httpcore2` y `truststore`; `pip check` sin conflictos.
- HU-S1-08 queda ✅ en `docs/SPRINT2_BACKLOG.md`; el tag `v0.4.0` se crea al final
  de Sprint 2 (HU-S1-07).
