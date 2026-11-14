# Backlog Sprint 1 — singing-service

> Alcance: **solo `singing-service`**. No incluye tareas del Core ni del frontend.
> Base: v0.2.0 (Sprint 0 cerrado, handoff firmado).

## Objetivo del sprint

Pasar de análisis de pitch básico a análisis de canto completo (pitch + ritmo) con
métricas comparativas más ricas, preparado para integrar con el Core en producción.

## Historias

### HU-S1-01 — Implementar `rhythm_eval` real

- **Descripción:** reemplazar el stub por análisis de tempo y onsets.
- **Criterios de aceptación:**
  - `librosa.beat.beat_track` para `estimated_tempo_bpm`.
  - `onset_stability` (desviación estándar de intervalos entre onsets).
  - `tempo_deviation_bpm` vs `tempo_bpm` si se envía.
  - Feedback "tempo rápido/lento" con timestamp del primer onset desviado.
  - `rhythm_accuracy` deja de ser `null` en comparative.
- **Fuera de alcance:** alineamiento por beats vs referencia (Sprint 2).
- **Esfuerzo:** M

### HU-S1-02 — `pitch_contour` con downsample

- **Descripción:** exponer `pitch_contour` cuando `include_contour=true`.
- **Criterios:** downsample a 10 Hz, máx. 6000 puntos, JSON < 1 MB. Test con audio de
  10 min.
- **Esfuerzo:** S

### HU-S1-03 — Evaluación CREPE vs `librosa.pyin`

- **Descripción:** benchmark en 3 audios (voz masculina, femenina, infantil).
  Documentar precisión y latencia.
- **Criterios:** informe en `docs/PITCH_EVALUATION.md` con tabla. Decisión de mantener
  pyin o migrar a CREPE.
- **Esfuerzo:** M

### HU-S1-04 — Alineamiento temporal robusto en comparative

- **Descripción:** v0.2.0 ya compara por tiempo (`compare.align_by_time`,
  nearest-neighbor). Sprint 1 mejora la tolerancia para offsets de ~200 ms
  (interpolación/remuestreo de la referencia), **sin FastDTW todavía**.
- **Criterios:** `average_cent_deviation` baja en audios con offset de 200 ms;
  tests con referencia desplazada.
- **Esfuerzo:** M

### HU-S1-05 — Timeout interno y métricas Prometheus

- **Descripción:** el servicio no hace llamadas salientes al Core (es el Core quien
  llama al servicio). Protegerse de peticiones colgadas con timeout interno de
  pyin/FFmpeg y exponer latencia en `/metrics`.
- **Criterios:** timeout configurable para pyin/comparación; `/metrics` con
  contadores de análisis y latencias (Prometheus); test de timeout.
- **Esfuerzo:** S

### HU-S1-06 — Warm-up de librosa/numba

- **Descripción:** mitigar el JIT frío del primer request (~25 s observados en el
  primer análisis tras arrancar el contenedor).
- **Criterios:** `/health` con `warmup: true`; script de warm-up en el Dockerfile
  (procesar 1 s de silencio al arrancar); el primer request real baja de 10 s.
- **Esfuerzo:** S

### HU-S1-07 — Empaquetar versión 0.3.0

- **Descripción:** tag `v0.3.0`, actualizar `CHANGELOG.md`, notificar a Core.
- **Criterios:** CHANGELOG con sección 0.3.0; snapshot OpenAPI regenerado; handoff
  actualizado si cambia el contrato.
- **Esfuerzo:** S

## Fuera de alcance (Sprint 2+)

- FastDTW / alineamiento avanzado.
- GPU / CREPE en producción.
- `mode=absolute` con referencia opcional.
- Métricas de expresión / vibrato.
