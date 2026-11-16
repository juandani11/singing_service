"""Tests HU-S1-04: FastDTW cableado en `mode=comparative`."""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AnalysisResult
from tests.audio_utils import tone_wav

client = TestClient(app)
FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"
MASTMELODY = FIXTURES / "mastmelody_per.m4a"
MASTREF = FIXTURES / "mastmelody_ref.m4a"


def _post(
    audio: bytes,
    attempt_id: str,
    *,
    reference: bytes | None = None,
    name: str = "alumno.wav",
    ref_name: str = "ref.wav",
) -> dict:
    files = {"audio": (name, audio, "audio/wav")}
    if reference is not None:
        files["reference_audio"] = (ref_name, reference, "audio/wav")
    response = client.post(
        "/api/v1/analyze",
        files=files,
        data={"attempt_id": attempt_id, "routine_id": "r-hu104", "mode": "comparative"},
    )
    assert response.status_code == 202, response.text
    return response.json()


def _get(analysis_id: str) -> AnalysisResult:
    response = client.get(f"/api/v1/analyze/{analysis_id}")
    assert response.status_code == 200, response.text
    return AnalysisResult.model_validate(response.json())


@pytest.mark.integration
def test_mastmelody_fastdtw_improvement() -> None:
    """MASTmelody con FastDTW: 44.4 es la respuesta honesta para este cantante
    amateur con umbral de 50 cents (antes 20.7 con align_by_time). La calibración
    de umbrales es HU-S4-XX. Requiere fixtures locales; la imagen Docker no los copia.
    """
    if not MASTMELODY.exists() or not MASTREF.exists():
        pytest.skip("faltan fixtures MASTmelody (la imagen Docker no copia fixtures)")

    accepted = _post(
        MASTMELODY.read_bytes(),
        "hu104-mast",
        reference=MASTREF.read_bytes(),
        name="mastmelody_per.m4a",
        ref_name="mastmelody_ref.m4a",
    )
    result = _get(accepted["analysis_id"])

    assert result.metrics.alignment_method == "fastdtw"
    assert result.metrics.pitch_accuracy is not None
    assert result.metrics.pitch_accuracy >= 40
    assert result.metrics.average_cent_deviation is not None
    assert result.metrics.average_cent_deviation < 100


def test_offset_200ms_fastdtw_supera_align_by_time() -> None:
    """Offset de 200 ms: FastDTW alinea; align_by_time (tolerance 0.1 s) fallaría.

    Student = 200 ms de silencio + 4.8 s de sine 440; reference = 5 s de sine 440.
    """
    reference = tone_wav(duration=5.0, freq=440.0, silence=0.0)
    student = tone_wav(duration=5.0, freq=440.0, silence=0.2)

    accepted = _post(student, "hu104-offset", reference=reference)
    result = _get(accepted["analysis_id"])

    assert result.metrics.alignment_method == "fastdtw"
    assert result.metrics.pitch_accuracy is not None
    assert result.metrics.pitch_accuracy > 80


def test_sine_440_vs_442_regression() -> None:
    """FastDTW no rompe el caso casi perfecto (442 vs 440 ≈ 7.9 cents)."""
    reference = tone_wav(duration=3.0, freq=440.0, silence=0.0)
    student = tone_wav(duration=3.0, freq=442.0, silence=0.0)

    accepted = _post(student, "hu104-sine", reference=reference)
    result = _get(accepted["analysis_id"])

    assert result.metrics.alignment_method == "fastdtw"
    assert result.metrics.pitch_accuracy is not None
    assert result.metrics.pitch_accuracy >= 95


def test_comparative_without_reference_400() -> None:
    response = client.post(
        "/api/v1/analyze",
        files={"audio": ("alumno.wav", tone_wav(1.0), "audio/wav")},
        data={
            "attempt_id": "hu104-noref",
            "routine_id": "r-hu104",
            "mode": "comparative",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "MISSING_REFERENCE"


def test_align_fallback_on_exception(monkeypatch, caplog) -> None:
    def boom(*_args, **_kwargs):
        raise RuntimeError("fastdtw boom")

    monkeypatch.setattr("app.api.routes.analyze.align_frames", boom)
    reference = tone_wav(duration=3.0, freq=440.0, silence=0.0)
    student = tone_wav(duration=3.0, freq=440.0, silence=0.0)

    with caplog.at_level(logging.WARNING, logger="singing"):
        accepted = _post(student, "hu104-fallback", reference=reference)
        result = _get(accepted["analysis_id"])

    assert result.metrics.alignment_method == "time"
    assert result.metrics.pitch_accuracy is not None
    assert "align_fastdtw_failed" in caplog.text
