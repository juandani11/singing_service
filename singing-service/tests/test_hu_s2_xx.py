"""Tests HU-S2-XX: cache de ritmo por hash y latencia de `rhythm_eval`.

B y C (hop 1024 / downsample 11 kHz) se rechazaron por precisión de tempo
(>2 BPM); el baseline se mantiene. Ver `CIERRE_HU_S2_XX.md`.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import rhythm_cache
from app.services.rhythm_cache import (
    clear_rhythm_cache,
    rhythm_cache_key,
)
from tests.audio_utils import pulse_wav

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_rhythm_cache()
    yield
    clear_rhythm_cache()


def _post(attempt_id: str, audio: bytes, *, tempo_bpm: float | None = None):
    data = {"attempt_id": attempt_id, "routine_id": "r-s2", "mode": "absolute"}
    if tempo_bpm is not None:
        data["tempo_bpm"] = str(tempo_bpm)
    return client.post(
        "/api/v1/analyze",
        files={"audio": ("pulses.wav", audio, "audio/wav")},
        data=data,
    )


def _result(response):
    assert response.status_code == 202, response.text
    accepted = response.json()
    got = client.get(f"/api/v1/analyze/{accepted['analysis_id']}")
    assert got.status_code == 200, got.text
    return got.json()


def _count_calls(monkeypatch) -> dict:
    calls = {"n": 0}
    real = rhythm_cache.analyze_rhythm

    def counting(*args, **kwargs):
        calls["n"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(rhythm_cache, "analyze_rhythm", counting)
    return calls


def test_cache_hit_second_call() -> None:
    audio = pulse_wav(120.0, 5.0)

    first = _result(_post("s2-cache-1", audio))
    second = _result(_post("s2-cache-2", audio))

    assert second["timings"]["rhythm_ms"] < 10
    assert second["timings"]["rhythm_ms"] <= first["timings"]["rhythm_ms"]
    assert second["metrics"]["estimated_tempo_bpm"] == first["metrics"]["estimated_tempo_bpm"]


def test_cache_miss_different_audio(monkeypatch) -> None:
    calls = _count_calls(monkeypatch)

    _result(_post("s2-miss-1", pulse_wav(120.0, 5.0, freq=440.0)))
    _result(_post("s2-miss-2", pulse_wav(120.0, 5.0, freq=660.0)))

    assert calls["n"] == 2


def test_cache_key_includes_tempo_hint(monkeypatch) -> None:
    calls = _count_calls(monkeypatch)
    audio = pulse_wav(120.0, 5.0)

    _result(_post("s2-hint-1", audio, tempo_bpm=120.0))
    _result(_post("s2-hint-2", audio, tempo_bpm=130.0))

    assert calls["n"] == 2


def test_cache_clear_forces_reanalysis(monkeypatch) -> None:
    calls = _count_calls(monkeypatch)
    audio = pulse_wav(120.0, 5.0)

    _result(_post("s2-clear-1", audio))
    _result(_post("s2-clear-2", audio))
    assert calls["n"] == 1

    clear_rhythm_cache()
    _result(_post("s2-clear-3", audio))
    assert calls["n"] == 2


def test_cache_hit_preserves_metrics() -> None:
    audio = pulse_wav(120.0, 5.0)
    first = _result(_post("s2-preserve-1", audio))
    second = _result(_post("s2-preserve-2", audio))

    for field in (
        "estimated_tempo_bpm",
        "onset_count",
        "onset_stability",
        "rhythm_accuracy",
    ):
        assert second["metrics"][field] == first["metrics"][field]


def test_rhythm_ms_60s_under_20s() -> None:
    result = _result(_post("s2-60s", pulse_wav(120.0, 60.0)))

    assert result["timings"]["rhythm_ms"] < 20_000


def test_tempo_precision_120_bpm() -> None:
    result = _result(_post("s2-tempo", pulse_wav(120.0, 60.0)))

    assert 115.0 <= result["metrics"]["estimated_tempo_bpm"] <= 125.0
    assert 107 <= result["metrics"]["onset_count"] <= 131  # ±10 % de 119


def test_cache_key_scoped_by_sr_and_hint() -> None:
    audio = b"same-audio-bytes"

    assert rhythm_cache_key(audio, 16000, 120) == rhythm_cache_key(
        audio, 16000, 120.0
    )
    assert rhythm_cache_key(audio, 16000, 120) != rhythm_cache_key(
        audio, 16000, 130
    )
    assert rhythm_cache_key(audio, 16000, 120) != rhythm_cache_key(
        audio, 11025, 120
    )
