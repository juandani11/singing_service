# integration/ — Handoff Core ↔ singing-service

Scripts ejecutables para que el equipo de **Core API** integre la tarea Celery de
`audio_queue` sin adivinar el contrato.

Contrato completo: [`../docs/celery-contract.md`](../docs/celery-contract.md).

## Requisitos

- Python 3.12+ (probado con 3.14).
- `pip install -r integration/requirements.txt` (`requests`, `pytest`, `numpy`).
- `ffmpeg` en `PATH` (para generar fixtures m4a/mp3/aac/ogg).
- Servicio levantado en `http://localhost:5000` (o `SINGING_SERVICE_URL`).
- Docker opcional (el script de verificación puede levantarlo).

## Scripts

> Ejecutar los comandos Python desde `singing-service/` (o ajustar las rutas).

### 1. Simular el worker Celery

```bash
python integration/simulate_celery_worker.py \
    --audio integration/fixtures/sine_440hz_5s.wav --mode absolute
python integration/simulate_celery_worker.py \
    --audio integration/fixtures/sine_442hz_5s.wav \
    --mode comparative --reference integration/fixtures/sine_440hz_5s.wav
```

- Lee `SINGING_SERVICE_URL` (base o URL completa; default `http://localhost:5000/api/v1/analyze`).
- Hace `POST` + `GET` del resultado, con `timeout=(5, 300)`.
- Exit: `0` (200/202), `1` (4xx), `2` (5xx o fallo de red).
- `--include-contour` se acepta pero **v1 lo ignora** (`pitch_contour` es futuro).

> **Campo multipart:** el servicio espera `audio` (simétrico con `reference_audio`).
> Se envían además `attempt_id` y `routine_id`, obligatorios en el contrato v1.

### 2. Matriz de errores

```bash
python integration/test_error_scenarios.py
```

Verifica 8 escenarios reales (422 `INVALID_MODE`, 400 `MISSING_REFERENCE`,
413 `AUDIO_TOO_LARGE`, 413 `AUDIO_TOO_LONG`, `.txt` → 400 `UNSUPPORTED_FORMAT`,
`.txt` renombrado `.wav` → 400 `INVALID_AUDIO`, sin `audio` → 422, servicio caído →
`ConnectionError`). Exit 0 si todos pasan.

### 3. Generar fixtures

```bash
python integration/generate_fixtures.py
python integration/generate_fixtures.py --include-long   # añade long_11min.wav
```

Genera en `integration/fixtures/` (ignorado por git): WAV 44.1 kHz 5 s (440 y 442 Hz),
M4A/MP3/AAC/OGG, silencio 3 s y, con `--include-long`, un WAV de 11 min a 8 kHz
(10.6 MB) para `AUDIO_TOO_LONG`.

### 4. Verificación end-to-end

Desde la raíz del monorepo:

```bash
bash singing-service/integration/verify_handoff.sh
```

Levanta el servicio (si hay Docker), espera `/health` 200 (60 s), genera fixtures,
corre la simulación en ambos modos y la matriz de errores. Imprime `X/4 checks OK`.

## Limitaciones de plataforma

- `verify_handoff.sh` requiere **Git Bash o WSL** en Windows. En PowerShell nativo no
  funciona (es un script bash).
- Alternativa en Windows: correr `python integration/simulate_celery_worker.py` y
  `python integration/test_error_scenarios.py` individualmente.
- Los scripts Python (`simulate_celery_worker.py`, `test_error_scenarios.py`,
  `generate_fixtures.py`) **sí** funcionan en PowerShell nativo.

## Códigos de error y acción del Core

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
| 503 | — | `/health` degradado (sin `detail.code`) | No encolar; alertar |
| — | `ConnectionError` | servicio caído / red | **Reintentar con backoff** |

> **Nota de wire real.** El servicio **no** emite `INTERNAL_ERROR` ni `SERVICE_DEGRADED`;
> son etiquetas del Core. Un **5xx sin JSON parseable** es recuperable: reintentar con
> backoff (máx. 3); si persiste, marcar `Attempt` como fallido y alertar.
> `VALIDATION_ERROR` es la etiqueta del Core para la lista de validación de FastAPI.

## Configurar `SINGING_SERVICE_URL`

`docker-compose.yml` del Core:

```yaml
services:
  core-api:
    environment:
      SINGING_SERVICE_URL: http://singing-service:5000
```

Celery (worker):

```python
import os
SINGING_SERVICE_URL = os.environ["SINGING_SERVICE_URL"]  # http://singing-service:5000
```

La URL de análisis es `{SINGING_SERVICE_URL}/api/v1/analyze`. Si el Core usa otro
nombre de variable, actualizar el documento, no el servicio.
