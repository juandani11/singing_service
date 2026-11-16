"""Tests HU-S1-05: timeout interno (pyin/align) y `/metrics` Prometheus."""

import re
import time

from fastapi.testclient import TestClient

from app.api.routes import analyze as analyze_route
from app.core.config import settings
from app.main import app
from tests.audio_utils import tone_wav

client = TestClient(app)


def _post(
    attempt_id: str,
    *,
    mode: str = "absolute",
    reference: bytes | None = None,
    headers: dict | None = None,
):
    files = {"audio": ("alumno.wav", tone_wav(1.0, 440.0, silence=0.0), "audio/wav")}
    data = {"attempt_id": attempt_id, "routine_id": "r-hu105", "mode": mode}
    if reference is not None:
        files["reference_audio"] = ("ref.wav", reference, "audio/wav")
    return client.post(
        "/api/v1/analyze", files=files, data=data, headers=headers or {}
    )


def _metric(text: str, name: str) -> float:
    """Valor de una métrica Prometheus (0.0 si aún no existe)."""
    match = re.search(rf"^{re.escape(name)} ([0-9.eE+-]+)$", text, re.MULTILINE)
    return float(match.group(1)) if match else 0.0


def test_timeout_pyin_504(monkeypatch) -> None:
    def slow_extract(*_args, **_kwargs):
        time.sleep(2.0)

    monkeypatch.setattr(analyze_route, "extract_pitch", slow_extract)
    monkeypatch.setattr(settings, "pyin_timeout_seconds", 0.5)
    before = analyze_route._analysis_semaphore._value

    response = _post("hu105-timeout-pyin", headers={"X-Request-ID": "timeout-pyin"})

    assert response.status_code == 504
    detail = response.json()["detail"]
    assert detail["code"] == "ANALYSIS_TIMEOUT"
    assert detail["request_id"] == "timeout-pyin"
    assert response.headers["x-request-id"] == "timeout-pyin"
    # El semáforo se libera aunque el hilo huérfano siga vivo (limitación doc.).
    assert analyze_route._analysis_semaphore._value == before


def test_timeout_align_504(monkeypatch) -> None:
    def slow_align(*_args, **_kwargs):
        time.sleep(2.0)

    monkeypatch.setattr(analyze_route, "align_frames", slow_align)
    monkeypatch.setattr(settings, "align_timeout_seconds", 0.5)
    before = analyze_route._analysis_semaphore._value
    reference = tone_wav(1.0, 440.0, silence=0.0)

    response = _post(
        "hu105-timeout-align",
        mode="comparative",
        reference=reference,
        headers={"X-Request-ID": "timeout-align"},
    )

    assert response.status_code == 504
    detail = response.json()["detail"]
    assert detail["code"] == "ANALYSIS_TIMEOUT"
    assert detail["request_id"] == "timeout-align"
    assert analyze_route._analysis_semaphore._value == before


def test_timeout_increments_counter(monkeypatch) -> None:
    def slow_extract(*_args, **_kwargs):
        time.sleep(2.0)

    monkeypatch.setattr(analyze_route, "extract_pitch", slow_extract)
    monkeypatch.setattr(settings, "pyin_timeout_seconds", 0.5)
    label = 'analysis_timeouts_total{phase="pyin"}'
    before = _metric(client.get("/metrics").text, label)

    assert _post("hu105-timeout-metric").status_code == 504

    text = client.get("/metrics").text
    assert label in text
    assert _metric(text, label) == before + 1


def test_no_timeout_happy_path(monkeypatch) -> None:
    monkeypatch.setattr(settings, "pyin_timeout_seconds", 10.0)
    monkeypatch.setattr(settings, "align_timeout_seconds", 10.0)

    response = _post("hu105-happy")

    assert response.status_code == 202
    assert response.json()["status"] == "completed"


def test_metrics_endpoint_200() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    content_type = response.headers["content-type"]
    assert "text/plain" in content_type
    assert "version=0.0.4" in content_type


def test_metrics_contains_counters() -> None:
    label = 'analysis_requests_total{mode="absolute",status="success"}'
    before = _metric(client.get("/metrics").text, label)

    assert _post("hu105-metrics-counter").status_code == 202

    text = client.get("/metrics").text
    assert label in text
    assert _metric(text, label) == before + 1


def test_metrics_duration_histogram() -> None:
    label = 'analysis_duration_seconds_count{mode="absolute"}'
    before = _metric(client.get("/metrics").text, label)

    assert _post("hu105-metrics-histogram").status_code == 202

    text = client.get("/metrics").text
    assert label in text
    assert _metric(text, label) == before + 1


def test_metrics_no_auth() -> None:
    assert client.get("/metrics").status_code == 200
