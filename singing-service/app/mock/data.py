"""Respuestas simuladas coherentes con el prototipo Figma (Sprints 1-4, plan §2.2).

Valores de la pantalla "02 · Canto — Análisis vocal":
score vocal 71, afinación 71, estabilidad 66, control de volumen 80, sin voz 4%,
segmentos 00:12 (45 cents), 00:27 (sin voz), 00:41 (72 cents).
"""

from __future__ import annotations

import math

from app.schemas.analyze import (
    AnalysisMode,
    AnalysisResult,
    FeedbackItem,
    Metrics,
    PitchCurves,
    PitchPoint,
    Scores,
    Segment,
    Timings,
)

_DURATION_SEC = 45.0
_HOP_MS = 46
_N_FRAMES = int(_DURATION_SEC * 1000 / _HOP_MS)

# Ventanas de error conocidas (segundos) — deben coincidir con `segments`
_TUNE_WINDOW_A = (12.0, 12.6)
_TUNE_WINDOW_B = (41.0, 41.6)
_NO_VOICE_WINDOW = (27.1, 28.0)


def _reference_f0(t: float) -> float:
    """Frase cantada simulada de la referencia (base ~220 Hz)."""
    return 220.0 * (1.0 + 0.08 * math.sin(2 * math.pi * 0.21 * t))


def _student_cents(t: float) -> float:
    """Desviación del alumno en cents: base leve + picos de los segmentos."""
    if _TUNE_WINDOW_A[0] <= t < _TUNE_WINDOW_A[1]:
        return 45.0
    if _TUNE_WINDOW_B[0] <= t < _TUNE_WINDOW_B[1]:
        return 72.0
    return 8.0 + 6.0 * math.sin(2 * math.pi * 0.13 * t)


def _student_voiced(t: float) -> bool:
    """Entrada sin voz al inicio + pausa del segmento 00:27."""
    if t < 0.4:
        return False
    if _NO_VOICE_WINDOW[0] <= t < _NO_VOICE_WINDOW[1]:
        return False
    return True


def _curves() -> PitchCurves:
    student: list[PitchPoint] = []
    reference: list[PitchPoint] = []
    for i in range(_N_FRAMES):
        t = round(i * _HOP_MS / 1000.0, 3)
        voiced = _student_voiced(t)
        f0_ref = _reference_f0(t)
        f0_stu = f0_ref * (2.0 ** (_student_cents(t) / 1200.0))
        student.append(PitchPoint(t=t, f0=round(f0_stu, 2) if voiced else None, voiced=voiced))
        reference.append(PitchPoint(t=t, f0=round(f0_ref, 2), voiced=True))
    return PitchCurves(student=student, reference=reference, hop_ms=_HOP_MS)


def build_result(
    analysis_id: str,
    attempt_id: str,
    routine_id: str,
    *,
    duration_sec: float = _DURATION_SEC,
    preprocess_ms: int = 180,
    algorithm_version: str = "1.0.0-mock",
    mode: AnalysisMode = "absolute",
    metrics: Metrics | None = None,
    pitch: PitchCurves | None = None,
    silence_pct: int = 4,
    scores: Scores | None = None,
    segments: list[Segment] | None = None,
    feedback: list[FeedbackItem] | None = None,
    pitch_ms: int = 640,
    dtw_ms: int = 210,
    scoring_ms: int = 30,
) -> AnalysisResult:
    """Fixture con defaults del prototipo Figma (plan §2.2).

    No está expuesto por la API desde el contrato híbrido (Sprint 0): se
    conserva para demos offline. Los tests/E2E usan el pipeline real.
    """
    if pitch is None:
        curves = _curves()
        student = [p for p in curves.student if p.t <= duration_sec]
        reference = [p for p in curves.reference if p.t <= duration_sec]
        hop_ms = curves.hop_ms
    else:
        student = [p for p in pitch.student if p.t <= duration_sec]
        reference = [p for p in pitch.reference if p.t <= duration_sec]
        hop_ms = pitch.hop_ms

    if scores is None:
        scores = Scores(
            vocal=71, afinacion=71, estabilidad=66, control_volumen=80, silence_pct=silence_pct
        )
    if segments is None:
        segments = _segments()
    segments = [s for s in segments if s.end <= duration_sec]
    if feedback is None:
        feedback = _feedback(scores.silence_pct) if segments else []

    return AnalysisResult(
        analysis_id=analysis_id,
        attempt_id=attempt_id,
        routine_id=routine_id,
        status="completed",
        mode=mode,
        algorithm_version=algorithm_version,
        duration_sec=duration_sec,
        pitch=PitchCurves(
            student=student,
            reference=reference if mode == "comparative" else None,
            hop_ms=hop_ms,
        ),
        segments=segments,
        scores=scores,
        metrics=metrics or Metrics(),
        feedback=feedback,
        timings=Timings(
            preprocess_ms=preprocess_ms,
            pitch_ms=pitch_ms,
            dtw_ms=dtw_ms,
            scoring_ms=scoring_ms,
        ),
    )


def _segments() -> list[Segment]:
    return [
        Segment(
            start=_TUNE_WINDOW_A[0],
            end=_TUNE_WINDOW_A[1],
            type="out_of_tune",
            expected_note="E4",
            sung_note="F#4",
            delta_cents=45,
            severity="medium",
        ),
        Segment(
            start=_NO_VOICE_WINDOW[0],
            end=_NO_VOICE_WINDOW[1],
            type="no_voice",
            severity="info",
        ),
        Segment(
            start=_TUNE_WINDOW_B[0],
            end=_TUNE_WINDOW_B[1],
            type="out_of_tune",
            expected_note="A4",
            sung_note="G#4",
            delta_cents=72,
            severity="high",
        ),
    ]


def _feedback(silence_pct: int = 4) -> list[FeedbackItem]:
    return [
        FeedbackItem(
            code="SUSTAIN_2ND_BAR",
            message="Sostén la afinación en el segundo compás: hasta 72 cents de desviación.",
        ),
        FeedbackItem(
            code="LOW_VOLUME_ENTRY",
            message=(
                f"Detectamos {silence_pct}% del tiempo sin voz; "
                "es distinto a una desafinación."
            ),
        ),
    ]
