"""Tests HU-S1-01: ritmo real (tempo/onsets) + warm-up extendido."""

import logging
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app, app_state
from app.schemas.analyze import AnalysisResult
from app.services.rhythm_eval import analyze_rhythm
from tests.audio_utils import noise_wav, pulse_wav, tone_wav

client = TestClient(app)
MASTMELODY = (
    Path(__file__).resolve().parents[1]
    / "integration"
    / "fixtures"
    / "mastmelody_per.m4a"
)


def _post(
    data: bytes,
    attempt_id: str,
    *,
    mode: str = "absolute",
    tempo_bpm: float | None = None,
    reference: bytes | None = None,
    name: str = "alumno.wav",
) -> dict:
    files = {"audio": (name, data, "audio/wav")}
    if reference is not None:
        files["reference_audio"] = ("ref.wav", reference, "audio/wav")
    form = {"attempt_id": attempt_id, "routine_id": "r-hu1", "mode": mode}
    if tempo_bpm is not None:
        form["tempo_bpm"] = str(tempo_bpm)
    response = client.post("/api/v1/analyze", files=files, data=form)
    assert response.status_code == 202, response.text
    return response.json()


def _get(analysis_id: str) -> AnalysisResult:
    response = client.get(f"/api/v1/analyze/{analysis_id}")
    assert response.status_code == 200, response.text
    return AnalysisResult.model_validate(response.json())


def test_absolute_120_bpm() -> None:
    accepted = _post(pulse_wav(bpm=120, duration=5.0), "hu1-120")
    result = _get(accepted["analysis_id"])

    assert result.metrics.onset_count >= 8
    assert result.metrics.estimated_tempo_bpm is not None
    assert 115 <= result.metrics.estimated_tempo_bpm <= 125
    assert result.metrics.rhythm_accuracy is not None
    assert result.metrics.rhythm_accuracy > 80
    assert result.metrics.tempo_deviation_bpm is None
    assert result.scores.ritmo is not None
    assert 0 <= result.scores.ritmo <= 100


def test_absolute_60_bpm() -> None:
    accepted = _post(pulse_wav(bpm=60, duration=6.0), "hu1-60")
    result = _get(accepted["analysis_id"])

    assert result.metrics.estimated_tempo_bpm is not None
    assert 55 <= result.metrics.estimated_tempo_bpm <= 65
    assert result.metrics.rhythm_accuracy is not None
    assert result.metrics.rhythm_accuracy > 80


def test_absolute_silence_has_no_rhythm() -> None:
    accepted = _post(tone_wav(duration=5.0, silence=5.0), "hu1-silence")
    result = _get(accepted["analysis_id"])

    assert result.metrics.onset_count == 0
    assert result.metrics.rhythm_accuracy is None
    assert result.scores.ritmo is None


def test_absolute_white_noise_is_irregular() -> None:
    accepted = _post(noise_wav(duration=5.0), "hu1-noise")
    result = _get(accepted["analysis_id"])

    assert result.metrics.onset_count > 5
    assert result.metrics.rhythm_accuracy is not None
    assert result.metrics.rhythm_accuracy < 50
    assert result.scores.ritmo is not None


def test_absolute_pure_sine_has_no_rhythm() -> None:
    accepted = _post(tone_wav(duration=5.0, freq=440.0, silence=0.0), "hu1-pure")
    result = _get(accepted["analysis_id"])

    assert result.metrics.onset_count < 2
    assert result.metrics.rhythm_accuracy is None
    assert result.scores.ritmo is None


def test_mastmelody_has_rhythm_accuracy() -> None:
    if not MASTMELODY.exists():
        pytest.skip(f"falta {MASTMELODY} (la imagen Docker no copia fixtures)")
    accepted = _post(
        MASTMELODY.read_bytes(),
        "hu1-mastmelody",
        name="mastmelody_per.m4a",
    )
    result = _get(accepted["analysis_id"])

    assert result.metrics.rhythm_accuracy is not None
    assert 20 <= result.metrics.rhythm_accuracy <= 95
    assert result.scores.ritmo is not None
    assert result.metrics.onset_count >= 2


def test_comparative_tempo_hint_deviation() -> None:
    student = pulse_wav(bpm=110, duration=5.0)
    accepted = _post(
        student,
        "hu1-comparative",
        mode="comparative",
        tempo_bpm=120,
        reference=student,
    )
    result = _get(accepted["analysis_id"])

    assert result.mode == "comparative"
    assert result.metrics.tempo_deviation_bpm is not None
    assert result.metrics.tempo_deviation_bpm == pytest.approx(-10, abs=2)
    assert result.metrics.rhythm_accuracy is not None
    assert result.scores.ritmo is not None


def test_feedback_out_of_rhythm_worst_case() -> None:
    accepted = _post(
        pulse_wav(bpm=120, duration=6.0, gap=(2.0, 4.0)),
        "hu1-rhythm-feedback",
    )
    result = _get(accepted["analysis_id"])

    rhythm_segments = [s for s in result.segments if s.type == "out_of_rhythm"]
    assert rhythm_segments
    worst = max(rhythm_segments, key=lambda s: s.interval_ms or 0)
    assert worst.interval_ms is not None and worst.interval_ms >= 2000
    assert worst.severity in {"medium", "high"}
    assert "OUT_OF_RHYTHM" in [item.code for item in result.feedback]


def test_warmup_beat_track_log(monkeypatch, caplog) -> None:
    monkeypatch.delenv("SKIP_WARMUP", raising=False)
    monkeypatch.delenv("SKIP_WARMUP_BEAT", raising=False)

    with caplog.at_level(logging.INFO, logger="singing"):
        with TestClient(app) as lifespan_client:
            assert app_state.ready is True
            assert app_state.warmup_beat_track_completed is True
            assert app_state.warmup_beat_track_duration_ms is not None
            health = lifespan_client.get("/health").json()
            assert health["checks"]["rhythm_warmup"]["ok"] is True

    assert "warmup_beat_track_completed" in caplog.text


def test_warmup_beat_track_failure_does_not_crash(monkeypatch, caplog) -> None:
    from app.main import _warmup_beat_track

    def boom(*_args, **_kwargs):
        raise RuntimeError("beat_track boom")

    monkeypatch.setattr("librosa.beat.beat_track", boom)
    monkeypatch.setattr(app_state, "warmup_beat_track_completed", False)
    monkeypatch.setattr(app_state, "warmup_beat_track_duration_ms", None)

    with caplog.at_level(logging.WARNING, logger="singing"):
        _warmup_beat_track()

    assert app_state.warmup_beat_track_completed is False
    assert app_state.warmup_beat_track_duration_ms is not None
    assert "warmup_beat_track_failed" in caplog.text


def test_skip_warmup_skips_rhythm(monkeypatch, caplog) -> None:
    monkeypatch.setenv("SKIP_WARMUP", "true")

    with caplog.at_level(logging.INFO, logger="singing"):
        with TestClient(app) as lifespan_client:
            assert app_state.ready is True
            assert app_state.warmup_completed is False
            assert app_state.warmup_beat_track_completed is False
            assert lifespan_client.get("/ready").status_code == 200

    assert "warmup_skipped" in caplog.text


def test_rhythm_eval_empty_audio() -> None:
    result = analyze_rhythm(np.asarray([], dtype=np.float32), 16000)

    assert result.onset_count == 0
    assert result.rhythm_accuracy is None
    assert result.feedback_items == []


def test_rhythm_eval_failure_returns_empty() -> None:
    result = analyze_rhythm(np.zeros(100, dtype=np.float32), 0)

    assert result.onset_count == 0
    assert result.rhythm_accuracy is None
    assert result.feedback_items == []
