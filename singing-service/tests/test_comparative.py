"""mode=comparative (Sprint 0 — gap O1): referencia por audio o notas JSON."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AnalysisResult
from tests.audio_utils import CENTS_80_HZ, tone_wav

client = TestClient(app)


def _post(
    student: bytes,
    *,
    attempt_id: str,
    reference: bytes | None = None,
    reference_notes: str | None = None,
    student_name: str = "alumno.wav",
) -> dict:
    files = {"audio": (student_name, student, "audio/wav")}
    if reference is not None:
        files["reference_audio"] = ("ref.wav", reference, "audio/wav")
    data = {"attempt_id": attempt_id, "routine_id": "r-cmp", "mode": "comparative"}
    if reference_notes is not None:
        data["reference_notes"] = reference_notes
    response = client.post("/api/v1/analyze", files=files, data=data)
    assert response.status_code == 202, response.text
    return response.json()


def _get(analysis_id: str) -> AnalysisResult:
    response = client.get(f"/api/v1/analyze/{analysis_id}")
    assert response.status_code == 200, response.text
    return AnalysisResult.model_validate(response.json())


def test_comparative_identical_reference_scores_high() -> None:
    tone = tone_wav(duration=3.0, freq=440.0, silence=0.0)
    accepted = _post(tone, attempt_id="cmp-identical", reference=tone)
    result = _get(accepted["analysis_id"])

    assert result.mode == "comparative"
    assert result.pitch.reference is not None
    assert result.metrics.pitch_accuracy is not None
    assert result.metrics.pitch_accuracy >= 95.0
    assert result.metrics.average_cent_deviation is not None
    assert result.metrics.average_cent_deviation <= 10.0
    assert result.metrics.rhythm_accuracy is None  # O4-B: ritmo diferido
    assert result.scores.afinacion >= 95


def test_comparative_known_deviation_80_cents() -> None:
    accepted = _post(
        tone_wav(duration=3.0, freq=CENTS_80_HZ, silence=0.0),
        attempt_id="cmp-80cents",
        reference=tone_wav(duration=3.0, freq=440.0, silence=0.0),
    )
    result = _get(accepted["analysis_id"])

    assert result.metrics.pitch_accuracy is not None
    assert result.metrics.pitch_accuracy <= 20.0
    assert result.metrics.average_cent_deviation is not None
    assert 65.0 <= result.metrics.average_cent_deviation <= 95.0
    tune = [s for s in result.segments if s.type == "out_of_tune"]
    assert tune and tune[0].delta_cents is not None
    assert 70 <= tune[0].delta_cents <= 90
    assert "OUT_OF_TUNE" in [f.code for f in result.feedback]


def test_comparative_with_reference_notes_json() -> None:
    notes = [
        {"t": round(i * 0.1, 2), "f0": 440.0} for i in range(30)
    ]
    accepted = _post(
        tone_wav(duration=3.0, freq=440.0, silence=0.0),
        attempt_id="cmp-notes",
        reference_notes=json.dumps(notes),
    )
    result = _get(accepted["analysis_id"])

    assert result.mode == "comparative"
    assert result.pitch.reference is not None
    assert result.pitch.reference[0].f0 == 440.0
    assert result.metrics.pitch_accuracy is not None
    assert result.metrics.pitch_accuracy >= 80.0


def test_comparative_reference_notes_accept_note_names() -> None:
    notes = [{"t": 0.0, "note": "A4"}, {"t": 1.0, "note": "A4"}, {"t": 2.0, "note": "A4"}]
    accepted = _post(
        tone_wav(duration=2.5, freq=440.0, silence=0.0),
        attempt_id="cmp-notes-names",
        reference_notes=json.dumps(notes),
    )
    result = _get(accepted["analysis_id"])
    assert result.pitch.reference is not None
    assert result.pitch.reference[0].f0 == 440.0


def test_comparative_invalid_reference_notes_returns_400() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("alumno.wav", tone_wav(1.0), "audio/wav")},
        data={
            "attempt_id": "cmp-bad-notes",
            "routine_id": "r-cmp",
            "mode": "comparative",
            "reference_notes": "esto-no-es-json",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_REFERENCE_NOTES"


def test_comparative_reference_audio_takes_precedence_over_notes() -> None:
    tone = tone_wav(duration=2.0, freq=440.0, silence=0.0)
    response = client.post(
        "/api/v1/analyze",
        files={
            "audio": ("alumno.wav", tone, "audio/wav"),
            "reference_audio": ("ref.wav", tone, "audio/wav"),
        },
        data={
            "attempt_id": "cmp-both",
            "routine_id": "r-cmp",
            "mode": "comparative",
            "reference_notes": "no-importa",
        },
    )
    assert response.status_code == 202, response.text
    result = _get(response.json()["analysis_id"])
    assert result.metrics.pitch_accuracy is not None
