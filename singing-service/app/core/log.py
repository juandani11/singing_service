"""Logs estructurados: una línea JSON por evento (RNF-03).

Sin PII (RNF-06): sólo ids opacos (`analysis_id`, `attempt_id`, `routine_id`),
códigos y métricas; nunca audio, rutas temporales ni nombres de archivo.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.middleware.request_id import get_request_id

logger = logging.getLogger("singing")


def log_event(level: int, event: str, **fields: object) -> None:
    """Emite un evento estructurado (JSON en una sola línea)."""
    payload: dict[str, object] = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "request_id": get_request_id(),
        "event": event,
    }
    payload.update(fields)
    logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))
