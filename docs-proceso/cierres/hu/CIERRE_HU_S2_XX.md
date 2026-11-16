# CIERRE_HU_S2_XX — Optimización de latencia de `rhythm_eval`

> Rama `sprint2` (HEAD previo `9caa08f`). Tag `v0.3.0` intacto en `0016e2e`.
> Fecha: 2026-11-16 · 138 tests por defecto + 3 integración (141) · 98 % · ruff OK · HANDOFF OK.

## 1. Fase 1 — Medición baseline (real, Docker)

Entorno: imagen `singing-service`, 16 kHz, beat hop **960**, onset hop **512**,
régimen estable (JIT ya calentado). `pitch_ms` y `rhythm_ms` son de
`analyze_rhythm`; `beat_track_ms`/`onset_detect_ms` son desglose directo (misma
configuración, ejecución separada; Docker Desktop varía ±30–50 %).

| Audio | Duración | `pitch_ms` | `rhythm_ms` | `beat_track_ms` | `onset_detect_ms` | tempo | onsets |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sine 440 | 5 s | 154 | 6.3 | 2.7 | 3.6 | null | 0 |
| Sine 440 | 30 s | 394 | 41.0 | 12.2 | 28.8 | null | 0 |
| Sine 440 | 60 s | 701 | 77.7 | 36.4 | 41.3 | null | 0 |
| Pulsos 120 BPM | 60 s | 598 | 80.5 | 36.4 | 44.2 | 125.0 | 119 |
| MASTmelody | 4.78 s | 101 | 15.8 | 11.0 | 4.9 | 90.9 | 14 |
| MASTmelody ×10 | 47.8 s | 610 | 73.4 | 21.2 | 52.3 | 90.9 | 58 |

**Hallazgo clave:** el `rhythm_ms ≈ 3.8 s` del contexto **no es el coste por
audio**: es el **primer request tras arrancar**, que paga el JIT de la ruta de
onsets. Medición real con el servicio recién arrancado y 60 s de pulsos:

```text
1er POST tras restart (warm-up de sine): rhythm_ms = 3994
2do POST (steady):                       rhythm_ms = 114–151
```

El warm-up existente usaba un **sine** (sin onsets), así que `onset_detect` no
compilaba la ruta de peak-picking. En régimen estable el baseline ya está muy por
debajo del SLO (<2 s), y no hay margen para una mejora 3x de cómputo.

## 2. Fase 2 — Optimizaciones medidas

Mediana de 5 ejecuciones de `analyze_rhythm` sobre 60 s de pulsos 120 BPM y
MASTmelody 4.78 s (Docker):

| Optimización | `rhythm_ms` (60 s) | Mejora | Tempo pulsos | Tempo MAST | Onsets | Veredicto |
|---|---:|---:|---:|---:|---:|---|
| Baseline (beat 960, onset 512, 16 kHz) | 63.9 | — | 125.0 | 90.9 | 119 | — |
| **A — cache por hash** | **0 ms (hit)** | ~∞ en re-análisis | 125.0 (exacto) | 90.9 (exacto) | 119 | **✅** |
| B — hop 1024 | 47.0 | 1.36x | 117.2 (**−7.8**) | 85.2 (**−5.7**) | 119 | ❌ |
| C — downsample 11 kHz | 49.6 | 1.29x | 114.8 (**−10.2**) | 86.1 (**−4.8**) | 119 | ❌ |
| C — downsample 12 kHz | 52.8 | 1.21x | 125.0 (0) | 83.3 (**−7.6**) | 120 | ❌ |
| B+C (1024 + 11 kHz) | 36.1 | 1.77x | 129.2 (**+4.2**) | 92.3 (+1.4) | 74 (**−38 %**) | ❌ |
| **D — warm-up con pulsos** | **262 ms (1er request)** | **15.2x vs 3994 ms** | 125.0 | 90.9 | 119 | **✅** |

Detalle de B/C:
- **B** y **C** desvían el tempo >2 BPM (criterio de rechazo). No alcanzan 3x.
- **C 12 kHz** acierta el tempo en pulsos, pero falla en MASTmelody (−7.6 BPM).
- **B+C** además pierde onsets (−38 %), fuera del ±10 %.
- Las variantes no aportan una mejora 3x; el baseline ya cumple `<20 s`.

## 3. Fase 3 — Decisión

**Implementadas:**
- **A — cache en memoria por hash de audio** (`sha256(audio_bytes)[:16]` + `sr` +
  `tempo_bpm_hint`). TTL 1 h, máximo 128 entradas. Segunda llamada con el mismo
  audio/hint: `rhythm_ms = 0` y métricas idénticas. No persiste entre reinicios
  (Redis en Sprint 3+).
- **D — warm-up de ritmo con pulsos 120 BPM** en lugar de sine. Elimina el JIT de
  la ruta de onsets: primer request con onsets **3994 ms → 262 ms**. Coste: el
  warm-up sube a ~5.5 s y el startup a ~19 s (una vez).

**Rechazadas:** B (hop 1024), C (11/12 kHz) y B+C por desviar el tempo >2 BPM
(y B+C además los onsets). No se tocó `rhythm_eval.py`.

## 4. Fase 4 — Diff resumido

```text
 singing-service/CHANGELOG.md                    |  ...
 singing-service/app/api/routes/analyze.py       |  cache por hash en la fase de ritmo
 singing-service/app/main.py                     |  warm-up de ritmo con pulsos
 singing-service/docs/ARCHITECTURE.md            |  §2/§6.2/§7 (cache, warm-up, latencia)
 singing-service/docs/SPRINT2_BACKLOG.md         |  HU-S2-XX ✅
 singing-service/docs/celery-contract.md         |  §3 nota de latencia
 singing-service/app/services/rhythm_cache.py    |  NUEVO (cache TTL + LRU)
 singing-service/tests/test_hu_s2_xx.py          |  NUEVO (8 tests)
```

- `rhythm_eval.py`, `pitch.py`, `align.py`, `compare.py`, `scoring.py` y
  `feedback.py`: **sin cambios**.
- `hop_ms` del response sigue siendo **32 ms** (pitch). Los hops de ritmo son
  internos y no cambian; no se alteró el shape de `/analyze`.

## 5. Fase 5 — Verificación

### `pytest -v`

```text
tests\test_hu_s2_xx.py ........                                          [ 77%]
...
=============== 138 passed, 3 deselected, 2 warnings in 27.14s ================
```

### Integración local

```text
...                                                                      [100%]
# 3 passed
```

### Docker

```text
$ docker compose exec -T singing-service python -m pytest --no-cov
138 passed, 3 deselected, 2 warnings in 32.53s

$ docker compose exec -T singing-service python -m pytest -m integration --no-cov
1 passed, 2 skipped, 138 deselected, 1 warning in 1.66s
```

### `ruff check .`

```text
All checks passed!
```

### HANDOFF

```text
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

## 6. Medición post-optimización (real, Docker)

Servicio reiniciado (warm-up con pulsos), mismo audio de 60 s de pulsos 120 BPM:

| Escenario | `rhythm_ms` | tempo | onsets |
|---|---:|---:|---:|
| 1er POST tras restart, **antes** de D | 3994 | 125.0 | 119 |
| 1er POST tras restart, **con D** | 262 | 125.0 | 119 |
| 2º POST mismo audio (cache hit) | **0** | 125.0 | 119 |
| 3er POST mismo audio (cache hit) | **0** | 125.0 | 119 |
| Baseline estable (mediana 5×) | 63.9 | 125.0 | 119 |
| MASTmelody estable (mediana 5×) | 12.1 | 90.9 | 14 |

El SLO <2 s se cumple en el primer request (262 ms) y en régimen estable
(~64 ms). La re-analización del mismo audio es ~0 ms.

## 7. Confirmaciones

- **Contrato no roto:** no cambian endpoints, request ni shape de `AnalysisResult`.
  `pitch.hop_ms` sigue en 32 ms; los hops de ritmo son internos.
- **`core-api/` intacto:** no existe en este workspace y no se tocó nada fuera de
  `singing-service/`.
- **Tag `v0.3.0` intacto:**

```text
$ git rev-parse v0.3.0^{commit}
0016e2e65266ea6086e8c50253932497668e5e8d
```

- **Sin tag ni merge:** no se creó `v0.4.0` ni se hizo merge a `master`.

## 8. Limitaciones / seguimiento

- El cache no persiste entre reinicios; para producción multi-réplica, Redis
  (Sprint 3+).
- El warm-up de pulsos añade ~5.5 s al startup (una vez); el primer request queda
  caliente. Si el startup debe ser más corto, se puede medir un pulso más corto
  sin perder el JIT (el coste es la compilación, no la señal).
- B/C quedan documentadas como rechazadas; si en el futuro se acepta ±5 BPM, se
  podría reevaluar C 12 kHz (pero falla en MASTmelody).
- HU-S2-XX queda ✅ en `docs/SPRINT2_BACKLOG.md`; el tag `v0.4.0` se crea al final
  de Sprint 2 (HU-S1-07).
