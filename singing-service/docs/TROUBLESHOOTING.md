# Troubleshooting — singing-service

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `422 Field required` en `/analyze` | Se envió `file` en vez de `audio` | Usar `audio` (ver [`celery-contract.md`](celery-contract.md) §2) |
| `400 INVALID_AUDIO` | Audio corrupto o M4A mal decodificado | Verificar con `ffprobe`; reconstruir imagen (`docker compose build --no-cache singing-service`) |
| `400 UNSUPPORTED_FORMAT` | Extensión no permitida | Usar `wav/m4a/mp3/aac/ogg` |
| `413 AUDIO_TOO_LARGE` | > 50 MB | Comprimir en Flutter antes de subir |
| `413 AUDIO_TOO_LONG` | > 600 s | Truncar o dividir el audio |
| `503` en `/health` | FFmpeg no instalado o librosa no carga | `docker compose build --no-cache singing-service` y revisar logs |
| Primer request tarda 10+ s | JIT frío de numba | Warm-up (HU-S1-06); timeout de Celery ≥ 300 s |
| `verify_handoff.sh` falla en Windows | Requiere Git Bash/WSL | Ver [`../integration/README.md`](../integration/README.md) §Limitaciones de plataforma |
| Tests fallan por snapshot OpenAPI | Rename de campo no regeneró snapshot | Regenerar `tests/snapshots/openapi_v1.json` tras cambios de contrato |
| `429 SERVICE_BUSY` | 2 análisis simultáneos ya en curso | Reintentar con backoff (15–30 s) |
| `400 "Invalid HTTP request received."` (text/plain) | `Content-Length` falso o cliente HTTP malformado | uvicorn lo rechaza antes del middleware; no hay `X-Request-ID`. Usar un cliente HTTP válido (curl/requests/httpx) |
| `500 FFMPEG_NOT_FOUND` | FFmpeg no está en el PATH del contenedor/host | Instalar FFmpeg o definir `FFMPEG_BINARY` |

## Cómo debuggear un audio problemático

### 1. Inspeccionar el contenedor/formato

```bash
ffprobe -v error -show_format -show_streams intento.m4a
```

Buscar `codec_name`, `sample_rate`, `channels`, `duration` y que exista un stream de
audio (`codec_type=audio`).

### 2. Verificar que FFmpeg puede decodificarlo

```bash
ffmpeg -v error -i intento.m4a -f null -
```

Si falla aquí, el servicio devolverá `400 INVALID_AUDIO` o `400 UNSUPPORTED_FORMAT`.
Probar una conversión explícita:

```bash
ffmpeg -y -i intento.m4a -ar 16000 -ac 1 intento_16k.wav
```

### 3. Estadísticas de la señal (opcional, requiere sox)

```bash
sox intento_16k.wav -n stat
```

Revisar `Maximum amplitude` (silencio/volumen), `RMS amplitude` y duración. Si el audio
está en silencio, el servicio reportará `voiced_ratio≈0` y `NO_VOICE`.

### 4. Extraer un clip de 5 s para reproducir el fallo

```bash
# desde el segundo 10, 5 segundos, sin recomprimir
ffmpeg -ss 00:00:10 -i intento.wav -t 5 -c copy clip.wav

# si el contenedor no acepta -c copy, recomprimir a PCM
ffmpeg -ss 00:00:10 -i intento.m4a -t 5 -ar 16000 -ac 1 clip.wav
```

### 5. Reproducir contra el servicio

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@clip.wav" \
  -F "attempt_id=debug-1" \
  -F "routine_id=debug" \
  -F "mode=absolute"
```

### 6. Revisar logs y health

```bash
docker compose logs -f singing-service
curl http://localhost:5000/health
```

Los logs emiten una línea JSON por evento (`analysis_accepted`, `analysis_failed`,
`analysis_not_found`, `analysis_idempotent_hit`). Correlacionar por `attempt_id`.

### 7. Problemas de decodificación persistentes

- Reconstruir la imagen sin caché: `docker compose build --no-cache singing-service`.
- Verificar la versión de FFmpeg dentro del contenedor:
  `docker compose exec singing-service ffmpeg -version`.
- Si el host define `FFMPEG_BINARY`, confirmar que apunta a un binario válido.
