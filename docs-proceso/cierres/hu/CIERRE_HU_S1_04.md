# CIERRE_HU_S1_04 — FastDTW cableado en `mode=comparative`

> HU-S1-04 en `sprint1`. Base `v0.2.3` (`f744a8e`). Versión de trabajo **0.3.0-dev**.
> Fecha: 2026-11-16. **115 tests por defecto + 3 integración (118), 98 %, ruff OK, HANDOFF OK.**

## 1. Diff resumido

| Archivo | Cambio |
|---|---|
| `app/api/routes/analyze.py` | `align_frames` (FastDTW) en `comparative`; fallback `align_by_time` con log `align_fastdtw_failed`; `alignment_method`; `align_ms`; `dtw_ms` alias; `_accepted` log con `align_ms`. |
| `app/schemas/analyze.py` | `Metrics.alignment_method` (`"fastdtw"`/`"time"`); `Timings.align_ms`; `dtw_ms` documentado como alias. |
| `tests/test_hu_s1_04.py` | **Nuevo**: MASTmelody (integración), offset 200 ms, sine 440/442, `MISSING_REFERENCE`, fallback. |
| `tests/snapshots/openapi_v1.json` | Regenerado (campos aditivos). |
| `docs/celery-contract.md` | §4: `alignment_method`, `align_ms`, `dtw_ms` alias; nota no-BREAKING. |
| `Docs/scoring.md` | FastDTW cableado; accuracy real amateur ~40–50; calibración HU-S4-XX. |
| `docs/ARCHITECTURE.md` | `align.py` cableado; fallback; flujo; counts 118. |
| `docs/SPRINT1_BACKLOG.md` | HU-S1-04 ✅ ejecutada; FastDTW fuera de “Sprint 2+”. |
| `CHANGELOG.md` | FastDTW, `alignment_method`, `align_ms`, 20.7→44.4; counts 115+3. |
| `README.md` / `CONTRIBUTING.md` | 115 + 3 (Docker 115 + 1 passed + 2 skipped). |

## 2. Tests y cobertura

```
$ pytest -q                 → 115 passed, 3 deselected
$ pytest -q -m integration  → 3 passed, 115 deselected
$ pytest --cov=app.core --cov=app.main --cov-report=term-missing
TOTAL 243 4 98%   (app/main.py 100%, app/core/store.py 93%)
$ ruff check .              → All checks passed!
$ bash integration/verify_handoff.sh
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
Docker: 115 passed, 3 deselected; -m integration → 1 passed, 2 skipped (fixtures MASTmelody)
```

## 3. Medición antes/después (MASTmelody, JSON real)

| Métrica | Antes (`align_by_time`) | Después (`align_frames` FastDTW) |
|---|---:|---:|
| `pitch_accuracy` | **20,7** | **44,4** |
| `average_cent_deviation` | **153,9** | **92,9** |
| `pitch_stability_cents` | 229,2 | **123,2** |
| `segments` / `out_of_tune` | 3 / 3 | 4 / 4 |
| `timings.align_ms` / `dtw_ms` | 1–2 ms | **21 ms** (17,1 ms en banco aislado) |
| `metrics.alignment_method` | — | **`"fastdtw"`** |

GET real (extracto):

```json
{"metrics": {"pitch_stability_cents": 123.2, "mean_pitch_hz": 314.3, "voiced_ratio": 0.9467, "pitch_accuracy": 44.4, "rhythm_accuracy": 72.7, "estimated_tempo_bpm": 90.9, "onset_count": 14, "onset_stability": 72.7, "tempo_deviation_bpm": null, "alignment_method": "fastdtw", "average_cent_deviation": 92.9}, "scores": {"vocal": 38, "afinacion": 44, "estabilidad": 0, "control_volumen": 62, "ritmo": 73, "silence_pct": 5}, "timings": {"preprocess_ms": 378, "pitch_ms": 5658, "rhythm_ms": 2037, "align_ms": 21, "dtw_ms": 21, "scoring_ms": 4}, "segments": [{"start": 0.16, "end": 1.056, "type": "out_of_tune", "expected_note": "C4", "sung_note": "C#4", "delta_cents": 120, "interval_ms": null, "message": null, "severity": "high"}, {"start": 2.72, "end": 3.2, "type": "out_of_tune", "expected_note": "G4", "sung_note": "F#4", "delta_cents": 170, "interval_ms": null, "message": null, "severity": "high"}, {"start": 3.584, "end": 4.0, "type": "out_of_tune", "expected_note": "E4", "sung_note": "G4", "delta_cents": 320, "interval_ms": null, "message": null, "severity": "high"}, {"start": 4.032, "end": 4.608, "type": "out_of_tune", "expected_note": "C4", "sung_note": "D4", "delta_cents": 210, "interval_ms": null, "message": null, "severity": "high"}]}
```

> `44.4` es la respuesta honesta para este cantante amateur con umbral 50 cents
> (antes 20.7). La calibración de umbrales es **HU-S4-XX**; no se toca `scoring.py`.

## 4. Test clave: offset 200 ms

Student = 200 ms de silencio + 4.8 s sine 440; reference = 5 s sine 440.
`align_by_time` (tolerance 0.1 s) fallaría por diseño; FastDTW alinea:

```json
{"metrics": {"pitch_stability_cents": 0.8, "mean_pitch_hz": 439.82, "voiced_ratio": 0.9682, "pitch_accuracy": 100.0, "rhythm_accuracy": null, "estimated_tempo_bpm": 125.0, "onset_count": 1, "onset_stability": null, "tempo_deviation_bpm": null, "alignment_method": "fastdtw", "average_cent_deviation": 0.1}, "scores": {"vocal": 98, "afinacion": 100, "estabilidad": 98, "control_volumen": 94, "ritmo": null, "silence_pct": 3}, "timings": {"preprocess_ms": 343, "pitch_ms": 345, "rhythm_ms": 23, "align_ms": 17, "dtw_ms": 17, "scoring_ms": 4}, "segments": []}
```

`pitch_accuracy=100` y `alignment_method="fastdtw"` (>80 exigido).

## 5. Regresión y fallback

- **Sine 440 vs 442**: `pitch_accuracy=100`, `average_cent_deviation=10`, `alignment_method="fastdtw"`, `segments=[]`.
- **Sin referencia**: `400 MISSING_REFERENCE` (no llega a FastDTW; no crashea).
- **Fallback**: `align_frames` mockeado a `RuntimeError` → `alignment_method="time"`, respuesta 200, log `align_fastdtw_failed` (test `test_align_fallback_on_exception`).

## 6. Notas de rendimiento

- `fastdtw` **no usa numba** (`numba modules after import fastdtw: []`): **no requiere warm-up**.
- `align_frames` aislado: **17,1 ms** para 4,78 s; en la ruta real `align_ms` 17–21 ms. Aceptable.
- El primer `/analyze` de MASTmelody en el banco local mostró `pitch_ms=5658`/`rhythm_ms=2037`
  por el JIT de pyin/beat_track (el `TestClient` no ejecuta lifespan); el servicio real
  tiene warm-up de ambos y el primer request baja a <2 s.

## 7. Confirmaciones

- **Contrato no roto**: solo aditivos (`metrics.alignment_method`, `timings.align_ms`);
  `dtw_ms` se mantiene como alias del mismo valor.
- **`core-api/` intacto** (no existe).
- **Tag `v0.2.3` intacto** (`f744a8e`); commit solo en `sprint1`; sin merge ni tag nuevo.
- **`pitch.py`, `rhythm_eval.py`, `scoring.py`, `feedback.py` intactos** (umbrales/calibración = HU-S4-XX).
- `test_align.py` (15) y `test_comparative.py` (6) siguen verdes; idéntico→≥95, 80 cents→≤20,
  notas JSON→≥80, precedencia de `reference_audio` preservada.
- 115 tests por defecto + 3 integración (118); Docker 115 + 1 passed + 2 skipped; 98 %; ruff OK; HANDOFF 4/4.
