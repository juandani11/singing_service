"""Contrato OpenAPI v1 del análisis vocal (plan §2.2) — híbrido absolute/comparative."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

AnalysisStatus = Literal["queued", "completed", "failed"]
AnalysisMode = Literal["absolute", "comparative"]
SegmentType = Literal["out_of_tune", "no_voice", "out_of_rhythm"]
Severity = Literal["info", "medium", "high"]


class AcceptedResponse(BaseModel):
    """Respuesta 202 del POST /api/v1/analyze."""

    analysis_id: str = Field(description="Identificador del análisis encolado")
    status: AnalysisStatus
    mode: AnalysisMode = Field(description="Modo de análisis aplicado")


class PitchPoint(BaseModel):
    """Un frame de la curva F0."""

    t: float = Field(ge=0, description="Segundos desde el inicio del audio")
    f0: float | None = Field(
        default=None,
        description="Frecuencia fundamental en Hz; null si no hay voz",
    )
    voiced: bool = Field(description="True si hay voz detectada en este frame")


class PitchCurves(BaseModel):
    student: list[PitchPoint] = Field(description="Curva F0 del alumno")
    reference: list[PitchPoint] | None = Field(
        default=None,
        description="Curva F0 de la referencia; null en mode=absolute",
    )
    hop_ms: int = Field(gt=0, description="Distancia entre frames en milisegundos")


class Segment(BaseModel):
    """Segmento vocal con mayor desviación (HU-45/HU-46)."""

    start: float = Field(ge=0, description="Inicio en segundos")
    end: float = Field(gt=0, description="Fin en segundos")
    type: SegmentType = Field(
        description=(
            "out_of_tune = desafinado; no_voice = ausencia de voz; "
            "out_of_rhythm = intervalo entre onsets anómalo"
        )
    )
    expected_note: str | None = Field(default=None, description="Nota esperada (out_of_tune)")
    sung_note: str | None = Field(default=None, description="Nota cantada (out_of_tune)")
    delta_cents: int | None = Field(default=None, description="Desviación en cents (out_of_tune)")
    interval_ms: int | None = Field(
        default=None, ge=0, description="Intervalo entre onsets (out_of_rhythm)"
    )
    message: str | None = Field(
        default=None, description="Mensaje del segmento (out_of_rhythm)"
    )
    severity: Severity

    @model_validator(mode="after")
    def _check_fields_by_type(self) -> Self:
        if self.type == "out_of_tune":
            if self.delta_cents is None or self.expected_note is None or self.sung_note is None:
                raise ValueError("out_of_tune requiere delta_cents, expected_note y sung_note")
            if self.interval_ms is not None:
                raise ValueError("out_of_tune no debe llevar interval_ms")
        elif self.type == "no_voice":
            faltan_nulos = (
                self.delta_cents is not None
                or self.expected_note is not None
                or self.sung_note is not None
            )
            if faltan_nulos:
                raise ValueError("no_voice no debe llevar delta_cents ni notas")
            if self.interval_ms is not None:
                raise ValueError("no_voice no debe llevar interval_ms")
        else:  # out_of_rhythm
            if self.interval_ms is None or self.message is None:
                raise ValueError("out_of_rhythm requiere interval_ms y message")
            if (
                self.delta_cents is not None
                or self.expected_note is not None
                or self.sung_note is not None
            ):
                raise ValueError("out_of_rhythm no debe llevar delta_cents ni notas")
        if self.end <= self.start:
            raise ValueError("end debe ser mayor que start")
        return self


class Scores(BaseModel):
    """Puntajes 0-100 (score vocal documentado en docs/scoring.md, Sprint 4)."""

    vocal: int = Field(ge=0, le=100)
    afinacion: int = Field(ge=0, le=100)
    estabilidad: int = Field(ge=0, le=100)
    control_volumen: int = Field(ge=0, le=100)
    ritmo: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Ritmo 0-100 (HU-S1-01); null si no hay onsets",
    )
    silence_pct: int = Field(ge=0, le=100, description="% del tiempo sin voz")


class Metrics(BaseModel):
    """Métricas del contrato híbrido (Sprint 0 + ritmo HU-S1-01).

    - `pitch_stability_cents`, `mean_pitch_hz`, `voiced_ratio`: en ambos modos.
    - `pitch_accuracy`, `average_cent_deviation`: sólo `mode=comparative` (null en absolute).
    - `rhythm_accuracy` y campos de ritmo: en ambos modos; null si no hay onsets.
    """

    pitch_stability_cents: float | None = Field(default=None, ge=0)
    mean_pitch_hz: float | None = Field(default=None, gt=0)
    voiced_ratio: float | None = Field(default=None, ge=0, le=1)
    pitch_accuracy: float | None = Field(default=None, ge=0, le=100)
    rhythm_accuracy: float | None = Field(default=None, ge=0, le=100)
    estimated_tempo_bpm: float | None = Field(default=None, gt=0)
    onset_count: int = Field(default=0, ge=0)
    onset_stability: float | None = Field(default=None, ge=0, le=100)
    tempo_deviation_bpm: float | None = Field(default=None)
    alignment_method: Literal["fastdtw", "time"] = Field(
        default="time",
        description=(
            "Método de alineación en comparative: fastdtw (HU-S1-04) o time (fallback); "
            "time también en absolute"
        ),
    )
    average_cent_deviation: float | None = Field(default=None, ge=0)


class FeedbackItem(BaseModel):
    code: str = Field(description="Código estable para i18n/trazabilidad")
    message: str = Field(description="Mensaje en español (HU-46/RF-39)")


class Timings(BaseModel):
    """Trazabilidad HU-20/RF-25 y métrica §15.1 (tiempo de procesamiento)."""

    preprocess_ms: int = Field(ge=0)
    pitch_ms: int = Field(ge=0)
    rhythm_ms: int = Field(default=0, ge=0, description="Análisis de tempo/onsets (HU-S1-01)")
    align_ms: int = Field(
        default=0,
        ge=0,
        description="Alineación temporal (FastDTW o fallback time; HU-S1-04)",
    )
    dtw_ms: int = Field(ge=0, description="Alias de align_ms (compatibilidad)")
    scoring_ms: int = Field(ge=0)


class AnalysisResult(BaseModel):
    """Resultado completo que el Core persiste en PostgreSQL (fuente de verdad)."""

    analysis_id: str
    attempt_id: str
    routine_id: str
    status: AnalysisStatus
    mode: AnalysisMode
    algorithm_version: str = Field(description="Versión del algoritmo que produjo el resultado")
    duration_sec: float = Field(gt=0)
    pitch: PitchCurves
    segments: list[Segment]
    scores: Scores
    metrics: Metrics
    feedback: list[FeedbackItem]
    timings: Timings
