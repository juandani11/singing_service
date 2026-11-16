# AUDITORIA_ALINEACION — `singing-service` (SyncDance AI)

> **Fecha:** 2026-11-16 · **Rama:** `sprint1` · **HEAD:** `432d926` · **Tag base:** `v0.2.3` (`f744a8e`)
> **Alcance:** solo lectura sobre el repo. **No se modificó código, tests ni docs existentes.**
> **Método:** inventario de `Docs/`, `Docs/Obsidian/`, código, tests, commits/tags y ejecución de la suite.

---

## Resumen ejecutivo

El `singing-service` **está alineado con el núcleo vocal del plan base** (EP-08: RF-37/38/39 y HU-43/44/45/46, con matices) y con el contrato operativo del Core, pero **no está en el Sprint 1 del plan base**. El plan original (`Docs/plan-implementacion-singing-service.md`) define S0–S5 y el documento de requisitos define S0–S5 + Post-MVP; el repo ejecutó **ese S0–S5 completo bajo la etiqueta local “Sprint 0”** (v0.2.0 → v0.2.3). El `sprint1` actual (HU-S1-01…08) es un **sprint nuevo, post-MVP/calidad**, que no aparece en el documento base ni en el plan original. Las desviaciones principales son: (1) `rhythm_eval`/`scores.ritmo` es **scope creep** justificado en `SPRINT1_BACKLOG.md` pero sin RF base; (2) **FastDTW existe en código (`align.py`) pero no está cableado en la ruta** (se usa `compare.align_by_time`); (3) la **numeración de RF del documento base (docx) y de Obsidian no coincide** (audio: RF-37…40 vs RF-26…29); (4) hay **docs históricos desactualizados** (`HANDOFF_CORE`, `MENSAJE_CORE`, `INDEX_DOCUMENTADOR`, `ESTADO_ACTUAL`, `Docs/integracion-core`) que aún dicen `rhythm_accuracy=null`/83 tests; (5) `Docs/Obsidian/` está **untracked**. La calidad del servicio es buena (111+2 tests, 98 %, ruff OK, HANDOFF 4/4, Docker 111+1+1), pero la **trazabilidad documental** es el riesgo principal. Recomendación: commitear el contenido markdown de Obsidian (sin `.obsidian/`), crear un `Docs/ALCANCE_SINGING_SERVICE.md` + mapa RF único, actualizar los docs históricos y priorizar el cableado/test de FastDTW (HU-S1-04).

---

## 1. Inventario de documentación (Fase 1)

### 1.1 `Docs/` (raíz)

Salida real:

```
Mode   LastWriteTime             Length Name
d----- 15/11/2026 09:36:47 p. m.        Obsidian
-a---- 14/11/2026 02:17:23 p. m. 7793   integracion-core.md
-a---- 06/10/2026 05:19:31 p. m. 34643  plan-implementacion-singing-service.md
-a---- 06/10/2026 05:34:10 p. m. 21850  prompt-agente-figma-canto.md
-a---- 06/10/2026 06:05:21 p. m. 147311 prototipo.png
-a---- 15/11/2026 09:09:07 p. m. 5281   scoring.md
-a---- 04/10/2026 12:43:55 p. m. 125076 SyncDance AI Requisitos y Alcance Propuesto.docx
```

- **Documento de requisitos y alcance (exacto):** `Docs/SyncDance AI Requisitos y Alcance Propuesto.docx`
  — **125.076 bytes**, fecha **04/10/2026 12:43:55**, versión **1.0 — Backlog base para planificación y desarrollo**, septiembre 2026.
  Es un `.docx` (binario); se extrajo su texto con `zipfile` + XML a un temporal:
  **53.633 caracteres / 1.837 líneas** (legible; sin pérdida relevante).
- **Plan del microservicio:** `Docs/plan-implementacion-singing-service.md` (34.643 bytes, 06/10/2026).
- **Guía Core:** `Docs/integracion-core.md` (7.793 bytes, 14/11/2026).
- **Scoring:** `Docs/scoring.md` (5.281 bytes, 15/11/2026).
- **Prompt Figma:** `Docs/prompt-agente-figma-canto.md` (21.850 bytes).
- **Prototipo:** `Docs/prototipo.png` (147.311 bytes; imagen, no se inspecciona contenido visual aquí).

### 1.2 `Docs/Obsidian/`

- Existe; **56 archivos**, **1.973.567 bytes** en total.
- Contenido:
  - `Requisitos Funcionales.md` (5.362 bytes, 76 líneas) — lista RF-01…RF-40.
  - `FT. Captura de Requisitos/FT Captura de Requisitos.md` (19.663 bytes, 184 líneas) — actores, **CU-01…CU-47**, priorización, include/extend.
  - `FT. Captura de Requisitos/CU1…CU47/Detalle de caso de uso.md` — **47** detalles de CU.
  - `FT. Analisis/Identificar Paquetes.md` (4.813 bytes, 27 líneas) — paquetes P1…P7.
  - `PUDS_Proyecto_Final.eap` (~1,9 MB; **binario Enterprise Architect**, **NO LEGIBLE** como texto).
  - `.obsidian/` (5 JSON de configuración/workspace; **no es documentación de producto**).
- **No hay un plan de sprints explícito en Obsidian**; el plan de sprints está en el `.docx` (§9) y en `Docs/plan-implementacion-singing-service.md` (§4).
- **No hay mapa de trazabilidad RF→HU→sprint en Obsidian**; el `.docx` §10 sí lo tiene (RF→HU→Sprint), y `FT Captura` mapea CU→RF.

### 1.3 Tracking en git

```
$ git status --short Docs/
?? Docs/Obsidian/

$ git ls-files Docs/
Docs/SyncDance AI Requisitos y Alcance Propuesto.docx
Docs/integracion-core.md
Docs/plan-implementacion-singing-service.md
Docs/prompt-agente-figma-canto.md
Docs/prototipo.png
Docs/scoring.md
```

- **`Docs/Obsidian/` está untracked** (no commiteado).
- **El documento de requisitos `.docx` está commiteado**.
- `Docs/Obsidian/` incluye `.obsidian/` (workspace personal) y un `.eap` binario; **no debe commitearse tal cual**.

### 1.4 Contenido del documento base (`.docx`)

Extraído completo (1.837 líneas). Lo relevante:

- **41 RF** (RF-01…RF-41), con prioridad P0–P3. Los vocales son **RF-37 (pitch), RF-38 (afinación), RF-39 (feedback vocal), RF-40 (multimodal)**; RF-41 es administración.
- **9 épicas** (EP-01…EP-09). EP-08 = “Análisis vocal multimodal” (RF-37…RF-40).
- **49 HU** (HU-01…HU-49). Las vocales son **HU-43…HU-47**, **Sprint 5**, P2; HU-48 notificación (S5), HU-49 PDF (Post-MVP).
- **Sprints:** S0 fundación; **S1 HU-01…HU-12 (usuarios/rutinas/asignaciones — Core)**; S2 HU-13…HU-20 (captura/async — Core); S3 HU-21…HU-30 (IA de baile — Core/IA); S4 HU-31…HU-41 (feedback/visualización — Core/Frontend); **S5 HU-42…HU-48 (vocal + admin + notificación)**; Post-MVP HU-49.
- **Stack de referencia:** Django/DRF, Angular, Flutter, PostgreSQL, Redis + Celery, workers IA.
- **Arquitectura:** flujo instructor→alumno→backend→workers IA→comparación→resultado; el vocal es **extensión posterior** (“si el tiempo lo permite”, §3.3).
- **Criterios de aceptación por incremento** (§11): el incremento “Innovación vocal” exige pitch, comparación, score vocal y feedback **sin romper el flujo de baile**.
- **Riesgos/supuestos:** sprints de 2 semanas (hipótesis); SP Fibonacci; prioridad P0/P1/P2/P3; datos de prueba §12.1.

### 1.5 Contenido de Obsidian

- `Requisitos Funcionales.md`: **RF-01…RF-40**, pero con **numeración distinta a la del `.docx`**:
  - Obsidian **RF-26 pitch, RF-27 afinación, RF-28 feedback vocal, RF-29 multimodal**.
  - `.docx` **RF-37 pitch, RF-38 afinación, RF-39 feedback vocal, RF-40 multimodal**.
  - Obsidian **RF-30 feedback técnico … RF-40 notificación**; `.docx` **RF-26 feedback técnico … RF-36 notificación**.
  - Obsidian **omite RF-41 (administración)**; el `.docx` lo incluye.
- `FT Captura`: **CU-33…CU-36** son el módulo de audio (pitch, afinación, feedback vocal, multimodal); **CU-37** es feedback técnico; **CU-38…CU-47** visualización/seguimiento. Prioriza CU-33/34/36 como **críticos** (si el cliente exige canto desde la primera versión).
- `Identificar Paquetes`: **P5 = Análisis de Audio y Canto** (pitch, afinación, feedback vocal, multimodal); **P6 = feedback/visualización**; **P7 = seguimiento**.
- **Contradicciones detectadas (explícitas):**
  1. **RF audio**: `.docx` RF-37…40 vs Obsidian RF-26…29. `Docs/plan` y `Docs/scoring` usan la numeración del `.docx` (RF-37…40), **no** la de Obsidian.
  2. **RF-41**: existe en el `.docx`; **no existe** en Obsidian.
  3. **Sprints**: Obsidian no define sprints; el `.docx` sí. No hay contradicción de sprints, sino **ausencia** en Obsidian.
  4. **Alcance vocal**: el `.docx` lo pone en **S5/P2** y “si el tiempo lo permite”; el plan del microservicio lo **adelanta a S3–S4** (decisión documentada en `Docs/plan` §1.1); el repo lo ejecutó en v0.2.0 (bajo “Sprint 0” local).

---

## 2. Inventario de la realidad (Fase 2)

### 2.1 Código

Módulos reales (`app/`):

```
app/main.py
app/api/routes/analyze.py
app/core/config.py, log.py, store.py
app/middleware/request_id.py
app/mock/data.py
app/schemas/analyze.py
app/services/align.py, compare.py, feedback.py, metrics.py,
             pitch.py, preprocess.py, rhythm_eval.py, scoring.py
```

- **No existe** `app/api/deps.py` (el plan lo listaba; no es necesario en la implementación actual).
- **`app/services/align.py`** contiene `align_frames` con **FastDTW real** (`from fastdtw import fastdtw`, distancia en cents, `VOICE_GAP_CENTS`), probado en `tests/test_align.py`.
- **La ruta `analyze.py` NO usa `align_frames`**: usa `compare.align_by_time` (nearest-neighbor temporal) para `mode=comparative`. Es una decisión del Sprint 0 (`compare.py` lo documenta; `ARCHITECTURE.md` dice “`align.py` reservado para Sprint 1; no en la ruta”).
- **`app/services/rhythm_eval.py`** es real (HU-S1-01): `beat_track` + `onset_detect`, `rhythm_accuracy`, `scores.ritmo`, `tempo_bpm`, `rhythm_ms`.

Tests (16 archivos en `tests/`): `test_absolute`, `test_align`, `test_busy`, `test_comparative`, `test_contract`, `test_e2e`, `test_exception_handlers`, `test_health`, `test_hu_s1_01`, `test_hu_s1_02`, `test_hu_s1_03`, `test_log`, `test_pitch`, `test_preprocess`, `test_request_id`, `test_store`.

Integración: `generate_fixtures.py`, `simulate_celery_worker.py`, `test_error_scenarios.py`, `verify_handoff.sh`; además `scripts/demo_e2e.py` y `postman_collection.json`.

### 2.2 Docs del servicio

`singing-service/docs/` (6):

| Doc | Propósito |
|---|---|
| `ARCHITECTURE.md` (8.359 B) | Qué es, stack, flujo, decisiones, warm-up, riesgos. |
| `celery-contract.md` (17.694 B) | Contrato Core/Celery, multipart, errores, timeouts, ritmo aditivo. |
| `SPRINT1_BACKLOG.md` (5.107 B) | Backlog local Sprint 1 (HU-S1-01…08), HU-S2-XX, HU-S4-01. |
| `SWAGGER_GUIDE.md` (4.538 B) | Cómo probar en Swagger UI. |
| `TROUBLESHOOTING.md` (3.573 B) | Problemas operativos. |
| `USAGE.md` (17.941 B) | Manual de consumo, ejemplos reales. |

### 2.3 Commits y tags

```
432d926 2026-11-15 fix(singing-service): cerrar issues HU-S1-01 — test_5xx, fixture Docker, latencia rhythm_eval
88273a8 2026-11-15 feat(singing-service): HU-S1-01 rhythm_eval real (v0.3.0-dev)
3375f95 2026-11-15 docs: acta de cierre del Sprint 0 (batch anterior, ajeno a HU-S1-03)
70ab517 2026-11-15 feat(singing-service): HU-S1-03 warm-up librosa/numba (v0.3.0-dev)
9ac255b 2026-11-15 feat(singing-service): HU-S1-02 /ready + /version (v0.3.0-dev)
d056e94 2026-11-15 docs: borrador de mensaje a Core para v0.2.3
4057b4b 2026-11-15 docs: paquete de documentación para el documentador (v0.2.3)
4387038 2026-11-15 docs: evidencia de auditoría B/C y cierre v0.2.3 (fuera del tag)
f744a8e 2026-11-15 docs(singing-service): v0.2.3 — nota C + deuda B
c836154 2026-11-14 docs: cierre final v0.2.2 (Docker 3.14.6 + docs con SHA)
dc98087 2026-11-14 docs: registrar release v0.2.2 (commit B) y cierre formal
1b9271b 2026-11-14 test/docs: exception handlers coverage (97%), V-01, Python note, HU-S1-08
42eda5a 2026-11-14 chore: singing-service v0.2.2 — cierre Sprint 0 + handoff Core
```

Tags: **`v0.2.2` → `c836154`**, **`v0.2.3` → `f744a8e`** (verificado). No hay tag `v0.3.0` (el `settings.version` es `0.3.0`; el tag sigue en v0.2.3).

### 2.4 Tests, cobertura y HANDOFF

```
$ pytest -q                 → 111 passed, 2 deselected
$ pytest -q -m integration  → 2 passed, 111 deselected
$ pytest --cov=app.core --cov=app.main --cov-report=term-missing
TOTAL 243 4 98%   (app/main.py 100%, app/core/store.py 93%)
$ ruff check .              → All checks passed!
$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
Docker: 111 passed, 2 deselected; -m integration → 1 passed, 1 skipped (fixture MASTmelody)
```

---

## 3. Comparación (Fase 3)

### Tabla 1 — Requisitos Funcionales (`.docx`)

> Los RF-01…RF-25 son **Core/IA de baile** (Django, Angular, Flutter, MediaPipe, PostgreSQL); no son del `singing-service`. Se agrupan para no repetir “⚪ fuera de alcance” 25 veces. Los RF-26…RF-41 se detallan.

| RF | Descripción | Sprint plan | Estado real | Evidencia | Alineado |
|---|---|---|---|---|---|
| RF-01…RF-10 | Identidad, perfiles, rutinas, asignación (EP-01/EP-02) | S1 | No en singing-service | Core Django/Angular | ⚪ Fuera de alcance |
| RF-11…RF-16 | Captura, upload, estados, async, preprocess maestro (EP-03/EP-04) | S2 | No en singing-service (el servicio recibe audio ya extraído) | Core/Celery; el servicio expone `POST` multipart | ⚪ Fuera de alcance |
| RF-17…RF-25 | Pose, normalización, alineación de baile, métricas, persistencia (EP-05) | S3 | No en singing-service | Core/IA de baile | ⚪ Fuera de alcance |
| RF-26 | Feedback técnico (dance) | S4 | No en singing-service (el feedback vocal es RF-39) | Core/Frontend; `feedback.py` es vocal | ⚪ Fuera de alcance |
| RF-27 | Resultado del alumno (UI) | S4 | No en singing-service | Flutter/Angular | ⚪ Fuera de alcance |
| RF-28 | Reproductor sincronizado | S4 | No en singing-service | Frontend | ⚪ Fuera de alcance |
| RF-29 | Overlay de pose | S4 | No en singing-service | Frontend | ⚪ Fuera de alcance |
| RF-30 | Marcadores de error | S4 | No en singing-service | Frontend | ⚪ Fuera de alcance |
| RF-31 | Historial | S4 | No en singing-service | Core/Frontend | ⚪ Fuera de alcance |
| RF-32 | Evolución | S4 | No en singing-service | Core/Frontend | ⚪ Fuera de alcance |
| RF-33 | Dashboard instructor | S4 | No en singing-service | Core/Angular | ⚪ Fuera de alcance |
| RF-34 | Detalle del intento (instructor) | S4 | No en singing-service | Core/Angular | ⚪ Fuera de alcance |
| RF-35 | Informe técnico | S4 | No en singing-service | Core/Angular | ⚪ Fuera de alcance |
| RF-36 | Notificación | S5 | No en singing-service | Core | ⚪ Fuera de alcance |
| **RF-37** | **Extracción de pitch** | **S5** | **Implementado** | `app/services/pitch.py`; `tests/test_pitch.py`; v0.2.0; `CIERRE_GAPS_SPRINT0` | **✅ Alineado** |
| **RF-38** | **Evaluación de afinación** | **S5** | **Implementado con alineación simple; FastDTW no cableado** | `scoring.py`, `metrics.py`, `compare.align_by_time`; `tests/test_align.py`, `test_comparative.py`; `align.py` FastDTW reservado | **🟡 Desviado** |
| **RF-39** | **Feedback vocal** | **S5** | **Implementado** | `feedback.py` (`OUT_OF_TUNE`, `NO_VOICE`, `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE`); `tests/test_absolute.py`, `test_e2e.py`, `test_hu_s1_01.py` | **✅ Alineado** |
| RF-40 | Puntaje multimodal | S5 | No en singing-service (entrega `scores.vocal`; el Core combina) | `celery-contract.md` §4; `integracion-core.md` §4 | ⚪ Fuera de alcance (Core) |
| RF-41 | Administración básica | S5 | No en singing-service | Core Django admin | ⚪ Fuera de alcance |

**Conclusión RF:** de los 4 RF vocales del plan, **2 ✅ (37, 39), 1 🟡 (38), 1 ⚪ Core (40)**. No hay RF 🔴 en el servicio; el 🟡 de RF-38 es por FastDTW no cableado, no por ausencia de evaluación (la evaluación simple funciona y está probada).

### Tabla 2 — HUs del plan vs ejecutadas

> HU-01…HU-42 son Core/Frontend/IA de baile (no `singing-service`). Se agrupan. Se detallan HU-43…HU-49 y el Sprint 1 local.

| HU | Sprint plan | Estado | Commit/evidencia |
|---|---|---|---|
| HU-01…HU-42 | S1–S5 | No en singing-service | Core/Frontend/IA de baile |
| **HU-43** pitch | S5 (plan micro: S3) | **✅** | `pitch.py`; v0.2.0; `test_pitch.py` |
| **HU-44** alinear referencia | S5 (plan micro: S4) | **🟡** | `align.py` (FastDTW) **existe y está testeado**, pero la ruta usa `compare.align_by_time`; `SPRINT1_BACKLOG` HU-S1-04 dice “sin FastDTW todavía” |
| **HU-45** afinación/errores | S5 (plan micro: S4) | **✅** | `scoring.py`, `metrics.py`; `test_align.py`, `test_comparative.py` |
| **HU-46** feedback vocal | S5 (plan micro: S4–S5) | **✅** | `feedback.py`; `test_e2e.py`, `test_absolute.py`; Nota C (1 por tipo) |
| HU-47 multimodal | S5 | No en singing-service | Core combina `scores.vocal`; `celery-contract` §4 |
| HU-48 notificación | S5 | No en singing-service | Core |
| HU-49 PDF | Post-MVP | No en singing-service | Core/Frontend |

**Sprint 1 local (`SPRINT1_BACKLOG.md`) vs ejecución real:**

| HU local | Backlog dice | Estado real | Evidencia |
|---|---|---|---|
| HU-S1-01 rhythm | rhythm_eval real | **✅** | `88273a8` + `432d926`; `rhythm_eval.py`; `test_hu_s1_01.py` |
| HU-S1-02 | `pitch_contour` + downsample | **❌ (no ejecutada)**; **la HU-S1-02 ejecutada fue `/ready` + `/version`** | `9ac255b`; `test_hu_s1_02.py`; `CIERRE_HU_S1_02.md` |
| HU-S1-03 | CREPE vs pyin | **❌ (no ejecutada)**; **la HU-S1-03 ejecutada fue warm-up** | `70ab517`; `test_hu_s1_03.py`; `CIERRE_HU_S1_03.md` |
| HU-S1-04 | FastDTW/alineamiento robusto | **❌ pendiente** | `SPRINT1_BACKLOG`; `align.py` reservado; ruta `align_by_time` |
| HU-S1-05 | Timeout + `/metrics` | **❌ pendiente** | No hay `/metrics`; FFmpeg timeout 120 s; pyin sin timeout |
| HU-S1-06 | Warm-up | **✅ (ejecutada como HU-S1-03)** | `70ab517`; `CIERRE_HU_S1_03.md` |
| HU-S1-07 | Empaquetar 0.3.0 | **❌ pendiente** | `settings.version=0.3.0`; tag sigue `v0.2.3` |
| HU-S1-08 | Migrar a httpx2 | **❌ pendiente** | Warning `StarletteDeprecationWarning` en pytest |
| HU-S2-XX | Optimizar latencia rhythm | **❌ pendiente (S2)** | `SPRINT1_BACKLOG`; MASTmelody 3,8 s |
| HU-S4-01 | Recalibrar estabilidad | **❌ pendiente (S4)** | `Docs/scoring`; deuda B; MASTmelody 229,2 → 0 |

**Hallazgo fuerte:** el `SPRINT1_BACKLOG` **no refleja la ejecución**: HU-S1-02/03 están reutilizadas para `/ready`+`/version` y warm-up; HU-S1-06 (warm-up) se ejecutó como HU-S1-03; pitch_contour/CREPE/timeout/metrics/0.3.0/httpx2 siguen pendientes. Es un **gap de proceso/documentación**, no de código.

### Tabla 3 — Sprints: planificado vs ejecutado

| Sprint | Plan original | Ejecutado | Desviación |
|---|---|---|---|
| **S0** | Fundación técnica (repo, Docker, CI, esqueleto) | `42eda5a` v0.2.2; `f744a8e` v0.2.3; “Sprint 0” local | ✅ Ejecutado (el “Sprint 0” local absorbe el S0 del plan) |
| **S1 (docx)** | HU-01…HU-12: usuarios, rutinas, asignaciones (Core) | No en este repo | ⚪ Es Core (Django/Angular/Flutter) |
| **S1 (plan micro)** | Contrato OpenAPI + mock + `/docs` + Postman | v0.2.0; `test_contract`; `postman_collection.json` | ✅ Ejecutado dentro del “Sprint 0” local |
| **S2 (docx)** | HU-13…HU-20: captura, upload, async, preprocess maestro (Core) | `preprocess.py` del servicio; el resto Core | 🟡 Parcial (solo el preprocess del audio) |
| **S2 (plan micro)** | Preprocesamiento FFmpeg/pydub | `preprocess.py`; `test_preprocess.py` | ✅ |
| **S3 (docx)** | HU-21…HU-30: IA de baile (pose, normalización, DTW baile) | No en este repo | ⚪ IA de baile |
| **S3 (plan micro)** | Pitch `librosa.pyin` (HU-43) | `pitch.py`; `test_pitch.py` | ✅ |
| **S4 (docx)** | HU-31…HU-41: feedback/visualización/seguimiento | Feedback vocal del servicio; UI/Core no | 🟡 Parcial (solo backend vocal) |
| **S4 (plan micro)** | FastDTW + cents + score + feedback (HU-44/45/46) | `scoring.py`/`feedback.py` ✅; `align.py` FastDTW **no cableado** | **🟡 FastDTW pendiente de integración** |
| **S5 (docx)** | HU-42…HU-48: vocal + admin + notificación + E2E/demo | Vocal ✅; admin/notificación ⚪; E2E/handoff ✅ | 🟡 Parcial |
| **S5 (plan micro)** | Integración Core/Celery + HU-47 + hardening + E2E | Contrato/handoff/E2E del servicio ✅; Core real no (externo) | 🟡 Contract-only |
| **Sprint 1 actual (local)** | **No existe en el plan base**; `SPRINT1_BACKLOG` HU-S1-01…08 | 2/8 HUs cerradas + 2 ejecutadas con IDs distintos | **🟡 Sprint nuevo post-MVP/calidad** |
| **Post-MVP** | HU-49 PDF | No en singing-service | ⚪ Core/Frontend |

**¿Estamos en el sprint correcto?** **No respecto al plan base.** El plan base (docx) tiene **S1 = usuarios/rutinas (Core)**; el plan del microservicio tiene **S1 = contrato+mock**, ya ejecutado en v0.2.0 dentro del “Sprint 0” local. El `sprint1` actual es un **sprint nuevo** (post-MVP/calidad) que no aparece en el docx ni en el plan original. La etiqueta “Sprint 0” del repo **no es el S0 del docx**: es la ejecución comprimida del **S0–S5 del plan del microservicio** (confirmado por `ESTADO_ACTUAL.md`: “Sprints ejecutados: S0–S5”).

### Tabla 4 — Arquitectura: diseño vs realidad

| Componente | Diseño (docs base/plan) | Realidad (código) | Alineado |
|---|---|---|---|
| Stack del servicio | FastAPI + librosa + FastDTW + FFmpeg | FastAPI 0.142.2 + librosa 1.0.0 + fastdtw 0.3.4 + FFmpeg 7.1.5 | ✅ |
| Stateless / sin DB | Sin DB, TTL, fuente de verdad Core | `core/store.py` TTL 1 h; sin DB | ✅ |
| Sin auth / red interna | Sin JWT/roles | Sin auth; red Docker | ✅ |
| `POST /api/v1/analyze` | Plan: `file`, `reference_file`, `mode=mock\|real` | `audio`, `reference_audio`, `mode=absolute\|comparative` | 🟡 **BREAKING vs plan** (documentado en `INDEX_DOCUMENTADOR` §3.7) |
| `GET /analyze/{id}` | 200 `AnalysisResult` | 200 `AnalysisResult` | ✅ |
| FastDTW (HU-44) | Plan S4; `Docs/scoring` lo describe en el pipeline | `align.py` **tiene FastDTW**, pero la ruta usa `compare.align_by_time`; `ARCHITECTURE` dice “reservado”; `SPRINT1_BACKLOG` dice “sin FastDTW todavía” | **🟡 Contradicción doc-código** |
| Pitch (HU-43) | `librosa.pyin`, F0 + voiced | `pitch.py`; fmin 65/fmax 1600; `hop 512` | ✅ |
| Afinación/score (HU-45) | Cents, segmentos, score 0–100 documentado | `scoring.py`, `metrics.py`, `align.py` (segmentos), `Docs/scoring` | ✅ (con alineación simple) |
| Feedback (HU-46) | `OUT_OF_TUNE` ≠ `NO_VOICE` | `feedback.py`; 1 ítem/tipo (Nota C) | ✅ |
| Ritmo (`rhythm_accuracy`) | **No existe en el plan base**; diferido en v0.2.x | `rhythm_eval.py` real; `scores.ritmo`, `tempo_bpm`, `rhythm_ms` | **🟡 Scope creep** (documentado en Sprint 1) |
| `/ready`, `/version` | No en el plan base; operativo | `main.py`; `test_hu_s1_02` | 🟡 Operativo |
| Warm-up JIT | Riesgo del plan; mitigación S5 | `main.py` warm-up pyin + beat_track; `SKIP_WARMUP` | ✅ (adelantado; documentado) |
| `/metrics`, timeout pyin | Plan S5/HU-S1-05 | No hay `/metrics`; pyin sin timeout | **❌ Pendiente** |
| `X-Request-ID`, `UNHANDLED_ERROR` | Plan S5 (RNF-03) | `middleware/request_id.py`; handlers; tests | ✅ |
| Semáforo/429 | Plan S5 | `_analysis_semaphore`; `SERVICE_BUSY` | ✅ |
| Docker/compose | Plan S0 | Dockerfile multi-stage; compose; `verify_handoff` | ✅ |
| Core/Celery real | Plan S5 | Contrato/handoff/E2E del servicio; **Core externo**; no `core-api/` | 🟡 Contract-only |
| Tests del plan | `test_scoring.py`, `test_api.py`, `test_align.py`, `test_contract.py`, `test_preprocess.py`, `test_pitch.py` | `test_align.py`/`test_contract.py`/`test_e2e.py` cubren; **no** `test_scoring.py`/`test_api.py`; `test_pitch.py`/`test_preprocess.py` sí | 🟡 Nombres/cobertura distintos |
| Postman/demo | Plan S1/S5 | `postman_collection.json` (7.495 B); `scripts/demo_e2e.py` (6.971 B) | ✅ |
| `app/api/deps.py` | Plan lo lista | No existe (no necesario) | 🟡 Diferencia de árbol |

### Tabla 5 — Documentación: qué existe y qué falta

| Doc requerido por la base/plan | Existe | Ubicación | Estado |
|---|---|---|---|
| Manual de usuario | ✅ | `singing-service/docs/USAGE.md` | Completo; actualizado a 0.3.0-dev (ritmo, warm-up) |
| Contrato API/Celery | ✅ | `singing-service/docs/celery-contract.md` | Completo; actualizado (ritmo aditivo, `tempo_bpm`, `rhythm_ms`) |
| Arquitectura | ✅ | `singing-service/docs/ARCHITECTURE.md` | Completo; actualizado |
| Scoring | ✅ | `Docs/scoring.md` | Completo; **contradicción FastDTW** (dice FastDTW; la ruta usa `align_by_time`) |
| Backlog del sprint | ✅ | `singing-service/docs/SPRINT1_BACKLOG.md` | **Desactualizado vs ejecución** (HU-S1-02/03/06) |
| Handoff Core | ✅ | `HANDOFF_CORE.md` | **Desactualizado**: `rhythm_accuracy=null` (varias líneas); no refleja 0.3.0-dev |
| Guía Core | ✅ | `Docs/integracion-core.md` | **Desactualizado**: `rhythm_accuracy` “siempre null”; sin `tempo_bpm`/`scores.ritmo`/`rhythm_ms` |
| Índice documentador | ✅ | `INDEX_DOCUMENTADOR.md` | **Desactualizado**: v0.2.3, 83 tests/97 % |
| Mensaje Core | ✅ | `MENSAJE_CORE.md` | **Desactualizado**: v0.2.3, 83 tests |
| Estado actual | ✅ | `ESTADO_ACTUAL.md` | **Obsoleto** (el propio `INDEX` lo marca “snapshot obsoleto”); dice “sin ritmo”/“sin comparative” |
| Cierres | ✅ | `CIERRE_*.md` (Sprint 0, v0.2.2, v0.2.3, HU-S1-01/02/03, issues) | Actualizados; evidencia real |
| Requisitos y alcance | ✅ | `Docs/SyncDance AI Requisitos y Alcance Propuesto.docx` | v1.0 (septiembre 2026); base autoritativa; no actualizado con 0.3.0-dev |
| Requisitos Obsidian | ✅ (untracked) | `Docs/Obsidian/` | **Untracked**; RF renumerados vs docx; `.eap` binario; `.obsidian/` personal |
| Plan del microservicio | ✅ | `Docs/plan-implementacion-singing-service.md` | v1.0 (octubre); **desactualizado** en API (`file`/`reference_file`/`mode=mock\|real`) y en el estado (S0–S5 ya ejecutados) |
| Changelog | ✅ | `singing-service/CHANGELOG.md` | v0.2.3 + 0.3.0-dev; actualizado |
| README / CONTRIBUTING | ✅ | `singing-service/README.md`, `CONTRIBUTING.md` | Actualizados (111+2, 98 %) |
| Postman | ✅ | `singing-service/postman_collection.json` | Existe (7.495 B) |
| Demo E2E | ✅ | `singing-service/scripts/demo_e2e.py` | Existe (6.971 B) |
| `PUDS` EA | ❌ legible | `Docs/Obsidian/PUDS_Proyecto_Final.eap` | Binario EA; **no se pudo leer** |

---

## 4. Análisis de desviaciones (Fase 4)

| # | Desviación | Impacto | Causa | Acción recomendada |
|---|---|---|---|---|
| **D1** | `rhythm_eval`/`scores.ritmo` **no está en el plan base** (docx/Obsidian); es una HU nueva del Sprint 1 local | **Medio** | Decisión de producto del Sprint 1 (`HU-S1-01`), no del backlog base | Mantener (aporta valor), pero **documentar como extensión** y mapearla a un RF nuevo o a RF-38/39 ampliado; mantener HU-S2-XX para latencia |
| **D2** | **FastDTW no cableado**: `align.py` tiene FastDTW y tests, pero la ruta usa `compare.align_by_time`; `SPRINT1_BACKLOG` lo difiere y `Docs/scoring` lo describe como pipeline | **Alto** | Sprint 0 priorizó entrega; el plan micro lo dejó para “Sprint 1”; el backlog lo difiere | **Priorizar HU-S1-04**: cablear `align_frames` en `mode=comparative`, tests con offset ~200 ms, actualizar `Docs/scoring`/`ARCHITECTURE` |
| **D3** | **Integración Core real** no está en este repo (contrato/handoff sí) | **Medio** | El Core es externo (Django/Celery); `core-api/` no existe; bloqueado por monorepo | Fuera del alcance del servicio; mantener `verify_handoff` y `HANDOFF_CORE`; coordinar con Core |
| **D4** | **Numeración RF contradictoria**: docx RF-37…40 (audio) vs Obsidian RF-26…29 (audio); Obsidian omite RF-41 | **Alto** | Dos documentos base con numeraciones distintas; Obsidian es análisis derivado | **Un solo mapa RF** (docx como fuente de verdad) + tabla de equivalencia docx↔Obsidian; actualizar Obsidian o marcarlo “análisis, no normativo” |
| **D5** | **Sprint actual no es el Sprint 1 del plan**: `sprint1` es post-MVP/calidad; el S1 docx es Core; el S1 del plan micro (contrato/mock) ya está en v0.2.0 | **Medio** | El repo avanzó y creó un sprint local con otra semántica | Crear `Docs/ALCANCE_SINGING_SERVICE.md`/roadmap que explique “Sprint 0 local = S0–S5 del plan micro” y “Sprint 1 local = post-MVP/calidad” |
| **D6** | **`SPRINT1_BACKLOG` no refleja la ejecución**: HU-S1-02/03 reutilizadas (`/ready`+`/version`, warm-up); HU-S1-06 warm-up ejecutada como HU-S1-03; pitch_contour/CREPE/metrics/0.3.0/httpx2 pendientes | **Medio** | Re-scoping durante el sprint no reflejado en el backlog | Actualizar el backlog: mover pitch_contour/CREPE a HU-S1-02/03 reales, marcar warm-up como HU-S1-06, añadir `/ready`+`/version` como HU nueva, y dejar explícitas las pendientes |
| **D7** | **Docs históricos desactualizados**: `HANDOFF_CORE` (`rhythm_accuracy=null`), `MENSAJE_CORE` (v0.2.3/83), `INDEX_DOCUMENTADOR` (83/97), `ESTADO_ACTUAL` (sin ritmo/comparative), `Docs/integracion-core` (rhythm null) | **Medio** | No se actualizaron tras v0.3.0-dev/HU-S1-01 | Marcar como “histórico v0.2.x” o actualizar; la fuente actual es `celery-contract`/`USAGE`/`ARCHITECTURE`/`CHANGELOG` |
| **D8** | **`Docs/Obsidian/` untracked**; incluye `.obsidian/` y `.eap` binario | **Medio** | Documentación nueva no commiteada | Commitear el **markdown** (RF, FT, CU, Identificar); **excluir** `.obsidian/`; decidir el `.eap` (binario EA; opcional) |
| **D9** | **`Docs/scoring` describe FastDTW** en pipeline/HU-44; el código de ruta usa `align_by_time` | **Medio** | Doc aspiracional del Sprint 4; la ruta se simplificó en Sprint 0 | Aclarar en scoring: “FastDTW disponible en `align.py`, **no cableado**; la ruta usa `align_by_time` hasta HU-S1-04” |
| **D10** | **Artefactos del plan ausentes/diferentes**: `app/api/deps.py`, `tests/test_scoring.py`, `tests/test_api.py`; el plan los lista, el repo no los tiene (la cobertura está en `test_align`/`test_contract`/`test_e2e`) | **Bajo** | El árbol del plan era orientativo | Actualizar el árbol del plan o añadir los tests que falten; no es un gap funcional |
| **D11** | **HU-S1-07 (tag 0.3.0) pendiente**; `settings.version=0.3.0` pero tag `v0.2.3`; HU-S1-08 (httpx2) pendiente; HU-S1-05 (timeout/metrics) pendiente | **Medio/Bajo** | Sprint 1 en curso | Cerrar HU-S1-05/07/08 antes de declarar 0.3.0; el warning de httpx2 es P2 |

**Desviaciones justificadas (documentadas):** D1 (ritmo, `SPRINT1_BACKLOG` + `CIERRE_HU_S1_01`), D3 (Core externo, `ESTADO_ACTUAL`/`HANDOFF`), D5 (plan micro §1.1 adelantó el algoritmo; el “Sprint 0” local lo ejecutó), D6 (re-scoping; pero **no está actualizado** el backlog → parcialmente justificada), D11 (Sprint 1 en curso).

**Desviaciones no justificadas / deuda documental:** D2 (FastDTW no cableado; el plan dice S4; el código existe; el backlog lo difiere sin cerrar la decisión), D4 (RF numbering), D7 (docs históricos), D8 (Obsidian untracked), D9 (scoring FastDTW), D6 (backlog vs ejecución).

---

## 5. Conclusiones (Fase 5)

### 5.1 ¿Estamos alineados con el plan original?

**Parcialmente.**

- **Sí** en el núcleo vocal EP-08: pitch (RF-37), afinación/score (RF-38 con alineación simple), feedback vocal (RF-39), contrato Core, Docker, tests, handoff.
- **Sí** en la ejecución del plan del microservicio S0–S5 (bajo la etiqueta local “Sprint 0”): contrato/mock, preprocess, pitch, scoring/feedback, hardening, E2E/handoff.
- **No** en el Sprint 1 actual: no es el S1 del docx (Core usuarios/rutinas) ni el S1 del plan micro (contrato/mock, ya hecho); es un **sprint nuevo post-MVP/calidad**.
- **No** en FastDTW: el plan micro S4/HU-44 lo pedía; el código existe, pero **no está en la ruta**; el backlog lo difiere.
- **No** en la numeración RF: docx y Obsidian no coinciden; el servicio sigue el docx.

### 5.2 ¿Nos hemos desviado? ¿Por qué?

**Sí.** Desviaciones principales:

1. **Ritmo (`rhythm_eval`/`scores.ritmo`)**: no está en el docx/Obsidian; es **scope creep** del Sprint 1 local, justificado en `SPRINT1_BACKLOG` y `CIERRE_HU_S1_01` (aporta valor; latencia documentada; HU-S2-XX).
2. **FastDTW no cableado**: el plan micro S4/HU-44 lo pedía; el código `align.py` está y se testea, pero la ruta usa `align_by_time`; el `SPRINT1_BACKLOG` lo difiere a “Sprint 2+”. **No está justificado como cierre**: es una **deuda funcional** con impacto alto en comparative.
3. **`/ready`, `/version`, warm-up, `/metrics` (pendiente), release 0.3.0 (pendiente), httpx2 (pendiente)**: operativos/calidad, no RF del docx; están en el Sprint 1 local; el warm-up se adelantó y se documentó.
4. **API distinta al plan micro** (`audio` vs `file`, `reference_audio` vs `reference_file`, `mode=absolute|comparative` vs `mock|real`): **BREAKING** vs el plan; documentado en `INDEX_DOCUMENTADOR` §3.7 y en el contrato actual.
5. **Docs históricos** (`HANDOFF_CORE`, `MENSAJE_CORE`, `INDEX_DOCUMENTADOR`, `ESTADO_ACTUAL`, `Docs/integracion-core`) no reflejan 0.3.0-dev/ritmo; **no justificado** (deuda documental).
6. **RF numbering** docx vs Obsidian: **no justificado**; falta un mapa.
7. **`Docs/Obsidian/` untracked**: **no justificado**; la base no está en git.

### 5.3 ¿Qué falta para cerrar el alcance del `singing-service`?

**Pendientes del plan/backlog (con esfuerzo orientativo):**

| Pendiente | Origen | Esfuerzo |
|---|---|---|
| **HU-S1-04 — cablear FastDTW** (`align_frames`) + tests offset 200 ms + actualizar scoring/architecture | Plan micro S4/HU-44; `SPRINT1_BACKLOG` | **M** |
| **HU-S1-02 — `pitch_contour` + downsample** (10 Hz, ≤6000 puntos, JSON <1 MB, test 10 min) | `SPRINT1_BACKLOG` (no ejecutada) | **S** |
| **HU-S1-03 — CREPE vs pyin** (3 audios, informe, decisión) | `SPRINT1_BACKLOG` (no ejecutada) | **M** |
| **HU-S1-05 — timeout interno pyin/DTW + `/metrics` Prometheus** | `SPRINT1_BACKLOG` | **S** |
| **HU-S1-07 — empaquetar 0.3.0** (tag, CHANGELOG, snapshot, handoff) | `SPRINT1_BACKLOG` | **S** |
| **HU-S1-08 — migrar TestClient a httpx2** (0 warnings) | `SPRINT1_BACKLOG` (P2) | **S** |
| **HU-S2-XX — optimizar latencia rhythm** (MASTmelody <2 s; 60 s <20 s; ±2 BPM) | `SPRINT1_BACKLOG` (nueva) | **M** |
| **HU-S4-01 — recalibrar `scores.estabilidad`** con datos reales | `SPRINT1_BACKLOG` (deuda B) | **M** |
| **Core real (Celery/DB) + HU-47 multimodal** | docx S5/HU-47; Core externo | **L** (Core) |
| **Docx S1–S5 restantes (usuarios, rutinas, captura, IA de baile, UI/seguimiento)** | docx | **XL** (Core/Frontend/IA) |

### 5.4 ¿La documentación base está desactualizada?

**Sí, en partes críticas.**

- El **docx v1.0** (septiembre) no refleja 0.3.0-dev, el ritmo, `/ready`/`/version`, el warm-up, ni los cambios de API; sigue siendo la **fuente autoritativa** de RF/HU/sprints.
- El **plan micro** (octubre) usa `file`/`reference_file`/`mode=mock|real` y un árbol de tests que ya no coincide; el estado S0–S5 ya se ejecutó.
- **`Docs/scoring`** describe FastDTW en el pipeline, pero la ruta usa `align_by_time`.
- **`SPRINT1_BACKLOG`** no refleja la ejecución real (HU-S1-02/03/06).
- **`HANDOFF_CORE`/`MENSAJE_CORE`/`INDEX_DOCUMENTADOR`/`ESTADO_ACTUAL`/`Docs/integracion-core`** son snapshots v0.2.x; `rhythm_accuracy=null`/83 tests ya no son ciertos.
- **Obsidian** (nuevo) tiene una numeración RF distinta y no está commiteado.

**Dónde debería documentarse:** en `Docs/ALCANCE_SINGING_SERVICE.md` (nuevo), un **mapa RF único** (docx↔Obsidian↔HU), y actualizando/marcando como histórico los docs anteriores. El `CHANGELOG` y los `CIERRE_*` ya documentan los cambios; falta la **vista de alcance** y la **reconciliación de RF**.

### 5.5 ¿Riesgos de seguir así?

- **Scope creep:** el Sprint 1 local añade ritmo, `/ready`/`/version`, warm-up, release, httpx2; no están en el docx; si no se mapean, el alcance “oficial” no cuadra.
- **Scope gap:** FastDTW no cableado; `pitch_contour`, CREPE, timeout/metrics, 0.3.0, httpx2 pendientes; el docx HU-44 no está realmente integrado.
- **Deuda técnica no documentada:** la latencia de ritmo (3,8 s/4,8 s; 5 min → ~4 min) está documentada en contract/backlog/CIERRE, pero no en el docx; la estabilidad (deuda B) sigue.
- **Inconsistencia doc-código:** scoring FastDTW vs `align_by_time`; `SPRINT1_BACKLOG` vs ejecución; handoff/mensaje/índice/estado/integracion-core vs 0.3.0-dev; RF numbering.
- **Base documental fuera de git:** `Docs/Obsidian/` untracked; el `.eap` binario no es legible; el `.obsidian/` personal no debe commitearse.
- **Integración Core:** contract-only; el E2E real depende del Core/monorepo; el `ESTADO_ACTUAL` lo marca bloqueado.

---

## 6. Recomendaciones (Fase 6)

### 6.1 Acciones inmediatas (antes de HU-S1-04)

1. **Commitear `Docs/Obsidian/`**: sí, pero **solo el contenido markdown** (`Requisitos Funcionales.md`, `FT. Captura de Requisitos/`, `FT. Analisis/`). **Excluir `.obsidian/`** (workspace personal) y decidir el `.eap` (binario EA; si el equipo usa EA, commitearlo; si no, documentarlo como artefacto externo). Justificación: la base no puede quedar untracked.
2. **Reconciliar la numeración RF**: crear un **mapa único** docx↔Obsidian (audio docx RF-37…40 ↔ Obsidian RF-26…29; RF-41 docx sin equivalente Obsidian) y declarar el **docx v1.0 como fuente normativa** (o actualizar Obsidian para que coincida). El servicio seguirá usando la numeración del docx.
3. **Crear `Docs/ALCANCE_SINGING_SERVICE.md`** con el alcance real: EP-08 (RF-37…40/HU-43…47), el ritmo como **extensión** (HU-S1-01), las HUs operativas (ready/version/warm-up/metrics/release/httpx2), el límite Core (multimodal/persistencia/notificación), y el “Sprint 0 local = S0–S5 del plan micro; Sprint 1 local = post-MVP/calidad”.
4. **Actualizar `SPRINT1_BACKLOG`** para que refleje la ejecución: HU-S1-02/03 reales (`/ready`+`/version`, warm-up) y mover `pitch_contour`/CREPE a HUs nuevas o a “pendiente”; marcar HU-S1-06 (warm-up) como ejecutada; dejar explícitas las pendientes (HU-S1-04/05/07/08, HU-S2-XX, HU-S4-01).
5. **Marcar/actualizar los docs históricos**: `HANDOFF_CORE`, `MENSAJE_CORE`, `INDEX_DOCUMENTADOR`, `ESTADO_ACTUAL`, `Docs/integracion-core` como “v0.2.x (histórico)” o actualizarlos a 0.3.0-dev (ritmo, `tempo_bpm`, `scores.ritmo`, `rhythm_ms`, 111+2/98 %).

### 6.2 Acciones de sprint

- **HU-S1-04 (FastDTW) sigue siendo la prioridad**: el plan micro S4/HU-44 lo pedía; el código existe y está testeado; cablearlo en `mode=comparative`, tests con offset ~200 ms, y actualizar `Docs/scoring`/`ARCHITECTURE`. Impacto alto en la calidad de `comparative`.
- **HU-S2-XX (latencia rhythm)** debe adelantarse si el SLO <2 s es requisito de producto; MASTmelody 3,8 s en Docker; el downsample 8 kHz se descartó; evaluar downsample selectivo/cache/hop.
- **HU-S1-05 (timeout/metrics)** y **HU-S1-07 (0.3.0)** deberían cerrarse antes de declarar 0.3.0; **HU-S1-08 (httpx2)** es P2 (warning).
- **HU-S1-02 (pitch_contour)** y **HU-S1-03 (CREPE)** están en el backlog pero no ejecutadas; decidir si entran en el sprint o se posponen explícitamente.
- **HU-S4-01 (estabilidad)** sigue siendo deuda de calidad; no adelantarla antes de FastDTW (enmascara el problema real).

### 6.3 Acciones de documentación

- **Actualizar**: `HANDOFF_CORE` (ritmo número/null; 111+2; 0.3.0-dev; `tempo_bpm`/`scores.ritmo`/`rhythm_ms`), `MENSAJE_CORE`, `INDEX_DOCUMENTADOR`, `Docs/integracion-core` (ritmo, `tempo_bpm`, `scores.ritmo`, `rhythm_ms`, warm-up/startup), `ESTADO_ACTUAL` (o marcarlo obsoleto), `Docs/scoring` (FastDTW vs `align_by_time`; sección de ritmo ya existe), `Docs/plan` (API actual; estado S0–S5 ejecutado; “Sprint 0 local”; árbol de tests/`deps.py`).
- **Crear**: `Docs/ALCANCE_SINGING_SERVICE.md`; el **mapa RF** docx↔Obsidian↔HU; una nota de **roadmap** (“Sprint 0 local = S0–S5; Sprint 1 local = post-MVP/calidad”).
- **Commitear**: el markdown de `Docs/Obsidian/`; **no** `.obsidian/`; el `.eap` como artefacto opcional.
- **No crear HUs en código** en esta auditoría; las pendientes quedan sugeridas en §5.3/§6.2.

---

## Anexo — Archivos leídos (trazabilidad)

> **Leído completo** salvo indicación. Los binarios se indican.

| Archivo | Tamaño | Modo |
|---|---:|---|
| `Docs/SyncDance AI Requisitos y Alcance Propuesto.docx` | 125.076 B | Binario `.docx`; texto extraído (53.633 chars / 1.837 líneas) |
| `Docs/plan-implementacion-singing-service.md` | 34.643 B | Completo |
| `Docs/integracion-core.md` | 7.793 B | Completo |
| `Docs/scoring.md` | 5.281 B | Completo |
| `Docs/prompt-agente-figma-canto.md` | 21.850 B | No leído (prompt Figma; ajeno) |
| `Docs/prototipo.png` | 147.311 B | Imagen; no inspeccionada |
| `Docs/Obsidian/Requisitos Funcionales.md` | 5.362 B | Completo |
| `Docs/Obsidian/FT. Captura de Requisitos/FT Captura de Requisitos.md` | 19.663 B | Completo |
| `Docs/Obsidian/FT. Analisis/Identificar Paquetes.md` | 4.813 B | Completo |
| `Docs/Obsidian/PUDS_Proyecto_Final.eap` | ~1,9 MB | **NO LEGIBLE** (binario Enterprise Architect) |
| `Docs/Obsidian/.obsidian/*.json` | 5 archivos | Config/workspace; no leídos (no producto) |
| `Docs/Obsidian/FT. Captura de Requisitos/CU1…CU47/*.md` | 47 archivos | Estructura y nombres verificados; no se leyó cada detalle |
| `HANDOFF_CORE.md` | 58.642 B | Parcial (grep de ritmo/sprints/HUs) |
| `ESTADO_ACTUAL.md` | 35.345 B | Parcial (grep; marcado obsoleto por `INDEX`) |
| `INDEX_DOCUMENTADOR.md` | 5.062 B | Completo |
| `MENSAJE_CORE.md` | 2.843 B | Completo |
| `CIERRE_HU_S1_01.md` | 8.792 B | Completo |
| `CIERRE_HU_S1_02.md` | 4.453 B | No leído completo (referenciado) |
| `CIERRE_HU_S1_03.md` | 4.701 B | No leído completo (referenciado) |
| `CIERRE_ISSUES_HU_S1_01.md` | 6.338 B | Completo |
| `CIERRE_v0.2.3.md` | 3.661 B | No leído completo (referenciado) |
| `CIERRE_SPRINT0_FINAL.md` | 3.405 B | No leído completo (referenciado) |
| `CIERRE_GAPS_SPRINT0.md` | 19.196 B | Parcial (grep de gaps/O4/FastDTW) |
| `singing-service/docs/ARCHITECTURE.md` | 8.359 B | Completo |
| `singing-service/docs/celery-contract.md` | 17.694 B | Completo (partes) |
| `singing-service/docs/SPRINT1_BACKLOG.md` | 5.107 B | Completo |
| `singing-service/docs/USAGE.md` | 17.941 B | Completo (partes) |
| `singing-service/docs/SWAGGER_GUIDE.md` | 4.538 B | No leído (referenciado) |
| `singing-service/docs/TROUBLESHOOTING.md` | 3.573 B | No leído (referenciado) |
| `singing-service/CHANGELOG.md` | 6.825 B | Parcial (0.3.0-dev) |
| `singing-service/README.md` | 1.887 B | Completo |
| `singing-service/CONTRIBUTING.md` | 2.361 B | Completo |
| `singing-service/postman_collection.json` | 7.495 B | Existencia/tamaño; no validado |
| `singing-service/scripts/demo_e2e.py` | 6.971 B | Existencia/tamaño; no leído |
| `singing-service/app/**/*.py` | — | Inventario; lectura de `align.py`, `compare.py`, `main.py`, `analyze.py`, `rhythm_eval.py`, `scoring.py`, `feedback.py`, `schemas/analyze.py` |
| `singing-service/tests/test_*.py` | — | Inventario (16 archivos); lectura de `test_hu_s1_01.py`, `test_hu_s1_02.py`, `test_hu_s1_03.py`, `test_align.py` (grep) |
| `singing-service/integration/*` | — | Inventario; lectura de `verify_handoff.sh`, `test_error_scenarios.py` |
| `singing-service/requirements.txt` | 618 B | Completo |
| `singing-service/pyproject.toml` | 606 B | Completo |

**No legibles / no inspeccionados:** `PUDS_Proyecto_Final.eap` (binario EA), `prototipo.png` (imagen), `.docx` (binario; texto extraído), `.obsidian/*.json` (config personal), los 47 detalles de CU (solo estructura/nombres). **No se inventó contenido de estos.**

---

## Salida de comandos de verificación (real)

```
$ pytest -q
111 passed, 2 deselected

$ pytest -q -m integration
2 passed, 111 deselected

$ pytest --cov=app.core --cov=app.main --cov-report=term-missing
TOTAL 243 4 98%   (app/main.py 100%, app/core/store.py 93%)

$ ruff check .
All checks passed!

$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK

$ docker compose exec singing-service pytest -q
111 passed, 2 deselected
$ docker compose exec singing-service pytest -q -m integration
1 passed, 1 skipped

$ git rev-parse v0.2.3^{commit}
f744a8e18e7dac14bb0e6b7d5dbf36258efab7be
```

---

*Fin de la auditoría. No se modificó ningún archivo existente; el único archivo creado es este `AUDITORIA_ALINEACION.md`.*
