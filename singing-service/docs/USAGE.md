# Manual de uso — singing-service

## 1. ¿Qué es este servicio?

Microservicio **stateless** de análisis de canto de SyncDance AI. Recibe un audio
(intento del alumno) y, opcionalmente, un audio de referencia; devuelve pitch,
métricas, segmentos y feedback. No gestiona autenticación, no persiste y no conoce
usuarios: la fuente de verdad es el Core (PostgreSQL). Corre en el puerto `5000`
dentro de la red interna de Docker.

## 2. Quick start (5 minutos)

### 2.1 Levantar con Docker

```bash
cd singing-service
docker compose up -d --build singing-service
```

Esperar a que `/health` responda 200:

```bash
curl http://localhost:5000/health
```

```json
{"status":"ok","service":"singing-service","version":"0.3.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.0"},"models_loaded":{"ok":true},"disk_space_mb":936554,"warmup":{"ok":true,"duration_ms":9360.74},"rhythm_warmup":{"ok":true,"duration_ms":1274.22}},"request_id":"d1ccb46c79e44a19a011afa8b31524fb","timestamp":"2026-11-16T01:07:07.526390+00:00"}
```

### 2.2 Primer request (curl)

Generar un WAV de prueba (440 Hz, 5 s) con el generador incluido:

```bash
python integration/generate_fixtures.py
```

Enviar el audio:

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@integration/fixtures/sine_440hz_5s.wav" \
  -F "attempt_id=manual-abs-1" \
  -F "routine_id=manual" \
  -F "mode=absolute"
```

Respuesta real (`202 Accepted`):

```json
{"analysis_id":"aba39561505d47c4abcee05c370c6f82","status":"completed","mode":"absolute"}
```

Consultar el resultado (copiar el `analysis_id`):

```bash
curl http://localhost:5000/api/v1/analyze/aba39561505d47c4abcee05c370c6f82
```

Resultado real (resumen; `pitch.student` tiene 156 frames y aquí se recorta):

```json
{
  "analysis_id": "aba39561505d47c4abcee05c370c6f82",
  "attempt_id": "manual-abs-1",
  "routine_id": "manual",
  "status": "completed",
  "mode": "absolute",
  "algorithm_version": "0.5.0-hybrid-modes",
  "duration_sec": 5.0,
  "pitch": {
    "student": [{"t": 0.0, "f0": 439.8, "voiced": true}],
    "reference": null,
    "hop_ms": 32
  },
  "segments": [],
  "scores": {"vocal": 99, "afinacion": 100, "estabilidad": 100, "control_volumen": 97, "ritmo": null, "silence_pct": 0},
  "metrics": {"pitch_stability_cents": 0.0, "mean_pitch_hz": 439.8, "voiced_ratio": 1.0, "pitch_accuracy": null, "rhythm_accuracy": null, "estimated_tempo_bpm": null, "onset_count": 0, "onset_stability": null, "tempo_deviation_bpm": null, "average_cent_deviation": null},
  "feedback": [],
  "timings": {"preprocess_ms": 353, "pitch_ms": 110, "rhythm_ms": 7, "dtw_ms": 0, "scoring_ms": 2}
}
```

### 2.3 Ritmo (HU-S1-01)

`rhythm_accuracy` es `null` si no hay onsets (p. ej. sine puro). Con audio con
pulsos/voz real es un número 0–100 y se refleja en `scores.ritmo`.

Sin `tempo_bpm` (sin referencia de tempo):

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@integration/fixtures/mastmelody_per.m4a" \
  -F "attempt_id=manual-rhythm-1" \
  -F "routine_id=manual" \
  -F "mode=absolute"
```

Resultado real (extracto de `metrics`/`scores`):

```json
{"metrics": {"rhythm_accuracy": 72.7, "estimated_tempo_bpm": 90.9, "onset_count": 14, "onset_stability": 72.7, "tempo_deviation_bpm": null}, "scores": {"ritmo": 73}}
```

Con `tempo_bpm=120` (comparative; `tempo_deviation_bpm = estimated − 120`):

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@integration/fixtures/mastmelody_per.m4a" \
  -F "reference_audio=@integration/fixtures/mastmelody_ref.m4a" \
  -F "attempt_id=manual-rhythm-2" \
  -F "routine_id=manual" \
  -F "mode=comparative" \
  -F "tempo_bpm=120"
```

Resultado real (extracto):

```json
{"metrics": {"rhythm_accuracy": 57.2, "estimated_tempo_bpm": 90.9, "onset_count": 14, "onset_stability": 72.7, "tempo_deviation_bpm": -29.1}, "scores": {"ritmo": 57}}
```

### 2.4 Verificar que funciona

```bash
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:5000/health   # 200
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:5000/docs     # 200
curl -s http://localhost:5000/openapi.json | head -c 200                 # JSON OpenAPI
```

## 3. Endpoints

### POST /api/v1/analyze

- **Descripción:** analiza un audio de canto y devuelve métricas de pitch, segmentos
  y feedback.
- **URL:** `POST http://singing-service:5000/api/v1/analyze`
- **Auth:** ninguna (red interna de confianza; sin JWT).
- **Request** (`multipart/form-data`):

| Campo | Tipo | Requerido | Ejemplo | Notas |
|---|---|---|---|---|
| `audio` | archivo | **sí** | `intento.m4a` | wav/m4a/mp3/aac/ogg; ≤50 MB, ≤600 s |
| `attempt_id` | form (str) | **sí** | `attempt-123` | idempotencia |
| `routine_id` | form (str) | **sí** | `routine-9` | rutina |
| `mode` | form (str) | **sí** | `absolute` \| `comparative` | default `absolute` |
| `reference_audio` | archivo | sólo comparative | `referencia.wav` | alternativa: `reference_notes` (JSON) |
| `reference_notes` | form (JSON) | alternativa | `[{"t":0.0,"f0":440.0}]` | cada nota: `t` + `f0`/`note`/`midi` |
| `include_contour` | form (bool) | no | `false` | **futuro** (Sprint 1); v0.2.0 lo ignora |
| `tempo_bpm` | form (float) | no | `120` | tempo esperado (BPM); habilita `tempo_deviation_bpm` (HU-S1-01) |

- **Response 202 (Accepted):**

```json
{"analysis_id": "aba39561505d47c4abcee05c370c6f82", "status": "completed", "mode": "absolute"}
```

> El endpoint devuelve **202**, no 200. El resultado completo se consulta con
> `GET /api/v1/analyze/{analysis_id}`.

- **Errores posibles:** ver §6.
- **Ejemplo curl:** §2.2.
- **Ejemplo Python (`requests`):**

```python
import requests

URL = "http://localhost:5000/api/v1/analyze"
with open("integration/fixtures/sine_440hz_5s.wav", "rb") as f:
    r = requests.post(
        URL,
        data={"attempt_id": "manual-py-1", "routine_id": "manual", "mode": "absolute"},
        files={"audio": ("sine.wav", f, "audio/wav")},
        timeout=(5, 300),
    )
print("POST", r.status_code, r.json())
aid = r.json()["analysis_id"]
g = requests.get(f"{URL}/{aid}", timeout=10)
print("GET", g.status_code, g.json()["metrics"])
```

Salida real:

```
POST 202 {'analysis_id': 'dc8e2f7959314537b360d4e145f9ae9e', 'status': 'completed', 'mode': 'absolute'}
GET 200 {'pitch_stability_cents': 0.0, 'mean_pitch_hz': 439.8, 'voiced_ratio': 1.0, 'pitch_accuracy': None, 'rhythm_accuracy': None, 'average_cent_deviation': None}
```

- **Ejemplo desde Celery (Core):** ver §8.4 y el contrato completo en
  [`celery-contract.md`](celery-contract.md).

### GET /api/v1/analyze/{analysis_id}

- **Descripción:** devuelve el `AnalysisResult` completo.
- **URL:** `GET http://singing-service:5000/api/v1/analyze/{analysis_id}`
- **Auth:** ninguna.
- **Response 200:** `AnalysisResult` (ver §2.2). En `absolute`, `pitch.reference`,
  `pitch_accuracy` y `average_cent_deviation` son `null`; `rhythm_accuracy` puede
  ser número si hay onsets (HU-S1-01).
- **Errores:** `404 ANALYSIS_NOT_FOUND` (id inexistente o TTL 1 h expirado).
- **curl:**

```bash
curl http://localhost:5000/api/v1/analyze/<analysis_id>
```

### GET /health

- **Descripción:** estado del servicio y dependencias.
- **URL:** `GET http://singing-service:5000/health`
- **Response 200** (real):

```json
{"status":"ok","service":"singing-service","version":"0.3.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.0"},"models_loaded":{"ok":true},"disk_space_mb":936554,"warmup":{"ok":true,"duration_ms":9360.74},"rhythm_warmup":{"ok":true,"duration_ms":1274.22}},"request_id":"d1ccb46c79e44a19a011afa8b31524fb","timestamp":"2026-11-16T01:07:07.526390+00:00"}
```

- **Response 503** si falta FFmpeg o librosa no carga (ver §9).
- **curl:** `curl http://localhost:5000/health`

### GET /ready

- **Descripción:** readiness para K8s/Docker; distinto de `/health` (liveness).
- **URL:** `GET http://singing-service:5000/ready`
- **Response 200** (real):

```json
{"ready":true,"reason":null,"request_id":"bbad70aa396342e18d128fc66c36b64e"}
```

- **Response 503** con `reason`: `warmup` (arranque), `shutting_down` (SIGTERM) o
  `ffmpeg_unavailable`.
- **curl:** `curl http://localhost:5000/ready`

### GET /version

- **Descripción:** metadatos de versión y build (debug).
- **URL:** `GET http://singing-service:5000/version`
- **Response 200** (real):

```json
{"version":"0.3.0","git_sha":"abc1234","build_time":"2026-11-15T12:00:00Z","python":"3.14.6","ffmpeg":"7.1.5-0+deb13u1","fastapi":"0.142.2","librosa":"1.0.0","request_id":"5ec99b15ffe14d359cefd91c6b2ba045"}
```

- **Header `X-Request-ID`:** se refleja; ejemplo:

```bash
curl -H "X-Request-ID: test-123" http://localhost:5000/version
```

- `git_sha`/`build_time` vienen de `GIT_SHA`/`BUILD_TIME` inyectados en build; si
  faltan, `"unknown"`.

## 4. Formatos de audio soportados

| Formato | Extensión | Notas |
|---|---|---|
| WAV | `.wav` | PCM; se convierte a 16 kHz mono |
| M4A / AAC | `.m4a`, `.aac` | típico de mobile |
| MP3 | `.mp3` | |
| OGG | `.ogg` | Vorbis |

- **Límites:** 50 MB (`MAX_FILE_MB`) y 600 s (`MAX_DURATION_SEC`).
- El servicio decodifica por **contenido** (FFmpeg), no solo por extensión.

Verificar un archivo antes de enviarlo:

```bash
ffprobe -v error -show_format -show_streams intento.m4a
ffmpeg -v error -i intento.m4a -f null -      # valida decodificación
```

## 5. Modos de análisis

### 5.1 `absolute` (default)

Sin referencia. Devuelve estabilidad interna, pitch medio y proporción con voz.
`pitch_accuracy`, `average_cent_deviation` y `rhythm_accuracy` son `null`.
Feedback por umbrales absolutos (`NO_VOICE`, `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE`).

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@integration/fixtures/sine_440hz_5s.wav" \
  -F "attempt_id=abs-1" -F "routine_id=r1" -F "mode=absolute"
```

### 5.2 `comparative`

Compara contra `reference_audio` (o `reference_notes`). Requiere referencia
(`400 MISSING_REFERENCE` si falta). Añade `pitch_accuracy` y
`average_cent_deviation`; produce segmentos `out_of_tune`.

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@integration/fixtures/sine_442hz_5s.wav" \
  -F "reference_audio=@integration/fixtures/sine_440hz_5s.wav" \
  -F "attempt_id=cmp-1" -F "routine_id=r1" -F "mode=comparative"
```

Resultado real (resumen): `pitch_accuracy=100.0`, `average_cent_deviation=10.0`,
`rhythm_accuracy=null`.

### 5.3 Tabla comparativa

| Campo | `absolute` | `comparative` |
|---|---|---|
| `pitch.reference` | `null` | lista |
| `metrics.pitch_accuracy` | `null` | 0–100 |
| `metrics.average_cent_deviation` | `null` | número (cents) |
| `metrics.rhythm_accuracy` | `null` | `null` (diferido) |
| `segments` | `no_voice` | `out_of_tune` + `no_voice` |
| `feedback` | `NO_VOICE`, `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE` | `OUT_OF_TUNE`, `NO_VOICE` |

## Request ID (X-Request-ID)

Todas las respuestas incluyen el header `X-Request-ID`. Es **opcional** en el request:
si el Core envía uno válido (`^[A-Za-z0-9_-]{1,128}$`), el servicio lo reutiliza; si no,
genera un UUID hex. Los **errores** incluyen `request_id` en el body y `/health` también.

**Core debe:** generar un id único por intento (p. ej. `uuid.uuid4().hex`), enviarlo en
el header y loguearlo junto al `attempt_id` para correlacionar los logs.

```bash
curl -D - -X POST http://localhost:5000/api/v1/analyze \
  -H "X-Request-ID: attempt-123" \
  -F "audio=@integration/fixtures/sine_440hz_5s.wav" \
  -F "attempt_id=attempt-123" -F "routine_id=r1" -F "mode=absolute"
# HTTP/1.1 202 Accepted
# x-request-id: attempt-123
```

Error 400 (body con `request_id`):

```json
{"detail":{"code":"INVALID_AUDIO","message":"No se pudo decodificar el audio","request_id":"attempt-123"}}
```

> Un cliente HTTP malformado (p. ej. `Content-Length` falso) es rechazado por uvicorn
> **antes** del middleware: devuelve `400` con texto plano y sin `X-Request-ID`. Ver
> [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## 6. Códigos de error

| HTTP | Code | Causa | Acción para Core |
|---|---|---|---|
| 400 | `UNSUPPORTED_FORMAT` | Extensión no permitida | No reintentar |
| 400 | `INVALID_AUDIO` | Contenido corrupto/no decodificable | No reintentar |
| 400 | `MISSING_REFERENCE` | comparative sin referencia | No reintentar (bug del cliente) |
| 400 | `INVALID_REFERENCE_NOTES` | JSON de notas inválido | No reintentar |
| 400 | `NO_AUDIO_TRACK` | archivo sin pista de audio | No reintentar |
| 400 | `EMPTY_FILE` / `EMPTY_AUDIO` | archivo vacío/sin muestras | No reintentar |
| 400 | `CONVERT_TIMEOUT` | FFmpeg > 120 s | Reintentar 1 vez |
| 400 | `PITCH_EXTRACT_FAILED` | pyin falló | Reintentar 1 vez |
| 413 | `AUDIO_TOO_LARGE` | > 50 MB | No reintentar |
| 413 | `AUDIO_TOO_LONG` | > 600 s | No reintentar |
| 422 | `INVALID_MODE` | mode inválido | No reintentar |
| 422 | — (lista) | campo faltante (p. ej. `audio`) | No reintentar |
| 429 | `SERVICE_BUSY` | 2 análisis en curso | **Reintentar con backoff** |
| 500 | `FFMPEG_NOT_FOUND` | sin FFmpeg | Reintentar 1-2 veces |
| 500 | `UNHANDLED_ERROR` | excepción no capturada (bug del servicio) | Reintentar con backoff; alertar; reportar con `request_id` |
| 503 | — | `/health` degradado | No encolar; alertar |

- **`UNHANDLED_ERROR` (500):** error interno no capturado. El body incluye
  `request_id`; úsalo para reportar el bug. Core debe reintentar con backoff.
- **Content-Length inválido:** caso especial manejado por uvicorn **antes** de la app.
  Devuelve `400 text/plain` sin `X-Request-ID` ni body JSON. Ver
  `docs/celery-contract.md` §5 nota V-01.

> El servicio **no** emite `INTERNAL_ERROR` ni `SERVICE_DEGRADED`; son etiquetas del
> Core. Un 5xx sin JSON es recuperable (ver contrato §5).

## 7. Uso con Swagger

- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`
- OpenAPI: `http://localhost:5000/openapi.json`

Guía detallada: [`SWAGGER_GUIDE.md`](SWAGGER_GUIDE.md).

Pasos para probar `/analyze` desde Swagger UI:

1. Abrir `/docs` y desplegar `POST /api/v1/analyze`.
2. **Try it out**.
3. En `audio`, elegir un archivo (WAV/M4A/MP3/AAC/OGG).
4. Completar `attempt_id`, `routine_id` y `mode` (`absolute`).
5. **Execute**.
6. Ver el `202` y copiar `analysis_id`; luego ejecutar el `GET`.

Descargar el OpenAPI:

```bash
curl http://localhost:5000/openapi.json > openapi.json
```

## 8. Integración con Core (Celery)

### 8.1 Flujo

```
Core recibe intento con audio
   │
   ▼
task analyze_vocal(attempt_id, routine_id, audio, reference?)
   │  POST /api/v1/analyze  (multipart) → 202 {analysis_id}
   ▼
GET /api/v1/analyze/{analysis_id} → 200 AnalysisResult
   │
   ▼
Core persiste scores/metrics/segments/feedback en su DB
```

### 8.2 URL a usar

`http://singing-service:5000/api/v1/analyze` (nombre del servicio Docker, **no**
`localhost`). Configurar `SINGING_SERVICE_URL=http://singing-service:5000`.

### 8.3 Timeouts recomendados

`connect=5 s`, `read=300 s` (un audio de 10 min puede tardar ~4 min; JIT mitigado por
warm-up en v0.3.0).

### 8.4 Tarea Celery de ejemplo

Ver el código completo en [`celery-contract.md`](celery-contract.md) §6. Resumen:

```python
@shared_task(bind=True, autoretry_for=(httpx.TransportError,), retry_backoff=True,
             max_retries=3, soft_time_limit=330, time_limit=360)
def analyze_vocal(self, attempt_id, routine_id, audio_path, reference_path=None):
    mode = "comparative" if reference_path else "absolute"
    # POST multipart con "audio" (+ "reference_audio" si aplica), timeout (5, 300)
    # 429/5xx -> self.retry(backoff); 4xx -> marcar Attempt failed (no retry)
    # 5xx sin JSON -> retry (guard, sin KeyError)
    # 2xx -> GET /analyze/{id} y persistir
```

### 8.5 Checklist de integración

1. [ ] `SINGING_SERVICE_URL` configurada.
2. [ ] `/health` 200 desde el worker.
3. [ ] POST con `audio`, `attempt_id`, `routine_id`, `mode`.
4. [ ] comparative envía `reference_audio`.
5. [ ] timeouts `connect=5`, `read=300`.
6. [ ] 4xx no se reintenta; se persiste `detail.code`.
7. [ ] 429/5xx/red se reintentan con backoff.
8. [ ] GET + persistencia de `scores`, `metrics`, `segments`, `feedback`.
9. [ ] tolerancia a `null` (`pitch.reference`, `pitch_accuracy`, `rhythm_accuracy`).
10. [ ] `verify_handoff.sh` OK e idempotencia por `attempt_id`.

## 9. Troubleshooting rápido

| Síntoma | Causa | Solución |
|---|---|---|
| `422 Field required` | se envió `file` en vez de `audio` | usar `audio` |
| `400 INVALID_AUDIO` | audio corrupto | `ffprobe`/`ffmpeg -f null -`; reconstruir imagen |
| `413 AUDIO_TOO_LARGE` | > 50 MB | comprimir en Flutter |
| `413 AUDIO_TOO_LONG` | > 600 s | truncar/dividir |
| `503` en `/health` | falta FFmpeg/librosa | `docker compose build --no-cache singing-service` |
| primer request lento | JIT de numba | mitigado en v0.3.0 (warm-up en lifespan); timeout ≥ 60 s por si el warm-up falla |
| `verify_handoff.sh` falla en Windows | requiere Git Bash/WSL | ver `integration/README.md` |

Detalle: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## 10. Referencia

- [`celery-contract.md`](celery-contract.md) — contrato con Core.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitectura interna.
- [`SWAGGER_GUIDE.md`](SWAGGER_GUIDE.md) — guía de Swagger/OpenAPI.
- [`SPRINT1_BACKLOG.md`](SPRINT1_BACKLOG.md) — siguiente sprint.
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — problemas comunes.
