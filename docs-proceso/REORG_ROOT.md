# Reorganización del root — `docs-proceso/`

> Fecha: 2026-11-16 · Rama `sprint2` · Tag `v0.4.0` intacto en `ddfe6ef`.
> Nada se borró: 29 `.md` movidos con `git mv` + 2 README nuevos.

## 1. `ls *.md` antes

```text
AUDITORIA_ALINEACION.md
AUDITORIA_BUGS_B_C.md
AUDITORIA_v0.2.0.md
CIERRE_BATCH_DOCS.md
CIERRE_BUGS_B_C.md
CIERRE_FINAL_v0.2.2.md
CIERRE_FORMAL_v0.2.2.md
CIERRE_GAPS_SPRINT0.md
CIERRE_HU_S1_01.md
CIERRE_HU_S1_02.md
CIERRE_HU_S1_03.md
CIERRE_HU_S1_04.md
CIERRE_HU_S1_05.md
CIERRE_HU_S1_08.md
CIERRE_HU_S1_09.md
CIERRE_HU_S2_XX.md
CIERRE_ISSUES_HU_S1_01.md
CIERRE_SPRINT0_FINAL.md
CIERRE_v0.2.2.md
CIERRE_v0.2.3.md
CIERRE_v0.3.0.md
CIERRE_v0.4.0.md
CONSISTENCY_FIX.md
DOCS_CONTINUATION.md
ESTADO_ACTUAL.md
FIX_P0-01.md
HANDOFF_CORE.md
INDEX_DOCUMENTADOR.md
MENSAJE_CORE.md
```

Archivos fuera de la lista objetivo: `CIERRE_BATCH_DOCS.md` y `CIERRE_v0.3.0.md`
→ movidos a `historico/` (no se borraron).

## 2. `ls *.md` después

```text
README.md
```

## 3. `git status --short` antes del commit

```text
R  AUDITORIA_ALINEACION.md -> docs-proceso/auditorias/AUDITORIA_ALINEACION.md
R  AUDITORIA_BUGS_B_C.md -> docs-proceso/auditorias/AUDITORIA_BUGS_B_C.md
R  AUDITORIA_v0.2.0.md -> docs-proceso/auditorias/AUDITORIA_v0.2.0.md
R  CIERRE_BUGS_B_C.md -> docs-proceso/cierres/fixes/CIERRE_BUGS_B_C.md
R  CONSISTENCY_FIX.md -> docs-proceso/cierres/fixes/CONSISTENCY_FIX.md
R  FIX_P0-01.md -> docs-proceso/cierres/fixes/FIX_P0-01.md
R  CIERRE_HU_S1_01.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_01.md
R  CIERRE_HU_S1_02.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_02.md
R  CIERRE_HU_S1_03.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_03.md
R  CIERRE_HU_S1_04.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_04.md
R  CIERRE_HU_S1_05.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_05.md
R  CIERRE_HU_S1_08.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_08.md
R  CIERRE_HU_S1_09.md -> docs-proceso/cierres/hu/CIERRE_HU_S1_09.md
R  CIERRE_HU_S2_XX.md -> docs-proceso/cierres/hu/CIERRE_HU_S2_XX.md
R  CIERRE_ISSUES_HU_S1_01.md -> docs-proceso/cierres/hu/CIERRE_ISSUES_HU_S1_01.md
R  CIERRE_FINAL_v0.2.2.md -> docs-proceso/cierres/sprint0/CIERRE_FINAL_v0.2.2.md
R  CIERRE_FORMAL_v0.2.2.md -> docs-proceso/cierres/sprint0/CIERRE_FORMAL_v0.2.2.md
R  CIERRE_GAPS_SPRINT0.md -> docs-proceso/cierres/sprint0/CIERRE_GAPS_SPRINT0.md
R  CIERRE_SPRINT0_FINAL.md -> docs-proceso/cierres/sprint0/CIERRE_SPRINT0_FINAL.md
R  CIERRE_v0.2.2.md -> docs-proceso/cierres/sprint0/CIERRE_v0.2.2.md
R  CIERRE_v0.2.3.md -> docs-proceso/cierres/sprint0/CIERRE_v0.2.3.md
R  CIERRE_v0.4.0.md -> docs-proceso/cierres/sprint0/CIERRE_v0.4.0.md
R  HANDOFF_CORE.md -> docs-proceso/handoff/HANDOFF_CORE.md
R  INDEX_DOCUMENTADOR.md -> docs-proceso/handoff/INDEX_DOCUMENTADOR.md
R  MENSAJE_CORE.md -> docs-proceso/handoff/MENSAJE_CORE.md
R  CIERRE_BATCH_DOCS.md -> docs-proceso/historico/CIERRE_BATCH_DOCS.md
R  CIERRE_v0.3.0.md -> docs-proceso/historico/CIERRE_v0.3.0.md
R  DOCS_CONTINUATION.md -> docs-proceso/historico/DOCS_CONTINUATION.md
R  ESTADO_ACTUAL.md -> docs-proceso/historico/ESTADO_ACTUAL.md
?? README.md
?? docs-proceso/README.md
```

## 4. Árbol final

```text
docs-proceso/
├── README.md
├── REORG_ROOT.md
├── auditorias/
│   ├── AUDITORIA_ALINEACION.md
│   ├── AUDITORIA_BUGS_B_C.md
│   └── AUDITORIA_v0.2.0.md
├── cierres/
│   ├── fixes/
│   │   ├── CIERRE_BUGS_B_C.md
│   │   ├── CONSISTENCY_FIX.md
│   │   └── FIX_P0-01.md
│   ├── hu/
│   │   ├── CIERRE_HU_S1_01.md
│   │   ├── CIERRE_HU_S1_02.md
│   │   ├── CIERRE_HU_S1_03.md
│   │   ├── CIERRE_HU_S1_04.md
│   │   ├── CIERRE_HU_S1_05.md
│   │   ├── CIERRE_HU_S1_08.md
│   │   ├── CIERRE_HU_S1_09.md
│   │   ├── CIERRE_HU_S2_XX.md
│   │   └── CIERRE_ISSUES_HU_S1_01.md
│   └── sprint0/
│       ├── CIERRE_FINAL_v0.2.2.md
│       ├── CIERRE_FORMAL_v0.2.2.md
│       ├── CIERRE_GAPS_SPRINT0.md
│       ├── CIERRE_SPRINT0_FINAL.md
│       ├── CIERRE_v0.2.2.md
│       ├── CIERRE_v0.2.3.md
│       └── CIERRE_v0.4.0.md
├── handoff/
│   ├── HANDOFF_CORE.md
│   ├── INDEX_DOCUMENTADOR.md
│   └── MENSAJE_CORE.md
└── historico/
    ├── CIERRE_BATCH_DOCS.md
    ├── CIERRE_v0.3.0.md
    ├── DOCS_CONTINUATION.md
    └── ESTADO_ACTUAL.md
```

## 5. Verificación

```text
$ pytest --no-cov
138 passed, 3 deselected, 1 warning in 31.60s

$ pytest -m integration --no-cov
3 passed, 138 deselected in 4.15s

$ ruff check .
All checks passed!

$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 6. Confirmaciones

- **Nada borrado:** 29 archivos movidos con `git mv` (git los reporta como `R`).
- **`Docs/` intacto:** sin cambios en el commit.
- **`singing-service/` intacto:** sin cambios de código; tests y ruff verdes.
- **Tag `v0.4.0` intacto** en `ddfe6ef`.
- **Root limpio:** solo `README.md`.
