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

> **FastDTW cableado (HU-S1-04).** `analyze.py` usa `align_frames` en
> `mode=comparative` y cae a `align_by_time` si FastDTW falla
> (`metrics.alignment_method` = `"fastdtw"` | `"time"`). Con voz real amateur,
> `pitch_accuracy` queda ~40–50 con umbral 50 cents (MASTmelody: 20.7 → 44.4;
> `average_cent_deviation` 153.9 → 92.9). La calibración de umbrales es HU-S4-XX.

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
| `out_of_rhythm` | intervalo entre onsets > 2× la mediana | — | `medium` si ratio < 3; `high` si ≥ 3 |

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

## Ritmo (HU-S1-01)

Se analiza el WAV 16 kHz con `librosa.beat.beat_track` (tempo, `hop=960` = 60 ms)
y `librosa.onset.onset_detect` (`hop=512`, `wait=5`); se descarta el onset
artificial <50 ms del inicio. El coste JIT de `beat_track` se cubre en el warm-up
del lifespan. Se probó downsample a 8 kHz para acelerar MASTmelody, pero rompía
la calibración de ruido/tempo (onsets falsos y tempo 117 vs 110 BPM); se descartó.
Con `hop=960`, MASTmelody tarda ~1.5 s en local y ~3.8 s en Docker (documentado;
el primer/segundo `/analyze` con sine queda <2 s).

| Métrica | Fórmula | Notas |
|---|---|---|
| `estimated_tempo_bpm` | salida de `beat_track` | null si el tempo no es finito o ≤ 0 |
| `onset_count` | número de onsets | 0 en silencio/tono puro |
| `onset_intervals_cv` | `σ(intervalos) / μ(intervalos)` | null si < 2 onsets; `μ > 0` |
| `onset_stability` | `max(0, 100·(1 − CV))` | 100 = onsets perfectamente regulares |
| `tempo_deviation_bpm` | `estimated_tempo_bpm − tempo_bpm` | null si no se envía `tempo_bpm` |
| `rhythm_accuracy` | sin hint: `onset_stability`; con hint: `0.5·onset_stability + 0.5·max(0, 100 − 2·|deviation|)` | null si < 2 onsets |
| `scores.ritmo` | `round(rhythm_accuracy)` | null si `rhythm_accuracy` es null |

- `rhythm_accuracy` se calcula en **ambos modos** (`absolute` y `comparative`).
- El feedback `OUT_OF_RHYTHM` reporta **1 ítem por tipo** con el **peor intervalo**
  (máximo `interval_ms`), consistente con la Nota C de `OUT_OF_TUNE`.
- Los segmentos `out_of_rhythm` llevan `start`, `end`, `severity`, `message` e
  `interval_ms`; los detalles completos están en `segments[]`.

## Feedback (HU-46 / RF-39)

Códigos estables para i18n; **siempre distinguen *sin voz* de *desafinación***:

| code | Cuándo | Mensaje |
|---|---|---|
| `OUT_OF_TUNE` | existe ≥1 segmento `out_of_tune` | peor desviación en cents + notas esperado/cantado |
| `NO_VOICE` | existe ≥1 segmento `no_voice` | % del tiempo sin voz + aclaración de que no es desafinación |
| `OUT_OF_RHYTHM` | existe ≥1 segmento `out_of_rhythm` | peor intervalo entre onsets + recomendación de pulso estable |

Sin segmentos → sin feedback (un intento afinado y continuo no genera mensajes).
Cada código aparece **una sola vez** por análisis (1 ítem por tipo).

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
- HU-S1-01 → `analyze_rhythm` (`app/services/rhythm_eval.py`) + `scores.ritmo`
- Tests: `tests/test_align.py` (15), `tests/test_pitch.py` (3),
  `tests/test_hu_s1_01.py` (13)
- Versión del algoritmo con todo real: `0.4.0-align-scoring`
