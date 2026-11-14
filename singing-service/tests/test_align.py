"""Tests de alineación, segmentación, scoring y feedback (Sprint 4 — plan §4)."""

import io
import math
import struct
import wave
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AcceptedResponse, AnalysisResult, PitchPoint, Segment
from app.services.align import align_frames, build_segments, hz_to_note
from app.services.feedback import build_feedback
from app.services.scoring import compute_scores

client = TestClient(app)

_HOP = 0.032  # 512 @ 16 kHz


def _points(freqs: list[float | None]) -> list[PitchPoint]:
    return [
        PitchPoint(t=round(i * _HOP, 3), f0=f, voiced=f is not None)
        for i, f in enumerate(freqs)
    ]


def _tone_wav(duration: float, freq: float, silence: float = 0.5) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        frames = bytearray()
        silence_frames = int(silence * 16000)
        for i in range(int(duration * 16000)):
            if i < silence_frames:
                sample = 0
            else:
                sample = int(10000 * math.sin(2 * math.pi * freq * i / 16000))
            frames += struct.pack("<h", sample)
        w.writeframes(bytes(frames))
    return buf.getvalue()


# --- alineación (HU-44) -----------------------------------------------------


def test_align_identical_curves_give_zero_cents() -> None:
    points = _points([440.0] * 30)
    aligned = align_frames(points, points)
    assert len(aligned) == 30
    assert all(f.cents is not None and abs(f.cents) < 1.0 for f in aligned)


def test_align_offset_gives_expected_cents() -> None:
    student = _points([460.0] * 30)
    reference = _points([440.0] * 30)
    aligned = align_frames(student, reference)
    # 1200·log2(460/440) ≈ 77.4 cents
    assert all(f.cents is not None and 70.0 <= f.cents <= 85.0 for f in aligned)


def test_align_unvoiced_frames_are_not_judged() -> None:
    student = _points([None, None, 440.0, 440.0])
    reference = _points([None, None, 440.0, 440.0])
    aligned = align_frames(student, reference)
    assert aligned[0].cents is None and aligned[1].cents is None
    assert aligned[2].cents is not None and abs(aligned[2].cents) < 1.0


def test_align_handles_different_lengths() -> None:
    student = _points([440.0] * 20)
    reference = _points([440.0] * 45)
    aligned = align_frames(student, reference)
    assert len(aligned) == 20
    assert all(f.cents is not None and abs(f.cents) < 5.0 for f in aligned)


def test_hz_to_note() -> None:
    assert hz_to_note(440.0) == "A4"
    assert hz_to_note(220.0) == "A3"
    assert hz_to_note(261.63) == "C4"
    assert hz_to_note(None) is None


# --- segmentos (HU-45) ------------------------------------------------------


def test_build_segments_out_of_tune_high_severity() -> None:
    points = _points([460.0] * 100)  # 3.2 s
    aligned = align_frames(points, _points([440.0] * 100))
    segments = build_segments(
        points, aligned, hop_ms=32, duration_sec=3.2, cent_threshold=50
    )
    assert len(segments) == 1
    seg = segments[0]
    assert seg.type == "out_of_tune"
    assert seg.delta_cents is not None and 70 <= seg.delta_cents <= 85
    assert seg.severity == "high"  # ≥ cent_threshold (50)
    assert seg.expected_note == "A4" and seg.sung_note == "A#4"
    assert seg.end <= 3.2


def test_build_segments_medium_below_threshold() -> None:
    points = _points([440.0] * 100)
    aligned = align_frames(points, _points([440.0] * 100))
    for frame in aligned:
        object.__setattr__(frame, "cents", 40.0)  # frozen dataclass: valor sintético
    segments = build_segments(
        points, aligned, hop_ms=32, duration_sec=3.2, cent_threshold=50
    )
    assert len(segments) == 1
    assert segments[0].severity == "medium"  # 40 < 50
    assert segments[0].delta_cents == 40


def test_build_segments_short_runs_are_ignored() -> None:
    freqs = [440.0] * 30 + [460.0] * 5 + [440.0] * 30  # 0.16 s fuera de tono
    points = _points(freqs)
    aligned = align_frames(points, _points([440.0] * 65))
    segments = build_segments(
        points, aligned, hop_ms=32, duration_sec=2.1, cent_threshold=50
    )
    assert segments == []


def test_build_segments_no_voice_run() -> None:
    freqs = [440.0] * 20 + [None] * 25 + [440.0] * 20  # hueco de 0.8 s
    points = _points(freqs)
    aligned = align_frames(points, _points([440.0] * 65))
    segments = build_segments(
        points, aligned, hop_ms=32, duration_sec=2.1, cent_threshold=50
    )
    assert [s.type for s in segments] == ["no_voice"]
    assert segments[0].severity == "info"
    assert segments[0].end - segments[0].start >= 0.6


def test_build_segments_short_silence_ignored() -> None:
    freqs = [440.0] * 20 + [None] * 10 + [440.0] * 20  # hueco de 0.32 s
    points = _points(freqs)
    aligned = align_frames(points, _points([440.0] * 50))
    segments = build_segments(
        points, aligned, hop_ms=32, duration_sec=1.6, cent_threshold=50
    )
    assert segments == []


# --- scoring ----------------------------------------------------------------


def test_scoring_perfect_match(tmp_path: Path) -> None:
    wav = tmp_path / "tono.wav"
    wav.write_bytes(_tone_wav(duration=2.0, freq=440.0, silence=0.0))  # tono continuo
    points = _points([440.0] * 60)
    scores = compute_scores(
        cents=[0.0, 1.0, -1.0] * 20,
        points=points,
        silence_pct=5,
        student_wav=wav,
        hop_length=512,
        sample_rate=16000,
        cent_threshold=50,
    )
    assert scores.afinacion == 100
    assert scores.estabilidad >= 95
    assert scores.control_volumen >= 80
    assert scores.vocal >= 90
    assert scores.silence_pct == 5


def test_scoring_all_mismatched() -> None:
    wav = Path("no-importa.wav")  # control_volumen → 0 si no se puede leer
    points = _points([440.0] * 30)
    scores = compute_scores(
        cents=[200.0] * 30,
        points=points,
        silence_pct=10,
        student_wav=wav,
        hop_length=512,
        sample_rate=16000,
        cent_threshold=50,
    )
    assert scores.afinacion == 0
    assert scores.estabilidad == 100  # desviación constante = estable
    assert scores.vocal <= 50


def test_scoring_without_matched_frames() -> None:
    wav = Path("no-importa.wav")
    points = _points([None] * 30)
    scores = compute_scores(
        cents=[None] * 30,
        points=points,
        silence_pct=100,
        student_wav=wav,
        hop_length=512,
        sample_rate=16000,
        cent_threshold=50,
    )
    assert scores.afinacion == 0
    assert scores.estabilidad == 0
    assert scores.control_volumen == 0
    assert scores.vocal == 0


# --- feedback (HU-46) -------------------------------------------------------


def test_feedback_distinguishes_no_voice_from_out_of_tune() -> None:
    tune = Segment(
        start=1.0, end=2.0, type="out_of_tune", expected_note="A4", sung_note="G#4",
        delta_cents=72, severity="high",
    )
    quiet = Segment(start=2.5, end=3.4, type="no_voice", severity="info")
    items = build_feedback([tune, quiet], duration_sec=4.0)
    assert [i.code for i in items] == ["OUT_OF_TUNE", "NO_VOICE"]
    assert "72 cents" in items[0].message
    assert "22% del tiempo sin voz" in items[1].message  # 0.9/4.0 = 22.5 → round

    assert build_feedback([], duration_sec=4.0) == []


# --- ruta real (integración) ------------------------------------------------


def test_comparative_mode_reports_out_of_tune_segment() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={
            "audio": ("alumno.wav", _tone_wav(3.0, 460.0), "audio/wav"),
            "reference_audio": ("ref.wav", _tone_wav(3.0, 440.0), "audio/wav"),
        },
        data={
            "attempt_id": "att-cmp-mismatch",
            "routine_id": "routine-1",
            "mode": "comparative",
        },
    )
    assert response.status_code == 202, response.text
    accepted = AcceptedResponse.model_validate(response.json())
    result = AnalysisResult.model_validate(
        client.get(f"/api/v1/analyze/{accepted.analysis_id}").json()
    )

    assert result.algorithm_version == "0.5.0-hybrid-modes"
    tune = [s for s in result.segments if s.type == "out_of_tune"]
    assert len(tune) >= 1
    assert tune[0].delta_cents is not None and 70 <= tune[0].delta_cents <= 90
    assert tune[0].severity == "high"
    assert tune[0].expected_note == "A4" and tune[0].sung_note == "A#4"

    assert "OUT_OF_TUNE" in [f.code for f in result.feedback]
    assert result.scores.afinacion <= 20  # todo el audio desafinado
    assert result.timings.dtw_ms >= 0 and result.timings.scoring_ms >= 0
