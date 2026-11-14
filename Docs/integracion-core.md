# Integración `singing-service` ↔ Core (Django/Celery)

Guía operativa para el compañero de Django (plan §3 punto 3, Sprint 5; actualizada en el
cierre de gaps del Sprint 0).
Contrato vivo: **`http://singing-service:5000/docs`** (snapshot congelado en
`singing-service/tests/snapshots/openapi_v1.json`).
Contrato listo para copiar: **`singing-service/docs/celery-contract.md`**.

> **Variable canónica: `SINGING_SERVICE_URL`.** El Core debe leer esta variable; si usa
> otro nombre, actualizar este documento, **no** el código del servicio.

## 1. Flujo recomendado (worker Celery)

```
Core recibe intento con audio
   │  (audio de referencia de la rutina ya conocido por la rutina)
   ▼
task analyze_vocal(attempt_id, routine_id, audio, reference?)
   │  POST /api/v1/analyze  (multipart)          → 202 {analysis_id, status, mode}
   ▼
GET /api/v1/analyze/{analysis_id}                → 200 AnalysisResult
   │
   ▼
Core persiste scores/metrics/segments/feedback en su DB (fuente de verdad)
```

El servicio es **stateless**: guarda resultados en memoria con TTL de 1 h.
Si pierdes el `analysis_id`, relanza el `POST` con el **mismo `attempt_id`**.

## 2. Contrato mínimo

### POST `/api/v1/analyze` (202)

| Campo | Tipo | Notas |
|---|---|---|
| `audio` | archivo | intento del alumno; `wav/m4a/mp3/aac/ogg` (+flac/video), ≤ `MAX_FILE_MB` (50), ≤ `MAX_DURATION_SEC` (600) |
| `reference_audio` | archivo | referencia de la rutina; **requerido en `comparative`** (o `reference_notes`) |
| `reference_notes` | form JSON | alternativa a `reference_audio`: `[{"t":0.0,"f0":440.0}, ...]` |
| `attempt_id` | form (req) | id del intento en el Core — **clave de idempotencia** |
| `routine_id` | form (req) | rutina a la que pertenece el intento |
| `mode` | form | **`absolute`** (default, sin referencia) \| **`comparative`** (con referencia) |

### GET `/api/v1/analyze/{analysis_id}` (200 / 404)

Devuelve `AnalysisResult` completo: `mode`, `pitch` (curvas alumno/referencia; referencia
`null` en absolute), `segments`, `scores` (0-100), `metrics` (ver abajo), `feedback`
(códigos estables), `timings`.

`metrics`:

- ambos modos: `pitch_stability_cents`, `mean_pitch_hz`, `voiced_ratio`.
- sólo `comparative`: `pitch_accuracy`, `average_cent_deviation`.
- siempre `null` en v1: `rhythm_accuracy` (ritmo diferido a Sprint 1).

### Idempotencia y reintentos

- Mismo `attempt_id` **con análisis ya completado** → devuelve el mismo
  `analysis_id` sin recomputar (reintento barato).
- Tras un **error** no queda índice: el reintento con el mismo `attempt_id`
  re-ejecuta el análisis (el fallo nunca corrompe el intento, RNF-07).
- El Core debe persistir sus propios estados (`queued/completed/failed` del
  intento): en error HTTP use `detail.code` como `code` del intento fallido.
  Los valores `queued`/`failed` del enum de respuesta están **reservados** para
  un futuro modo asíncrono; el flujo actual siempre responde `completed`.

### Manejo de errores (tabla completa en `singing-service/README.md`)

| Situación | HTTP | `detail.code` | Acción del worker |
|---|---|---|---|
| Reintento válido | 202 | — | usar `analysis_id` devuelto |
| Falta referencia en comparative | 400 | `MISSING_REFERENCE` | marcar fallido (bug del Core) |
| Audio inválido / sin pista / formato | 400 | `INVALID_AUDIO`, `NO_AUDIO_TRACK`, `UNSUPPORTED_FORMAT` | marcar intento fallido (no reintentar) |
| Notas JSON inválidas | 400 | `INVALID_REFERENCE_NOTES` | marcar fallido (no reintentar) |
| Archivo/duración excedidos | 413 | `AUDIO_TOO_LARGE`, `AUDIO_TOO_LONG` | marcar intento fallido |
| `mode` inválido | 422 | `INVALID_MODE` | bug del Core: no reintentar |
| **Servicio saturado** | 429 | `SERVICE_BUSY` | **reintentar con backoff** (semáforo `MAX_CONCURRENT_ANALYSES=2`, espera `BUSY_TIMEOUT_SEC=30`) |
| Error interno (sin FFmpeg, pyin) | 500/400 | `FFMPEG_NOT_FOUND`, `PITCH_EXTRACT_FAILED` | reintentar 1-2 veces; si persiste → alerta operativa |
| Servicio degradado | 503 | — | no encolar; alerta operativa |
| Análisis expirado (>1 h) | 404 | `ANALYSIS_NOT_FOUND` | rehacer `POST` con mismo `attempt_id` |

**Timeouts del cliente:** `connect=5 s`, `read=300 s` (FFmpeg ≤120 s + pyin + comparación;
margen para JIT frío de numba). `GET` read=10 s.
`httpx.Timeout(connect=5.0, read=300.0)`.

## 3. Esqueleto de tarea Celery

```python
import os

import httpx
from celery import shared_task

SINGING_SERVICE_URL = os.environ["SINGING_SERVICE_URL"]  # http://singing-service:5000
ANALYZE_URL = f"{SINGING_SERVICE_URL}/api/v1/analyze"


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyze_vocal(self, attempt_id: str, routine_id: str,
                  audio_path: str, reference_path: str | None = None) -> dict:
    mode = "comparative" if reference_path else "absolute"
    data = {"attempt_id": attempt_id, "routine_id": routine_id, "mode": mode}
    files = {"audio": (audio_path, open(audio_path, "rb"), "application/octet-stream")}
    if reference_path:
        files["reference_audio"] = (
            reference_path, open(reference_path, "rb"), "application/octet-stream"
        )

    try:
        with httpx.Client(timeout=httpx.Timeout(connect=5.0, read=300.0)) as client:
            r = client.post(ANALYZE_URL, data=data, files=files)
            if r.status_code == 429:
                raise self.retry(countdown=15)
            if r.status_code == 503:
                raise self.retry(countdown=30)
            if r.status_code >= 400:
                code = r.json().get("detail", {}).get("code", "UNKNOWN")
                return {"status": "failed", "code": code}
            analysis_id = r.json()["analysis_id"]
            result = client.get(f"{ANALYZE_URL}/{analysis_id}", timeout=10.0).json()
            return {"status": "completed", "analysis": result}
    except httpx.HTTPError as exc:
        raise self.retry(exc=exc)
```

## 4. HU-47 — evaluación combinada baile + canto

El `singing-service` entrega `scores` por dimensión; **la ponderación global la
decide el Core** (§3 punto 2):

- `scores.vocal` = 0.5·afinación + 0.25·estabilidad + 0.25·control de volumen
  (fórmula y umbrales: `Docs/scoring.md`).
- Los sub-scores (`afinacion`, `estabilidad`, `control_volumen`,
  `silence_pct`) se verifican por separado (CA de HU-47).
- `metrics.pitch_accuracy` y `average_cent_deviation` sólo existen en
  `comparative`; en `absolute` el Core debe usar `pitch_stability_cents`.
- Sugerencia a validar en refinement: `combinado = w·baile + (1−w)·vocal`
  con `w` configurable por la rutina; **no** se expone endpoint `/combine`
  hasta decisión explícita del equipo (§3 punto 2).
- Feedback para el alumno: `feedback[].code` (`OUT_OF_TUNE`, `NO_VOICE`,
  `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE`) es estable para i18n.

## 5. Observabilidad (RNF-03)

El servicio emite **una línea JSON por evento** en stdout (logger `singing`):

- `analysis_accepted` — `analysis_id`, `attempt_id`, `routine_id`, `mode`,
  `algorithm_version`, `duration_sec`, `vocal`, `timings{...}`
- `analysis_failed` — `attempt_id`, `code`, `http_status`
- `analysis_not_found` — `analysis_id`
- `analysis_idempotent_hit` — `attempt_id`, `analysis_id`

Correlacione sus logs con los del Core por `attempt_id`. Sin PII ni audio
(RNF-06).

## 6. Variables de entorno relevantes

| Env | Default | Efecto |
|---|---|---|
| `SINGING_SERVICE_URL` | `http://singing-service:5000` | **canónica** para el Core |
| `MAX_FILE_MB` / `MAX_DURATION_SEC` | 50 / 600 | límites de subida |
| `MAX_CONCURRENT_ANALYSES` | 2 | análisis simultáneos (semáforo) |
| `BUSY_TIMEOUT_SEC` | 30 | espera máxima antes del 429 `SERVICE_BUSY` |
| `ANALYSIS_TTL_SECONDS` | 3600 | vida del resultado en memoria |
