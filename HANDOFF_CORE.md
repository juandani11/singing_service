# HANDOFF_CORE — Integración `singing-service` ↔ Core API (Celery)

> **Versión:** v0.2.2
> **Tag git:** `v0.2.2` (annotated; tag object `fdad4cc5dc5c9dd2576e375e2bfdbe431864e71c`)
> **Commit SHA:** `1b9271bc22db876416772893afc48ca753600a05`
> **Fecha:** 2026-11-14T16:20:37-04:00
> **Fingerprint (respaldo):** `821a796d9f6e27e49b1a22c35319ba0fe227600ed90c5defb4b05bece31e92ae`
> **Estado:** ✅ LISTO PARA INTEGRACIÓN CON CORE
> **Tests:** 83 passed, 97% cobertura, ruff OK
> **Verificación:** `bash singing-service/integration/verify_handoff.sh` → 4/4 HANDOFF OK
> **Documentación vigente:** `singing-service/docs/celery-contract.md` (v0.2.2), `singing-service/docs/USAGE.md`, `singing-service/docs/SWAGGER_GUIDE.md`

> Handoff ejecutable para el equipo de Core API. El servicio está cerrado
> (70 tests, 93 % cobertura, Docker OK). Esta entrega **solo añade** `integration/`
> y documentación; no modifica `app/`, `core/` ni `tests/`.
> Fecha: 2026-11-12 (UTC).

## Resumen

| Entregable | Ruta | Estado |
|---|---|---|
| Simulador de worker Celery | `singing-service/integration/simulate_celery_worker.py` | probado (absolute + comparative) |
| Matriz de errores | `singing-service/integration/test_error_scenarios.py` | **8/8 PASS** |
| Generador de fixtures | `singing-service/integration/generate_fixtures.py` | 8 archivos generados |
| Verificación E2E | `singing-service/integration/verify_handoff.sh` | **4/4 checks OK** |
| Contrato Celery | `singing-service/docs/celery-contract.md` | 7 secciones |
| README de integración | `singing-service/integration/README.md` | requisitos + uso |

**Desviaciones del enunciado (reales, no inventadas):**

1. El campo multipart canónico es **`audio`** (simétrico con `reference_audio`).
   El nombre previo `file` se corrigió en `CONSISTENCY_FIX.md`; enviar `file` ahora
   produce 422 `Field required`.
2. Un `.txt` renombrado a `.wav` devuelve **400 `INVALID_AUDIO`** (datos corruptos),
   no `UNSUPPORTED_FORMAT`. `UNSUPPORTED_FORMAT` se verifica con extensión `.txt`.
   La matriz comprueba ambos casos reales.
3. `verify_handoff.sh` es bash: en Windows ejecutar con **Git Bash** o **WSL**.

---

## 1. Estructura de `integration/`

```
singing-service/integration/
├── README.md                     # requisitos, uso, códigos, config Core
├── requirements.txt              # requests, pytest, numpy
├── generate_fixtures.py          # O3: WAV/M4A/MP3/AAC/OGG + long_11min (--include-long)
├── simulate_celery_worker.py     # O1: POST + GET como el worker (timeout 5/300)
├── test_error_scenarios.py       # O2: matriz de 8 errores reales
├── verify_handoff.sh             # O5: docker + health + fixtures + simulación + errores
└── fixtures/                     # generado, GITIGNORED (no se commitea)
    ├── sine_440hz_5s.wav         # 430.7 KB
    ├── sine_440hz_5s.m4a         # 78.9 KB
    ├── sine_440hz_5s.mp3         # 20.6 KB
    ├── sine_440hz_5s.aac         # 78.8 KB
    ├── sine_440hz_5s.ogg         # 11.9 KB
    ├── sine_442hz_5s.wav         # 430.7 KB
    ├── silence_3s.wav            # 258.4 KB
    └── long_11min.wav            # 10.07 MB (solo con --include-long)
```

`.gitignore` incluye `integration/fixtures/`.

---

## 2. Output real — simulación `mode=absolute`

Comando:

```bash
python integration/simulate_celery_worker.py --audio integration/fixtures/sine_440hz_5s.wav --mode absolute
```

Salida real completa (run en caliente; exit code 0):

```
POST http://localhost:5000/api/v1/analyze
  attempt_id=sim-bb9e0be2c668 routine_id=sim-routine mode=absolute
STATUS: 202
ELAPSED_MS: 1174
BODY:
{
  "analysis_id": "8386a02e0cc8495a8d63523b3fc86b19",
  "status": "completed",
  "mode": "absolute"
}

GET http://localhost:5000/api/v1/analyze/8386a02e0cc8495a8d63523b3fc86b19
STATUS: 200
ELAPSED_MS: 79
RESULT:
{
  "analysis_id": "8386a02e0cc8495a8d63523b3fc86b19",
  "attempt_id": "sim-bb9e0be2c668",
  "routine_id": "sim-routine",
  "status": "completed",
  "mode": "absolute",
  "algorithm_version": "0.5.0-hybrid-modes",
  "duration_sec": 5.0,
  "pitch": {
    "student": [
      {
        "t": 0.0,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.032,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.064,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.096,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.128,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.16,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.192,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.224,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.256,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.288,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.32,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.352,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.384,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.416,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.448,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.48,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.512,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.544,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.576,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.608,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.64,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.672,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.704,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.736,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.768,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.8,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.832,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.864,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.896,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.928,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.96,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.992,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.024,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.056,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.088,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.12,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.152,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.184,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.216,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.248,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.28,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.312,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.344,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.376,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.408,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.44,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.472,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.504,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.536,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.568,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.6,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.632,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.664,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.696,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.728,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.76,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.792,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.824,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.856,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.888,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.92,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.952,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.984,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.016,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.048,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.08,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.112,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.144,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.176,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.208,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.24,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.272,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.304,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.336,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.368,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.4,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.432,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.464,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.496,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.528,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.56,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.592,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.624,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.656,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.688,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.72,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.752,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.784,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.816,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.848,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.88,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.912,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.944,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.976,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.008,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.04,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.072,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.104,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.136,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.168,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.2,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.232,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.264,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.296,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.328,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.36,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.392,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.424,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.456,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.488,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.52,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.552,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.584,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.616,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.648,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.68,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.712,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.744,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.776,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.808,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.84,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.872,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.904,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.936,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.968,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.0,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.032,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.064,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.096,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.128,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.16,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.192,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.224,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.256,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.288,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.32,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.352,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.384,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.416,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.448,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.48,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.512,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.544,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.576,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.608,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.64,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.672,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.704,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.736,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.768,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.8,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.832,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.864,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.896,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.928,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.96,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.992,
        "f0": 439.8,
        "voiced": true
      }
    ],
    "reference": null,
    "hop_ms": 32
  },
  "segments": [],
  "scores": {
    "vocal": 99,
    "afinacion": 100,
    "estabilidad": 100,
    "control_volumen": 97,
    "silence_pct": 0
  },
  "metrics": {
    "pitch_stability_cents": 0.0,
    "mean_pitch_hz": 439.8,
    "voiced_ratio": 1.0,
    "pitch_accuracy": null,
    "rhythm_accuracy": null,
    "average_cent_deviation": null
  },
  "feedback": [],
  "timings": {
    "preprocess_ms": 762,
    "pitch_ms": 289,
    "dtw_ms": 0,
    "scoring_ms": 8
  }
}
```

---

## 3. Output real — simulación `mode=comparative`

Comando:

```bash
python integration/simulate_celery_worker.py --audio integration/fixtures/sine_442hz_5s.wav \
    --mode comparative --reference integration/fixtures/sine_440hz_5s.wav
```

Salida real completa (exit code 0):

```
POST http://localhost:5000/api/v1/analyze
  attempt_id=sim-79e232bf8bb4 routine_id=sim-routine mode=comparative
STATUS: 202
ELAPSED_MS: 1208
BODY:
{
  "analysis_id": "5a995a1432804532b862599f39a6522f",
  "status": "completed",
  "mode": "comparative"
}

GET http://localhost:5000/api/v1/analyze/5a995a1432804532b862599f39a6522f
STATUS: 200
ELAPSED_MS: 41
RESULT:
{
  "analysis_id": "5a995a1432804532b862599f39a6522f",
  "attempt_id": "sim-79e232bf8bb4",
  "routine_id": "sim-routine",
  "status": "completed",
  "mode": "comparative",
  "algorithm_version": "0.5.0-hybrid-modes",
  "duration_sec": 5.0,
  "pitch": {
    "student": [
      {
        "t": 0.0,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.032,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.064,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.096,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.128,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.16,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.192,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.224,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.256,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.288,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.32,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.352,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.384,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.416,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.448,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.48,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.512,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.544,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.576,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.608,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.64,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.672,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.704,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.736,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.768,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.8,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.832,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.864,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.896,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.928,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.96,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 0.992,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.024,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.056,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.088,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.12,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.152,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.184,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.216,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.248,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.28,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.312,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.344,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.376,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.408,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.44,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.472,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.504,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.536,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.568,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.6,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.632,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.664,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.696,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.728,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.76,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.792,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.824,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.856,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.888,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.92,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.952,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 1.984,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.016,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.048,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.08,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.112,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.144,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.176,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.208,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.24,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.272,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.304,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.336,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.368,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.4,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.432,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.464,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.496,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.528,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.56,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.592,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.624,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.656,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.688,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.72,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.752,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.784,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.816,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.848,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.88,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.912,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.944,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 2.976,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.008,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.04,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.072,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.104,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.136,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.168,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.2,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.232,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.264,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.296,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.328,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.36,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.392,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.424,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.456,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.488,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.52,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.552,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.584,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.616,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.648,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.68,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.712,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.744,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.776,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.808,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.84,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.872,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.904,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.936,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 3.968,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.0,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.032,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.064,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.096,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.128,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.16,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.192,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.224,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.256,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.288,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.32,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.352,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.384,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.416,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.448,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.48,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.512,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.544,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.576,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.608,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.64,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.672,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.704,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.736,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.768,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.8,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.832,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.864,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.896,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.928,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.96,
        "f0": 442.35,
        "voiced": true
      },
      {
        "t": 4.992,
        "f0": 442.35,
        "voiced": true
      }
    ],
    "reference": [
      {
        "t": 0.0,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.032,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.064,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.096,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.128,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.16,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.192,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.224,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.256,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.288,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.32,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.352,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.384,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.416,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.448,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.48,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.512,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.544,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.576,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.608,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.64,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.672,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.704,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.736,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.768,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.8,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.832,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.864,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.896,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.928,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.96,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 0.992,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.024,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.056,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.088,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.12,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.152,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.184,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.216,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.248,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.28,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.312,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.344,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.376,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.408,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.44,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.472,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.504,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.536,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.568,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.6,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.632,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.664,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.696,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.728,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.76,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.792,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.824,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.856,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.888,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.92,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.952,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 1.984,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.016,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.048,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.08,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.112,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.144,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.176,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.208,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.24,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.272,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.304,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.336,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.368,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.4,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.432,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.464,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.496,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.528,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.56,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.592,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.624,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.656,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.688,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.72,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.752,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.784,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.816,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.848,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.88,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.912,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.944,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 2.976,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.008,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.04,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.072,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.104,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.136,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.168,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.2,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.232,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.264,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.296,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.328,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.36,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.392,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.424,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.456,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.488,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.52,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.552,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.584,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.616,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.648,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.68,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.712,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.744,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.776,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.808,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.84,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.872,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.904,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.936,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 3.968,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.0,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.032,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.064,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.096,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.128,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.16,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.192,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.224,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.256,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.288,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.32,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.352,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.384,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.416,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.448,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.48,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.512,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.544,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.576,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.608,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.64,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.672,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.704,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.736,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.768,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.8,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.832,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.864,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.896,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.928,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.96,
        "f0": 439.8,
        "voiced": true
      },
      {
        "t": 4.992,
        "f0": 439.8,
        "voiced": true
      }
    ],
    "hop_ms": 32
  },
  "segments": [],
  "scores": {
    "vocal": 99,
    "afinacion": 100,
    "estabilidad": 100,
    "control_volumen": 97,
    "silence_pct": 0
  },
  "metrics": {
    "pitch_stability_cents": 0.0,
    "mean_pitch_hz": 442.35,
    "voiced_ratio": 1.0,
    "pitch_accuracy": 100.0,
    "rhythm_accuracy": null,
    "average_cent_deviation": 10.0
  },
  "feedback": [],
  "timings": {
    "preprocess_ms": 842,
    "pitch_ms": 271,
    "dtw_ms": 2,
    "scoring_ms": 3
  }
}
```

---

## 4. Output real — matriz de errores

Comando:

```bash
python integration/test_error_scenarios.py
```

Salida real completa (exit code 0):

```
Servicio OK: http://localhost:5000/health -> 200

[PASS] mode_invalido: HTTP 422 code=INVALID_MODE (esperado 422/INVALID_MODE)
[PASS] comparative_sin_referencia: HTTP 400 code=MISSING_REFERENCE (esperado 400/MISSING_REFERENCE)
[PASS] audio_mayor_50mb: HTTP 413 code=AUDIO_TOO_LARGE (esperado 413/AUDIO_TOO_LARGE)
[PASS] audio_mayor_600s: HTTP 413 code=AUDIO_TOO_LONG (esperado 413/AUDIO_TOO_LONG)
[PASS] txt_renombrado_a_wav: HTTP 400 code=INVALID_AUDIO (esperado 400/INVALID_AUDIO)  NOTE: el servicio clasifica datos corruptos como INVALID_AUDIO (no UNSUPPORTED_FORMAT)
[PASS] extension_txt_no_soportada: HTTP 400 code=UNSUPPORTED_FORMAT (esperado 400/UNSUPPORTED_FORMAT)
[PASS] sin_campo_audio: HTTP 422 code=VALIDATION_ERROR (body.audio: Field required) (esperado 422/None)
[PASS] servicio_caido: ConnectionError (sin respuesta 5xx)

RESUMEN: 8/8 checks OK
```

---

## 5. Output real — `verify_handoff.sh`

Comando (desde la raíz del monorepo, Windows con Git Bash):

```bash
bash singing-service/integration/verify_handoff.sh
```

Salida real completa (exit code 0):

```
=== singing-service :: verify_handoff ===
service_dir : /c/Users/HP/Documents/PROYECTOS/App-SyncDance/singing-service
python      : /c/Users/HP/Documents/PROYECTOS/App-SyncDance/singing-service/.venv/Scripts/python.exe
analyze_url : http://localhost:5000/api/v1/analyze

-- 1/4 docker compose up + health --
docker compose up: OK
[PASS] health 200 (http://localhost:5000/health)

-- 2/4 fixtures --
fixtures: OK (8 archivos)

-- 3/4 simulacion de worker (absolute + comparative) --
[PASS] simulate absolute
[PASS] simulate comparative

-- 4/4 matriz de errores --
[PASS] test_error_scenarios

=== RESUMEN: 4/4 checks OK ===
RESULTADO: HANDOFF OK
```

---

## 6. Contrato Celery — secciones críticas

Archivo completo: [`singing-service/docs/celery-contract.md`](singing-service/docs/celery-contract.md).

### Sección 4 — Matriz de response por modo

| Campo | `absolute` | `comparative` | Notas |
|---|---|---|---|
| `mode` | `"absolute"` | `"comparative"` | eco del modo usado |
| `pitch.student` | lista | lista | curva F0 del alumno |
| `pitch.reference` | **`null`** | lista | sin referencia en absolute |
| `scores.*` | 0–100 | 0–100 | `afinacion` en absolute = consistencia interna |
| `metrics.pitch_stability_cents` | número | número | desviación interna (cents) |
| `metrics.mean_pitch_hz` | número | número | media de frames con voz |
| `metrics.voiced_ratio` | 0–1 | 0–1 | proporción con voz |
| `metrics.pitch_accuracy` | **`null`** | 0–100 | % de frames dentro de `CENT_THRESHOLD` |
| `metrics.average_cent_deviation` | **`null`** | número | desviación media absoluta (cents) |
| `metrics.rhythm_accuracy` | **`null`** | **`null`** | **ritmo diferido a Sprint 1 (ambos modos)** |
| `segments` | sólo `no_voice` | `out_of_tune` + `no_voice` | sin referencia no hay desafinación |
| `feedback[].code` | `NO_VOICE`, `UNSTABLE_PITCH`, `PITCH_OUT_OF_RANGE` | `OUT_OF_TUNE`, `NO_VOICE` | códigos estables para i18n |
| `timings` | preprocess/pitch/dtw/scoring | idem | `dtw_ms` = comparación temporal simple |

**Crítico:** tolerar `null` en `pitch.reference`, `pitch_accuracy`,
`average_cent_deviation` y `rhythm_accuracy`.

### Sección 5 — Matriz de errores

| Código HTTP | Code | Causa | Acción recomendada para Core |
|---|---|---|---|
| 400 | `UNSUPPORTED_FORMAT` | Extensión no permitida (`.txt`, `.pdf`) | No reintentar; error del cliente |
| 400 | `INVALID_AUDIO` | Contenido corrupto o no decodificable | No reintentar; error del cliente |
| 400 | `MISSING_REFERENCE` | `comparative` sin referencia | No reintentar; bug del cliente |
| 413 | `AUDIO_TOO_LARGE` | > 50 MB | No reintentar |
| 413 | `AUDIO_TOO_LONG` | > 600 s | No reintentar |
| 422 | `INVALID_MODE` | `mode` no válido | No reintentar |
| 422 | `VALIDATION_ERROR` | Campo faltante (p. ej. `audio`) | No reintentar; bug del cliente |
| 500 | `INTERNAL_ERROR` | Fallo del servicio | Reintentar con backoff |
| 503 | `SERVICE_DEGRADED` | FFmpeg o dependencias no disponibles | Reintentar con backoff; alertar |

**Códigos adicionales:** `INVALID_REFERENCE_NOTES`, `NO_AUDIO_TRACK`, `EMPTY_FILE`,
`EMPTY_AUDIO`, `CONVERT_TIMEOUT`, `PITCH_EXTRACT_FAILED` (400, no reintentar),
`SERVICE_BUSY` (429, backoff), `FFMPEG_NOT_FOUND` (500, reintentar 1-2 veces) y
`ConnectionError` (backoff).

> `VALIDATION_ERROR` es la etiqueta de la lista de validación de FastAPI (sin
> `detail.code`). `INTERNAL_ERROR`/`SERVICE_DEGRADED` son etiquetas de manejo del Core;
> el servicio emite `FFMPEG_NOT_FOUND` (500) y `/health` 503 sin `code`.

### Sección 6 — Tarea Celery de ejemplo (código real)

Dependencias del Core: `celery`, `httpx`, `django`. Adaptar `core.models` a los modelos
reales (campos JSON pueden ser `JSONField`).

```python
import os
from pathlib import Path

import httpx
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# Persistencia (adaptar a los modelos reales del Core)
from core.models import Attempt, VocalAnalysis

SINGING_SERVICE_URL = os.environ.get(
    "SINGING_SERVICE_URL", "http://singing-service:5000"
).rstrip("/")
ANALYZE_URL = f"{SINGING_SERVICE_URL}/api/v1/analyze"
TIMEOUT = httpx.Timeout(connect=5.0, read=300.0)

NO_RETRY_STATUS = {400, 413, 422}


def _code(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        return "UNKNOWN"
    if isinstance(detail, dict):
        return detail.get("code", "UNKNOWN")
    return "VALIDATION_ERROR"


def _persist_failure(attempt_id: str, code: str) -> None:
    Attempt.objects.filter(pk=attempt_id).update(status="failed", failure_code=code)


def _persist_result(attempt_id: str, payload: dict) -> None:
    Attempt.objects.filter(pk=attempt_id).update(status="completed")
    VocalAnalysis.objects.update_or_create(
        attempt_id=attempt_id,
        defaults={
            "algorithm_version": payload["algorithm_version"],
            "duration_sec": payload["duration_sec"],
            "scores": payload["scores"],
            "metrics": payload["metrics"],
            "segments": payload["segments"],
            "feedback": payload["feedback"],
        },
    )


@shared_task(
    bind=True,
    autoretry_for=(httpx.TransportError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=330,
    time_limit=360,
)
def analyze_vocal(
    self,
    attempt_id: str,
    routine_id: str,
    audio_path: str,
    reference_path: str | None = None,
) -> dict:
    mode = "comparative" if reference_path else "absolute"
    data = {"attempt_id": attempt_id, "routine_id": routine_id, "mode": mode}
    files = {
        "audio": (
            Path(audio_path).name,
            open(audio_path, "rb"),
            "application/octet-stream",
        )
    }
    reference_handle = None
    if reference_path:
        reference_handle = open(reference_path, "rb")
        files["reference_audio"] = (
            Path(reference_path).name,
            reference_handle,
            "application/octet-stream",
        )

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(ANALYZE_URL, data=data, files=files)

            if response.status_code in NO_RETRY_STATUS:
                code = _code(response)
                _persist_failure(attempt_id, code)
                return {"status": "failed", "code": code}

            if response.status_code == 429:
                raise self.retry(countdown=15)
            if response.status_code >= 500:
                raise self.retry(countdown=30)

            response.raise_for_status()
            analysis_id = response.json()["analysis_id"]

            result = client.get(f"{ANALYZE_URL}/{analysis_id}", timeout=10.0)
            result.raise_for_status()
            payload = result.json()
            _persist_result(attempt_id, payload)
            return {"status": "completed", "analysis_id": analysis_id}
    except SoftTimeLimitExceeded:
        _persist_failure(attempt_id, "WORKER_TIMEOUT")
        raise
    finally:
        files["audio"][1].close()
        if reference_handle is not None:
            reference_handle.close()
```

---

## 7. Checklist de integración para Core (10 ítems verificables)

1. [ ] **`SINGING_SERVICE_URL` configurada** (`http://singing-service:5000`).
   Verificar: `docker compose exec core-api printenv SINGING_SERVICE_URL`.
2. [ ] **Servicio alcanzable desde el worker**.
   Verificar: `docker compose exec core-api curl -fsS http://singing-service:5000/health`
   → `{"status":"ok",...}`.
3. [ ] **POST con `audio`, `attempt_id`, `routine_id`, `mode`**.
   Verificar: `python integration/simulate_celery_worker.py --audio ... --mode absolute`
   → `STATUS: 202`.
4. [ ] **`comparative` envía `reference_audio`**.
   Verificar: el comando comparative del §3 → `STATUS: 202` y `mode: comparative`.
5. [ ] **Timeouts `connect=5`, `read=300`**.
   Verificar: grep del cliente (`httpx.Timeout(connect=5.0, read=300.0)` o
   `requests timeout=(5, 300)`); probar un audio de 10 min.
6. [ ] **4xx no se reintenta**.
   Verificar: con un `.txt`, el worker marca `failed` con `UNSUPPORTED_FORMAT` y no
   reprograma la tarea (test unitario con mock).
7. [ ] **429/5xx/red se reintentan con backoff**.
   Verificar: parar el servicio y encolar; revisar `retries`/`countdown` en Celery.
8. [ ] **GET + persistencia**.
   Verificar: tras un 202, el Core guarda `scores`, `metrics`, `segments`, `feedback`
   (`VocalAnalysis.objects.get(attempt_id=...)`).
9. [ ] **Tolerancia a `null`**.
   Verificar: en absolute, `pitch.reference=null`, `pitch_accuracy=null`,
   `rhythm_accuracy=null`; el serializador del Core no falla.
10. [ ] **Verificación E2E + idempotencia**.
    Verificar: `bash singing-service/integration/verify_handoff.sh` → `4/4 checks OK`;
    repetir el POST con el mismo `attempt_id` → mismo `analysis_id`.

---

## 8. Notas y limitaciones

- **Campo `audio`:** el contrato canónico usa `audio`; `file` era el nombre previo
  (corregido en `CONSISTENCY_FIX.md`). Enviar `file` ahora produce
  `422 {"detail":[{"loc":["body","audio"],...}]}`.
- **`.txt` renombrado `.wav`:** devuelve `400 INVALID_AUDIO` (datos corruptos).
  `UNSUPPORTED_FORMAT` se reserva para extensión/codec no soportado (probado con `.txt`).
- **`rhythm_accuracy`:** siempre `null` en v1 (ritmo diferido a Sprint 1). No usarlo
  para puntuar.
- **`include_contour`:** el flag se acepta en el script pero el servicio v1 lo ignora
  (`pitch_contour` no implementado).
- **Primer request en frío:** el JIT de numba/librosa puede tardar ~25 s en el primer
  análisis con audio tras arrancar el contenedor (observado: `ELAPSED_MS: 25278`); los
  siguientes bajan a ~1.2 s. Por eso `read=300 s` y `soft_time_limit=330`.
- **Windows:** `verify_handoff.sh` requiere Git Bash o WSL. Los scripts Python son
  multiplataforma (`pathlib`, sin rutas hardcodeadas).
- **Fixtures:** se generan en `integration/fixtures/` y están en `.gitignore`; no se
  commitean binarios.
- **Docker:** `verify_handoff.sh` intenta `docker compose up -d singing-service`; si no
  hay Docker, asume que el servicio ya está corriendo.

## Historial de versiones

| Versión | Fecha | Cambios clave |
|---|---|---|
| v0.1.0 | 2026-10-06 | Versión inicial con librosa.pyin |
| v0.2.0 | 2026-11-12 | Contrato híbrido absolute/comparative, ffmpeg, M4A/AAC/MP3/OGG |
| v0.2.1 | 2026-11-14 | Auditoría v0.2.0: OpenAPI completo, manual USAGE, SWAGGER_GUIDE |
| v0.2.2 | 2026-11-14 | X-Request-ID middleware, UNHANDLED_ERROR, nota V-01, fingerprint |


