"""mode=absolute (Sprint 0 — gap O1): sin referencia, métricas internas."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AnalysisResult, PitchPoint
from app.services.align import note_to_hz
from app.services.feedback import build_absolute_feedback
from tests.audio_utils import tone_wav

client = TestClient(app)


def _post(data: bytes, attempt_id: str, name: str = "alumno.wav") -> dict:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": (name, data, "audio/wav")},
        data={"attempt_id": attempt_id, "routine_id": "r-abs", "mode": "absolute"},
    )
    assert response.status_code == 202, response.text
    return response.json()


def _get(analysis_id: str) -> AnalysisResult:
    response = client.get(f"/api/v1/analyze/{analysis_id}")
    assert response.status_code == 200, response.text
    return AnalysisResult.model_validate(response.json())


def test_absolute_metrics_for_440_tone() -> None:
    accepted = _post(tone_wav(duration=3.0, freq=440.0, silence=0.5), "abs-440")
    result = _get(accepted["analysis_id"])

    assert result.mode == "absolute"
    assert result.pitch.reference is None
    assert result.metrics.mean_pitch_hz is not None
    assert abs(result.metrics.mean_pitch_hz - 440.0) < 20.0
    assert result.metrics.voiced_ratio is not None
    assert 0.5 <= result.metrics.voiced_ratio <= 1.0
    assert result.metrics.pitch_stability_cents is not None
    assert result.metrics.pitch_stability_cents < 30.0
    # Sin referencia no hay accuracy ni desviación media
    assert result.metrics.pitch_accuracy is None
    assert result.metrics.average_cent_deviation is None
    assert result.metrics.rhythm_accuracy is None


def test_absolute_pure_silence_reports_no_voice() -> None:
    accepted = _post(tone_wav(duration=1.0, silence=1.0), "abs-silence")
    result = _get(accepted["analysis_id"])

    assert result.metrics.voiced_ratio == pytest.approx(0.0, abs=0.01)
    assert result.metrics.mean_pitch_hz is None
    assert result.scores.silence_pct >= 90
    assert "NO_VOICE" in [f.code for f in result.feedback]


def test_absolute_feedback_flags_out_of_range_notes() -> None:
    points = [
        PitchPoint(t=i * 0.032, f0=f0, voiced=True)
        for i, f0 in enumerate([60.0] * 5 + [440.0] * 5 + [1500.0] * 5)
    ]
    feedback = build_absolute_feedback(
        points, segments=[], stability_cents=0.0, duration_sec=0.5
    )
    codes = [item.code for item in feedback]
    assert "PITCH_OUT_OF_RANGE" in codes


def test_absolute_feedback_flags_unstable_pitch() -> None:
    points = [PitchPoint(t=i * 0.032, f0=440.0, voiced=True) for i in range(10)]
    feedback = build_absolute_feedback(
        points, segments=[], stability_cents=80.0, duration_sec=0.32
    )
    assert [item.code for item in feedback] == ["UNSTABLE_PITCH"]


def test_note_to_hz() -> None:
    assert note_to_hz("A4") == pytest.approx(440.0)
    assert note_to_hz("A3") == pytest.approx(220.0)
    assert note_to_hz("C4") == pytest.approx(261.63, abs=0.01)
    assert note_to_hz("F#3") == pytest.approx(185.0, abs=0.1)
    with pytest.raises(ValueError):
        note_to_hz("H9")
