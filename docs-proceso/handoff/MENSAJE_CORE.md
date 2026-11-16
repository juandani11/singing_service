# Mensaje para Core — singing-service v0.4.0 listo para integrar

📢 **`singing-service v0.4.0` — LISTO PARA INTEGRAR (Sprint 2 completo, production-ready)**

**Tag:** `v0.4.0` (commit `ddfe6ef`)
**Verificación:** `git rev-parse v0.4.0^{commit}` → `ddfe6ef8d0285823d7ff60704eb7a17a993bcc57`
**API:** contrato **sin cambios BREAKING** respecto a `v0.3.0`. Todo lo nuevo es aditivo.

**Cómo obtener:**
```bash
git checkout v0.4.0
cd singing-service
docker compose up -d
bash integration/verify_handoff.sh   # debe dar HANDOFF OK
```

## Contrato (sin cambios)

`POST /api/v1/analyze` → **202** `{analysis_id, status, mode}`

Multipart requerido: `audio`, `attempt_id`, `routine_id`

Opcional: `mode` (default `absolute`), `reference_audio` (req. en comparative), `reference_notes`, `tempo_bpm`, `include_contour` (default `false`).

`GET /api/v1/analyze/{analysis_id}` → **200** `AnalysisResult` (TTL 1h)

Formatos: wav, m4a, mp3, aac, ogg. Límites: 50 MB, 600 s.

Salud/sistema: `GET /health`, `GET /ready`, `GET /version`, `GET /metrics`.

## Aditivos nuevos en v0.4.0 (no BREAKING)

**Timeout interno (HU-S1-05):** `PYIN_TIMEOUT_SECONDS` (default 120 s) y `ALIGN_TIMEOUT_SECONDS` (default 30 s). Al vencer, `POST /analyze` responde **504 `ANALYSIS_TIMEOUT`** con `request_id`. Limitación: librosa/FastDTW no son interrumpibles; el hilo huérfano termina por su cuenta (el executor lo acota).

**Métricas Prometheus (HU-S1-05):** `GET /metrics` (sin auth; red interna) con `analysis_requests_total{mode,status}`, `analysis_duration_seconds{mode}`, `pitch_duration_seconds`, `align_duration_seconds{method}`, `rhythm_duration_seconds`, `active_requests` y `analysis_timeouts_total{phase}`.

**`pitch_contour` (HU-S1-09):** con `include_contour=true`, el `AnalysisResult` añade `pitch_contour` con `student` y `reference` (comparative), downsampleados a ~10 Hz (`t`, `f0`, `note`, `voiced`), máximo 6000 puntos por curva. JSON <1 MB para 10 min. Sin el flag, `pitch_contour: null`.

**Cache de ritmo (HU-S2-XX):** cache en memoria por `sha256(audio)` + `sr` + `tempo_bpm` (TTL 1 h, 128 entradas). La segunda llamada con el mismo audio/hint tiene `timings.rhythm_ms ≈ 0`. No persiste entre reinicios.

**Warm-up de ritmo (HU-S2-XX):** el lifespan precalienta `beat_track`/`onset_detect` con un tren de pulsos 120 BPM (no un sine). El primer request con onsets baja de ~4.0 s a ~0.26 s.

**Latencia corregida (HU-S2-XX):** el “3.8 s” de versiones anteriores era **JIT frío del primer request**, no el coste por audio. En régimen estable (Docker): MASTmelody 4.78 s → **8–19 ms**; 60 s → **45–80 ms**; 5 min → **250–400 ms**. SLO <2 s cumplido.

## Recordatorios críticos (vigentes)

**Timeout del worker:** ≥ **300 s** (`read=300 s`), por audios largos y arranque en frío.

**Reintentos:** `504 ANALYSIS_TIMEOUT` y `500 UNHANDLED_ERROR` → reintentar con **backoff exponencial** (máx. 3); si persiste, marcar el intento como fallido y alertar.

**`/metrics`:** scrape cada **15 s** desde Prometheus (red interna). Útil para latencia, timeouts y saturación.

**V-01:** Content-Length inválido → 400 text/plain sin `X-Request-ID`. No reintentar.

**X-Request-ID:** propagar desde Flutter o generar UUID.

**`feedback` (Nota C):** 1 ítem por tipo (`OUT_OF_TUNE`, `NO_VOICE`), no 1 por segmento. El detalle por segmento está en `segments[]`.

**`scores.estabilidad` (deuda B):** fórmula `100 − 2·σ` cae a 0 con σ≥50 (vibrato natural). Es diseño documentado; recalibración en Sprint 4 (`HU-S4-01`). No abrir ticket.

## BREAKING acumulados (desde v0.2.0; sin cambios en v0.4.0)

`file`→`audio`, `mock|real`→`absolute|comparative`, `reference_file`→`reference_audio`, `INVALID_MODE` 400→422, `FILE_TOO_LARGE`→`AUDIO_TOO_LARGE`, `pitch.reference` nullable, `severity`/timestamps en `segments[]`, `X-Request-ID` header, `UNHANDLED_ERROR` code.

## Qué necesitamos de Core

1. Tarea Celery en `audio_queue`: POST → 202 → GET con `analysis_id`.
2. Propagar `X-Request-ID`.
3. Mapear `UNHANDLED_ERROR` (500) y `ANALYSIS_TIMEOUT` (504) a reintento con backoff.
4. `SINGING_SERVICE_URL=http://singing-service:5000` en compose/K8s.
5. Timeout del worker ≥ **300 s**.
6. Usar `GET /ready` como readiness probe y `GET /version` para trazabilidad del deploy.
7. Scrape de `GET /metrics` cada **15 s**.
8. **Opcional:** enviar `tempo_bpm` de la rutina y `include_contour=true` si el frontend dibuja la curva.

## Calidad

**138 tests por defecto + 3 de integración (141)**, **98 % cobertura**, `ruff` OK, `HANDOFF OK` (4/4), Docker 138 + 1 passed + 2 skipped (fixtures MASTmelody), snapshot OpenAPI `0.4.0` verificado.

## Documentación

- `singing-service/docs/celery-contract.md` — contrato + tarea Celery copiable (actualizado a v0.4.0).
- `singing-service/docs/USAGE.md` — manual completo (incluye `/metrics` e `include_contour`).
- `Docs/ALCANCE_SINGING_SERVICE.md` — alcance, mapeo sprints/RF/HUs y límites Core/Frontend (Sprint 2).
- `singing-service/CHANGELOG.md` — `## [0.4.0] — 2026-11-16`.
- `CIERRE_v0.4.0.md` — release y tabla de Sprint 2.
- `integration/` — simulador, fixtures y `verify_handoff.sh`.

**Sesión de integración:** propongo 30 min esta semana. Corremos `verify_handoff.sh` contra su worker y validamos el primer E2E con `mode=comparative` (FastDTW) + `include_contour=true`. ¿Cuándo les viene bien?
