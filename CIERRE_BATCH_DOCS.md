# CIERRE_BATCH_DOCS — deuda documental Sprint 1

> Rama `sprint1`, HEAD base `ed29ac1`, tag `v0.2.3` (`f744a8e`). **Solo docs; sin
> cambios de código/tests.** 115 tests por defecto + 3 integración; 98 %; HANDOFF OK.

## 1. Diff resumido (solo docs)

| Archivo | Cambio |
|---|---|
| `.gitignore` | Ignora `Docs/Obsidian/.obsidian/`, `.trash/` y `**/*.eap`. |
| `Docs/Obsidian/` | Commit del **markdown** (50 `.md`); `.obsidian/` (5) y `.eap` (1) ignorados. |
| `Docs/ALCANCE_SINGING_SERVICE.md` | **Nuevo**: mapeo sprints, RF docx↔Obsidian, extensiones, HUs, API, límites Core/Frontend. |
| `singing-service/docs/SPRINT1_BACKLOG.md` | HU-S1-01/02/03/04/06 ✅ con commits; HU-S1-09 (`pitch_contour`) y HU-S1-10 (CREPE) nuevas; “Pendientes reales”. |
| `HANDOFF_CORE.md` | Banner **HISTÓRICO v0.2.x** (v0.2.2). Contenido intacto. |
| `MENSAJE_CORE.md` | Banner **HISTÓRICO v0.2.x** (v0.2.3). Contenido intacto. |
| `INDEX_DOCUMENTADOR.md` | Banner **HISTÓRICO v0.2.x** (v0.2.3). Contenido intacto. |
| `ESTADO_ACTUAL.md` | Banner **HISTÓRICO v0.2.x** (Sprint 0). Contenido intacto. |
| `Docs/integracion-core.md` | Banner **HISTÓRICO v0.2.x** (Sprint 0). Contenido intacto. |
| `Docs/scoring.md` | Nota “Estado (v0.3.0-dev)” FastDTW cableado + fallback + HU-S4-XX. |
| `AUDITORIA_ALINEACION.md` | Commiteada como evidencia de la auditoría. |
| `CIERRE_BATCH_DOCS.md` | **Nuevo**: este reporte. |

## 2. `Docs/Obsidian/` — solo markdown

```
$ git ls-files Docs/Obsidian/ | wc -l
50
$ git ls-files Docs/Obsidian/ | grep -c "\.md$"
50
$ git ls-files Docs/Obsidian/ | grep -c "\.eap$" || echo "0 .eap (correcto)"
0 .eap (correcto)
$ git ls-files Docs/Obsidian/ | grep -c "\.obsidian" || echo "0 .obsidian (correcto)"
0 .obsidian (correcto)
```

- **50 `.md`** commiteados (47 CU + `Requisitos Funcionales.md` + `FT Captura de
  Requisitos.md` + `Identificar Paquetes.md`).
- **6 ignorados**: 5 `.obsidian/` (workspace personal) + 1 `.eap` (binario EA ~1,9 MB).

## 3. Verificación

```
$ pytest -q
115 passed, 3 deselected

$ ruff check .
All checks passed!

$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK

$ git rev-parse v0.2.3^{commit}
f744a8e18e7dac14bb0e6b7d5dbf36258efab7be
```

- **Código/tests intactos**: `git status` solo muestra `.md`, `.gitignore` y
  `Docs/ALCANCE...`; no `app/`, `tests/`, `integration/`.
- **No se tocaron** `singing-service/docs/celery-contract.md`, `USAGE.md`,
  `ARCHITECTURE.md` (ya actualizados en HU-S1-04).
- **Sin tag**: `v0.3.0` queda para HU-S1-07.

## 4. Pendientes para Sprint 2

- **HU-S1-05** — `/metrics` Prometheus + timeout interno de pyin/comparación.
- **HU-S1-07** — empaquetar `v0.3.0` (tag, CHANGELOG, snapshot, handoff).
- **HU-S1-08** — migrar `TestClient` a `httpx2` (P2; warning actual).
- **HU-S1-09** — `pitch_contour` + downsample (10 Hz, ≤6000 puntos, <1 MB).
- **HU-S1-10** — CREPE vs `librosa.pyin` (3 audios, informe, decisión).
- **HU-S2-XX** — latencia de `rhythm_eval` (MASTmelody <2 s; 60 s <20 s).
- **HU-S4-01** — recalibrar `scores.estabilidad` con datos reales.
- **Sesión Core** — integrar el worker Celery real (contract-only hoy).

## 5. Confirmaciones

- Tag `v0.2.3` intacto (`f744a8e`); commit solo en `sprint1`; sin merge ni tag.
- `Docs/Obsidian/` solo markdown; `.obsidian/`/`.eap` ignorados.
- `pytest` 115 + 3; `ruff` OK; HANDOFF 4/4.
- `AUDITORIA_ALINEACION.md` commiteada como evidencia.
