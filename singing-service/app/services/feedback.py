"""Feedback del análisis (Sprint 4 — HU-46/RF-39; Sprint 0 — modo absolute).

HU-46 exige distinguir *sin voz* de *desafinación*: cada tipo de segmento
genera su propio código estable (i18n) y mensaje en español.

En `mode=absolute` no hay referencia, así que el feedback se basa sólo en
umbrales absolutos: estabilidad, silencios y notas fuera del rango humano.
"""

from __future__ import annotations

from app.schemas.analyze import FeedbackItem, PitchPoint, Segment
from app.services.metrics import HUMAN_F0_MAX_HZ, HUMAN_F0_MIN_HZ, out_of_range_count

UNSTABLE_PITCH_CENTS = 50.0


def build_feedback(segments: list[Segment], *, duration_sec: float) -> list[FeedbackItem]:
    items: list[FeedbackItem] = []

    tune = [s for s in segments if s.type == "out_of_tune" and s.delta_cents is not None]
    if tune:
        worst = max(tune, key=lambda s: s.delta_cents or 0)
        items.append(
            FeedbackItem(
                code="OUT_OF_TUNE",
                message=(
                    f"Desviación de hasta {worst.delta_cents} cents "
                    f"(esperado {worst.expected_note}, cantado {worst.sung_note})."
                ),
            )
        )

    quiet = [s for s in segments if s.type == "no_voice"]
    if quiet:
        total = sum(s.end - s.start for s in quiet)
        pct = round(100 * total / duration_sec) if duration_sec > 0 else 0
        # Redondeo: con segmentos presentes nunca informa "0%"
        pct = max(1, pct)
        items.append(
            FeedbackItem(
                code="NO_VOICE",
                message=(
                    f"Detectamos {pct}% del tiempo sin voz; "
                    "es distinto a una desafinación."
                ),
            )
        )

    return items


def build_absolute_feedback(
    points: list[PitchPoint],
    *,
    segments: list[Segment],
    stability_cents: float | None,
    duration_sec: float,
) -> list[FeedbackItem]:
    """Feedback sin referencia: silencios + estabilidad + rango humano."""
    items = build_feedback(segments, duration_sec=duration_sec)

    if stability_cents is not None and stability_cents > UNSTABLE_PITCH_CENTS:
        items.append(
            FeedbackItem(
                code="UNSTABLE_PITCH",
                message=(
                    f"Tu afinación osciló ±{stability_cents:.0f} cents alrededor "
                    "de tu propia nota; intenta sostener la nota más estable."
                ),
            )
        )

    out_of_range = out_of_range_count(points)
    if out_of_range:
        items.append(
            FeedbackItem(
                code="PITCH_OUT_OF_RANGE",
                message=(
                    f"{out_of_range} frames quedaron fuera del rango humano de canto "
                    f"({HUMAN_F0_MIN_HZ:.0f}-{HUMAN_F0_MAX_HZ:.0f} Hz)."
                ),
            )
        )

    return items
