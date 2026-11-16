# CIERRE_v0.4.0 — Sprint 2 completo (production-ready)

> `singing-service` v0.4.0 en rama `sprint2` → tag annotated **`v0.4.0` = `ddfe6ef`**
> Fecha: 2026-11-16 · 138 tests por defecto + 3 integración (141) · 98 % · ruff OK · HANDOFF OK.

## 1. Git

```text
$ git log --oneline -6
ddfe6ef chore(singing-service): release v0.4.0 — Sprint 2 (production-ready)
8d10789 chore(singing-service): HU-S1-08 migrar TestClient a httpx2 (v0.4.0-dev)
4343068 perf(singing-service): HU-S2-XX cache de ritmo + warm-up de pulsos (v0.4.0-dev)
9caa08f feat(singing-service): HU-S1-09 pitch_contour downsample 10 Hz (v0.4.0-dev)
5278a2b feat(singing-service): HU-S1-05 timeout interno + /metrics Prometheus (v0.4.0-dev)
5c1366d docs: MENSAJE_CORE actualizado a v0.3.0 (aditivos ritmo/alignment)

$ git tag -l
v0.2.2
v0.2.3
v0.3.0
v0.4.0

$ git rev-parse v0.4.0^{commit}
ddfe6ef8d0285823d7ff60704eb7a17a993bcc57
$ git rev-parse HEAD
ddfe6ef8d0285823d7ff60704eb7a17a993bcc57
```

## 2. CHANGELOG `[0.4.0]`

```markdown
## [0.4.0] — 2026-11-16

### Añadido

- Timeout interno configurable (HU-S1-05): `PYIN_TIMEOUT_SECONDS` (default 120 s,
  `0 < x < 300`) para `librosa.pyin` y `ALIGN_TIMEOUT_SECONDS` (default 30 s,
  `0 < x < 120`) para FastDTW. Al vencer responde **504 `ANALYSIS_TIMEOUT`** con
  `request_id`; el semáforo se libera. Limitación: el hilo huérfano no es
  interrumpible (librosa/FastDTW) y termina por su cuenta.
- `GET /metrics` Prometheus (sin auth; red interna): `analysis_requests_total`
  (`mode`, `status`), `analysis_duration_seconds` (`mode`), `pitch_duration_seconds`,
  `align_duration_seconds` (`method`), `rhythm_duration_seconds`, `active_requests`
  y `analysis_timeouts_total` (`phase`).
- `prometheus-client==0.21.0` en `requirements.txt`.
- `pitch_contour` opcional (`include_contour=true`, HU-S1-09): downsample a ~10 Hz
  (`step=3` con hop 32 ms → 96 ms, ~10.42 Hz), máximo 6000 puntos; `student` y
  `reference` con `t`, `f0`, `note`, `voiced`. Aditivo; `null` por defecto.
- Cache de ritmo por hash de audio (HU-S2-XX): `app/services/rhythm_cache.py`,
  TTL 1 h, máximo 128 entradas; segunda llamada ~0 ms.
- Warm-up de ritmo con pulsos 120 BPM (HU-S2-XX): el primer request con onsets
  baja de ~4.0 s a ~0.26 s.
- Migrado `TestClient` de `httpx` a `httpx2==2.16.2` (HU-S1-08): `pytest -v` sin
  `StarletteDeprecationWarning`.
- `tests/test_hu_s1_05.py` (8), `tests/test_hu_s1_09.py` (7) y
  `tests/test_hu_s2_xx.py` (8); total **138 por defecto + 3 integración (141)**.
- `ANALYSIS_TIMEOUT` (504) documentado en OpenAPI (`responses` de `/analyze`).

### Cambiado

- Latencia de `rhythm_eval` (HU-S2-XX): el “3.8 s” de versiones anteriores era el
  **JIT frío del primer request**, no el coste por audio. En régimen estable
  (warm-up completo): MASTmelody 4.78 s → **~8–19 ms**; 60 s → **~45–80 ms**;
  5 min → **~250–400 ms**. SLO <2 s cumplido. B (hop 1024) y C (downsample
  11–12 kHz) rechazadas por desviar el tempo >2 BPM.

### Documentación

- `docs/celery-contract.md` §3 (timeouts internos y latencia), §5 (504
  `ANALYSIS_TIMEOUT`) y §2/§4 (`include_contour`/`pitch_contour`);
  `docs/ARCHITECTURE.md` §1/§2/§3/§6/§6.2/§6.3/§7; `docs/USAGE.md` (`/metrics`,
  tabla de errores y ejemplo de `include_contour`); `docs/SPRINT2_BACKLOG.md`
  (HU-S1-05 ✅, HU-S1-09 ✅, HU-S2-XX ✅, HU-S1-08 ✅);
  `Docs/ALCANCE_SINGING_SERVICE.md` (Sprint 2).
```

## 3. Sprint 2 — 4/4 HUs

| HU | Commit | Impacto |
|---|---|---|
| HU-S1-05 | `5278a2b` | Timeout (504 `ANALYSIS_TIMEOUT`) + `/metrics` Prometheus |
| HU-S1-09 | `9caa08f` | `pitch_contour` a 10 Hz (702 KB para 10 min) |
| HU-S2-XX | `4343068` | Cache ritmo (0 ms hit) + warm-up (3994 ms → 262 ms) |
| HU-S1-08 | `8d10789` | `httpx2`, cero warnings de deprecación |

## 4. Verificación final

```text
$ pytest --no-cov
138 passed, 3 deselected, 1 warning in 22.80s

$ pytest -m integration --no-cov
3 passed, 138 deselected in 4.93s

$ ruff check .
All checks passed!

$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

Cobertura: **98 %** (`app/core/config.py` 100 %, `app/main.py` 100 %,
`app/core/store.py` 93 %).

Docker (imagen v0.4.0):

```text
$ docker compose exec -T singing-service python -m pytest --no-cov
138 passed, 3 deselected, 1 warning in 28.78s

$ docker compose exec -T singing-service python -m pytest -m integration --no-cov
1 passed, 2 skipped, 138 deselected in 1.27s

$ curl -s http://localhost:5000/version
{"version":"0.4.0", ...}
```

Snapshot OpenAPI verificado: `version: "0.4.0"`, `include_contour`,
`pitch_contour`, `ANALYSIS_TIMEOUT` (504) y `/metrics`.

## 5. Tags

```text
v0.2.2  c83615424958f90cacd3885eb59109e547ee4dc9
v0.2.3  f744a8e18e7dac14bb0e6b7d5dbf36258efab7be
v0.3.0  0016e2e65266ea6086e8c50253932497668e5e8d
v0.4.0  ddfe6ef8d0285823d7ff60704eb7a17a993bcc57
HEAD    ddfe6ef8d0285823d7ff60704eb7a17a993bcc57
```

## 6. Para Core

> **Usar `v0.4.0`.** Mismos BREAKING acumulados + aditivos de Sprint 2:
> `ANALYSIS_TIMEOUT` (504), `/metrics`, `pitch_contour` + `include_contour`,
> cache de ritmo y warm-up de pulsos. El contrato de `/analyze` no cambia.

## 7. Confirmaciones

- **`core-api/` intacto:** no existe en este workspace y no se tocó nada fuera de
  `singing-service/` y `Docs/`.
- **Lógica de análisis intacta:** solo se bumpó `settings.version` (0.4.0), se
  actualizaron los ejemplos de `/health`/`/version`, la descripción de
  `include_contour` y las aserciones de versión en tests. `pitch.py`, `align.py`,
  `compare.py`, `scoring.py`, `feedback.py` y `rhythm_eval.py` sin cambios.
- **Tag `v0.3.0` intacto** en `0016e2e`.
- **Sin merge a `master`:** el merge se hará después de la sesión con Core.

## 8. Corrección de documentación de latencia

Se corrigieron las menciones antiguas a “~4 min para 10 min” y “MASTmelody ~4 s”
en `docs/celery-contract.md` §3. La nota vigente distingue **JIT frío del primer
request** (mitigado por el warm-up de pulsos) del **régimen estable** (8–19 ms
para MASTmelody, 45–80 ms para 60 s, 250–400 ms para 5 min).
