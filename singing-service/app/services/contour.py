"""Curva de pitch downsampleada para el frontend (HU-S1-09).

La extracción F0 (`pitch.py`) queda intacta: aquí solo se seleccionan frames y se
formatea cada punto con su nota temperada. Objetivo ~10 Hz, máximo 6000 puntos.

Con `hop_ms=32`, `step = round(100/32) = 3` → un punto cada 96 ms (~10.42 Hz).
Si el resultado supera 6000 puntos (audios > ~9.6 min), se seleccionan 6000
índices equiespaciados sobre la curva original: el hop efectivo crece y la
frecuencia baja de 10 Hz (p. ej. 30 min → ~3.33 Hz), siempre respetando el límite.
"""

from __future__ import annotations

import numpy as np

from app.schemas.analyze import PitchContour, PitchContourPoint, PitchPoint
from app.services.align import hz_to_note

CONTOUR_DOWNSAMPLE_HZ = 10
CONTOUR_MAX_POINTS = 6000


def _step_for(hop_ms: int) -> int:
    """Frames a saltar para acercarse a `CONTOUR_DOWNSAMPLE_HZ`."""
    return max(1, round((1.0 / CONTOUR_DOWNSAMPLE_HZ) / (hop_ms / 1000.0)))


def _indices(n_points: int, step: int) -> list[int]:
    if n_points <= 0:
        return []
    indices = np.arange(0, n_points, step, dtype=int)
    if indices.size > CONTOUR_MAX_POINTS:
        indices = np.linspace(0, n_points - 1, CONTOUR_MAX_POINTS, dtype=int)
    return indices.tolist()


def _to_contour_point(point: PitchPoint) -> PitchContourPoint:
    voiced = bool(point.voiced and point.f0 is not None)
    return PitchContourPoint(
        t=point.t,
        f0=point.f0 if voiced else None,
        note=hz_to_note(point.f0) if voiced else None,
        voiced=voiced,
    )


def build_contour(points: list[PitchPoint], *, hop_ms: int) -> list[PitchContourPoint]:
    """Downsamplea una curva F0 a ~10 Hz (máx. 6000 puntos)."""
    step = _step_for(hop_ms)
    return [_to_contour_point(points[i]) for i in _indices(len(points), step)]


def build_pitch_contour(
    student_points: list[PitchPoint],
    reference_points: list[PitchPoint] | None,
    *,
    hop_ms: int,
) -> PitchContour:
    """Construye `pitch_contour` (student + reference opcional)."""
    return PitchContour(
        student=build_contour(student_points, hop_ms=hop_ms),
        reference=(
            build_contour(reference_points, hop_ms=hop_ms)
            if reference_points is not None
            else None
        ),
        downsample_hz=CONTOUR_DOWNSAMPLE_HZ,
    )
