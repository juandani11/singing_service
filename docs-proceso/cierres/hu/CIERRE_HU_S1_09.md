# CIERRE_HU_S1_09 — `pitch_contour` con downsample ~10 Hz

> Rama `sprint2` (HEAD previo `5278a2b`). Tag `v0.3.0` intacto en `0016e2e`.
> Fecha: 2026-11-16 · 130 tests por defecto + 3 integración (133) · 98 % · ruff OK · HANDOFF OK.

## 1. Diff resumido

```text
 singing-service/CHANGELOG.md                    |  13 ++-
 singing-service/app/api/routes/analyze.py       |  14 ++++
 singing-service/app/schemas/analyze.py          |  36 +++++++++
 singing-service/docs/ARCHITECTURE.md            |  13 +--
 singing-service/docs/SPRINT1_BACKLOG.md         |   6 +-
 singing-service/docs/SPRINT2_BACKLOG.md         |   9 ++-
 singing-service/docs/USAGE.md                   |  34 +++++++-
 singing-service/docs/celery-contract.md         |  18 ++++-
 singing-service/tests/snapshots/openapi_v1.json | 102 ++++++++++++++++++++++++
 9 files changed, 224 insertions(+), 21 deletions(-)

Nuevos:
  singing-service/app/services/contour.py
  singing-service/tests/test_hu_s1_09.py
```

`pitch.py` **no se tocó**: la extracción F0 queda igual. El downsample y el formato
viven en `app/services/contour.py`.

## 2. Implementación

### 2.1 Request

Nuevo form field opcional:

```python
include_contour: bool = Form(default=False)
```

Default `false` (no rompe clientes). Si `true`, se construye `pitch_contour`; si
`false`/ausente, el campo existe con valor `null`.

### 2.2 Response (aditivo)

```json
"pitch_contour": {
  "student": [{"t": 0.0, "f0": 439.8, "note": "A4", "voiced": true}],
  "reference": [{"t": 0.0, "f0": 439.8, "note": "A4", "voiced": true}] | null,
  "downsample_hz": 10
} | null
```

- `reference` es `null` en `absolute` (y en comparative solo si no hay referencia,
  caso ya rechazado por el contrato).
- `f0` y `note` son `null` cuando `voiced=false`.
- `note` usa `hz_to_note` (temperamento igual, A4=440).

### 2.3 Downsample (`app/services/contour.py`)

```python
step = max(1, round(0.1 / (hop_ms / 1000)))   # hop 32 ms -> step 3
indices = np.arange(0, n, step)
if len(indices) > 6000:
    indices = np.linspace(0, n - 1, 6000, dtype=int)
```

- Hop efectivo normal: **96 ms** (3 × 32 ms) → **~10.42 Hz**, no 10.000 Hz exactos.
- Límite: **6000 puntos**. Para 10 min (18,750 frames) se recortan 6000 índices
  equiespaciados → 600 s / 5999 ≈ 100.02 ms → **~9.999 Hz**.
- 30 min: 6000 puntos sobre 1800 s → **~3.33 Hz** (límite respetado; documentado).
- `t` es el `t` del frame original seleccionado (alineado al frame más cercano).

## 3. Evidencia

### 3.1 `pytest -v` (local)

```text
tests\test_hu_s1_09.py .......                                           [ 76%]
...
=============== 130 passed, 3 deselected, 2 warnings in 26.62s ================
```

### 3.2 `pytest -m integration` (local)

```text
...                                                                      [100%]
# 3 passed
```

### 3.3 `ruff check .`

```text
All checks passed!
```

### 3.4 Docker (imagen reconstruida)

```text
$ docker compose exec -T singing-service python -m pytest --no-cov
130 passed, 3 deselected, 2 warnings in 31.80s

$ docker compose exec -T singing-service python -m pytest -m integration --no-cov
1 passed, 2 skipped, 130 deselected, 1 warning in 1.41s
# 2 skipped: fixtures MASTmelody no se copian a la imagen
```

### 3.5 HANDOFF

```text
=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

### 3.6 POST sin flag → `pitch_contour: null` (real, Docker)

```text
$ curl -s -X POST http://localhost:5000/api/v1/analyze \
    -F "audio=@hu109_5s.wav" -F "attempt_id=hu109-no-flag" \
    -F "routine_id=r-hu109" -F "mode=absolute"
{"analysis_id":"f7c6c0b644ac4ad1a20cc43eba007dd5","status":"completed","mode":"absolute"}

$ curl -s .../f7c6c0b644ac4ad1a20cc43eba007dd5 | jq '.pitch_contour'
null
pitch_contour is null: True
```

### 3.7 POST `include_contour=true` absolute (real, Docker)

```text
{"analysis_id":"e1b6fee0a59046b1b38cc27d42283db3","status":"completed","mode":"absolute"}

downsample_hz: 10
student_count: 53
reference_is_null: true
pitch_student_count: 157        # curva original (hop 32 ms)

primeros 3 puntos:
[
  {"t": 0.0,   "f0": 439.8, "note": "A4", "voiced": true},
  {"t": 0.096, "f0": 439.8, "note": "A4", "voiced": true},
  {"t": 0.192, "f0": 439.8, "note": "A4", "voiced": true}
]
```

### 3.8 POST comparative con flag (real, Docker)

```text
{"analysis_id":"b86660e45f76497e9563b95920752854","status":"completed","mode":"comparative"}

downsample_hz: 10
student_count: 32
reference_count: 32
alignment_method: "fastdtw"

student[0..1]:   t=0.0/0.096, f0=439.8, note=A4, voiced=true
reference[0..1]: t=0.0/0.096, f0=439.8, note=A4, voiced=true
```

### 3.9 Tamaño JSON 10 min (real, 18,750 frames equivalentes)

```text
student_points 6000
reference_points 6000
student_json_bytes 351324
student_plus_reference_json_bytes 702671
under_1MB True
```

Se mide sobre `build_pitch_contour` con 18,750 frames (10 min a hop 32 ms) para no
pagar el coste de `rhythm_eval` (~0.79x real-time) en un POST real de 10 min. Los
curls E2E de 5 s/3 s validan el camino completo HTTP.

## 4. Confirmaciones

- **Contrato no roto:** solo se añaden `include_contour` (form, default false) y
  `pitch_contour` (nullable) a `AnalysisResult`; el resto del shape no cambia.
  Snapshot OpenAPI regenerado (`+102` líneas).
- **`pitch.py` intacto** (y `rhythm_eval.py`, `scoring.py`, `feedback.py`,
  `compare.py`, `align.py` sin cambios).
- **`core-api/` intacto:** no existe en este workspace y no se tocó nada fuera de
  `singing-service/`.
- **Tag `v0.3.0` intacto:**

```text
$ git rev-parse v0.3.0^{commit}
0016e2e65266ea6086e8c50253932497668e5e8d
```

- **Sin tag ni merge:** no se creó `v0.4.0` ni se hizo merge a `master`.

## 5. Notas

- El hop efectivo es 96 ms (~10.42 Hz), no 100 ms exactos, por el redondeo de
  `step` a 3. Está documentado en el contrato y en `USAGE`.
- Los tests de 10 min usan 18,750 `PitchPoint` sintéticos (equivalentes al hop
  32 ms) para mantener la suite rápida; el recorte a 6000 y el tamaño <1 MB quedan
  cubiertos de forma determinista.
- HU-S1-09 queda ✅ en `docs/SPRINT2_BACKLOG.md`; el tag `v0.4.0` se crea al final
  de Sprint 2 (HU-S1-07).
