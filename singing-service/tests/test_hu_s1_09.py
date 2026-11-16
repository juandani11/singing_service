"""Tests HU-S1-09: `pitch_contour` opcional con downsample ~10 Hz."""

import json

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AnalysisResult, PitchPoint
from app.services.contour import (
    CONTOUR_MAX_POINTS,
    build_contour,
    build_pitch_contour,
)
from tests.audio_utils import tone_wav

client = TestClient(app)


def _post(
    attempt_id: str,
    *,
    include: bool | None = None,
    mode: str = "absolute",
    reference: bytes | None = None,
    duration: float = 2.0,
    silence: float = 0.0,
):
    files = {
        "audio": (
            "alumno.wav",
            tone_wav(duration, 440.0, silence=silence),
            "audio/wav",
        )
    }
    data = {"attempt_id": attempt_id, "routine_id": "r-hu109", "mode": mode}
    if include is not None:
        data["include_contour"] = "true" if include else "false"
    if reference is not None:
        files["reference_audio"] = ("ref.wav", reference, "audio/wav")
    return client.post("/api/v1/analyze", files=files, data=data)


def _get(analysis_id: str) -> AnalysisResult:
    response = client.get(f"/api/v1/analyze/{analysis_id}")
    assert response.status_code == 200, response.text
    return AnalysisResult.model_validate(response.json())


def test_include_contour_false_default() -> None:
    accepted = _post("hu109-default")
    assert accepted.status_code == 202, accepted.text

    result = _get(accepted.json()["analysis_id"])

    assert result.pitch_contour is None


def test_include_contour_true_absolute() -> None:
    accepted = _post("hu109-absolute", include=True)
    assert accepted.status_code == 202, accepted.text

    result = _get(accepted.json()["analysis_id"])

    assert result.pitch_contour is not None
    assert result.pitch_contour.downsample_hz == 10
    assert result.pitch_contour.student
    assert result.pitch_contour.reference is None
    point = result.pitch_contour.student[0]
    assert set(point.model_dump()) == {"t", "f0", "note", "voiced"}


def test_include_contour_true_comparative() -> None:
    reference = tone_wav(3.0, 440.0, silence=0.0)
    accepted = _post(
        "hu109-comparative",
        include=True,
        mode="comparative",
        reference=reference,
        duration=3.0,
    )
    assert accepted.status_code == 202, accepted.text

    result = _get(accepted.json()["analysis_id"])

    assert result.pitch_contour is not None
    assert result.pitch_contour.student
    assert result.pitch_contour.reference
    assert result.pitch_contour.downsample_hz == 10


def test_contour_downsample_10hz() -> None:
    accepted = _post("hu109-downsample", include=True, duration=5.0)
    assert accepted.status_code == 202, accepted.text

    result = _get(accepted.json()["analysis_id"])
    assert result.pitch_contour is not None

    # 5 s a hop 32 ms ≈ 156 frames; con step=3 quedan ~52 puntos (no 156).
    assert 45 <= len(result.pitch_contour.student) <= 55
    assert len(result.pitch_contour.student) < len(result.pitch.student)


def test_contour_max_6000_points() -> None:
    # Equivalente a 10 min con hop 32 ms (18,750 frames), sin ejecutar pyin.
    points = [
        PitchPoint(t=round(i * 0.032, 3), f0=440.0, voiced=True)
        for i in range(18_750)
    ]

    contour = build_contour(points, hop_ms=32)

    assert len(contour) == CONTOUR_MAX_POINTS == 6000
    assert contour[0].t == 0.0
    assert contour[-1].t == 599.968
    assert len({p.t for p in contour}) == 6000


def test_contour_json_size_under_1mb() -> None:
    points = [
        PitchPoint(t=round(i * 0.032, 3), f0=440.0 + (i % 5), voiced=True)
        for i in range(18_750)
    ]

    contour = build_pitch_contour(points, points, hop_ms=32)
    payload = json.dumps(contour.model_dump(), ensure_ascii=False)

    assert len(contour.student) == 6000
    assert len(contour.reference or []) == 6000
    assert len(payload) < 1_000_000


def test_contour_voiced_null() -> None:
    accepted = _post("hu109-voiced", include=True, duration=1.0, silence=0.5)
    assert accepted.status_code == 202, accepted.text

    result = _get(accepted.json()["analysis_id"])
    assert result.pitch_contour is not None

    unvoiced = [p for p in result.pitch_contour.student if not p.voiced]
    assert unvoiced
    assert all(p.f0 is None and p.note is None for p in unvoiced)
    assert any(p.voiced for p in result.pitch_contour.student)
