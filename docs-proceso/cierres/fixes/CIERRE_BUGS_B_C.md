# CIERRE_BUGS_B_C — notas documentales (sin cambios de código)

> Cierre documental autorizado tras `AUDITORIA_BUGS_B_C.md`.
> Fecha: 2026-11-15. **No se tocó código, tests ni `Docs/scoring.md`.**
> Tag v0.2.2 intacto; contrato sin cambio de shape.

## 1. Diff resumido (3 archivos)

```
$ git diff --stat
 singing-service/CHANGELOG.md            |  7 +++++++
 singing-service/docs/SPRINT1_BACKLOG.md | 18 ++++++++++++++++++
 singing-service/docs/celery-contract.md |  2 ++
 3 files changed, 27 insertions(+)
```

| Archivo | Cambio |
|---|---|
| `singing-service/docs/celery-contract.md` | §4: blockquote **Nota C — cardinalidad de `feedback`** (1 ítem por tipo, no por segmento; peor desviación en `OUT_OF_TUNE`; detalles en `segments[]`; referencia a `Docs/scoring.md` §Feedback). |
| `singing-service/docs/SPRINT1_BACKLOG.md` | Nueva sección **Deuda técnica (Sprint 4)** con **HU-S4-01 — Recalibrar `scores.estabilidad` con datos reales** (contexto, no-bug, riesgos, criterios, dependencias, esfuerzo M). |
| `singing-service/CHANGELOG.md` | Nueva sección **`[Unreleased]` → Documentación** con las dos notas. |

### Nota C (texto exacto añadido)

> **Nota C — cardinalidad de `feedback`.** El array `feedback` contiene **1 ítem por tipo** (`OUT_OF_TUNE`, `NO_VOICE`), **no 1 por segmento**. En `OUT_OF_TUNE` se reporta la **peor desviación** (mayor `delta_cents`). Los detalles completos por segmento están en `segments[]`. Comportamiento documentado en `Docs/scoring.md` §Feedback. Un cambio a 1 feedback por segmento sería BREAKING y requiere coordinación con Core.

### HU-S4-01 (resumen)

- **Contexto:** `100 − 2·σ(cents)` (mín. 0, `Docs/scoring.md` línea 47) cae a 0 con
  `σ ≥ 50`; evidencia `AUDITORIA_BUGS_B_C.md` A3 + MASTmelody (229.2 → 0).
- **No es bug:** documentado.
- **Riesgos:** UX pobre si no se hace; enmascarar el pitch bajo si se hace antes de
  Sprint 1.
- **Criterios:** 10+ cantantes reales, curva justificada, tests reales, actualizar
  `Docs/scoring.md`.
- **Dependencias:** FastDTW + datos reales. **Sprint 4. Esfuerzo M.**

## 2. Verificación de las notas (grep real)

```
$ grep -rn "Nota C" docs/celery-contract.md
118:> **Nota C — cardinalidad de `feedback`.** El array `feedback` contiene **1 ítem por tipo** (`OUT_OF_TUNE`, `NO_VOICE`), **no 1 por segmento**. En `OUT_OF_TUNE` se reporta la **peor desviación** (mayor `delta_cents`). Los detalles completos por segmento están en `segments[]`. Comportamiento documentado en `Docs/scoring.md` §Feedback. Un cambio a 1 feedback por segmento sería BREAKING y requiere coordinación con Core.
```

```
$ grep -rn "Recalibrar .scores.estabilidad" docs/SPRINT1_BACKLOG.md
83:### HU-S4-01 — Recalibrar `scores.estabilidad` con datos reales
```

`Docs/scoring.md` existe con mayúscula (`Test-Path` → `True`, 3.214 bytes). No se
encontraron referencias lowercase `docs/scoring.md` en los documentos; no hay enlace
roto.

## 3. Tests (sin cambios de código)

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
======================= 83 passed, 1 warning in 8.87s ========================
```

`ruff check .` → `All checks passed!`

## 4. Handoff

```
-- 1/4 docker compose up + health --
docker compose up: OK
[PASS] health 200 (http://localhost:5000/health)

-- 2/4 fixtures --
fixtures: OK (11 archivos)

-- 3/4 simulacion de worker (absolute + comparative) --
[PASS] simulate absolute
[PASS] simulate comparative

-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 5. Confirmaciones

- **No se tocó `app/` ni `tests/`.** El diff solo contiene 3 documentos.
- **No se tocó `Docs/scoring.md`** (fuente de verdad); solo se referencia.
- **No cambió la fórmula de estabilidad** (`100 − 2·σ` sigue igual).
- **No cambió la cardinalidad de `feedback`** (1 por tipo; el código sigue igual).
- **El contrato no cambió de shape:** solo se añadió un blockquote aclaratorio en §4;
  los campos, tipos y códigos HTTP siguen intactos.
- **Tag v0.2.2 intacto**; no se re-taggeó ni se hizo commit (los cambios de docs están
  en el working tree, listos para que el líder los revise/commitee).
- **`Docs/scoring.md` existe con mayúscula**; no se creó una referencia rota.
- **83 tests verdes, 97 % cobertura, ruff OK, HANDOFF OK.**
