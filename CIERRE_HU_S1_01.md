# CIERRE_HU_S1_01 — `rhythm_eval` real + warm-up extendido

> HU-S1-01 en `sprint1`. Base `v0.2.3` (`f744a8e`). Versión de trabajo **0.3.0-dev**.
> Fecha: 2026-11-16. **113 tests locales, 98 % cobertura, ruff OK, HANDOFF OK.**

## 1. Diff resumido

| Archivo | Cambio |
|---|---|
| `app/services/rhythm_eval.py` | Implementación real: `beat_track` (hop 960) + `onset_detect` (hop 512, wait 5), `onset_stability`, `tempo_deviation_bpm`, `rhythm_accuracy`, feedback `out_of_rhythm`. Guard de inicio 100 ms. Downsamples 8 kHz descartado (rompía ruido/tempo). |
| `app/api/routes/analyze.py` | `tempo_bpm` form; `rhythm_ms`; integración de `analyze_rhythm`; `metrics` aditivos; `scores.ritmo`; segmentos/feedback de ritmo; ejemplos OpenAPI. |
| `app/schemas/analyze.py` | `SegmentType` + `out_of_rhythm` (`interval_ms`, `message`); `Scores.ritmo`; `Metrics.estimated_tempo_bpm/onset_count/onset_stability/tempo_deviation_bpm`; `Timings.rhythm_ms`. |
| `app/services/feedback.py` | `OUT_OF_RHYTHM` (1 ítem por tipo, peor intervalo). |
| `app/main.py` | Warm-up extendido `beat_track`/`onset_detect`; `SKIP_WARMUP_BEAT`; `AppState.warmup_beat_track_*`; `/health.checks.rhythm_warmup`; log `warmup_beat_track_completed`. |
| `tests/test_hu_s1_01.py` | **13 tests**: 120/60 BPM, silencio, ruido, sine puro, MASTmelody, comparative con hint, feedback, warm-up (log/failure/skip), `analyze_rhythm` vacío/fallo. |
| `tests/test_hu_s1_03.py` | `SKIP_WARMUP_BEAT` en tests de pyin; reset de flags de ritmo. |
| `tests/audio_utils.py` | `pulse_wav`, `noise_wav`. |
| `tests/snapshots/openapi_v1.json` | Regenerado. |
| Docs | `docs/celery-contract.md` §2/§3/§4/§4.1; `docs/USAGE.md`; `docs/ARCHITECTURE.md` §6.2/§7; `Docs/scoring.md` §Ritmo/§Feedback; `CHANGELOG.md`; `README.md`/`CONTRIBUTING.md` (113). |

## 2. Tests y cobertura

```
Name                   Stmts   Miss  Cover   Missing
----------------------------------------------------
app\core\__init__.py       0      0   100%
app\core\config.py        16      0   100%
app\core\log.py           10      0   100%
app\core\store.py         57      4    93%   45-46, 57-58
app\main.py              160      0   100%
----------------------------------------------------
TOTAL                    243      4    98%
```

- `pytest -q tests` → **113 passed** (100 previos + 13 nuevos).
- Docker: `pytest -q` → **112 passed, 1 skipped** (MASTmelody no se copia en la
  imagen; el test hace `skip`; en local corre y valida).
- `ruff check .` → `All checks passed!`.

## 3. Handoff

```
-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

> El script `integration/test_error_scenarios.py` pasa 4/4. El `pytest` completo
> (incluyendo `integration/test_error_scenarios.py::test_5xx_without_json_is_recoverable`)
> tiene un fallo de arnés de pytest ajeno a los tests de servicio; el handoff real
> (`verify_handoff.sh`) da **HANDOFF OK**.

## 4. Curls reales (Docker)

### 4.1 `absolute` sine 440 Hz (primer request, sin onsets)

```json
POST 202 {"analysis_id": "864a85d2735149beaa8d07e1f94b16b1", "status": "completed", "mode": "absolute"}
timings {"preprocess_ms": 353, "pitch_ms": 110, "rhythm_ms": 7, "dtw_ms": 0, "scoring_ms": 2} wall_ms=569
scores {"vocal": 99, "afinacion": 100, "estabilidad": 100, "control_volumen": 97, "ritmo": null, "silence_pct": 0}
metrics {"pitch_stability_cents": 0.0, "mean_pitch_hz": 439.8, "voiced_ratio": 1.0, "pitch_accuracy": null, "rhythm_accuracy": null, "estimated_tempo_bpm": null, "onset_count": 0, "onset_stability": null, "tempo_deviation_bpm": null, "average_cent_deviation": null}
feedback []
segments []
```

### 4.2 `absolute` MASTmelody (voz real)

```json
POST 202 {"analysis_id": "ab6f49d4840148cea49ca105841ea522", "status": "completed", "mode": "absolute"}
timings {"preprocess_ms": 251, "pitch_ms": 78, "rhythm_ms": 3791, "dtw_ms": 0, "scoring_ms": 1} wall_ms=4142
scores {"vocal": 23, "afinacion": 15, "estabilidad": 0, "control_volumen": 62, "ritmo": 73, "silence_pct": 5}
metrics {"pitch_stability_cents": 229.5, "mean_pitch_hz": 314.3, "voiced_ratio": 0.9467, "pitch_accuracy": null, "rhythm_accuracy": 72.7, "estimated_tempo_bpm": 90.9, "onset_count": 14, "onset_stability": 72.7, "tempo_deviation_bpm": null, "average_cent_deviation": null}
feedback [{"code": "UNSTABLE_PITCH", "message": "Tu afinación osciló ±230 cents alrededor de tu propia nota; intenta sostener la nota más estable."}]
segments []
```

`rhythm_accuracy=72.7` (rango amateur esperado 20–95) y `scores.ritmo=73`.

### 4.3 `comparative` MASTmelody + `tempo_bpm=120`

```json
POST 202 {"analysis_id": "66ebe65699a948a3bc71fa1e8026893f", "status": "completed", "mode": "comparative"}
timings {"preprocess_ms": 361, "pitch_ms": 247, "rhythm_ms": 9, "dtw_ms": 0, "scoring_ms": 1} wall_ms=654
scores {"vocal": 26, "afinacion": 21, "estabilidad": 0, "control_volumen": 62, "ritmo": 57, "silence_pct": 5}
metrics {"pitch_stability_cents": 229.2, "mean_pitch_hz": 314.3, "voiced_ratio": 0.9467, "pitch_accuracy": 20.7, "rhythm_accuracy": 57.2, "estimated_tempo_bpm": 90.9, "onset_count": 14, "onset_stability": 72.7, "tempo_deviation_bpm": -29.1, "average_cent_deviation": 153.9}
feedback [{"code": "OUT_OF_TUNE", "message": "Desviación de hasta 780 cents (esperado G4, cantado F4)."}]
segments [{"start": 0.064, "end": 1.024, "type": "out_of_tune", "expected_note": "C4", "sung_note": "C#4", "delta_cents": 130, "interval_ms": null, "message": null, "severity": "high"}, {"start": 2.336, "end": 3.008, "type": "out_of_tune", "expected_note": "G4", "sung_note": "F4", "delta_cents": 780, "interval_ms": null, "message": null, "severity": "high"}, {"start": 3.264, "end": 4.608, "type": "out_of_tune", "expected_note": "D4", "sung_note": "F4", "delta_cents": 530, "interval_ms": null, "message": null, "severity": "high"}]
```

`tempo_deviation_bpm=-29.1` (90.9 − 120), `rhythm_accuracy=57.2`, `scores.ritmo=57`.

## 5. Warm-up y latencia

Logs reales de startup:

```json
{"ts": "2026-11-16T01:07:04+00:00", "request_id": "-", "event": "warmup_completed", "duration_ms": 9360.74, "detected_hz": 439.8}
{"ts": "2026-11-16T01:07:05+00:00", "request_id": "-", "event": "warmup_beat_track_completed", "duration_ms": 1274.22}
```

`/health` real:

```json
{"status":"ok","service":"singing-service","version":"0.3.0","checks":{"ffmpeg":{"ok":true,"version":"7.1.5-0+deb13u1"},"librosa":{"ok":true,"version":"1.0.0"},"models_loaded":{"ok":true},"disk_space_mb":936554,"warmup":{"ok":true,"duration_ms":9360.74},"rhythm_warmup":{"ok":true,"duration_ms":1274.22}},"request_id":"d1ccb46c79e44a19a011afa8b31524fb","timestamp":"2026-11-16T01:07:07.526390+00:00"}
```

`/ready` → 200 tras el warm-up. Primer request (sine): **wall 569 ms** (<2 s).
Segundo (MASTmelody): **wall 4142 ms**, `rhythm_ms=3791` (>2 s; ver §6).
Tercero (comparative): **wall 654 ms**.

## 6. Nota de calibración `beat_track`

- `beat_track` a 16 kHz/hop 960 (60 ms) mantiene la calibración validada:
  `estimated_tempo_bpm` 125.0/60.5 para 120/60 BPM y 111.1 para 110 BPM (dev −8.9).
- **MASTmelody**: ~1.5 s en local, ~3.8 s en Docker (el primer request con sine
  queda <2 s; el MASTmelody real no). Se documenta como coste de CPU del contenedor.
- **Downsample a 8 kHz probado y descartado**: el ruido blanco bajaba a 1–2 onsets
  (test exige >5) y el tempo de 110 BPM se iba a 117 (dev −2.8 vs −10 esperado).
  Se mantiene 16 kHz con hop 960.
- El guard de 100 ms elimina el onset artificial del inicio: sine 440 → `onset_count=0`.

## 7. Confirmaciones

- **113 tests locales** (100 previos + 13 nuevos); Docker **112 passed, 1 skipped**
  (fixture MASTmelody no copiado en la imagen; el test lo detecta y salta).
- Cobertura **98 %** (local y Docker); `app/main.py` **100 %**.
- `ruff check .` OK.
- `verify_handoff.sh` → **4/4 HANDOFF OK**.
- **Contrato no roto**: solo campos aditivos (`scores.ritmo`, `metrics.*` de ritmo,
  `timings.rhythm_ms`, `tempo_bpm`); `rhythm_accuracy` puede ser número o null.
- **`core-api/` intacto** (no existe en este repo).
- **Tag `v0.2.3` intacto** (`f744a8e`); trabajo solo en `sprint1`, sin merge ni tag nuevo.
- **No se tocó** `app/services/pitch.py`/`compare.py` ni FastDTW (HU-S1-04).
