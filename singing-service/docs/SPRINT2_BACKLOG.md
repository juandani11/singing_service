# Backlog Sprint 2 — singing-service

> Rama `sprint2` (desde `sprint1`/`v0.3.0`, tag intacto en `0016e2e`).
> Alcance: **solo `singing-service`**. No incluye Core ni frontend.

## Objetivo del sprint

Hardening de producción: protegerse de análisis colgados, exponer observabilidad
Prometheus y cerrar deuda de calidad antes del tag `v0.4.0`.

## Historias

### HU-S1-05 — Timeout interno + `/metrics` Prometheus — ✅ Ejecutada (v0.4.0-dev)

- **Descripción:** timeout configurable para `librosa.pyin` y `align_frames`
  (FastDTW) y endpoint `/metrics` con contadores/histogramas.
- **Criterios:**
  - `PYIN_TIMEOUT_SECONDS` (default 120 s, `0 < x < 300`) y
    `ALIGN_TIMEOUT_SECONDS` (default 30 s, `0 < x < 120`).
  - Al vencer: **504 `ANALYSIS_TIMEOUT`** con `request_id`; semáforo liberado.
  - `/metrics` con `analysis_requests_total`, `analysis_duration_seconds`,
    `pitch_duration_seconds`, `align_duration_seconds`, `rhythm_duration_seconds`,
    `active_requests` y `analysis_timeouts_total`.
  - Tests de timeout, happy path y métricas (`tests/test_hu_s1_05.py`).
- **Limitación documentada:** librosa/FastDTW no son interrumpibles; el hilo
  huérfano sigue hasta terminar (el executor acota cuántos se acumulan).
- **Esfuerzo:** S

### HU-S1-07 — Empaquetar versión 0.4.0 (pendiente)

- **Descripción:** tag `v0.4.0`, `CHANGELOG` formal, snapshot OpenAPI y
  `MENSAJE_CORE.md` actualizado.
- **Criterios:** CHANGELOG sin `-dev`; `verify_handoff.sh` OK; tag annotated.
- **Esfuerzo:** S

### HU-S1-08 — Migrar TestClient a httpx2 (pendiente)

- **Descripción:** eliminar `StarletteDeprecationWarning` migrando a `httpx2`
  cuando la versión estable lo requiera.
- **Criterio:** 0 warnings en `pytest -v`.
- **Esfuerzo:** S. **Prioridad:** P2.

### HU-S1-09 — `pitch_contour` + downsample — ✅ Ejecutada (v0.4.0-dev)

- **Descripción:** exponer `pitch_contour` cuando `include_contour=true`
  (downsample a ~10 Hz, máx. 6000 puntos, JSON < 1 MB).
- **Ejecución:** `app/services/contour.py` + campo aditivo en `AnalysisResult`;
  `step=3` con hop 32 ms (96 ms ≈ 10.42 Hz); recorte equiespaciado a 6000 puntos;
  `note`/`f0` null sin voz. Tests `tests/test_hu_s1_09.py` (7).
- **Esfuerzo:** S.

### HU-S1-10 — Evaluación CREPE vs `librosa.pyin` (pendiente)

- **Descripción:** benchmark en 3 audios y decisión pyin vs CREPE.
- **Esfuerzo:** M.

### HU-S2-XX — Optimizar `rhythm_eval` (latencia) (pendiente)

- **Descripción:** reducir los ~3.8 s de `beat_track` + `onset_detect` en Docker
  (downsample selectivo, cache por hash o `n_fft` menor con validación).
- **Criterios:** MASTmelody < 2 s; audio 60 s < 20 s; tempo ±2 BPM.
- **Esfuerzo:** M.

### HU-S4-01 — Recalibrar `scores.estabilidad` (pendiente, Sprint 4)

- **Descripción:** la fórmula `100 − 2·σ` cae a 0 con σ ≥ 50 (vibrato natural).
  Recalibrar con datos reales.
- **Esfuerzo:** M.

## Pendientes reales

HU-S1-07, HU-S1-08, HU-S1-10, HU-S2-XX y HU-S4-01.
