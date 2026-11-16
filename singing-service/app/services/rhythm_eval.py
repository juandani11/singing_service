"""Evaluación de ritmo (HU-S1-01): tempo, onsets y estabilidad.

`librosa.beat.beat_track` estima el tempo y `librosa.onset.onset_detect`
(wait=5) detecta onsets. La estabilidad se mide con el coeficiente de
variación de los intervalos entre onsets; `rhythm_accuracy` combina esa
estabilidad con la desviación de tempo cuando el cliente envía `tempo_bpm`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import librosa
import numpy as np

_BEAT_HOP = 960  # 60 ms a 16 kHz: beat_track ~3x más rápido que hop 512
_ONSET_HOP = 512  # 32 ms a 16 kHz: resolución validada para pulsos de 40 ms
_ONSET_WAIT = 5  # 160 ms a 16 kHz; < periodo de 120 BPM
_START_GUARD_SEC = 0.1  # evita el onset artificial del inicio de archivo
_LONG_INTERVAL_FACTOR = 2.0


@dataclass
class RhythmResult:
    estimated_tempo_bpm: float | None
    onset_count: int
    onset_intervals_cv: float | None
    onset_stability: float | None
    tempo_deviation_bpm: float | None
    rhythm_accuracy: float | None
    feedback_items: list[dict] = field(default_factory=list)


def _empty_result() -> RhythmResult:
    return RhythmResult(
        estimated_tempo_bpm=None,
        onset_count=0,
        onset_intervals_cv=None,
        onset_stability=None,
        tempo_deviation_bpm=None,
        rhythm_accuracy=None,
        feedback_items=[],
    )


def _severity(ratio: float) -> str:
    return "high" if ratio >= 3.0 else "medium"


def _feedback_items(
    onsets: np.ndarray, intervals: np.ndarray
) -> list[dict]:
    if intervals.size == 0:
        return []
    median = float(np.median(intervals))
    items: list[dict] = []
    for index, interval in enumerate(intervals):
        if float(interval) <= _LONG_INTERVAL_FACTOR * median:
            continue
        interval_ms = int(round(float(interval) * 1000))
        items.append(
            {
                "start": round(float(onsets[index]), 3),
                "end": round(float(onsets[index + 1]), 3),
                "type": "out_of_rhythm",
                "severity": _severity(float(interval) / median),
                "interval_ms": interval_ms,
                "message": (
                    f"Intervalo de {interval_ms} ms entre onsets; "
                    "mantén un pulso estable."
                ),
            }
        )
    return items


def _analyze(
    y: np.ndarray, sr: int, tempo_bpm_hint: float | None
) -> RhythmResult:
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr, hop_length=_BEAT_HOP)
    raw_tempo = float(np.atleast_1d(tempo)[0])
    estimated = (
        round(raw_tempo, 1)
        if np.isfinite(raw_tempo) and raw_tempo > 0
        else None
    )

    onsets = librosa.onset.onset_detect(
        y=y,
        sr=sr,
        hop_length=_ONSET_HOP,
        units="time",
        wait=_ONSET_WAIT,
    )
    onsets = onsets[onsets > _START_GUARD_SEC]
    onset_count = int(len(onsets))

    cv: float | None = None
    stability: float | None = None
    intervals = np.diff(onsets) if onset_count >= 2 else np.asarray([])
    if onset_count >= 2 and intervals.size:
        mean = float(np.mean(intervals))
        if mean > 0:
            cv = float(np.std(intervals) / mean)
            stability = round(max(0.0, min(100.0, 100.0 * (1.0 - cv))), 1)

    deviation: float | None = None
    if tempo_bpm_hint is not None and estimated is not None:
        deviation = round(estimated - float(tempo_bpm_hint), 1)

    accuracy: float | None = None
    if stability is not None:
        if deviation is not None:
            tempo_score = max(0.0, 100.0 - 2.0 * abs(deviation))
            accuracy = round(
                max(0.0, min(100.0, 0.5 * stability + 0.5 * tempo_score)),
                1,
            )
        else:
            accuracy = stability

    return RhythmResult(
        estimated_tempo_bpm=estimated,
        onset_count=onset_count,
        onset_intervals_cv=round(cv, 4) if cv is not None else None,
        onset_stability=stability,
        tempo_deviation_bpm=deviation,
        rhythm_accuracy=accuracy,
        feedback_items=_feedback_items(onsets, intervals),
    )


def analyze_rhythm(
    y: np.ndarray, sr: int, tempo_bpm_hint: float | None = None
) -> RhythmResult:
    """Analiza tempo/onsets de la señal y calcula `rhythm_accuracy` 0-100."""
    try:
        if y.size == 0:
            return _empty_result()
        return _analyze(y, sr, tempo_bpm_hint)
    except Exception:  # audio degenerado: el análisis de pitch ya validó el WAV
        return _empty_result()
