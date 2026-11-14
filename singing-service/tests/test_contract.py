"""Tests del contrato OpenAPI v1 híbrido (absolute/comparative).

- `test_openapi_matches_v1_snapshot`: el esquema no cambia sin actualización consciente
  del snapshot (coordinación con el Core). Si cambias el contrato a propósito:
  regenera `tests/snapshots/openapi_v1.json` y avisa al equipo en el PR.
"""

import json
import pathlib

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AcceptedResponse, AnalysisResult
from tests.audio_utils import tone_wav

client = TestClient(app)
SNAPSHOT = pathlib.Path(__file__).parent / "snapshots" / "openapi_v1.json"


def _files(name: str = "alumno.wav") -> dict:
    return {"audio": (name, tone_wav(duration=2.0), "audio/wav")}


def _data(**overrides: str) -> dict:
    payload = {
        "attempt_id": "contract-att-1",
        "routine_id": "routine-1",
        "mode": "absolute",
    }
    payload.update(overrides)
    return payload


def test_openapi_matches_v1_snapshot() -> None:
    current = client.get("/openapi.json").json()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert current == snapshot, (
        "El contrato OpenAPI cambió. Regenera tests/snapshots/openapi_v1.json "
        "y coordina el cambio con el Core (Django) en el PR."
    )


def test_absolute_analyze_flow_validates_contract() -> None:
    post = client.post(
        "/api/v1/analyze", files=_files(), data=_data(attempt_id="contract-absolute")
    )
    assert post.status_code == 202, post.text
    accepted = AcceptedResponse.model_validate(post.json())
    assert accepted.status == "completed"
    assert accepted.mode == "absolute"

    get = client.get(f"/api/v1/analyze/{accepted.analysis_id}")
    assert get.status_code == 200
    result = AnalysisResult.model_validate(get.json())

    assert result.mode == "absolute"
    assert result.pitch.reference is None
    assert result.metrics.pitch_accuracy is None
    assert result.metrics.average_cent_deviation is None
    assert result.metrics.rhythm_accuracy is None
    assert result.metrics.mean_pitch_hz is not None
    assert 0.0 <= (result.metrics.voiced_ratio or 0.0) <= 1.0
    assert 0 <= result.scores.vocal <= 100
    assert result.algorithm_version == "0.5.0-hybrid-modes"


def test_analyze_is_idempotent_by_attempt_id() -> None:
    payload = _data(attempt_id="contract-idem")
    first = client.post("/api/v1/analyze", files=_files(), data=payload)
    second = client.post("/api/v1/analyze", files=_files(), data=payload)
    assert first.status_code == 202 and second.status_code == 202
    assert first.json()["analysis_id"] == second.json()["analysis_id"]
    assert second.json()["mode"] == "absolute"


def test_invalid_mode_returns_422() -> None:
    response = client.post(
        "/api/v1/analyze", files=_files(), data=_data(mode="turbo")
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_MODE"


def test_comparative_without_reference_returns_400() -> None:
    response = client.post(
        "/api/v1/analyze", files=_files(), data=_data(mode="comparative")
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "MISSING_REFERENCE"


def test_unknown_analysis_returns_404() -> None:
    response = client.get("/api/v1/analyze/no-existe")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ANALYSIS_NOT_FOUND"


def test_analyze_requires_audio() -> None:
    response = client.post(
        "/api/v1/analyze",
        data={"attempt_id": "a", "routine_id": "r", "mode": "absolute"},
    )
    assert response.status_code == 422


def test_empty_attempt_id_rejected() -> None:
    # ids vacíos no deben crear análisis huérfanos
    response = client.post(
        "/api/v1/analyze", files=_files(), data=_data(attempt_id="")
    )
    assert response.status_code == 422
