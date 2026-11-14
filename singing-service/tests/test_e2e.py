"""E2E del contrato §11 (Sprint 5): una ejecución con audio produce pitch,
comparación, score vocal y feedback sin romper el flujo.

Con audios de desviación **conocida** (§12.1): 460.8 Hz vs 440 Hz = 80 cents.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analyze import AnalysisResult
from tests.audio_utils import CENTS_80_HZ, tone_wav, transcode

client = TestClient(app)


def _post(
    attempt_id: str,
    data: bytes,
    name: str,
    ref: bytes,
    ref_name: str = "ref.wav",
) -> dict:
    resp = client.post(
        "/api/v1/analyze",
        files={
            "audio": (name, data, "audio/wav"),
            "reference_audio": (ref_name, ref, "audio/wav"),
        },
        data={"attempt_id": attempt_id, "routine_id": "r-e2e", "mode": "comparative"},
    )
    assert resp.status_code == 202, resp.text
    return resp.json()


def _get(analysis_id: str) -> AnalysisResult:
    resp = client.get(f"/api/v1/analyze/{analysis_id}")
    assert resp.status_code == 200, resp.text
    return AnalysisResult.model_validate(resp.json())


def test_e2e_known_deviation_full_contract() -> None:
    """§11: pitch + comparación + score vocal + feedback con desviación conocida."""
    accepted = _post(
        "e2e-80cents",
        tone_wav(duration=3.0, freq=CENTS_80_HZ, silence=0.0),
        "alumno.wav",
        tone_wav(duration=3.0, freq=440.0, silence=0.0),
    )
    result = _get(accepted["analysis_id"])

    assert result.status == "completed"
    assert result.mode == "comparative"
    assert result.algorithm_version == "0.5.0-hybrid-modes"
    # Pitch (HU-43)
    assert result.pitch.student and result.pitch.reference
    assert result.pitch.hop_ms == 32
    # Comparación temporal simple (Sprint 0): segmento ~80 cents, high
    tune = [s for s in result.segments if s.type == "out_of_tune"]
    assert tune, "la desviación conocida debe producir un segmento out_of_tune"
    assert tune[0].delta_cents is not None and 70 <= tune[0].delta_cents <= 90
    assert tune[0].severity == "high"
    assert tune[0].expected_note is not None and tune[0].sung_note is not None
    # Métricas comparativas
    assert result.metrics.pitch_accuracy is not None and result.metrics.pitch_accuracy <= 20
    assert result.metrics.average_cent_deviation is not None
    # Score vocal (RF-38): desviación sostenida → afinación baja
    assert result.scores.afinacion <= 20
    assert 0 <= result.scores.vocal <= 100
    # Feedback (HU-46/RF-39)
    assert [f.code for f in result.feedback] == ["OUT_OF_TUNE"]
    # Timings trazables (RNF-03)
    assert result.timings.pitch_ms >= 0
    assert result.timings.dtw_ms >= 0
    assert result.timings.scoring_ms >= 0

    # Reintento del Core con el mismo attempt_id → mismo análisis (§3.3)
    retry = _post(
        "e2e-80cents",
        tone_wav(duration=3.0, freq=CENTS_80_HZ, silence=0.0),
        "alumno.wav",
        tone_wav(duration=3.0, freq=440.0, silence=0.0),
    )
    assert retry["analysis_id"] == accepted["analysis_id"]


def test_e2e_long_pause_produces_no_voice_feedback() -> None:
    """§12.1: pausa larga → segmento no_voice + feedback NO_VOICE (no desafinación)."""
    accepted = _post(
        "e2e-pausa",
        tone_wav(duration=2.0, freq=440.0, silence=0.9),
        "alumno.wav",
        tone_wav(duration=2.0, freq=440.0, silence=0.0),
    )
    result = _get(accepted["analysis_id"])

    assert [s.type for s in result.segments] == ["no_voice"]
    assert [f.code for f in result.feedback] == ["NO_VOICE"]
    # Regresión: con segmentos presentes nunca informa "0%"
    assert "0%" not in result.feedback[0].message
    # La pausa no se contó como desafinación
    assert not any(s.type == "out_of_tune" for s in result.segments)


def test_e2e_pipeline_accepts_m4a() -> None:
    """§7 integración: M4A (mobile por defecto) → preprocess → pitch → JSON."""
    m4a = transcode(tone_wav(duration=2.0, freq=440.0, silence=0.0), "a.wav", "a.m4a")
    accepted = _post(
        "e2e-m4a",
        m4a,
        "alumno.m4a",
        tone_wav(duration=2.0, freq=440.0, silence=0.0),
    )
    result = _get(accepted["analysis_id"])

    assert result.status == "completed"
    assert result.scores.afinacion >= 80
    assert 0 <= result.scores.vocal <= 100
