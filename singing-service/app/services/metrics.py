"""Métricas del contrato híbrido (Sprint 0 — gap O1).

`absolute` no tiene referencia: mide estabilidad interna (desviación de cada
frame respecto a la mediana en cents), pitch medio y proporción con voz.
`comparative` compara contra la referencia con `services/compare.align_by_time`.
"""

from __future__ import annotations

import math
from statistics import median, pstdev

from app.schemas.analyze import Metrics, PitchPoint
from app.services.compare import ComparedFrame

# Rango humano de canto (HU-43): fuera de él se emite PITCH_OUT_OF_RANGE.
HUMAN_F0_MIN_HZ = 80.0
HUMAN_F0_MAX_HZ = 1100.0


def voiced_frequencies(points: list[PitchPoint]) -> list[float]:
    return [p.f0 for p in points if p.voiced and p.f0 is not None]


def voiced_ratio(points: list[PitchPoint]) -> float:
    if not points:
        return 0.0
    return round(len(voiced_frequencies(points)) / len(points), 4)


def out_of_range_count(points: list[PitchPoint]) -> int:
    return sum(
        1
        for f0 in voiced_frequencies(points)
        if f0 < HUMAN_F0_MIN_HZ or f0 > HUMAN_F0_MAX_HZ
    )


def absolute_metrics(points: list[PitchPoint]) -> Metrics:
    """Métricas sin referencia: estabilidad interna, pitch medio y voiced_ratio."""
    freqs = voiced_frequencies(points)
    if not freqs:
        return Metrics(
            pitch_stability_cents=None,
            mean_pitch_hz=None,
            voiced_ratio=voiced_ratio(points),
            pitch_accuracy=None,
            rhythm_accuracy=None,
            average_cent_deviation=None,
        )

    center = median(freqs)
    cents = [1200.0 * math.log2(f0 / center) for f0 in freqs]
    stability = pstdev(cents) if len(cents) >= 2 else 0.0

    return Metrics(
        pitch_stability_cents=round(stability, 1),
        mean_pitch_hz=round(sum(freqs) / len(freqs), 2),
        voiced_ratio=voiced_ratio(points),
        pitch_accuracy=None,
        rhythm_accuracy=None,
        average_cent_deviation=None,
    )


def comparative_metrics(
    points: list[PitchPoint],
    aligned: list[ComparedFrame],
    *,
    cent_threshold: int,
) -> Metrics:
    """Métricas contra referencia: accuracy, desviación media y estabilidad."""
    freqs = voiced_frequencies(points)
    matched = [f.cents for f in aligned if f.cents is not None]

    if not matched:
        return Metrics(
            pitch_stability_cents=None,
            mean_pitch_hz=round(sum(freqs) / len(freqs), 2) if freqs else None,
            voiced_ratio=voiced_ratio(points),
            pitch_accuracy=None,
            rhythm_accuracy=None,
            average_cent_deviation=None,
        )

    within = sum(1 for c in matched if abs(c) <= cent_threshold)
    stability = pstdev(matched) if len(matched) >= 2 else 0.0

    return Metrics(
        pitch_stability_cents=round(stability, 1),
        mean_pitch_hz=round(sum(freqs) / len(freqs), 2) if freqs else None,
        voiced_ratio=voiced_ratio(points),
        pitch_accuracy=round(100.0 * within / len(matched), 1),
        rhythm_accuracy=None,
        average_cent_deviation=round(sum(abs(c) for c in matched) / len(matched), 1),
    )
