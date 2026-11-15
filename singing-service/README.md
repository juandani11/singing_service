# singing-service — SyncDance

Microservicio **stateless** de análisis de canto (pitch, ritmo y feedback) para
SyncDance AI. Recibe un audio, devuelve métricas y feedback; no gestiona auth ni
persiste (la fuente de verdad es el Core).

**Estado:** Sprint 1 en curso (**v0.3.0-dev**). Base v0.2.3 (Sprint 0 cerrado).

## Quick start

```bash
docker compose up -d --build singing-service
curl http://localhost:5000/health
```

```bash
curl -X POST http://localhost:5000/api/v1/analyze \
  -F "audio=@intento.wav" \
  -F "attempt_id=demo-1" \
  -F "routine_id=demo" \
  -F "mode=absolute"
```

## Documentación

| Documento | Propósito |
|-----------|-----------|
| [docs/USAGE.md](docs/USAGE.md) | Manual de uso paso a paso (curl, Python, Celery) |
| [docs/SWAGGER_GUIDE.md](docs/SWAGGER_GUIDE.md) | Guía de Swagger UI / OpenAPI |
| [docs/celery-contract.md](docs/celery-contract.md) | Contrato con Core (multipart, errores, tarea Celery) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura interna |
| [docs/SPRINT1_BACKLOG.md](docs/SPRINT1_BACKLOG.md) | Siguiente sprint |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Problemas comunes |
| [integration/README.md](integration/README.md) | Kit de integración para Core |
| [CHANGELOG.md](CHANGELOG.md) | Historia de versiones |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir |
| [HANDOFF_CORE.md](../HANDOFF_CORE.md) | Acta de handoff (histórico) |
| [CONSISTENCY_FIX.md](../CONSISTENCY_FIX.md) | Fix de consistencia (histórico) |
| [Plan de implementación](../Docs/plan-implementacion-singing-service.md) | Plan del proyecto |

## Stack

FastAPI (≥0.115), Uvicorn, librosa, ffmpeg-python, soundfile, numpy, scipy.

## Calidad

**92 tests**, **97 % de cobertura**, `ruff` OK. `verify_handoff.sh` → `HANDOFF OK`.
