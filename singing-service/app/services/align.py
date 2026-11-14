"""Alineación temporal y segmentación (Sprint 4 — plan §4): FastDTW + cents.

HU-44: desviación en cents frame a frame alineando alumno vs referencia con
FastDTW. HU-45: segmentos `out_of_tune`/`no_voice` (HU-46 los distingue).

Notas:
- `fastdtw` convierte las entradas a float (`None` → `nan`), por eso la
  distancia trata `nan` como "sin voz" (penalización `VOICE_GAP_CENTS`).
- Segmentos: runs con duración mínima; gravedad `medium`/`high` según
  `settings.cent_threshold` (los ejemplos Figma 45c→medium, 72c→high
  quedan cubiertos por los valores congelados del mock).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from statistics import median

import numpy as np
from fastdtw import fastdtw

from app.schemas.analyze import PitchPoint, Segment, Severity

VOICE_GAP_CENTS = 600.0  # coste DTW cuando una curva tiene voz y la otra no
OUT_OF_TUNE_MIN_CENTS = 30.0  # umbral para formar un segmento desafinado
NO_VOICE_MIN_SEC = 0.6  # duración mínima de un segmento sin voz
OUT_OF_TUNE_MIN_SEC = 0.4  # duración mínima de un segmento desafinado

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass(frozen=True)
class AlignedFrame:
    """Resultado del emparejamiento DTW para un frame del alumno."""

    cents: float | None  # desviación vs referencia; None = no juzgable
    ref_f0: float | None  # F0 de referencia emparejado (para la nota esperada)


def _frame_distance(a: float, b: float) -> float:
    a_bad = not bool(np.isfinite(a))
    b_bad = not bool(np.isfinite(b))
    if a_bad and b_bad:
        return 0.0
    if a_bad or b_bad:
        return VOICE_GAP_CENTS
    return abs(1200.0 * math.log2(a / b))


def hz_to_note(freq: float | None) -> str | None:
    """Frecuencia → nombre de nota en temperamento igual (A4 = 440 Hz)."""
    if freq is None or freq <= 0:
        return None
    midi = int(round(12.0 * math.log2(freq / 440.0))) + 69
    return f"{_NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def note_to_hz(note: str) -> float:
    """Nombre de nota (p. ej. "A4", "F#3") → frecuencia en Hz (A4 = 440)."""
    match = re.fullmatch(r"([A-Ga-g])(#|b)?(-?\d+)", note.strip())
    if not match:
        raise ValueError(f"Nota inválida: {note!r}")
    name, accidental, octave = match.groups()
    semitone = _NOTE_NAMES.index(name.upper())
    if accidental == "#":
        semitone += 1
    elif accidental == "b":
        semitone -= 1
    midi = (int(octave) + 1) * 12 + semitone
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def align_frames(
    student: list[PitchPoint], reference: list[PitchPoint]
) -> list[AlignedFrame]:
    """Empareja cada frame del alumno con la referencia vía FastDTW (HU-44)."""
    if not student or not reference:
        return [AlignedFrame(cents=None, ref_f0=None) for _ in student]

    stu_f0 = np.array(
        [p.f0 if p.voiced and p.f0 is not None else np.nan for p in student],
        dtype=float,
    )
    ref_f0 = np.array(
        [p.f0 if p.voiced and p.f0 is not None else np.nan for p in reference],
        dtype=float,
    )

    _, path = fastdtw(stu_f0, ref_f0, dist=_frame_distance)

    # fastdtw puede emparejar un mismo i con varios j consecutivos → mediana
    paired: dict[int, list[int]] = {}
    for i, j in path:
        paired.setdefault(i, []).append(j)

    frames: list[AlignedFrame] = []
    for i, point in enumerate(student):
        js = paired.get(i)
        if not js or not point.voiced or point.f0 is None:
            frames.append(AlignedFrame(cents=None, ref_f0=None))
            continue
        j = int(median(js))
        j = min(max(j, 0), len(reference) - 1)
        ref_point = reference[j]
        if not ref_point.voiced or ref_point.f0 is None:
            frames.append(AlignedFrame(cents=None, ref_f0=None))
            continue
        cents = round(1200.0 * math.log2(point.f0 / ref_point.f0), 1)
        frames.append(AlignedFrame(cents=cents, ref_f0=ref_point.f0))
    return frames


def _median(values: list[float]) -> float | None:
    return median(values) if values else None


def build_segments(
    points: list[PitchPoint],
    aligned: list[AlignedFrame],
    *,
    hop_ms: int,
    duration_sec: float,
    cent_threshold: int,
) -> list[Segment]:
    """Segmenta los runs sin voz / desafinados con duración mínima (HU-45)."""
    if not points:
        return []
    hop_sec = hop_ms / 1000.0

    classes: list[str] = []
    for point, frame in zip(points, aligned, strict=True):
        if not point.voiced:
            classes.append("no_voice")
        elif frame.cents is not None and abs(frame.cents) >= OUT_OF_TUNE_MIN_CENTS:
            classes.append("out_of_tune")
        else:
            classes.append("ok")

    segments: list[Segment] = []
    run_start = 0
    for idx in range(len(classes) + 1):
        if idx < len(classes) and classes[idx] == classes[run_start]:
            continue
        kind = classes[run_start]
        start = points[run_start].t
        end = min(points[idx - 1].t + hop_sec, duration_sec)
        run_sec = end - start

        if kind == "no_voice" and run_sec >= NO_VOICE_MIN_SEC:
            segments.append(
                Segment(start=start, end=end, type="no_voice", severity="info")
            )
        elif kind == "out_of_tune" and run_sec >= OUT_OF_TUNE_MIN_SEC:
            run_points = points[run_start:idx]
            run_frames = aligned[run_start:idx]
            deltas = [
                abs(f.cents) for f in run_frames if f.cents is not None
            ]
            delta = round(max(deltas)) if deltas else 0
            severity: Severity = "medium" if delta < cent_threshold else "high"
            sung_f0 = [p.f0 for p in run_points if p.voiced and p.f0 is not None]
            expected_f0 = [f.ref_f0 for f in run_frames if f.ref_f0 is not None]
            segments.append(
                Segment(
                    start=start,
                    end=end,
                    type="out_of_tune",
                    expected_note=hz_to_note(_median(expected_f0)),
                    sung_note=hz_to_note(_median(sung_f0)),
                    delta_cents=delta,
                    severity=severity,
                )
            )
        run_start = idx
    return segments
