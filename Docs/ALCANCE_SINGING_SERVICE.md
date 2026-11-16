# Alcance — `singing-service` (SyncDance AI)

> Documento de trazabilidad para el docente/líder. El **docx v1.0** es la fuente
> normativa de RF/HU/sprints; `Docs/Obsidian/` es análisis derivado (no normativo).
> Estado: `sprint2` @ `8d10789`, tag `v0.4.0` (release), 138+3 tests, 98 %.

## 1. Qué es

Microservicio **stateless** de análisis de canto. Recibe audio (`absolute`) o audio +
referencia (`comparative`) y devuelve pitch, ritmo, métricas, segmentos y feedback.
Sin auth, sin DB, red interna Docker. El Core es la fuente de verdad.

## 2. Mapeo de sprints (crítico para el docente)

| Fase del repo | Equivalencia con plan base | Estado |
|---|---|---|
| **“Sprint 0 local”** (v0.2.0 → v0.2.3) | **S0–S5 del plan del microservicio** (comprimido) | ✅ Ejecutado |
| **`sprint1`** (v0.3.0-dev) | **Post-MVP / calidad** (no está en el docx ni en el plan original) | ✅ 4/4 HUs cerradas |
| **`sprint2`** (v0.4.0) | **Hardening / production-ready** | ✅ 4/4 HUs cerradas |

> El **“Sprint 0” del repo NO es el S1 del docx** (Core usuarios/rutinas). Es el
> **S0–S5 del plan del microservicio** ejecutado en un solo ciclo. `sprint1` fue
> calidad/observabilidad (v0.3.0); `sprint2` es hardening/production-ready
> (v0.4.0).

## 3. Requisitos Funcionales cubiertos (docx v1.0 como fuente normativa)

| RF docx | RF Obsidian | Descripción | Estado | Evidencia |
|---|---|---|---|---|
| RF-37 | RF-26 | Pitch (F0) | ✅ | `pitch.py`, `test_pitch.py` |
| RF-38 | RF-27 | Afinación / evaluación | ✅ | `scoring.py`, `align.py` (FastDTW cableado en HU-S1-04) |
| RF-39 | RF-28 | Feedback vocal | ✅ | `feedback.py` |
| RF-40 | RF-29 | Puntaje multimodal | ⚪ Core (servicio entrega `scores.vocal`) | `celery-contract.md` §4 |

**Nota:** el docx usa RF-37…40; Obsidian usa RF-26…29. El servicio sigue el docx.
**El docx v1.0 es la fuente normativa.** Obsidian es análisis derivado (no normativo).

## 4. Extensiones no previstas en el docx (scope creep justificado)

| Extensión | Por qué | Documentada en |
|---|---|---|
| `rhythm_eval` / `scores.ritmo` | Decisión de producto Sprint 1 (valor pedagógico) | `SPRINT1_BACKLOG.md`, `CIERRE_HU_S1_01.md` |
| `/ready`, `/version` | Observabilidad para K8s | `CIERRE_HU_S1_02.md` |
| Warm-up (JIT frío) | Mitiga latencia del primer request | `CIERRE_HU_S1_03.md` |
| FastDTW cableado | Cierra RF-38 con calidad real | `CIERRE_HU_S1_04.md` |
| Timeout interno + `/metrics` | Evita bloqueos y da observabilidad Prometheus | `CIERRE_HU_S1_05.md` |
| `pitch_contour` | Curva para superponer alumno vs referencia en el frontend | `CIERRE_HU_S1_09.md` |
| Cache de ritmo + warm-up de pulsos | Reduce latencia y elimina el JIT del primer request | `CIERRE_HU_S2_XX.md` |
| `httpx2` | Elimina warnings de deprecación en tests | `CIERRE_HU_S1_08.md` |

## 5. HUs ejecutadas vs backlog original

| HU backlog | Estado real |
|---|---|
| HU-S1-01 (rhythm_eval) | ✅ Ejecutada (88273a8) |
| HU-S1-02 (`/ready` + `/version`) | ✅ Ejecutada (9ac255b) — el backlog original la llamaba `pitch_contour` |
| HU-S1-03 (warm-up) | ✅ Ejecutada (70ab517) — el backlog original la llamaba CREPE |
| HU-S1-04 (FastDTW) | ✅ Ejecutada (ed29ac1) |
| HU-S1-06 (warm-up) | ✅ Ejecutada como HU-S1-03 (duplicada) |
| HU-S1-05 (timeout + `/metrics`) | ✅ Ejecutada (5278a2b) |
| HU-S1-09 (`pitch_contour`) | ✅ Ejecutada (9caa08f) |
| HU-S2-XX (latencia de ritmo) | ✅ Ejecutada (4343068) |
| HU-S1-08 (httpx2) | ✅ Ejecutada (8d10789) |

**Pendientes reales (post-v0.4.0):** HU-S1-10 (CREPE vs pyin) y HU-S4-01
(recalibrar estabilidad). HU-S1-07 cerrada con el tag `v0.4.0`.

## Sprint 2 (v0.4.0) — production-ready

- **HU-S1-05 — Timeout + `/metrics`:** `PYIN_TIMEOUT_SECONDS` /
  `ALIGN_TIMEOUT_SECONDS` → **504 `ANALYSIS_TIMEOUT`**; `/metrics` Prometheus
  (counters, histogramas, gauge `active_requests`).
- **HU-S1-09 — `pitch_contour`:** opt-in `include_contour=true`, downsample
  ~10 Hz, máximo 6000 puntos, JSON <1 MB para 10 min.
- **HU-S2-XX — Latencia de ritmo:** cache por hash (0 ms en hit) + warm-up con
  pulsos 120 BPM (primer request 3994 ms → 262 ms). El “3.8 s” era **JIT frío**,
  no coste por audio (estable: 8–19 ms para MASTmelody).
- **HU-S1-08 — `httpx2`:** `TestClient` migrado a `httpx2==2.16.2`; cero
  `StarletteDeprecationWarning`.

**Estado:** MVP funcional completo + hardening. **Listo para integración con
Core.**

## 6. API actual vs plan original (BREAKING documentados)

| Plan original | API real |
|---|---|
| `file` | `audio` |
| `reference_file` | `reference_audio` |
| `mode=mock\|real` | `mode=absolute\|comparative` |

## 7. Límite con Core

El `singing-service` **no** implementa: auth, DB, usuarios, rutinas, persistencia,
notificaciones ni multimodal (HU-47). Todo eso es Core. El servicio entrega
`AnalysisResult`; el Core lo persiste y lo combina con el análisis de baile.

## 8. Límite con Frontend

Flutter y Angular **no** consumen el `singing-service` directamente. Solo consumen
Core API.
