# AUDITORÍA BUGS B/C — singing-service v0.2.2

> Fase 1 (solo lectura + experimentos). **No se modificó código, tests ni docs.**
> Fecha: 2026-11-15. Baseline: 83 tests, 97 % cobertura, `ruff` OK.
> Prueba real reproducida con los ficheros MASTmelody del docente.

## 1. ¿Existe `docs/scoring.md`? ¿Qué dice?

No existe `docs/scoring.md` en minúsculas. El documento real es **`Docs/scoring.md`**
(raíz del workspace, `D` mayúscula). Contenido relevante:

- **Estabilidad (línea 47):** `estabilidad = 100 − 2·σ(cents)` (mín. 0);
  nota: “desviación constante → estable (100)”.
- **Segmentos (líneas 32–40):** `out_of_tune` si `|cents| ≥ 30` continuo ≥ 0.4 s;
  `medium` si `< 50`, `high` si `≥ 50`; `no_voice` si frames sin voz ≥ 0.6 s.
- **Feedback (líneas 54–63):**
  - `OUT_OF_TUNE` cuando existe **≥1** segmento `out_of_tune`; mensaje con la
    **“peor desviación”** en cents + notas esperado/cantado.
  - `NO_VOICE` cuando existe **≥1** segmento `no_voice`; mensaje con el **% agregado**
    del tiempo sin voz.
  - “Sin segmentos → sin feedback”.
- No documenta explícitamente “1 feedback por segmento”; la palabra **“peor”** y el
  hecho de que haya un solo código por tipo implican **1 feedback por tipo**.

## 2. Fórmula de estabilidad (código exacto)

Ruta real: **`app/services/scoring.py`** (no `app/core/scoring.py`).

**Comparative (`compute_scores`, líneas 54–59):**

```python
matched = [c for c in cents if c is not None]
if matched:
    within = sum(1 for c in matched if abs(c) <= cent_threshold)
    afinacion = round(100 * within / len(matched))
    stdev = float(np.std(matched)) if len(matched) >= 2 else 0.0
    estabilidad = int(round(max(0.0, 100.0 - stdev * 2.0)))
else:
    afinacion = 0
    estabilidad = 0
```

**Absolute (`compute_absolute_scores`, líneas 86–93):**

```python
freqs = [p.f0 for p in points if p.voiced and p.f0 is not None]
if freqs:
    center = float(np.median(freqs))
    cents = [1200.0 * float(np.log2(f0 / center)) for f0 in freqs]
    within = sum(1 for c in cents if abs(c) <= cent_threshold)
    afinacion = round(100 * within / len(cents))
    stdev = float(np.std(cents)) if len(cents) >= 2 else 0.0
    estabilidad = int(round(max(0.0, 100.0 - stdev * 2.0)))
```

- `σ` = desviación estándar **poblacional** (`np.std`, ddof=0).
- El score **lineal con pendiente 2** y **clamp a 0**: cualquier `σ ≥ 50` cents → 0.
- No hay TODO/FIXME ni comentario de calibración; la única justificación es
  `Docs/scoring.md` línea 47.

## 3. Fórmula de feedback (código exacto)

Ruta real: **`app/services/feedback.py`** (no `app/core/feedback_gen.py`).

**`build_feedback` (comparative, líneas 18–50):**

```python
tune = [s for s in segments if s.type == "out_of_tune" and s.delta_cents is not None]
if tune:
    worst = max(tune, key=lambda s: s.delta_cents or 0)
    items.append(FeedbackItem(code="OUT_OF_TUNE", message=... worst.delta_cents ...))

quiet = [s for s in segments if s.type == "no_voice"]
if quiet:
    total = sum(s.end - s.start for s in quiet)
    pct = max(1, round(100 * total / duration_sec)) if duration_sec > 0 else 0
    items.append(FeedbackItem(code="NO_VOICE", message=... pct ...))
```

- **1 solo `OUT_OF_TUNE`** (el segmento con mayor `delta_cents`) + **1 solo
  `NO_VOICE`** (suma de duraciones de todos los `no_voice`).
- **No itera** por segmento; el máximo posible es 2 feedbacks (uno por tipo).
- `build_absolute_feedback` añade `UNSTABLE_PITCH` (si `stability_cents > 50`) y
  `PITCH_OUT_OF_RANGE`; no cambia el comportamiento de C en comparative.

## 4. A3 — Tabla empírica (vibrato sintético, `mode=absolute`)

Generación: sine 440 Hz, vibrato sinusoidal a **2 Hz**, 5 s, 16 kHz, amplitud de
vibrato ±A cents (`f = 440·2^(A·sin(2π·2t)/1200)`), `soundfile` float32. Servicio
real v0.2.2 (Docker, Python 3.14.6, librosa 1.0.0). POST + GET.

| Caso (amplitud) | `pitch_stability_cents` medido | `scores.estabilidad` | `scores.afinacion` | `scores.vocal` | `voiced_ratio` |
|---|---|---|---|---|---|
| Sine 440 puro (A=0) | **0.0** | **100** | 100 | 99 | 1.0 |
| Vibrato ±10 cents | **7.8** | **84** | 100 | 95 | 1.0 |
| Vibrato ±50 cents | **32.0** | **36** | 91 | 79 | 1.0 |
| Vibrato ±150 cents | **95.7** | **0** | 24 | 36 | 1.0 |
| Vibrato ±300 cents | **191.5** | **0** | 10 | 29 | 1.0 |

Lectura:

- El `pitch_stability_cents` medido es **menor que la amplitud** del vibrato porque
  para una senoide `σ = A/√2` y pyin suaviza; el score usa el σ medido, no la
  amplitud. La columna “esperado” del enunciado (~10/50/150/300) corresponde a la
  amplitud, no al σ.
- El mapeo es **lineal y abrupto**: `100 − 2σ`. Con σ=32 → 36; con σ=95.7 → 0.
  **Cae a 0 en σ=50**, no en 100 o 200.

## 5. A4 — MASTmelody (reproducido)

Ficheros reales (fuera del workspace, en `C:\Users\HP\Downloads\MASTmelody_dataset\
audioFiles\MAST_melody_audio\MAST_melody_audio\`):

- `69_mel1_ref1126742.m4a` (0.07 MB)
- `69_mel1_per1126742.m4a` (0.07 MB)

POST `mode=comparative` (`audio=per`, `reference_audio=ref`) + GET. Resultado real:

```json
metrics: {
  "pitch_stability_cents": 229.2,
  "mean_pitch_hz": 314.3,
  "voiced_ratio": 0.9467,
  "pitch_accuracy": 20.7,
  "rhythm_accuracy": null,
  "average_cent_deviation": 153.9
}
scores: {"vocal": 26, "afinacion": 21, "estabilidad": 0, "control_volumen": 62, "silence_pct": 5}
segments: [
  {"start": 0.064, "end": 1.024, "type": "out_of_tune", "expected_note": "C4", "sung_note": "C#4", "delta_cents": 130, "severity": "high"},
  {"start": 2.336, "end": 3.008, "type": "out_of_tune", "expected_note": "G4", "sung_note": "F4", "delta_cents": 780, "severity": "high"},
  {"start": 3.264, "end": 4.608, "type": "out_of_tune", "expected_note": "D4", "sung_note": "F4", "delta_cents": 530, "severity": "high"}
]
feedback: [
  {"code": "OUT_OF_TUNE", "message": "Desviación de hasta 780 cents (esperado G4, cantado F4)."}
]
duration_sec: 4.7785, hop_ms: 32, student_frames: 150, reference_frames: 149
```

**Coincide exactamente con el baseline del docente:** `pitch_accuracy=20.7`,
`average_cent_deviation=153.9`, `scores.estabilidad=0`, `segments=3`,
`feedback=1`.

Los 3 segmentos son **todos `out_of_tune`** (130, 780, 530 cents); no hay segmento
`no_voice` (aunque `silence_pct=5`). Por eso `feedback` tiene **1** ítem
(`OUT_OF_TUNE`, el peor: 780). Si hubiera un `no_voice`, habría 2 (uno por tipo).

## 6. Diagnóstico

### Bug B — `scores.estabilidad=0` con `pitch_stability_cents=229.2`

**No es un bug de implementación.** El código coincide exactamente con la fórmula
documentada en `Docs/scoring.md` línea 47: `100 − 2·σ` con clamp a 0. Con
`σ=229.2`: `100 − 458.4 = −358.4 → 0`.

Es una **decisión de calibración agresiva** (0 a partir de σ=50), no un error de
código. Matices importantes:

1. **El mapeo propuesto en el enunciado (`100 − min(100, σ/2)`) tampoco resuelve
   MAST:** con σ=229.2 → `100 − 100 = 0`. Solo cambiaría casos moderados
   (σ=50 → 75, σ=100 → 50); MAST seguiría en 0.
2. **La causa real del MAST bajo no es la estabilidad:** `pitch_accuracy=20.7 %`,
   `average_cent_deviation=153.9` cents y segmentos de **780 y 530 cents**. El
   pitch/alineamiento es el problema (Sprint 1); recalibrar estabilidad subiría el
   score de forma cosmética sin mejorar el canto.
3. Si el producto quiere que 229 cents **no** sea 0, hace falta una curva más suave
   que `/2` (p. ej. `/4` → 42.7, o exponencial `100·exp(−σ/100)` → 10.1). Eso es una
   **decisión de producto** que altera todos los scores, no un bug fix.

**Conclusión:** B es **intencional/documentado**, con calibración cuestionable.
Recomendación: **mantener** salvo que el producto autorice una recalibración
explícita (y entonces definir la curva; `/2` no cumple el objetivo de MAST).

### Bug C — `feedback=1` con `segments=3`

**No es un bug.** `Docs/scoring.md` §Feedback dice explícitamente:

- `OUT_OF_TUNE` cuando hay ≥1 segmento `out_of_tune`, con la **“peor desviación”**.
- `NO_VOICE` cuando hay ≥1 `no_voice`, con el **% agregado**.

El código genera **1 feedback por tipo** (peor `out_of_tune` + `no_voice` agregado),
no uno por segmento. En MAST los 3 segmentos son `out_of_tune`; por tanto **1
feedback es el comportamiento diseñado**. Si el producto quisiera 3 feedbacks, sería
un **cambio de contrato BREAKING** (shape/conteo de `feedback`), no un bug.

**Conclusión:** C es **intencional/documentado**. Recomendación: **mantener**;
opcionalmente añadir una nota aclaratoria en `docs/celery-contract.md` §4
(“feedback: 1 ítem por tipo, peor desviación; no por segmento”) — solo documentación.

## 7. Decisión propuesta (Fase 1 → esperando autorización)

| Bug | Diagnóstico | Decisión propuesta | ¿Requiere cambio de código? |
|---|---|---|---|
| **B** | Intencional/documentado; calibración agresiva; MAST 0 es consistente con σ=229.2; `/2` no lo cambia; causa real = pitch/alineamiento | **Mantener** el diseño documentado. Si el producto quiere otra curva, es una decisión de calibración (p. ej. `/4` o exponencial) con tests/docs; **no** un bug fix. | **No** (salvo autorización de producto) |
| **C** | Intencional/documentado: 1 feedback por tipo, peor desviación; los 3 segments son `out_of_tune` | **Mantener**; añadir nota aclaratoria en contrato §4 (documentación) | **No** |

**No se modificó código, tests ni docs.** Baseline verificado: **83 tests, 97 %**,
`ruff` OK. Los ficheros MAST están fuera del workspace y se usaron en modo lectura.

**FASE 1 DETENIDA.** No se pasa a Fase 2 hasta que el líder humano revise este
diagnóstico y autorice (o rechace) una recalibración de producto para B y/o una nota
de contrato para C.
