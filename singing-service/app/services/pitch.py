"""Extracción de pitch F0 (Sprint 3 — plan §4): librosa.pyin + sin-voz (HU-43).

- `pyin` sobre el WAV 16 kHz mono que produce `services/preprocess`.
- Detección sin voz: frames no voceados (`voiced_flag` / F0 no finito) →
  `f0: null` en el contrato y `silence_pct` del resultado (HU-46 distingue
  después *sin voz* de *desafinación*; los segmentos llegan en S4).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np

from app.core.config import settings
from app.schemas.analyze import PitchPoint
from app.services.preprocess import PreprocessError

# Rango del detector algo más amplio que el rango humano (80-1100 Hz) para
# reportar `PITCH_OUT_OF_RANGE` (HU-43). fmin=65 evita que el ruido de silencio
# se detecte como una nota grave espuria.
_FMIN = 65.0
_FMAX = 1600.0
_FRAME_LENGTH = 2048


@dataclass(frozen=True)
class PitchExtraction:
    points: list[PitchPoint]
    silence_pct: int
    pitch_ms: int


def extract_pitch(path: Path, *, hop_length: int) -> PitchExtraction:
    """Extrae la curva F0 de un WAV 16 kHz mono con pyin."""
    started = time.perf_counter()
    sr = settings.sample_rate
    try:
        y, _ = librosa.load(str(path), sr=sr, mono=True)
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=_FMIN,
            fmax=_FMAX,
            sr=sr,
            hop_length=hop_length,
            frame_length=_FRAME_LENGTH,
        )
    except Exception as exc:  # señal degenerada u otro fallo de decodificación
        raise PreprocessError(
            "PITCH_EXTRACT_FAILED",
            "No se pudo extraer el pitch del audio",
            400,
        ) from exc

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    points: list[PitchPoint] = []
    for t, freq, voiced in zip(times, f0, voiced_flag, strict=True):
        has_voice = bool(voiced) and bool(np.isfinite(freq))
        points.append(
            PitchPoint(
                t=round(float(t), 3),
                f0=round(float(freq), 2) if has_voice else None,
                voiced=has_voice,
            )
        )

    if not points:
        raise PreprocessError("EMPTY_AUDIO", "El audio no contiene muestras", 400)

    unvoiced = sum(1 for p in points if not p.voiced)
    return PitchExtraction(
        points=points,
        silence_pct=round(unvoiced * 100 / len(points)),
        pitch_ms=int((time.perf_counter() - started) * 1000),
    )
