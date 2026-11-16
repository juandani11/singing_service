# Paquete de documentación — singing-service v0.2.3

> ⚠️ **HISTÓRICO v0.2.x.** Snapshot de 2026-11-15 (v0.2.3). Para el estado actual, ver `Docs/ALCANCE_SINGING_SERVICE.md`, `singing-service/docs/celery-contract.md` y `CHANGELOG.md`.

**Para:** Documentador del proyecto
**De:** Equipo singing-service
**Fecha:** 2026-11-15
**Versión:** v0.2.3 (misma API que v0.2.2 + notas aclaratorias)
**Tag git:** v0.2.3 (commit f744a8e)

---

## 1. Documentos de producto (integrar en el documento maestro)

| # | Archivo | Propósito | Sección sugerida |
|---|---------|-----------|------------------|
| 1 | `singing-service/docs/ARCHITECTURE.md` | Qué es el servicio, stack, decisiones de diseño | Arquitectura del sistema |
| 2 | `singing-service/docs/USAGE.md` | Manual de consumo (curl, Python, Swagger) | Manual de API |
| 3 | `singing-service/docs/SWAGGER_GUIDE.md` | Cómo probar con Swagger UI | Guía de validación |
| 4 | `singing-service/docs/celery-contract.md` | Contrato con Core API + BREAKING changes | Integración de servicios |
| 5 | `singing-service/docs/SPRINT1_BACKLOG.md` | Deuda técnica y próximos pasos | Trabajo futuro |
| 6 | `singing-service/CHANGELOG.md` | Historial de versiones (v0.1.0 → v0.2.3) | Evolución del servicio |
| 7 | `CIERRE_v0.2.3.md` | Acta de cierre del Sprint 0 | Hitos y entregables |
| 8 | `CIERRE_BUGS_B_C.md` | Evidencia de auditoría de bugs B y C | Calidad y rigor |
| 9 | `AUDITORIA_BUGS_B_C.md` | Evidencia empírica (tabla de vibrato, MASTmelody) | Validación empírica |

---

## 2. Documentos internos (NO integrar, se quedan en el repo)

Artefactos de proceso que no aportan al documento de producto:
- `ESTADO_ACTUAL.md` (snapshot obsoleto)
- `CIERRE_FORMAL_v0.2.2.md`, `CIERRE_FINAL_v0.2.2.md` (duplicados)
- `CONSISTENCY_FIX.md`, `DOCS_CONTINUATION.md`, `FIX_P0-01.md` (diffs internos)
- `singing-service/integration/` (código, no documentación)

---

## 3. Mensajes clave para el documento maestro

### 3.1 Qué es el servicio
Microservicio **stateless** de análisis de canto. Recibe audio (modo `absolute`) o audio + referencia (modo `comparative`), devuelve pitch, métricas, segmentos y feedback. Sin autenticación (red interna Docker). No persiste datos.

### 3.2 Contrato con Core (API)
- `POST /api/v1/analyze` → **202** `{analysis_id, status, mode}`
- Campos requeridos: `audio`, `attempt_id`, `routine_id`
- Opcionales: `mode` (default `absolute`), `reference_audio` (requerido en comparative), `reference_notes`
- `GET /api/v1/analyze/{analysis_id}` → **200** `AnalysisResult` (TTL 1h)
- Formatos: wav, m4a, mp3, aac, ogg. Límites: 50 MB, 600 s.

### 3.3 Stack tecnológico
FastAPI 0.115 + Uvicorn + librosa 1.0 + numba + scipy + ffmpeg. Python 3.14.6. Docker multi-stage, usuario no-root. Dependencias pinned.

### 3.4 Calidad verificada
- **83 tests**, **97% cobertura**, ruff OK.
- `verify_handoff.sh` → HANDOFF OK (4/4 checks).
- Matriz de errores 10/10 (incluye V-01: Content-Length inválido).
- Probado empíricamente con MASTmelody (voz real vs piano).

### 3.5 Limitaciones conocidas (documentadas, no ocultas)
| Limitación | Estado | Mitigación |
|-----------|--------|-----------|
| JIT frío: primer request ~10s | Conocido | Timeout worker ≥ 60s; warm-up en Sprint 1 (HU-S1-03) |
| `scores.estabilidad` agresivo (σ≥50 → 0) | Deuda técnica | HU-S4-01 (Sprint 4, con datos reales) |
| Ritmo (`rhythm_accuracy`) | Diferido | Sprint 1 (HU-S1-01) |
| Alineamiento temporal simple (no FastDTW) | Diferido | Sprint 1 |
| `/ready` y `/version` | Pendiente | Sprint 1 (HU-S1-02) |

### 3.6 Decisiones de diseño (para defender)
- **B no es bug:** `scores.estabilidad` = `100 − 2·σ` documentado en `Docs/scoring.md` línea 47. Recalibrar antes de FastDTW enmascararía el problema real (`pitch_accuracy=20.7` por falta de alineamiento).
- **C no es bug:** `feedback` = 1 ítem por tipo, no por segmento. Documentado en `Docs/scoring.md` §Feedback. Cambiarlo sería BREAKING.
- **V-01:** Uvicorn rechaza Content-Length inválido antes del middleware. 400 text/plain sin `X-Request-ID`. No reintentar.

### 3.7 BREAKING changes acumulados
1. `file` → `audio`
2. `mode=mock|real` → `mode=absolute|comparative`
3. `reference_file` → `reference_audio`
4. `INVALID_MODE` 400 → 422
5. `FILE_TOO_LARGE`/`DURATION_TOO_LONG` → `AUDIO_TOO_LARGE`/`AUDIO_TOO_LONG`
6. `pitch.reference` nullable en absolute
7. `severity`/timestamps en `segments[]` (no en `feedback[]`)
8. `X-Request-ID` header nuevo
9. `UNHANDLED_ERROR` (500) nuevo

---

## 4. Qué se pide al documentador

1. Integrar los 9 documentos en las secciones sugeridas del documento maestro.
2. Usar los "mensajes clave" para la presentación y la defensa.
3. No integrar los documentos internos (sección 2).
4. Si algo no cuadra o falta contexto, pedir capturas o aclaraciones.
5. Si el docente pregunta por limitaciones, la sección 3.5 es la respuesta honesta: están documentadas y priorizadas.

---

## 5. Trazabilidad

- Repo: `<ruta o URL>`
- Tag: `v0.2.3` (commit `f744a8e`)
- Verificación: `git rev-parse v0.2.3^{commit}` → `f744a8e18e7dac14bb0e6b7d5dbf36258efab7be`
- Evidencia de auditoría: `AUDITORIA_BUGS_B_C.md`, `CIERRE_BUGS_B_C.md` (commits posteriores al tag)
