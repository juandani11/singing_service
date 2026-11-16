# Backlog Sprint 1 — singing-service

> Alcance: **solo `singing-service`**. No incluye tareas del Core ni del frontend.
> Base: v0.2.0 (Sprint 0 cerrado, handoff firmado).

## Objetivo del sprint

Pasar de análisis de pitch básico a análisis de canto completo (pitch + ritmo) con
métricas comparativas más ricas, preparado para integrar con el Core en producción.

## Historias

### HU-S1-01 — Implementar `rhythm_eval` real — ✅ Ejecutada (88273a8)

- **Descripción:** reemplazar el stub por análisis de tempo y onsets.
- **Criterios de aceptación:**
  - `librosa.beat.beat_track` para `estimated_tempo_bpm`.
  - `onset_stability` (desviación estándar de intervalos entre onsets).
  - `tempo_deviation_bpm` vs `tempo_bpm` si se envía.
  - Feedback "tempo rápido/lento" con timestamp del primer onset desviado.
  - `rhythm_accuracy` deja de ser `null` en comparative.
- **Fuera de alcance:** alineamiento por beats vs referencia (Sprint 2).
- **Esfuerzo:** M

### HU-S1-02 — `/ready` + `/version` — ✅ Ejecutada (9ac255b)

- **Descripción:** readiness (`/ready`) y metadatos de build (`/version`).
- **Criterios:** `/ready` 200/503; `/version` con `version`, `git_sha`, `build_time`;
  tests.
- **Esfuerzo:** S

### HU-S1-09 — `pitch_contour` + downsample (pendiente)

- **Descripción:** exponer `pitch_contour` cuando `include_contour=true`.
- **Criterios:** downsample a 10 Hz, máx. 6000 puntos, JSON < 1 MB. Test con audio de
  10 min.
- **Esfuerzo:** S

### HU-S1-03 — Warm-up de librosa/numba — ✅ Ejecutada (70ab517)

- **Descripción:** warm-up de pyin en lifespan (sine 440 Hz) + `SKIP_WARMUP`;
  `/health` con `warmup`.
- **Criterios:** primer request <2 s; tests; warm-up extendido `beat_track`
  (HU-S1-01).
- **Esfuerzo:** S

### HU-S1-10 — Evaluación CREPE vs `librosa.pyin` (pendiente)

- **Descripción:** benchmark en 3 audios (voz masculina, femenina, infantil).
  Documentar precisión y latencia.
- **Criterios:** informe en `docs/PITCH_EVALUATION.md` con tabla. Decisión de mantener
  pyin o migrar a CREPE.
- **Esfuerzo:** M

### HU-S1-04 — Alineamiento temporal robusto en comparative — ✅ Ejecutada (ed29ac1)

- **Descripción:** `align_frames` (FastDTW) cableado en `mode=comparative`;
  fallback `align_by_time` si FastDTW falla; `metrics.alignment_method` y
  `timings.align_ms` (aditivos; `dtw_ms` alias).
- **Criterios:** MASTmelody `pitch_accuracy` 20.7→44.4 y
  `average_cent_deviation` 153.9→92.9; offset 200 ms alineado (>80); tests.
- **Esfuerzo:** M

### HU-S1-05 — Timeout interno y métricas Prometheus

- **Descripción:** el servicio no hace llamadas salientes al Core (es el Core quien
  llama al servicio). Protegerse de peticiones colgadas con timeout interno de
  pyin/FFmpeg y exponer latencia en `/metrics`.
- **Criterios:** timeout configurable para pyin/comparación; `/metrics` con
  contadores de análisis y latencias (Prometheus); test de timeout.
- **Esfuerzo:** S

### HU-S1-06 — Warm-up (duplicada de HU-S1-03) — ✅ Ejecutada

- **Descripción:** warm-up de librosa/numba; ejecutada como HU-S1-03 (70ab517).
- **Criterios:** `/health` con `warmup`; primer request <2 s.
- **Esfuerzo:** S

### HU-S1-07 — Empaquetar versión 0.3.0

- **Descripción:** tag `v0.3.0`, actualizar `CHANGELOG.md`, notificar a Core.
- **Criterios:** CHANGELOG con sección 0.3.0; snapshot OpenAPI regenerado; handoff
  actualizado si cambia el contrato.
- **Esfuerzo:** S

### HU-S1-08 — Migrar TestClient a httpx2

- **Descripción:** FastAPI/Starlette deprecó `httpx` en `TestClient`. Migrar a
  `httpx2` cuando la versión estable lo requiera.
- **Criterio:** 0 warnings de `StarletteDeprecationWarning` en `pytest -v`.
- **Esfuerzo:** S
- **Prioridad:** P2 (mantenimiento, no bloquea)

### HU-S2-XX — Optimizar `rhythm_eval` (latencia)

- **Contexto:** `beat_track` + `onset_detect` añaden ~3.8 s para 4.8 s de audio
  (~0.79x real-time). Para 5 min → ~4 min. Rompe el SLO <2 s para audios largos.
- **Causa:** análisis espectral sobre 16 kHz, hop 960. Downsample 8 kHz rompía
  ruido/tempo (descartado en HU-S1-01).
- **Opciones a evaluar:** (a) downsample selectivo solo para rhythm (mantener
  16 kHz para pitch); (b) cache por hash de audio; (c) reducir `hop_length` o
  `n_fft` con validación de precisión.
- **Criterios de aceptación:** MASTmelody (4.8 s) <2 s; audio 60 s <20 s;
  precisión de tempo mantenida (±2 BPM vs baseline).
- **Esfuerzo:** M.
- **Sprint objetivo:** 2.

## Pendientes reales (Sprint 2)

- HU-S1-05 (timeout/metrics), HU-S1-07 (tag 0.3.0), HU-S1-08 (httpx2),
  HU-S1-09 (`pitch_contour`), HU-S1-10 (CREPE), HU-S2-XX (latencia ritmo),
  HU-S4-01 (estabilidad).

## Deuda técnica (Sprint 4)

### HU-S4-01 — Recalibrar `scores.estabilidad` con datos reales

- **Contexto:** la fórmula actual `100 − 2·σ(cents)` (mín. 0, `Docs/scoring.md`
  línea 47) cae a 0 con `σ ≥ 50`, lo que ocurre con cualquier cantante con vibrato
  natural. Evidencia: `AUDITORIA_BUGS_B_C.md` A3 + MASTmelody (229.2 → 0).
- **No es bug:** documentado en `Docs/scoring.md`.
- **Riesgo de no hacerlo:** UX pobre; el alumno ve "0" en casos no catastróficos.
- **Riesgo de hacerlo antes de Sprint 1:** enmascara el problema real
  (`pitch_accuracy` bajo por falta de FastDTW).
- **Criterios de aceptación:** medir σ de 10+ cantantes reales
  (amateur/intermedio/avanzado), definir curva con justificación, tests con casos
  reales, actualizar `Docs/scoring.md`.
- **Dependencias:** FastDTW implementado + datos reales de usuarios.
- **Sprint objetivo:** 4 (cuando hay usuarios reales).
- **Esfuerzo:** M.

## Fuera de alcance (Sprint 2+)

- Alineamiento por beats vs referencia (FastDTW ya cableado en HU-S1-04).
- GPU / CREPE en producción.
- `mode=absolute` con referencia opcional.
- Métricas de expresión / vibrato.
