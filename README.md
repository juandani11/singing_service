# App-SyncDance

Monorepo de SyncDance AI. Microservicio de análisis de canto (`singing-service`).

## Cómo correr
```bash
cd singing-service
docker compose up -d
curl http://localhost:5000/health
```

## Documentación

| Tipo | Ubicación |
|---|---|
| Código | `singing-service/` |
| Docs del servicio | `singing-service/docs/` (arquitectura, contrato, USAGE) |
| Docs base del proyecto | `Docs/` (requisitos, plan, Obsidian, scoring) |
| Proceso | `docs-proceso/` (auditorías, cierres, handoffs) |
| Índice documentador | `docs-proceso/handoff/INDEX_DOCUMENTADOR.md` |
| Mensaje Core | `docs-proceso/handoff/MENSAJE_CORE.md` |

## Releases

- **v0.4.0** — production-ready (Sprint 2)
- **v0.3.0** — Sprint 1 (rhythm, FastDTW, /ready, /version)
- **v0.2.3** — docs-only
- **v0.2.2** — Sprint 0 cierre
