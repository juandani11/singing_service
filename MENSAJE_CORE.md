# Mensaje para Core — singing-service v0.3.0 listo para integrar

📢 **`singing-service v0.3.0` — LISTO PARA INTEGRAR (Sprint 1 completo)**

**Tag:** `v0.3.0` (commit `0016e2e`)
**Verificación:** `git rev-parse v0.3.0^{commit}` → `0016e2e65266ea6086e8c50253932497668e5e8d`
**API:** contrato **sin cambios BREAKING** respecto a `v0.2.3`. Todo lo nuevo es aditivo.

**Cómo obtener:**
```bash
git checkout v0.3.0
cd singing-service
docker compose up -d
bash integration/verify_handoff.sh   # debe dar HANDOFF OK
```

## Contrato (sin cambios)

`POST /api/v1/analyze` → **202** `{analysis_id, status, mode}`

Multipart requerido: `audio`, `attempt_id`, `routine_id`

Opcional: `mode` (default `absolute`), `reference_audio` (req. en comparative), `reference_notes`, `tempo_bpm` (BPM esperado de la rutina; si se envía se calcula `metrics.tempo_deviation_bpm`).

`GET /api/v1/analyze/{analysis_id}` → **200** `AnalysisResult` (TTL 1h)

Formatos: wav, m4a, mp3, aac, ogg. Límites: 50 MB, 600 s.

Salud/sistema: `GET /health`, `GET /ready`, `GET /version`.

## Aditivos nuevos en v0.3.0 (no BREAKING)

**Ritmo real:** `rhythm_accuracy` deja de ser siempre `null` (número si hay onsets). Nuevos: `scores.ritmo`, `metrics.estimated_tempo_bpm`, `metrics.onset_count`, `metrics.onset_stability`, `metrics.tempo_deviation_bpm`, `timings.rhythm_ms`.

**Alineación (comparative):** FastDTW cableado con fallback a alineación por tiempo. Nuevos: `metrics.alignment_method` (`"fastdtw"` | `"time"`) y `timings.align_ms` (`dtw_ms` se mantiene como alias). Mejora medida en MASTmelody: `pitch_accuracy` 20.7 → 44.4, `average_cent_deviation` 153.9 → 92.9; offset de 200 ms alineado.

**Observabilidad:** `GET /ready` (readiness: `warmup`, `shutting_down`, `ffmpeg_unavailable`), `GET /version` (version, git_sha, build_time, python, ffmpeg, fastapi, librosa), `/health` con `checks.warmup` y `checks.rhythm_warmup`.

**Warm-up:** `librosa.pyin` y `beat_track`/`onset_detect` se precalientan en el lifespan. Primer request ~10.2 s → **~345 ms**. Se puede omitir con `SKIP_WARMUP` / `SKIP_WARMUP_BEAT`.

## Recordatorios críticos (vigentes)

**JIT frío:** aunque hay warm-up, mantengan timeout del worker ≥ 60 s (arranque y contenedor frío).

**Latencia de ritmo:** `rhythm_eval` añade ~3.8 s en Docker (hop 960 = 60 ms). Documentado; optimización en HU-S2-XX.

**V-01:** Content-Length inválido → 400 text/plain sin `X-Request-ID`. No reintentar.

**X-Request-ID:** propagar desde Flutter o generar UUID.

**UNHANDLED_ERROR (500):** reintentar con backoff.

**`feedback` (Nota C):** 1 ítem por tipo (`OUT_OF_TUNE`, `NO_VOICE`), no 1 por segmento. El detalle por segmento está en `segments[]`.

**`scores.estabilidad` (deuda B):** fórmula `100 − 2·σ` cae a 0 con σ≥50 (vibrato natural). Es diseño documentado; recalibración en Sprint 4 (`HU-S4-01`). No abrir ticket.

## BREAKING acumulados (desde v0.2.0; sin cambios en v0.3.0)

`file`→`audio`, `mock|real`→`absolute|comparative`, `reference_file`→`reference_audio`, `INVALID_MODE` 400→422, `FILE_TOO_LARGE`→`AUDIO_TOO_LARGE`, `pitch.reference` nullable, `severity`/timestamps en `segments[]`, `X-Request-ID` header, `UNHANDLED_ERROR` code.

## Qué necesitamos de Core

1. Tarea Celery en `audio_queue`: POST → 202 → GET con `analysis_id`.
2. Propagar `X-Request-ID`.
3. Mapear `UNHANDLED_ERROR` y 5xx sin JSON a reintento con backoff.
4. `SINGING_SERVICE_URL=http://singing-service:5000` en compose/K8s.
5. Timeout del worker ≥ 60 s (arranque en frío).
6. **Nuevo:** usar `GET /ready` como readiness probe (no `/health`) y `GET /version` para trazabilidad del deploy.
7. **Opcional:** enviar `tempo_bpm` de la rutina para obtener `tempo_deviation_bpm`.

## Calidad

**115 tests por defecto + 3 de integración (118)**, **98 % cobertura**, `ruff` OK, `HANDOFF OK` (4/4), Docker 115 + 1 passed + 2 skipped (fixtures MASTmelody), snapshot OpenAPI `0.3.0` verificado.

## Documentación

- `singing-service/docs/celery-contract.md` — contrato + tarea Celery copiable (actualizado a v0.3.0).
- `singing-service/docs/USAGE.md` — manual completo.
- `Docs/ALCANCE_SINGING_SERVICE.md` — alcance, mapeo sprints/RF/HUs y límites Core/Frontend.
- `singing-service/CHANGELOG.md` — `## [0.3.0] — 2026-11-16`.
- `CIERRE_v0.3.0.md` — release y tabla de Sprint 1.
- `integration/` — simulador, fixtures y `verify_handoff.sh`.

**Sesión de integración:** propongo 30 min esta semana. Corremos `verify_handoff.sh` contra su worker y validamos el primer E2E con `mode=comparative` (FastDTW). ¿Cuándo les viene bien?
