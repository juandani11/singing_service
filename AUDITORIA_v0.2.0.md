# AUDITORIA v0.2.0 — singing-service

> Auditoría empírica (servicio ejecutándose) + manual de consumo.
> Fecha: 2026-11-14. Imagen reconstruida con `--no-cache`; 71 tests; 93 % cobertura.
> No se modificó lógica de negocio: sólo metadata OpenAPI y documentación.

## 1. Resumen ejecutivo

| Métrica | Resultado |
|---|---|
| RFs cumplidos | **11/12** (RF-40 diferido a Sprint 1; X-Request-ID ausente) |
| Bugs P0 (bloqueantes) | **1** (X-Request-ID ausente → P0-01) |
| Bugs P1 | **2** (`/version`+`/ready`, OpenAPI incompleto → **corregido**) |
| Bugs P2 | **2** (Content-Length falso; logs sin request_id/stack trace en errores tipados) |
| Bugs P3 | **2** (NaN aceptado sin documentar; p95 alto en concurrencia) |
| Decisión | **NO (P0-01) para el criterio estricto de la auditoría**; el contrato de análisis está funcionalmente listo |

El contrato de análisis (`POST`/`GET`/`/health`) funciona y coincide con lo documentado.
Los gaps son de **observabilidad** (`X-Request-ID`, `/version`, `/ready`) y de metadata
OpenAPI (ya enriquecida). No hay crashes ni 500 en los 15 casos límite.

## 2. Cumplimiento de requerimientos funcionales (evidencia real)

| RF | Descripción | Verificación (comando + output real) | Estado |
|---|---|---|---|
| RF-37 | Extracción de pitch | `POST absolute sine_440hz_5s.wav` → GET: `mean_pitch_hz=439.8` | ✅ |
| RF-38 | Afinación comparative | `POST comparative sine_442hz_5s.wav` vs `sine_440hz_5s.wav` → `average_cent_deviation=10.0`, `pitch_accuracy=100.0` (teórico 7.85 c; estimación pyin) | ✅ |
| RF-39 | Feedback/segmentos | `POST absolute gap_then_tone.wav` → `segments=[{start:0.0,end:0.9600000000000001,type:no_voice,severity:info}]` | ✅ |
| RF-40 | Puntaje multimodal (pitch+ritmo) | `rhythm_accuracy=null` en comparative (diferido a Sprint 1, documentado) | ✅ (diferido) |
| RF-XX | Modo absolute | `pitch_accuracy=null`, `pitch.reference=null` | ✅ |
| RF-XX | Modo comparative | `pitch_accuracy=100.0`, `reference_frames=94` | ✅ |
| RF-XX | Límite tamaño | WAV 51 MB → `HTTP 413 AUDIO_TOO_LARGE` | ✅ |
| RF-XX | Límite duración | WAV 601 s → `HTTP 413 AUDIO_TOO_LONG` | ✅ |
| RF-XX | Formatos M4A/AAC/MP3/OGG | cada uno → `HTTP 202` (`m4a 782 ms`, `mp3 796 ms`, `aac 803 ms`, `ogg 855 ms`) | ✅ (202, no 200) |
| RF-XX | Errores tipados | 400/413/422 con `detail.code` (`EMPTY_FILE`, `INVALID_AUDIO`, `AUDIO_TOO_LARGE`, `AUDIO_TOO_LONG`, `INVALID_MODE`, `MISSING_REFERENCE`) | ✅ |
| RF-XX | `/health` sano/degradado | sano `200`; sin ffmpeg `503 {"status":"degraded",...}`; restaurado `200` | ✅ |
| RF-XX | `X-Request-ID` | `resp.headers.get("x-request-id")` → `None` | ❌ **P0-01** |

## 3. Contrato real vs documentado

| Endpoint | Documentado | Real | ¿Coincide? |
|---|---|---|---|
| `POST /api/v1/analyze` (absolute) | `202 {analysis_id,status,mode}` + `GET` con `metrics` (pitch_accuracy null) | `202 {"analysis_id":"aba395…","status":"completed","mode":"absolute"}`; `metrics.pitch_accuracy=null` | ✅ |
| `POST /api/v1/analyze` (comparative) | `202` + `GET` con `pitch_accuracy`/`average_cent_deviation` | `202 {"analysis_id":"783dff…","mode":"comparative"}`; `pitch_accuracy=100.0`, `average_cent_deviation=10.0` | ✅ |
| `GET /api/v1/analyze/{id}` | `AnalysisResult` (pitch/segments/scores/metrics/feedback/timings) | idéntico; 404 `ANALYSIS_NOT_FOUND` | ✅ |
| `GET /health` | `{status,service,version,checks,timestamp}`; 503 degraded | idéntico; 503 sin ffmpeg | ✅ |
| `GET /ready` | No documentado | `404 {"detail":"Not Found"}` | ❌ **P1-02** (no implementado) |
| `GET /version` | No documentado | `404 {"detail":"Not Found"}` | ❌ **P1-02** (no implementado) |
| `GET /openapi.json` | — | disponible, OpenAPI 3.1.0 | ✅ |

## 4. Casos límite (15, ejecutados)

| # | Caso | Técnica | HTTP | Body/código real | Resultado |
|---|---|---|---|---|---|
| 1 | Archivo 0 bytes | `empty.wav` | 400 | `EMPTY_FILE` | ✅ error limpio |
| 2 | WAV con NaN | `scipy.io.wavfile` float32 NaN | 202 | análisis completado | ⚠️ aceptado (P3-01; documentar) |
| 3 | WAV clipping | amplitud 1.0 | 202 | análisis completado | ✅ |
| 4 | WAV silencio puro | 3 s de ceros | 202 | `voiced_ratio≈0`, `NO_VOICE` | ✅ |
| 5 | 192 kHz estéreo 5 min | WAV 51 MB (header 192k/2ch/300 s) | 413 | `AUDIO_TOO_LARGE` | ✅ límite de tamaño antes de decodificar (sin OOM) |
| 6 | WAV 8 canales | 8ch 16 kHz 2 s | 202 | downmix a mono | ✅ |
| 7 | `.wav` con contenido MP3 | MP3 copiado a `.wav` | 202 | FFmpeg detecta por contenido | ✅ |
| 8 | filename `../../evil.wav` | multipart filename | 202 | nombre temporal fijo | ✅ sin path traversal |
| 9 | filename unicode | `ñandú_测试.wav` | 202 | análisis completado | ✅ |
| 10 | `mode=invalid` | form | 422 | `INVALID_MODE` | ✅ |
| 11 | comparative sin referencia | form | 400 | `MISSING_REFERENCE` | ✅ |
| 12 | Sin campo `audio` | form sin archivo | 422 | `{"detail":[{"loc":["body","audio"],...}]}` | ✅ |
| 13 | `reference_audio` corrupto | texto `.wav` | 400 | `INVALID_AUDIO` | ✅ |
| 14 | Dos requests concurrentes 1 min | threads | 202/202 | `11820 ms` / `10714 ms` | ✅ sin 500 |
| 15 | Content-Length falso | socket crudo (999999 bytes, body corto) | — | respuesta vacía (`b''`) | ⚠️ cliente malformado; contenedor vivo (P2-01) |

Tras los 15 casos: `/health` 200, contenedor `Up (healthy)`, sin reinicios.

## 5. Concurrencia y estabilidad

5 requests concurrentes de audio de 1 min, 3 rondas (15 totales):

```
ronda 1: [(202, 16199 ms), (202, 18219 ms), (202, 10946 ms), (202, 20352 ms), (202, 12328 ms)]
ronda 2: [(202, 24123 ms), (202, 27096 ms), (202, 11975 ms), (202, 11973 ms), (202, 22862 ms)]
ronda 3: [(202, 11065 ms), (202, 12587 ms), (202, 15845 ms), (202, 18414 ms), (202, 20456 ms)]
latencias 202 (ms): n=15 p50=16199 p95=25015 p99=26679 max=27096
health post-concurrencia: HTTP 200
docker stats: mem=269.8MiB / 6.654GiB, cpu=0.45%
```

- **15/15 = 202**, ningún 500, sin crashes, contenedor vivo.
- Semáforo `MAX_CONCURRENT_ANALYSES=2` + 1 worker: las latencias altas son esperables
  (CPU-bound). `BUSY_TIMEOUT_SEC=30` queda cerca del máximo (27.1 s); audios más largos
  podrían devolver 429. Es comportamiento documentado, no bug.

## 6. Logs

- **Eventos estructurados** (JSON una línea): `analysis_accepted` con
  `analysis_id`, `attempt_id`, `routine_id`, `mode`, `duration_sec`, `vocal`, `timings`.
  Muestra real:

```json
{"ts": "2026-11-14T19:11:53+00:00", "event": "analysis_accepted", "analysis_id": "e45c6dc9fee546f292e9e182228e507e", "attempt_id": "audit-e912ed3beb", "routine_id": "audit", "mode": "absolute", "algorithm_version": "0.5.0-hybrid-modes", "duration_sec": 60.0, "vocal": 100, "timings": {"preprocess_ms": 2191, "pitch_ms": 1994, "dtw_ms": 3, "scoring_ms": 21}}
```

- **No hay `request_id`** en logs ni respuestas → **P0-01**.
- **No hay `Traceback`** para errores tipados (400/413/422): se registran como
  `analysis_failed` con `code`/`http_status` (diseño RNF-03). Los 500 no capturados sí
  producirían traceback de uvicorn. → **P2-02** (sin stack trace en errores esperados).
- **Sin datos sensibles:** no aparecen rutas absolutas (`/tmp/...`), ni contenido de
  audio, ni PII; sólo ids y timings. Access log muestra método/ruta/status.

## 7. OpenAPI

**Antes (auditoría):**

```
POST   /api/v1/analyze    summary='Solicitar análisis vocal de un intento' desc_len=0 tags=['analyze'] responses=['202','422'] examples=False
GET    /api/v1/analyze/{analysis_id} summary='Obtener el resultado de un análisis' desc_len=0 tags=['analyze'] responses=['200','422'] examples=False
GET    /health            summary='Health check con dependencias' desc_len=126 tags=['health'] responses=['200'] examples=False
openapi tags: None
```

**Después (metadata enriquecida, sin lógica):**

```
openapi: 3.1.0 | title: SyncDance AI — singing-service | version: 0.2.0
contact: {'name': 'SyncDance AI — Equipo 7'} | license: {'name': 'Uso interno — SyncDance AI'}
tags: [('Análisis', ...), ('Salud', ...), ('Sistema', ...)]
POST  /api/v1/analyze               summary='Analizar audio de canto' desc_len=775 tags=['Análisis'] responses=['202','400','413','422','429','500','503'] examples=True
GET   /api/v1/analyze/{analysis_id} summary='Obtener el resultado de un análisis' desc_len=364 tags=['Análisis'] responses=['200','404','422'] examples=True
GET   /health                       summary='Health check con dependencias' desc_len=141 tags=['Salud'] responses=['200','503'] examples=True
docs title: SyncDance AI — singing-service - Swagger UI
redoc status: 200
```

- `/docs` carga (título real arriba); `/redoc` 200; `openapi.json` 13.293 bytes.
- Cada operación tiene summary, description, tags, responses y examples.
- Nota: el POST devuelve **202** (no 200) y el 503 se documenta como “no aplica a
  `/analyze`; lo devuelve `/health`”.

## 8. Bugs y propuestas

| ID | Sev | Bug | Repro | Fix propuesto | ¿Aplicado? |
|---|---|---|---|---|---|
| P0-01 | P0 | `X-Request-ID` ausente en respuestas y logs | `curl -i /health` → sin header; `docker compose logs` sin `request_id` | middleware `RequestIDMiddleware` (genera/propaga `X-Request-ID` y lo inyecta en `log_event`) | **No** (requiere lógica; esperando autorización) |
| P1-02 | P1 | `GET /version` y `GET /ready` no existen (404) | `curl /version`, `curl /ready` | añadir endpoints de solo lectura (`version` desde settings; `ready` = health resumido) | **No** (feature nueva; hardening) |
| P1-03 | P1 | OpenAPI incompleto (sin descripciones/responses/examples/tags) | `curl /openapi.json` | metadata OpenAPI (tags, responses, examples, contacto/licencia) | **Sí** (solo metadata) |
| P2-01 | P2 | Content-Length falso → respuesta vacía, no 4xx limpio | socket crudo con `Content-Length: 999999` | dejar que uvicorn/h11 cierre; documentar como cliente malformado; opcional proxy que normalice | **No** (no rompe el servicio) |
| P2-02 | P2 | Errores tipados sin stack trace; logs sin `request_id` | logs de un 400/413 | `request_id` + logging de excepción opcional en 500 | **No** (misma familia que P0-01) |
| P3-01 | P3 | WAV con NaN se acepta (202) | `scipy.io.wavfile` float32 NaN | documentar comportamiento; opcional validar NaN en preprocess | **No** (aceptable; documentado) |
| P3-02 | P3 | p95 25 s con 5×1 min (1 worker) | 3 rondas de concurrencia | escalar réplicas / workers; warm-up (HU-S1-06) | **No** (hardening) |

**Hay 1 P0 (P0-01, X-Request-ID):** es un RF de observabilidad, no un fallo del análisis.
Ningún caso produjo 500 sin body ni dejó el contenedor inutilizable.

## 9. Decisión

- **Criterio estricto de esta auditoría: NO.** El RF `X-Request-ID` no se cumple
  (**P0-01**) y requiere un middleware (cambio de lógica) que **no se aplicó** a la
  espera de autorización, según las reglas.
- **Contrato de análisis: funcionalmente listo.** `POST`/`GET`/`/health` coinciden, los
  RFs de análisis se cumplen y los 15 casos límite no crashean. Una vez autorizado y
  aplicado el fix de `X-Request-ID` (y, opcionalmente, P1-02 `/version`/`/ready`), la
  decisión pasa a **SÍ**.
- **Producción estricta: NO** hasta cerrar P0-01 y P1-02. P1-03 (OpenAPI) ya está
  corregido con metadata.

## 10. Verificación del manual (`docs/USAGE.md`)

Todos los comandos ejecutados en terminal limpia contra el contenedor:

| Comando | Output real | OK |
|---|---|---|
| `curl /health` | `200` + JSON con `checks` | ✅ |
| `POST absolute sine_440hz_5s.wav` | `202 {"analysis_id":"aba395…","status":"completed","mode":"absolute"}` | ✅ |
| `GET /analyze/aba395…` | `mean_pitch_hz=439.8`, `voiced_ratio=1.0`, `pitch_accuracy=null` | ✅ |
| `POST comparative 442 vs 440` | `202 {"analysis_id":"783dff…","mode":"comparative"}` | ✅ |
| `GET` comparative | `pitch_accuracy=100.0`, `average_cent_deviation=10.0`, `rhythm_accuracy=null` | ✅ |
| `POST M4A` | `202 {"analysis_id":"abaf92…","mode":"absolute"}` | ✅ |
| `mode=invalid` | `422 {"detail":{"code":"INVALID_MODE",...}}` | ✅ |
| `comparative` sin referencia | `400 {"detail":{"code":"MISSING_REFERENCE",...}}` | ✅ |
| Python `requests` (USAGE §3) | `POST 202 …` / `GET 200 {'mean_pitch_hz': 439.8, ...}` | ✅ |
| `curl /openapi.json > openapi.json` | 13.293 bytes | ✅ |
| `ffprobe … sine_440hz_5s.m4a` | `codec_name=aac`, `sample_rate=44100`, `channels=1`, `duration=5.0` | ✅ |
| `ffmpeg -v error -i … -f null -` | exit 0 (decodifica) | ✅ |
| `curl /docs` | `<title>SyncDance AI — singing-service - Swagger UI` | ✅ |
| `curl /redoc` | `200` | ✅ |

**Confirmación:** todos los comandos de `docs/USAGE.md` fueron ejecutados y producen el
output documentado. Excepción: el comando de `openapi-generator-cli` de
`docs/SWAGGER_GUIDE.md` §6 no se ejecutó (herramienta no instalada); el `openapi.json`
sí se descargó y validó.

## 11. OpenAPI fragmento

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "SyncDance AI — singing-service",
    "version": "0.2.0",
    "contact": {"name": "SyncDance AI — Equipo 7"},
    "license": {"name": "Uso interno — SyncDance AI"}
  },
  "tags": [
    {"name": "Análisis", "description": "Análisis de canto: pitch, métricas, segmentos y feedback."},
    {"name": "Salud", "description": "Estado del servicio y de sus dependencias (ffmpeg, librosa, disco)."},
    {"name": "Sistema", "description": "Metadatos y documentación del servicio."}
  ]
}
```

Operaciones documentadas: `POST /api/v1/analyze` (202/400/413/422/429/500/503),
`GET /api/v1/analyze/{analysis_id}` (200/404/422), `GET /health` (200/503).

## 12. Cierre

```
pytest -v: 71 passed, 1 warning in 24.92s (cobertura 93%)
bash integration/verify_handoff.sh: 4/4 checks OK — HANDOFF OK
ruff check .: All checks passed!
```

- **No se rompió el contrato:** los shapes de `POST`/`GET`/`/health` no cambiaron; sólo
  se añadió metadata OpenAPI (snapshot regenerado) y documentación.
- **`core-api/` intacto** (no existe en el workspace).
- **Documentos históricos intactos:** `CIERRE_GAPS_SPRINT0.md`, `HANDOFF_CORE.md`,
  `CONSISTENCY_FIX.md`, `ESTADO_ACTUAL.md` no se modificaron.
- **Sin cambios de lógica:** `app/main.py` y `app/api/routes/analyze.py` sólo cambiaron
  decoradores/metadata (`tags`, `description`, `responses`, contacto/licencia).
