# CIERRE v0.2.3 — singing-service

> Release **docs-only**: Nota C (cardinalidad de `feedback`) + deuda técnica B
> (`HU-S4-01`). **Misma API que v0.2.2.** Sin cambios de código, tests,
> `Docs/scoring.md` ni shape del contrato.
> Fecha: 2026-11-15.

## 1. Git

### `git add` (solo los 3 docs) + `git status`

```
$ git add singing-service/CHANGELOG.md singing-service/docs/SPRINT1_BACKLOG.md singing-service/docs/celery-contract.md
$ git status
On branch master
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   singing-service/CHANGELOG.md
	modified:   singing-service/docs/SPRINT1_BACKLOG.md
	modified:   singing-service/docs/celery-contract.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	AUDITORIA_BUGS_B_C.md
	CIERRE_BUGS_B_C.md
```

Los 3 docs quedaron staged. Los dos archivos untracked son evidencia de la
auditoría/cierre de B/C y **no** forman parte del commit/tag.

### `git commit`

```
[master f744a8e] docs(singing-service): v0.2.3 — nota C (feedback cardinalidad) + deuda B (recalibrar estabilidad Sprint 4)
 3 files changed, 27 insertions(+)
```

### `git tag -a v0.2.3`

```
(sin salida; tag creado)
```

### `git rev-parse` / `git log` / `git tag -l`

```
$ git rev-parse HEAD
f744a8e18e7dac14bb0e6b7d5dbf36258efab7be
$ git rev-parse v0.2.3^{commit}
f744a8e18e7dac14bb0e6b7d5dbf36258efab7be
$ git log --oneline -3
f744a8e docs(singing-service): v0.2.3 — nota C (feedback cardinalidad) + deuda B (recalibrar estabilidad Sprint 4)
c836154 docs: cierre final v0.2.2 (Docker 3.14.6 + docs con SHA)
dc98087 docs: registrar release v0.2.2 (commit B) y cierre formal
$ git tag -l
v0.2.2
v0.2.3
```

**Confirmación:** `v0.2.3^{commit}` == `HEAD` ==
`f744a8e18e7dac14bb0e6b7d5dbf36258efab7be`. **v0.2.2 no se movió** (sigue en
`c836154`; API congelada).

## 2. Verificación

```
======================= 83 passed, 1 warning in 8.81s ========================
TOTAL                    138      4    97%
ruff check . → All checks passed!
```

```
-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 3. v0.2.2 (API) → v0.2.3 (docs only)

| Área | v0.2.2 | v0.2.3 | ¿Cambió? |
|---|---|---|---|
| Endpoints / métodos | `POST /api/v1/analyze`, `GET /{id}`, `/health` | idénticos | **No** |
| Modos | `absolute` / `comparative` | idénticos | **No** |
| Formatos / límites | wav/m4a/mp3/aac/ogg; 50 MB / 600 s | idénticos | **No** |
| Headers | `X-Request-ID` | idéntico | **No** |
| Códigos de error | 202/400/413/422/429/500/503 | idénticos | **No** |
| Shape de `feedback` | 1 ítem por tipo (peor desviación) | idéntico; **ahora documentado** en §4 | **No** (solo nota) |
| Fórmula de estabilidad | `100 − 2·σ` | idéntica | **No** |
| `app/` y `tests/` | — | intactos | **No** |
| `Docs/scoring.md` | fuente de verdad | intacto | **No** |
| Documentación | — | Nota C + `HU-S4-01` + `[Unreleased]` | **Sí** (solo docs) |

## 4. Instrucción para Core

**Usar `v0.2.3`.** La API es **idéntica** a `v0.2.2`; no hay cambios de cliente.
Solo se añaden notas:

- `feedback` sigue siendo **1 ítem por tipo** (no por segmento); los detalles están en
  `segments[]`. Un cambio a 1/segmento sería BREAKING y no se hizo.
- La deuda de calibración de `scores.estabilidad` queda planificada para Sprint 4
  (`HU-S4-01`); la fórmula actual no cambió.

## 5. Nota de working tree

Quedan untracked (evidencia, fuera del tag): `AUDITORIA_BUGS_B_C.md`,
`CIERRE_BUGS_B_C.md` y este `CIERRE_v0.2.3.md`. El commit/tag v0.2.3 contiene
exclusivamente los 3 documentos del release.
