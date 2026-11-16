# Mensaje para Core — singing-service v0.2.3 listo para integrar

> ⚠️ **HISTÓRICO v0.2.x.** Snapshot de 2026-11-15 (v0.2.3). Para el estado actual, ver `Docs/ALCANCE_SINGING_SERVICE.md`, `singing-service/docs/celery-contract.md` y `CHANGELOG.md`.

📢 **`singing-service v0.2.3` — LISTO PARA INTEGRAR**

**Tag:** `v0.2.3` (commit `f744a8e`)
**Verificación:** `git rev-parse v0.2.3^{commit}` → `f744a8e18e7dac14bb0e6b7d5dbf36258efab7be`
**Base API:** idéntica a `v0.2.2`. Solo documentación.

**Cómo obtener:**
```bash
git checkout v0.2.3
cd singing-service
docker compose up -d
bash integration/verify_handoff.sh   # debe dar HANDOFF OK
```

Contrato (sin cambios):

`POST /api/v1/analyze` → **202** `{analysis_id, status, mode}`

Multipart requerido: `audio`, `attempt_id`, `routine_id`

Opcional: `mode` (default `absolute`), `reference_audio` (req. en comparative), `reference_notes`

`GET /api/v1/analyze/{analysis_id}` → **200** `AnalysisResult` (TTL 1h)

Formatos: wav, m4a, mp3, aac, ogg. Límites: 50 MB, 600 s.

Aclaraciones nuevas en v0.2.3 (no BREAKING):

**Cardinalidad de `feedback` (Nota C):** 1 ítem por tipo (`OUT_OF_TUNE`, `NO_VOICE`), **NO 1 por segmento**. En `OUT_OF_TUNE` se reporta la peor desviación. Detalle por segmento en `segments[]`. No es BREAKING.

**`scores.estabilidad` (deuda B):** fórmula `100 − 2·σ` cae a 0 con σ≥50 (vibrato natural). No es bug, es diseño documentado. Recalibración en Sprint 4 (`HU-S4-01`). Si ven estabilidad: 0 con cantantes razonables, es esperado. No abrir ticket.

Recordatorios críticos (vigentes desde v0.2.2):

**JIT frío:** primer request ~10s, siguientes <500ms. Timeout del worker ≥ 60s.

**V-01:** Content-Length inválido → 400 text/plain sin `X-Request-ID`. No reintentar.

**X-Request-ID:** propagar desde Flutter o generar UUID.

**UNHANDLED_ERROR (500):** reintentar con backoff.

BREAKING acumulados (desde v0.2.0):

`file`→`audio`, `mock|real`→`absolute|comparative`, `reference_file`→`reference_audio`, `INVALID_MODE` 400→422, `FILE_TOO_LARGE`→`AUDIO_TOO_LARGE`, `pitch.reference` nullable, `severity`/timestamps en `segments[]`, `X-Request-ID` header, `UNHANDLED_ERROR` code.

**Qué necesitamos de Core:**

1. Tarea Celery en `audio_queue`: POST → 202 → GET con `analysis_id`.
2. Propagar `X-Request-ID`.
3. Mapear `UNHANDLED_ERROR` y 5xx sin JSON a reintento con backoff.
4. `SINGING_SERVICE_URL=http://singing-service:5000/api/v1/analyze` en compose/K8s.
5. Timeout del worker ≥ 60s (JIT frío).

**Calidad:** 83 tests, 97% cobertura, ruff OK, Docker==local (Python 3.14.6, deps pinned), HANDOFF OK, 10/10 matriz errores, MASTmelody validado.

**Documentación:**

`docs/celery-contract.md` (contrato + tarea Celery copiable)

`docs/USAGE.md` (manual completo)

`docs/SWAGGER_GUIDE.md`

`integration/` (simulador, fixtures, verify_handoff)

**Sesión de integración:** propongo 30 min esta semana. Corremos `verify_handoff.sh` contra su worker y validamos el primer E2E. ¿Cuándo les viene bien?
