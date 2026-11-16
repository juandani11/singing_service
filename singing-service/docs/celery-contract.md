# Contrato `singing-service` ↔ worker Celery del Core

> Documento ejecutable para el equipo de **Core API**. Versión del contrato: v1 híbrido
> (`absolute`/`comparative`). El servicio está cerrado: 70 tests, 93 % de cobertura.
> Cambios BREAKING vs contrato anterior: ver `CIERRE_GAPS_SPRINT0.md` §2.

## 1. URL y red

```
POST http://singing-service:5000/api/v1/analyze
GET  http://singing-service:5000/api/v1/analyze/{analysis_id}
```

- `singing-service` es el **nombre del servicio en la red interna de Docker** (no
  `localhost`). El Core y el worker Celery deben estar en la misma red de compose.
- **Producción:** no hardcodear; usar `SINGING_SERVICE_URL`
  (`http://singing-service:5000`). La URL de análisis es
  `{SINGING_SERVICE_URL}/api/v1/analyze`.
- Sin autenticación (red interna, decisión del equipo). No publicar el puerto 5000
  fuera de la red.

## 2. Multipart exacto

`POST /api/v1/analyze` (`multipart/form-data`):

| Campo | Tipo | Requerido | Ejemplo | Notas |
|---|---|---|---|---|
| `audio` | archivo | **sí** | `intento.m4a` | campo canónico (simétrico con `reference_audio`); wav/m4a/mp3/aac/ogg; ≤50 MB, ≤600 s |
| `attempt_id` | form (str) | **sí** | `attempt-123` | clave de idempotencia |
| `routine_id` | form (str) | **sí** | `routine-9` | rutina del intento |
| `mode` | form (str) | **sí** | `absolute` \| `comparative` | default del servicio: `absolute` |
| `reference_audio` | archivo | sólo `comparative` | `referencia.wav` | alternativa: `reference_notes` (JSON) |
| `reference_notes` | form (JSON) | alternativa | `[{"t":0.0,"f0":440.0}]` | cada nota: `t` + `f0`/`note`/`midi` |
| `include_contour` | form (bool) | no | `false` | **futuro**: v1 lo ignora (`pitch_contour` no implementado) |
| `tempo_bpm` | form (float) | no | `120` | tempo esperado en BPM; si se envía, se calcula `metrics.tempo_deviation_bpm` (HU-S1-01) |

| Header | Tipo | Requerido | Ejemplo | Notas |
|---|---|---|---|---|
| `X-Request-ID` | header | no (recomendado) | `abc-123` | 1–128 chars `[A-Za-z0-9_-]`; si es válido se reutiliza, si no se genera un UUID hex |

### requests (código real)

```python
import httpx

SINGING_SERVICE_URL = "http://singing-service:5000"
ANALYZE_URL = f"{SINGING_SERVICE_URL}/api/v1/analyze"

with open("/ruta/intento.m4a", "rb") as audio, open("/ruta/referencia.wav", "rb") as ref:
    response = httpx.post(
        ANALYZE_URL,
        data={
            "attempt_id": "attempt-123",
            "routine_id": "routine-9",
            "mode": "comparative",
        },
        files={
            "audio": ("intento.m4a", audio, "application/octet-stream"),
            "reference_audio": ("referencia.wav", ref, "application/octet-stream"),
        },
        timeout=httpx.Timeout(connect=5.0, read=300.0),
    )
```

### curl real

```bash
curl -X POST http://singing-service:5000/api/v1/analyze \
  -F "audio=@intento.m4a" \
  -F "reference_audio=@referencia.wav" \
  -F "attempt_id=attempt-123" \
  -F "routine_id=routine-9" \
  -F "mode=comparative"
```

Respuesta `202`:

```json
{"analysis_id": "50dfedcd6f254ea4bf97f2a9378159ec", "status": "completed", "mode": "comparative"}
```

## 3. Timeouts

| Parámetro | Valor | Justificación |
|---|---|---|
| connect | **5 s** | red interna Docker; si no conecta en 5 s, el servicio está caído |
| read | **300 s** | un audio de 10 min puede tardar hasta ~4 min (FFmpeg + pyin + comparación); margen de seguridad. El warm-up cubre pyin + `beat_track`/`onset_detect` (startup ~14 s); el sine primer/segundo `/analyze` queda <2 s; MASTmelody real ~4 s en Docker (documentado); mantener 300 s por si falla |

```python
httpx.Timeout(connect=5.0, read=300.0)
# o requests: timeout=(5, 300)
```

`GET /analyze/{id}` puede usar `read=10 s` (lookup en memoria).

> Si el Core usa `read < 300 s`, va a cortar audios largos (el servicio seguirá
> procesando y el resultado quedará huérfano hasta el TTL de 1 h).

> **Nota latencia `rhythm_eval`.** `rhythm_eval` (`beat_track` + `onset_detect`)
> añade ~3.8 s en un audio de 4.8 s (~0.79x real-time). Para 5 min → ~4 min. El
> warm-up mitiga el JIT frío, no el coste computacional. Core: timeout del worker
> ≥ 300 s (ya documentado). Optimización planificada en Sprint 2
> (HU-S2-XX: downsample selectivo o cache por hash de audio).

> **Timeouts internos (HU-S1-05).** Además del timeout del cliente, el servicio
> protege su worker con timeouts configurables: `PYIN_TIMEOUT_SECONDS` (default
> **120 s**; rango `0 < x < 300`) para `librosa.pyin` y `ALIGN_TIMEOUT_SECONDS`
> (default **30 s**; rango `0 < x < 120`) para FastDTW. Al vencer, `POST /analyze`
> responde **504 `ANALYSIS_TIMEOUT`** con `request_id`. Limitación: librosa/FastDTW
> no son interrumpibles; el request responde y libera el semáforo, pero el hilo
> huérfano termina por su cuenta (el executor acota cuántos se acumulan). Core:
> reintentar con backoff.

## 4. Matriz de response por modo

`GET /api/v1/analyze/{analysis_id}` → `200 AnalysisResult`.

| Campo | `absolute` | `comparative` | Notas |
|---|---|---|---|
| `mode` | `"absolute"` | `"comparative"` | eco del modo usado |
| `pitch.student` | lista | lista | curva F0 del alumno |
| `pitch.reference` | **`null`** | lista | sin referencia en absolute |
| `scores.vocal/afinacion/estabilidad/control_volumen/silence_pct` | 0–100 | 0–100 | `afinacion` en absolute = consistencia interna |
| `scores.ritmo` | 0–100 o **`null`** | 0–100 o **`null`** | `round(rhythm_accuracy)`; null sin onsets (HU-S1-01) |
| `metrics.pitch_stability_cents` | número | número | desviación interna (cents) |
| `metrics.mean_pitch_hz` | número | número | media de frames con voz |
| `metrics.voiced_ratio` | 0–1 | 0–1 | proporción con voz |
| `metrics.pitch_accuracy` | **`null`** | 0–100 | % de frames dentro de `CENT_THRESHOLD` |
| `metrics.average_cent_deviation` | **`null`** | número | desviación media absoluta (cents) |
| `metrics.rhythm_accuracy` | 0–100 o **`null`** | 0–100 o **`null`** | ritmo real (HU-S1-01); null sin onsets |
| `metrics.estimated_tempo_bpm` | número o **`null`** | número o **`null`** | tempo estimado por `beat_track` |
| `metrics.onset_count` | entero ≥0 | entero ≥0 | onsets detectados (`wait=5`) |
| `metrics.onset_stability` | 0–100 o **`null`** | 0–100 o **`null`** | `100·(1−CV)` de intervalos |
| `metrics.tempo_deviation_bpm` | **`null`** sin `tempo_bpm` | número con `tempo_bpm` | `estimated − tempo_bpm` |
| `metrics.alignment_method` | `"time"` | `"fastdtw"` o `"time"` | método de alineación (HU-S1-04); `time` = fallback |
| `segments` | `no_voice` (+ `out_of_rhythm`) | `out_of_tune` + `no_voice` (+ `out_of_rhythm`) | `out_of_rhythm` lleva `interval_ms`/`message` |
| `feedback[].code` | `NO_VOICE`, `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE`, `OUT_OF_RHYTHM` | `OUT_OF_TUNE`, `NO_VOICE`, `OUT_OF_RHYTHM` | códigos estables para i18n |
| `timings` | preprocess/pitch/rhythm/align/dtw/scoring | idem | `align_ms` = alineación (HU-S1-04); `dtw_ms` alias de `align_ms`; `rhythm_ms` = tempo/onsets |

> **Alineación (HU-S1-04, no-BREAKING).** `mode=comparative` usa FastDTW
> (`align_frames`) y cae a `align_by_time` si FastDTW falla. `metrics.alignment_method`
> indica `"fastdtw"` o `"time"`. `timings.align_ms` es aditivo; `dtw_ms` se mantiene
> como alias del mismo valor.

> **Nota C — cardinalidad de `feedback`.** El array `feedback` contiene **1 ítem por tipo** (`OUT_OF_TUNE`, `NO_VOICE`), **no 1 por segmento**. En `OUT_OF_TUNE` se reporta la **peor desviación** (mayor `delta_cents`). Los detalles completos por segmento están en `segments[]`. Comportamiento documentado en `Docs/scoring.md` §Feedback. Un cambio a 1 feedback por segmento sería BREAKING y requiere coordinación con Core.

> **Campos de ritmo aditivos (no-BREAKING).** `scores.ritmo`, `metrics.estimated_tempo_bpm`,
> `metrics.onset_count`, `metrics.onset_stability` y `metrics.tempo_deviation_bpm` se añaden
> en HU-S1-01; los clientes existentes que no los lean siguen funcionando. `rhythm_accuracy`
> deja de ser siempre `null`: puede ser número (o seguir siendo `null` si no hay onsets).

**Crítico para el Core:** tolerar `null` en `pitch.reference`, `pitch_accuracy`,
`average_cent_deviation`, `rhythm_accuracy` y en los campos de ritmo. `scores.ritmo`
es aditivo; úsalo solo si tu UI ya lo contempla.

## 4.1 Endpoints de sistema (`/ready`, `/version`)

- **`GET /ready` — readiness (K8s/Docker).** Diferente de `/health` (liveness).
  - `200` `{"ready": true, "reason": null, "request_id": "..."}` cuando el startup
    self-test terminó y FFmpeg está disponible.
  - `503` `{"ready": false, "reason": "warmup"}` durante arranque.
  - `503` `{"ready": false, "reason": "shutting_down"}` tras SIGTERM (flag para H-04).
  - `503` `{"ready": false, "reason": "ffmpeg_unavailable"}` si `/health` detectaría
    FFmpeg roto.
  - K8s: `/ready` para `readinessProbe`; `/health` para `livenessProbe`.
- **`GET /version` — metadatos de build.** `200` con `version`, `git_sha`,
  `build_time`, `python`, `ffmpeg`, `fastapi`, `librosa` y `request_id`.
  `git_sha`/`build_time` vienen de `GIT_SHA`/`BUILD_TIME` inyectados en build; si
  faltan, `"unknown"`. Para debug, no para lógica de Core.
- Ambas respuestas incluyen `X-Request-ID` (middleware).

```bash
curl http://singing-service:5000/ready
curl http://singing-service:5000/version
```

> `/health` incluye `checks.warmup` (`{"ok": bool, "duration_ms": float|null}`) y
> `checks.rhythm_warmup` (mismo shape, HU-S1-01) desde v0.3.0. Es **aditivo y
> no-BREAKING**: los clientes existentes lo ignoran.

## 5. Matriz de errores

| Código HTTP | Code | Causa | Acción recomendada para Core |
|---|---|---|---|
| 202 | — | aceptado | `GET /analyze/{id}` y persistir |
| 400 | `UNSUPPORTED_FORMAT` | Extensión no permitida (`.txt`, `.pdf`) | No reintentar; error del cliente |
| 400 | `INVALID_AUDIO` | Contenido corrupto o no decodificable | No reintentar; error del cliente |
| 400 | `MISSING_REFERENCE` | `comparative` sin referencia | No reintentar; bug del cliente |
| 400 | `INVALID_REFERENCE_NOTES` | JSON de notas inválido | No reintentar |
| 400 | `NO_AUDIO_TRACK` | video/archivo sin pista de audio | No reintentar |
| 400 | `EMPTY_FILE` / `EMPTY_AUDIO` | archivo vacío/sin muestras | No reintentar |
| 400 | `CONVERT_TIMEOUT` | FFmpeg > 120 s | Reintentar 1 vez; si persiste, alertar |
| 400 | `PITCH_EXTRACT_FAILED` | pyin falló | Reintentar 1 vez; si persiste, alertar |
| 413 | `AUDIO_TOO_LARGE` | > 50 MB | No reintentar |
| 413 | `AUDIO_TOO_LONG` | > 600 s | No reintentar |
| 422 | `INVALID_MODE` | `mode` no válido | No reintentar |
| 422 | — (lista de validación) | Campo faltante (p. ej. `audio`) | No reintentar; bug del cliente |
| 429 | `SERVICE_BUSY` | semáforo lleno (2 análisis) | **Reintentar con backoff** (15–30 s) |
| 500 | `FFMPEG_NOT_FOUND` | sin FFmpeg en el servicio | Reintentar 1-2 veces; si persiste, alertar |
| 500 | `UNHANDLED_ERROR` | Excepción no capturada (bug del servicio) | Reintentar con backoff; alertar; reportar con `request_id` |
| 503 | — | `/health` degradado (sin `detail.code`) | No encolar; alertar |
| 504 | `ANALYSIS_TIMEOUT` | timeout interno de pyin o alineación (HU-S1-05) | **Reintentar con backoff**; alertar si persiste |
| — | `ConnectionError` | servicio caído / red | **Reintentar con backoff** |

> **Nota de wire real.** El `singing-service` **no** emite `INTERNAL_ERROR` ni `SERVICE_DEGRADED`. Esos códigos son responsabilidad del Core al envolver la respuesta. Los únicos códigos que el servicio emite son los listados en la tabla. Si el worker de Core recibe un **5xx sin body JSON parseable** (crash no capturado, timeout del proxy, respuesta truncada), debe tratarlo como error recuperable: reintentar con backoff exponencial (máx. 3) y, si persiste, marcar el `Attempt` como `fallido` y alertar. El Core es quien mapea ese caso a su propio `INTERNAL_ERROR` antes de persistir.

> `VALIDATION_ERROR` es la etiqueta del Core para la **lista** de validación de FastAPI
> (`detail` es un array, no un objeto con `code`).

> **Request ID:** todas las respuestas incluyen el header `X-Request-ID`; los errores
> incluyen además `request_id` en el body (`detail.request_id` en 400/404/413/429/500;
> top-level en 422 de validación). Si el middleware captura una excepción no controlada,
> responde `500 UNHANDLED_ERROR` con `request_id` (sin stack en el body).

> **Nota V-01 — Content-Length inválido.** Uvicorn rechaza requests con `Content-Length` inconsistente **antes** de llegar al middleware. Respuesta: `400 Bad Request` con `text/plain: "Invalid HTTP request received."`, **sin** `X-Request-ID`, **sin** body JSON. El cliente de Core debe: (a) no manipular `Content-Length` manualmente (dejar que `requests` lo calcule), (b) tratar este caso como error de cliente (no reintentar), (c) loguear el `request_id` que él generó, no el que esperaba del servicio.

## 6. Tarea Celery de ejemplo (código real)

Dependencias del Core: `celery`, `httpx`, `django`. Adaptar `core.models` a los modelos
reales (los campos JSON pueden ser `JSONField`).

```python
import os
from pathlib import Path

import httpx
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# Persistencia (adaptar a los modelos reales del Core)
from core.models import Attempt, VocalAnalysis

SINGING_SERVICE_URL = os.environ.get(
    "SINGING_SERVICE_URL", "http://singing-service:5000"
).rstrip("/")
ANALYZE_URL = f"{SINGING_SERVICE_URL}/api/v1/analyze"
TIMEOUT = httpx.Timeout(connect=5.0, read=300.0)


def _code(body: object) -> str:
    """Extrae detail.code del body JSON del servicio."""
    if not isinstance(body, dict):
        return "UNKNOWN"
    detail = body.get("detail")
    if isinstance(detail, dict):
        return detail.get("code", "UNKNOWN")
    return "VALIDATION_ERROR"


def _persist_failure(attempt_id: str, code: str) -> None:
    Attempt.objects.filter(pk=attempt_id).update(status="failed", failure_code=code)


def _persist_result(attempt_id: str, payload: dict) -> None:
    Attempt.objects.filter(pk=attempt_id).update(status="completed")
    VocalAnalysis.objects.update_or_create(
        attempt_id=attempt_id,
        defaults={
            "algorithm_version": payload["algorithm_version"],
            "duration_sec": payload["duration_sec"],
            "scores": payload["scores"],
            "metrics": payload["metrics"],
            "segments": payload["segments"],
            "feedback": payload["feedback"],
        },
    )


@shared_task(
    bind=True,
    autoretry_for=(httpx.TransportError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=330,
    time_limit=360,
)
def analyze_vocal(
    self,
    attempt_id: str,
    routine_id: str,
    audio_path: str,
    reference_path: str | None = None,
) -> dict:
    mode = "comparative" if reference_path else "absolute"
    data = {"attempt_id": attempt_id, "routine_id": routine_id, "mode": mode}
    files = {
        "audio": (
            Path(audio_path).name,
            open(audio_path, "rb"),
            "application/octet-stream",
        )
    }
    reference_handle = None
    if reference_path:
        reference_handle = open(reference_path, "rb")
        files["reference_audio"] = (
            Path(reference_path).name,
            reference_handle,
            "application/octet-stream",
        )

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(ANALYZE_URL, data=data, files=files)

            # 429: saturado -> recuperable
            if response.status_code == 429:
                raise self.retry(countdown=15)

            # 5xx: recuperable. Guard: un 5xx sin JSON no debe lanzar KeyError.
            if response.status_code >= 500:
                try:
                    body = response.json()
                except ValueError:
                    # 5xx sin JSON parseable -> error recuperable
                    raise self.retry(
                        exc=RuntimeError(
                            f"Non-JSON response {response.status_code}"
                        ),
                        countdown=2 ** self.request.retries,
                    )
                raise self.retry(
                    exc=RuntimeError(
                        f"Service error {response.status_code} code={_code(body)}"
                    ),
                    countdown=30,
                )

            # 4xx: error del cliente -> NO reintentar
            if 400 <= response.status_code < 500:
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                code = _code(body)
                _persist_failure(attempt_id, code)
                return {"status": "failed", "code": code}

            # 2xx: éxito
            response.raise_for_status()
            analysis_id = response.json()["analysis_id"]

            result = client.get(f"{ANALYZE_URL}/{analysis_id}", timeout=10.0)
            result.raise_for_status()
            payload = result.json()
            _persist_result(attempt_id, payload)
            return {"status": "completed", "analysis_id": analysis_id}
    except SoftTimeLimitExceeded:
        _persist_failure(attempt_id, "WORKER_TIMEOUT")
        raise
    finally:
        files["audio"][1].close()
        if reference_handle is not None:
            reference_handle.close()
```

Notas:
- `autoretry_for` cubre errores de red/transporte con backoff exponencial + jitter.
- `429` y `5xx` se reintentan explícitamente; `4xx` **nunca** se reintenta.
- `soft_time_limit=330` > read=300: deja margen para que el timeout HTTP gane.
- El `POST` es idempotente por `attempt_id`: un reintento no duplica trabajo.

## 7. Checklist de integración para Core (10 ítems)

1. [ ] `SINGING_SERVICE_URL=http://singing-service:5000` en el compose del Core y en el worker.
2. [ ] `docker compose exec core-api curl -fsS http://singing-service:5000/health` → 200.
3. [ ] `POST` envía `audio`, `attempt_id`, `routine_id` y `mode` (multipart).
4. [ ] `mode=comparative` envía `reference_audio` (o `reference_notes`).
5. [ ] Timeouts `connect=5`, `read=300` configurados en el cliente HTTP.
6. [ ] `4xx` → marcar intento `failed` con `detail.code`; **sin reintento**.
7. [ ] `429`/`5xx`/`ConnectionError` → reintento con backoff (máx. 3).
8. [ ] `GET /analyze/{id}` y persistencia de `scores`, `metrics`, `segments`, `feedback`.
9. [ ] El código tolera `null` en `pitch.reference`, `pitch_accuracy`,
       `average_cent_deviation` y `rhythm_accuracy`.
10. [ ] `bash singing-service/integration/verify_handoff.sh` → `4/4 checks OK` y
        reintento con el mismo `attempt_id` devuelve el mismo `analysis_id`.
