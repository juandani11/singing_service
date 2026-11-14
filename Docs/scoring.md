# Scoring vocal — SyncDance AI (singing-service)

Documento exigido por el plan §4 Sprint 4 (HU-44/45 + RF-38/39). Define cómo se
calculan los scores `0–100`, los segmentos y el feedback que entrega
`GET /api/v1/analyze/{id}` cuando `mode=real`.

> Los resultados con `mode=mock` no pasan por este documento: son los valores
> congelados del prototipo Figma (vocal 71, afinación 71, estabilidad 66,
> control de volumen 80, sin voz 4 %).

## Pipeline (Sprints 2–4)

```
audio → FFmpeg (WAV 16 kHz mono, loudnorm) → librosa.pyin (F0 + sin voz)
      → FastDTW (alumno vs referencia) → cents por frame
      → segmentos → scores → feedback
```

## Desviación en cents (HU-44)

Para cada frame del alumno emparejado con la referencia vía FastDTW:

```
cents = 1200 · log2(f0_alumno / f0_referencia)
```

- Si alguna de las dos curvas está sin voz, el frame **no se juzga** (`cents: null`)
  y el coste DTW aplica la penalización `VOICE_GAP_CENTS = 600`.

## Segmentos (HU-45 / HU-46)

| Tipo | Se forma cuando | Duración mínima | Gravedad |
|---|---|---|---|
| `out_of_tune` | `\|cents\| ≥ 30` continuo | 0.4 s | `medium` si `\|cents\| < 50`; `high` si `≥ 50` |
| `no_voice` | frames sin voz continuos | 0.6 s | `info` |

- `delta_cents` = peor desviación del segmento; `expected_note`/`sung_note` =
  mediana de la F0 de referencia/alumno convertida a nota (A4 = 440 Hz).
- El umbral de gravedad (50) es `CENT_THRESHOLD` (env), coherente con los
  ejemplos Figma (45 cents → medium, 72 cents → high).

## Scores (RF-38)

| Score | Fórmula | Notas |
|---|---|---|
| `afinacion` | `100 · (% frames emparejados con \|cents\| ≤ 50)` | sin frames emparejados → 0 |
| `estabilidad` | `100 − 2·σ(cents)` (mín. 0) | desviación constante → estable (100) |
| `control_volumen` | `100 − 100·CV(RMS voceado)` | CV = σ/μ del RMS de los frames con voz |
| `silence_pct` | `% frames sin voz` | ya calculado en el Sprint 3 |
| `vocal` | `0.5·afinación + 0.25·estabilidad + 0.25·control_volumen` | compuesto |

Límites: todos enteros en `[0, 100]` (validados por el esquema Pydantic).

## Feedback (HU-46 / RF-39)

Códigos estables para i18n; **siempre distinguen *sin voz* de *desafinación***:

| code | Cuándo | Mensaje |
|---|---|---|
| `OUT_OF_TUNE` | existe ≥1 segmento `out_of_tune` | peor desviación en cents + notas esperado/cantado |
| `NO_VOICE` | existe ≥1 segmento `no_voice` | % del tiempo sin voz + aclaración de que no es desafinación |

Sin segmentos → sin feedback (un intento afinado y continuo no genera mensajes).

## Configuración (env)

| Variable | Default | Efecto |
|---|---|---|
| `CENT_THRESHOLD` | 50 | umbral de afinación y de gravedad `high` |
| `HOP_LENGTH` | 512 | distancia entre frames (32 ms @ 16 kHz) |
| `SAMPLE_RATE` | 16000 | tasa del WAV de trabajo |

## Trazabilidad

- HU-44 → `align_frames` (`app/services/align.py`) + `afinacion`
- HU-45 → `build_segments` + gravedad
- HU-46 → `build_feedback` (`app/services/feedback.py`)
- RF-38 → `compute_scores` (`app/services/scoring.py`)
- Tests: `tests/test_align.py` (15), `tests/test_pitch.py` (3)
- Versión del algoritmo con todo real: `0.4.0-align-scoring`
