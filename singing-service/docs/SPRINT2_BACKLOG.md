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

### HU-S2-XX — Optimizar `rhythm_eval` (latencia) — ✅ Ejecutada (v0.4.0-dev)

- **Descripción:** reducir la latencia de `beat_track` + `onset_detect` con
  medición previa (cache por hash, hop 1024 y downsample selectivo).
- **Resultado medido (Docker):** MASTmelody 4.78 s → ~8–19 ms; 60 s de pulsos
  120 BPM → ~45–69 ms estable; primer request ~4.0 s por JIT de onsets **antes**
  del warm-up de pulsos y ~0.26 s después. El SLO <2 s ya se cumplía en régimen
  estable; no había margen para una mejora 3x real de cómputo.
- **Decisión:** se implementó **A (cache por hash de audio)**: segunda llamada
  ~0 ms, precisión exacta. **D (hallazgo):** el warm-up de sine no compilaba la
  ruta de onsets; se cambió a un tren de pulsos 120 BPM y el primer request bajó
  de ~4.0 s a ~0.26 s. **B (hop 1024)** y **C (11–12 kHz)** se rechazaron por
  desviar `estimated_tempo_bpm` >2 BPM. B+C también falló (tempo y onsets).
- **Tests:** `tests/test_hu_s2_xx.py` (8).
- **Esfuerzo:** M.

### HU-S4-01 — Recalibrar `scores.estabilidad` (pendiente, Sprint 4)

- **Descripción:** la fórmula `100 − 2·σ` cae a 0 con σ ≥ 50 (vibrato natural).
  Recalibrar con datos reales.
- **Esfuerzo:** M.

## Pendientes reales

HU-S1-07, HU-S1-08, HU-S1-10 y HU-S4-01.
