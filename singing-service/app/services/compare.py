"""Comparación temporal simple alumno vs referencia (Sprint 0 — gap O1).

NO usa FastDTW: remuestrea la curva de referencia sobre los tiempos del alumno
(nearest-neighbor con tolerancia) y calcula la desviación en cents sólo en los
frames con voz en ambas curvas. El alineamiento avanzado (DTW) queda para
Sprint 1; `services/align.py` se conserva como referencia de esa iteración.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from app.schemas.analyze import PitchPoint
from app.services.align import note_to_hz


@dataclass(frozen=True)
class ComparedFrame:
    """Desviación del frame del alumno vs la referencia en el mismo instante."""

    cents: float | None
    ref_f0: float | None


def align_by_time(
    student: list[PitchPoint],
    reference: list[PitchPoint],
    *,
    tolerance_sec: float = 0.1,
) -> list[ComparedFrame]:
    """Empareja por tiempo (no por DTW) cada frame del alumno con la referencia."""
    if not student:
        return []

    ref_times = np.array(
        [p.t for p in reference if p.voiced and p.f0 is not None], dtype=float
    )
    ref_f0s = np.array(
        [p.f0 for p in reference if p.voiced and p.f0 is not None], dtype=float
    )

    frames: list[ComparedFrame] = []
    for point in student:
        if not point.voiced or point.f0 is None or ref_times.size == 0:
            frames.append(ComparedFrame(cents=None, ref_f0=None))
            continue

        idx = int(np.searchsorted(ref_times, point.t))
        candidates = [i for i in (idx - 1, idx) if 0 <= i < ref_times.size]
        best = min(candidates, key=lambda i: abs(ref_times[i] - point.t))
        if abs(ref_times[best] - point.t) > tolerance_sec:
            frames.append(ComparedFrame(cents=None, ref_f0=None))
            continue

        ref_f0 = float(ref_f0s[best])
        cents = round(1200.0 * float(np.log2(point.f0 / ref_f0)), 1)
        frames.append(ComparedFrame(cents=cents, ref_f0=ref_f0))
    return frames


def parse_reference_notes(raw: str) -> list[PitchPoint]:
    """JSON de referencia → curva F0. Acepta `f0` (Hz), `note` (p. ej. "A4") o `midi`.

    Formato: `[{"t": 0.0, "f0": 440.0}, {"t": 0.5, "note": "B4"}, ...]`
    (también válido `{"notes": [...]}`). Error de formato → ValueError.
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("reference_notes no es JSON válido") from exc

    if isinstance(payload, dict):
        payload = payload.get("notes")
    if not isinstance(payload, list) or not payload:
        raise ValueError("reference_notes debe ser una lista JSON no vacía")

    points: list[PitchPoint] = []
    for item in payload:
        if not isinstance(item, dict) or "t" not in item:
            raise ValueError("cada nota requiere 't' y 'f0', 'note' o 'midi'")
        try:
            t = float(item["t"])
            if "f0" in item:
                f0 = float(item["f0"])
            elif "note" in item:
                f0 = note_to_hz(str(item["note"]))
            elif "midi" in item:
                f0 = 440.0 * (2.0 ** ((float(item["midi"]) - 69) / 12.0))
            else:
                raise ValueError("cada nota requiere 'f0', 'note' o 'midi'")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"nota inválida en reference_notes: {item!r}") from exc
        if t < 0 or f0 <= 0:
            raise ValueError(f"nota fuera de rango en reference_notes: {item!r}")
        points.append(PitchPoint(t=round(t, 3), f0=round(f0, 2), voiced=True))

    points.sort(key=lambda p: p.t)
    return points
