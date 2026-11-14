# Guía de Swagger / OpenAPI — singing-service

## 1. Acceder

| Recurso | URL |
|---|---|
| Swagger UI | `http://localhost:5000/docs` |
| ReDoc | `http://localhost:5000/redoc` |
| OpenAPI JSON | `http://localhost:5000/openapi.json` |

Verificado:

```bash
curl -s http://localhost:5000/docs | grep -o '<title>[^<]*'
# <title>SyncDance AI — singing-service - Swagger UI
curl -o /dev/null -s -w "%{http_code}\n" http://localhost:5000/redoc
# 200
```

## 2. Autenticación

**No hay autenticación.** El servicio vive en la red interna de Docker y no se
publica fuera. No se envía `Authorization` ni API key. Si en el futuro se expone,
debe añadirse un proxy/mTLS en el Core (fuera del alcance de v0.2.0).

## 3. Probar `/analyze` desde Swagger UI

1. Abrir `http://localhost:5000/docs`.
2. Desplegar **POST /api/v1/analyze**.
3. Pulsar **Try it out**.
4. En el campo `audio`, pulsar **Choose File** y seleccionar un
   WAV/M4A/MP3/AAC/OGG.
5. Completar:
   - `attempt_id`: p. ej. `swagger-1`
   - `routine_id`: p. ej. `routine-9`
   - `mode`: `absolute` (o `comparative`)
   - `reference_audio`: sólo si `mode=comparative`
6. **Execute**.
7. La respuesta será `202`:

```json
{"analysis_id": "…", "status": "completed", "mode": "absolute"}
```

8. Copiar `analysis_id`, desplegar **GET /api/v1/analyze/{analysis_id}**, pegarlo y
   **Execute** para ver el `AnalysisResult`.

> El campo se llama **`audio`** (no `file`). Si se usa `file`, Swagger devuelve
> `422 Field required`.

## 4. Leer los schemas

En la sección **Schemas** de Swagger UI:

- `AcceptedResponse`: `{analysis_id, status, mode}`.
- `AnalysisResult`: `analysis_id`, `attempt_id`, `routine_id`, `status`, `mode`,
  `algorithm_version`, `duration_sec`, `pitch`, `segments`, `scores`, `metrics`,
  `feedback`, `timings`.
- `PitchCurves`: `student`, `reference` (nullable), `hop_ms`.
- `Metrics`: `pitch_stability_cents`, `mean_pitch_hz`, `voiced_ratio`,
  `pitch_accuracy` (nullable), `rhythm_accuracy` (nullable), `average_cent_deviation`
  (nullable).
- `Segment`: `start`, `end`, `type` (`out_of_tune`/`no_voice`), `expected_note`,
  `sung_note`, `delta_cents`, `severity`.
- `FeedbackItem`: `code`, `message`.
- `Timings`: `preprocess_ms`, `pitch_ms`, `dtw_ms`, `scoring_ms`.

Los ejemplos de request/response están en el propio OpenAPI (`responses` de cada
operación).

## 5. Exportar OpenAPI

```bash
curl http://localhost:5000/openapi.json > openapi.json
```

Verificado: el archivo resultante pesa **13.293 bytes** (OpenAPI 3.1.0) e incluye
3 operaciones (`POST /api/v1/analyze`, `GET /api/v1/analyze/{analysis_id}`,
`GET /health`), tags `Análisis`/`Salud`/`Sistema` y ejemplos.

## 6. Generar un cliente

Con `openapi-generator-cli` vía Docker (no requiere instalar Java):

```bash
# Python
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate \
  -i /local/openapi.json \
  -g python \
  -o /local/clients/python \
  --additional-properties=packageName=syncdance_singing

# TypeScript (fetch)
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate \
  -i /local/openapi.json \
  -g typescript-fetch \
  -o /local/clients/ts
```

En Windows PowerShell, usar `${PWD}` o la ruta absoluta:

```powershell
docker run --rm -v "${PWD}:/local" openapitools/openapi-generator-cli generate `
  -i /local/openapi.json -g python -o /local/clients/python
```

> El generador no se ejecutó en esta auditoría (no está instalado en el entorno);
> el comando es el estándar de `openapi-generator-cli`. El `openapi.json` sí se
> descargó y validó.

## 7. Limitaciones de Swagger UI

- **Multipart grandes:** Swagger UI carga el archivo en memoria del navegador. Para
  audios cercanos a 50 MB es más fiable usar `curl` o `requests`.
- **Sin auth:** no hay botón *Authorize*; es correcto para v0.2.0.
- **CORS:** Swagger UI se sirve desde el mismo origen (`localhost:5000`), no hay
  problemas de CORS.
- **`reference_notes`:** es un campo de texto JSON; en Swagger UI debe pegarse como
  string JSON válido.
- **Campos futuros:** `include_contour` y `tempo_bpm` aparecen como no implementados;
  v0.2.0 los ignora.

## 8. Troubleshooting

| Síntoma | Causa | Solución |
|---|---|---|
| `422 Field required` con `file` | campo incorrecto | usar `audio` |
| `413` al subir desde Swagger | archivo > 50 MB | comprimir o usar curl/requests |
| `/docs` no carga | servicio caído | `curl /health`; `docker compose logs` |
| OpenAPI sin ejemplos | imagen Docker vieja | `docker compose build singing-service` |
