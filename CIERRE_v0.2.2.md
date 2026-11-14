# Cierre v0.2.2 — singing-service

## Estado

✅ **LISTO PARA INTEGRACIÓN CON CORE**

## Versión

- **Tag:** `v0.2.2` (annotated; tag object
  `fdad4cc5dc5c9dd2576e375e2bfdbe431864e71c`).
- **Commit:** `1b9271bc22db876416772893afc48ca753600a05` (release commit).
- **Fecha:** 2026-11-14T16:20:37-04:00.
- **Fingerprint (respaldo):**
  `821a796d9f6e27e49b1a22c35319ba0fe227600ed90c5defb4b05bece31e92ae`
  (árbol `singing-service/`, excluye `.venv`, caches,
  `singing-service/integration/fixtures` y `CHANGELOG.md`).

## Cómo obtener esta versión

```bash
git clone <repo-url>
cd App-SyncDance
git checkout v0.2.2
cd singing-service
docker compose up -d singing-service
bash integration/verify_handoff.sh   # debe dar HANDOFF OK
```

Verificación de integridad: `git rev-parse v0.2.2^{commit}` debe devolver
`1b9271bc22db876416772893afc48ca753600a05`. `git rev-parse v0.2.2` devuelve el
objeto anotado `fdad4cc5dc5c9dd2576e375e2bfdbe431864e71c`.

## Calidad

- **Tests:** 83 passed (97 % cobertura).
- **Linter:** `ruff check .` → All checks passed.
- **Verificación:** `bash singing-service/integration/verify_handoff.sh` → **4/4 HANDOFF OK**.
- **Casos límite:** 15/15 sin crashes (auditoría v0.2.0).
- **Concurrencia:** 15/15 (5×1 min ×3), p95 ≈ 25 s.

## Contrato

- Endpoint: `POST /api/v1/analyze` (multipart `audio`, `mode=absolute|comparative`).
- Modos: `absolute` (sin referencia), `comparative` (con `reference_audio`).
- Formatos: wav, m4a, mp3, aac, ogg.
- Límites: 50 MB, 600 s.
- Headers: `X-Request-ID` en todas las respuestas (aplicación); `request_id` en bodies
  de error y `/health`.
- Códigos: 200, 202, 400, 413, 422, 500, 503.
- Docs: `singing-service/docs/celery-contract.md`,
  `singing-service/docs/USAGE.md`, `singing-service/docs/SWAGGER_GUIDE.md`.

## BREAKING changes acumulados (para Core)

1. `file` → `audio`
2. `mode=mock|real` → `mode=absolute|comparative`
3. `reference_file` → `reference_audio`
4. `INVALID_MODE` 400 → 422
5. `FILE_TOO_LARGE`/`DURATION_TOO_LONG` → `AUDIO_TOO_LARGE`/`AUDIO_TOO_LONG`
6. `pitch.reference` nullable
7. `severity` y timestamps en `segments[]`, no en `feedback[]`
8. `X-Request-ID` header nuevo
9. `UNHANDLED_ERROR` code nuevo (500)

## P1 diferidos a hardening P0 (Sprint 1)

- `/version` (404) → H-07
- `/ready` (404) → H-04
- V-01 (uvicorn rechaza `Content-Length` inválido sin `X-Request-ID`) → documentado, no fix
- Semáforo de concurrencia (H-01)
- Timeout request (H-03)
- Graceful shutdown (H-04)
- Matriz adversarial 20 casos (H-09)

## Pendiente de Core (no de singing-service)

1. Tarea Celery en `audio_queue` que llame a
   `http://singing-service:5000/api/v1/analyze`.
2. Propagar `X-Request-ID` desde Flutter (o generar UUID).
3. Mapear `UNHANDLED_ERROR` y 5xx sin JSON a reintento con backoff.
4. Configurar `SINGING_SERVICE_URL` en compose/K8s.
5. Correr `verify_handoff.sh` contra su worker.

## Handoff ejecutable

- `singing-service/integration/simulate_celery_worker.py` — simulador de worker.
- `singing-service/integration/test_error_scenarios.py` — 9/9 PASS.
- `singing-service/integration/generate_fixtures.py` — fixtures con ffmpeg.
- `singing-service/integration/verify_handoff.sh` — 4/4 HANDOFF OK.
- `singing-service/docs/celery-contract.md` §6 — tarea Celery real (copiable).

## Siguiente paso

Sesión de integración de 30 min. Core corre
`bash singing-service/integration/verify_handoff.sh` contra su worker y se valida el
primer intento end-to-end.

## Verificación de cierre (resumen)

| # | Comando | Resultado |
|---|---|---|
| 1 | `pytest -v` | 83 passed, 97 % |
| 2 | `pytest --cov=app.core --cov=app.main --cov-report=term-missing` | 83 passed, 97 % |
| 3 | `ruff check .` | All checks passed |
| 4 | `bash singing-service/integration/verify_handoff.sh` | 4/4 HANDOFF OK |
| 5 | `grep files={'file'` | 0 referencias |
| 6 | `grep -c X-Request-ID` | contrato 3, USAGE 6 |
| 7 | `grep -c UNHANDLED_ERROR` | contrato 2, USAGE 2 |
| 8 | `grep -c V-01` | contrato 1, USAGE 1 |
| 9 | `ls core-api/` | no existe |
| 10 | Links del README | 0 rotos |

## Documentos vigentes

| Documento | Propósito |
|-----------|-----------|
| `singing-service/docs/celery-contract.md` | Contrato Core (v0.2.2) |
| `singing-service/docs/USAGE.md` | Manual de consumo |
| `singing-service/docs/SWAGGER_GUIDE.md` | Guía Swagger/OpenAPI |
| `singing-service/docs/ARCHITECTURE.md` | Arquitectura interna |
| `singing-service/docs/TROUBLESHOOTING.md` | Problemas comunes |
| `singing-service/docs/SPRINT1_BACKLOG.md` | Hardening P0 (Sprint 1) |
| `singing-service/CHANGELOG.md` | Historia de versiones |
| `singing-service/CONTRIBUTING.md` | Cómo contribuir |
| `HANDOFF_CORE.md` | Handoff formal (con fingerprint) |
