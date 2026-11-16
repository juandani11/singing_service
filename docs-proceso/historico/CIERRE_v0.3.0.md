# CIERRE_v0.3.0 — Sprint 1 completo

> `singing-service` v0.3.0 · rama `sprint1` · tag annotated `v0.3.0` → **`0016e2e`**
> Fecha: 2026-11-16 · 115 tests por defecto + 3 integración (118) · 98 % · ruff OK · HANDOFF OK.

## 1. Git

```
$ git log --oneline -5
0016e2e chore(singing-service): release v0.3.0 — Sprint 1 completo
b0d39df docs: cerrar deuda documental Sprint 1 (ALCANCE, históricos, backlog)
e004402 docs: requisitos base de Obsidian (markdown, sin .obsidian/ ni .eap)
ed29ac1 feat(singing-service): HU-S1-04 FastDTW cableado en comparative (v0.3.0-dev)
432d926 fix(singing-service): cerrar issues HU-S1-01 — test_5xx, fixture Docker, latencia rhythm_eval

$ git tag -l
v0.2.2
v0.2.3
v0.3.0

$ git rev-parse v0.2.2^{commit} v0.2.3^{commit} v0.3.0^{commit}
c83615424958f90cacd3885eb59109e547ee4dc9
f744a8e18e7dac14bb0e6b7d5dbf36258efab7be
0016e2e65266ea6086e8c50253932497668e5e8d
```

`v0.3.0` se creó cuando `HEAD == 0016e2e`; este `CIERRE` es un commit de docs
posterior y el tag permanece en el commit de release.

## 2. CHANGELOG `[0.3.0]`

```markdown
## [0.3.0] — 2026-11-16

### Añadido
- GET /ready (readiness: warmup, shutting_down, ffmpeg_unavailable).
- GET /version (version, git_sha, build_time, python, ffmpeg, fastapi, librosa).
- app_state + lifespan con self-test de arranque y flag shutting_down.
- Dockerfile ARG/ENV GIT_SHA/BUILD_TIME; compose build.args.
- Warm-up de librosa.pyin en lifespan (sine 440 Hz en memoria) para mitigar el JIT.
- SKIP_WARMUP (default false) para omitir el warm-up.
- /health checks.warmup ({"ok": bool, "duration_ms": float|null}), aditivo.
- rhythm_eval real: beat_track (tempo, hop 960 = 60 ms) + onset_detect(wait=5)
  + filtro del onset artificial <50 ms. Downsamples a 8 kHz descartado.
- rhythm_accuracy deja de ser siempre null (número si hay onsets).
- Warm-up extendido: beat_track/onset_detect + SKIP_WARMUP_BEAT;
  /health checks.rhythm_warmup; log warmup_beat_track_completed.
- Campos aditivos: scores.ritmo, metrics.estimated_tempo_bpm,
  metrics.onset_count, metrics.onset_stability, metrics.tempo_deviation_bpm,
  timings.rhythm_ms, tempo_bpm (form).
- FastDTW (align_frames) cableado en mode=comparative; fallback align_by_time.
- metrics.alignment_method ("fastdtw" | "time") y timings.align_ms
  (aditivos; dtw_ms se mantiene como alias).
- MASTmelody pitch_accuracy 20.7→44.4; average_cent_deviation 153.9→92.9;
  offset 200 ms alineado (>80). Calibración de umbrales: HU-S4-XX.
- Tests de integración (@pytest.mark.integration) para MASTmelody y worker 5xx;
  pytest por defecto 115; pytest -m integration 3 (local) / 1+2 skipped (Docker).
- tests/test_hu_s1_02.py (9), test_hu_s1_03.py (8), test_hu_s1_01.py (13),
  test_hu_s1_04.py (5); total 115 por defecto + 3 integración (118).

### Cambiado
- settings.version 0.2.0 → 0.3.0.
- /health ahora async def + run_in_threadpool (mismo shape + checks.warmup y checks.rhythm_warmup).

### Documentación
- docs/celery-contract.md §2/§3/§4/§4.1; docs/USAGE.md; docs/ARCHITECTURE.md §6.1/§6.2/§7;
  Docs/scoring.md §Ritmo/§Feedback/FastDTW; docs/SPRINT1_BACKLOG.md;
  CIERRE_HU_S1_01.md §Limitaciones conocidas.
- Docs/ALCANCE_SINGING_SERVICE.md nuevo (mapeo Sprint 0 local = S0–S5; sprint1 = post-MVP/calidad;
  RF docx↔Obsidian; extensiones; HUs; API; límites Core/Frontend).
- 5 históricos con banner HISTÓRICO v0.2.x (HANDOFF_CORE, MENSAJE_CORE,
  INDEX_DOCUMENTADOR, ESTADO_ACTUAL, Docs/integracion-core).
- Docs/Obsidian/ commiteado (50 .md; .obsidian/ y .eap ignorados).
- docs/SPRINT1_BACKLOG.md actualizado (HU-S1-01/02/03/04/06 ✅, HU-S1-09/10, pendientes).
- CIERRE_BATCH_DOCS.md (batch de deuda documental).
```

## 3. Snapshot OpenAPI

```
version 0.3.0
paths /api/v1/analyze, /ready, /version
metrics rhythm_accuracy, estimated_tempo_bpm, onset_count, onset_stability,
        tempo_deviation_bpm, alignment_method
scores.ritmo True
timings.align_ms True
tempo_bpm form True
```

`pytest tests/ -k "snapshot or openapi" -v` → **2 passed**.

## 4. Verificación

```
$ pytest -q
115 passed, 3 deselected

$ pytest -q -m integration
3 passed, 115 deselected

$ ruff check .
All checks passed!

$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 5. Sprint 1 cerrado

| HU | Estado | Commit | Impacto |
|---|---|---|---|
| HU-S1-01 (rhythm) | ✅ | `88273a8` + `432d926` | `rhythm_accuracy` ≠ null; MASTmelody 72.7 |
| HU-S1-02 (`/ready`, `/version`) | ✅ | `9ac255b` | Observabilidad K8s |
| HU-S1-03 (warm-up) | ✅ | `70ab517` | Primer request 10.2 s → 345 ms |
| HU-S1-04 (FastDTW) | ✅ | `ed29ac1` | `pitch_accuracy` 20.7 → 44.4; offset 100 |

## 6. Confirmaciones

- Tags **v0.2.2** (`c836154`) y **v0.2.3** (`f744a8e`) intactos; **v0.3.0** (`0016e2e`) nuevo.
- `core-api/` intacto (no existe); lógica de `app/` intacta; solo CHANGELOG + snapshot + tag.
- 115+3 tests; 98 %; ruff OK; HANDOFF 4/4.

## 7. Para Core

> **Usar `v0.3.0`.** Mismos BREAKING que `v0.2.3` + aditivos: ritmo
> (`rhythm_accuracy`, `estimated_tempo_bpm`, `onset_count`, `onset_stability`,
> `tempo_deviation_bpm`, `scores.ritmo`, `tempo_bpm` form field),
> `alignment_method`, `align_ms`, `/ready`, `/version` y warm-up.
