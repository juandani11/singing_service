"""Evaluación de ritmo (Sprint 0 — decisión O4-B: diferida a Sprint 1).

Se deja un stub explícito para que el Core y el frontend no esperen métricas
de ritmo en el contrato v1. `rhythm_accuracy` viaja siempre como `null`.

Justificación de la decisión:
- `librosa.beat.beat_track` es fiable con percusión/onsets marcados, no con voz
  sostenida sin acompañamiento (caso de este servicio).
- Sin alineamiento temporal avanzado (Sprint 1) no hay base sólida para
  comparar tempo/onsets contra una referencia cantada.
"""

from __future__ import annotations

from typing import Any


def evaluate_rhythm(*_args: Any, **_kwargs: Any) -> dict[str, str]:
    """Contrato del stub: el endpoint NO lo invoca todavía."""
    return {"status": "not_implemented", "reason": "deferred to Sprint 1"}
