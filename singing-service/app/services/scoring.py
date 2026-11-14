"""Scoring 0-100 (Sprint 4 — plan §4): fórmulas documentadas en docs/scoring.md.

- `afinacion`: % de frames emparejados dentro de `cent_threshold` (HU-44).
- `estabilidad`: 100 − 2·σ de los cents (wobble); 100 = constante.
- `control_volumen`: 100 − 100·CV del RMS voceado (variación de intensidad).
- `vocal`: 0.5·afinación + 0.25·estabilidad + 0.25·control de volumen.
"""

from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np

from app.schemas.analyze import PitchPoint, Scores

_RMS_FRAME = 2048


def _control_volumen(
    wav: Path, points: list[PitchPoint], hop_length: int, sample_rate: int
) -> int:
    try:
        y, _ = librosa.load(str(wav), sr=sample_rate, mono=True)
        rms = librosa.feature.rms(y=y, frame_length=_RMS_FRAME, hop_length=hop_length)[0]
    except Exception:
        return 0

    n = min(len(rms), len(points))
    if n == 0:
        return 0
    voiced_rms = np.array([rms[i] for i in range(n) if points[i].voiced])
    if voiced_rms.size == 0:
        return 0
    mean = float(np.mean(voiced_rms))
    if mean <= 0:
        return 0
    cv = float(np.std(voiced_rms) / mean)
    return int(round(max(0.0, 100.0 - cv * 100.0)))


def compute_scores(
    *,
    cents: list[float | None],
    points: list[PitchPoint],
    silence_pct: int,
    student_wav: Path,
    hop_length: int,
    sample_rate: int,
    cent_threshold: int,
) -> Scores:
    """Calcula los scores 0-100 a partir del alineamiento y del audio."""
    matched = [c for c in cents if c is not None]
    if matched:
        within = sum(1 for c in matched if abs(c) <= cent_threshold)
        afinacion = round(100 * within / len(matched))
        stdev = float(np.std(matched)) if len(matched) >= 2 else 0.0
        estabilidad = int(round(max(0.0, 100.0 - stdev * 2.0)))
    else:
        afinacion = 0
        estabilidad = 0

    control_volumen = _control_volumen(student_wav, points, hop_length, sample_rate)
    vocal = round(0.5 * afinacion + 0.25 * estabilidad + 0.25 * control_volumen)

    return Scores(
        vocal=vocal,
        afinacion=afinacion,
        estabilidad=estabilidad,
        control_volumen=control_volumen,
        silence_pct=silence_pct,
    )


def compute_absolute_scores(
    *,
    points: list[PitchPoint],
    silence_pct: int,
    student_wav: Path,
    hop_length: int,
    sample_rate: int,
    cent_threshold: int,
) -> Scores:
    """Scores sin referencia: consistencia interna (mediana) + volumen."""
    freqs = [p.f0 for p in points if p.voiced and p.f0 is not None]
    if freqs:
        center = float(np.median(freqs))
        cents = [1200.0 * float(np.log2(f0 / center)) for f0 in freqs]
        within = sum(1 for c in cents if abs(c) <= cent_threshold)
        afinacion = round(100 * within / len(cents))
        stdev = float(np.std(cents)) if len(cents) >= 2 else 0.0
        estabilidad = int(round(max(0.0, 100.0 - stdev * 2.0)))
    else:
        afinacion = 0
        estabilidad = 0

    control_volumen = _control_volumen(student_wav, points, hop_length, sample_rate)
    vocal = round(0.5 * afinacion + 0.25 * estabilidad + 0.25 * control_volumen)

    return Scores(
        vocal=vocal,
        afinacion=afinacion,
        estabilidad=estabilidad,
        control_volumen=control_volumen,
        silence_pct=silence_pct,
    )
