"""Middleware `X-Request-ID` (fix P0-01).

- Lee `X-Request-ID` del request; si es válido lo reutiliza, si no genera
  `uuid4().hex`.
- Lo expone en `request.state.request_id` y en un `ContextVar` para logs.
- Añade el header a **todas** las respuestas, incluidas las de error y las
  excepciones no capturadas (que se convierten en un 500 JSON con `request_id`).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_VALID_REQUEST_ID = re.compile(r"^[a-zA-Z0-9\-_]{1,128}$")
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("singing")


def get_request_id() -> str:
    """Request id del contexto actual (para logs y bodies de error)."""
    return _request_id_var.get()


class RequestIDLogFilter(logging.Filter):
    """Inyecta `record.request_id` desde el ContextVar (sin `request.state`)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get()
        return True


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Garantiza `X-Request-ID` en la respuesta y en el contexto de logs."""

    async def dispatch(self, request: Request, call_next):
        raw = request.headers.get("X-Request-ID")
        request_id = (
            raw if raw and _VALID_REQUEST_ID.fullmatch(raw) else uuid.uuid4().hex
        )
        request.state.request_id = request_id
        token = _request_id_var.set(request_id)
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 (se convierte en 500 controlado)
            logger.error(
                json.dumps(
                    {
                        "ts": datetime.now(UTC).isoformat(),
                        "request_id": request_id,
                        "event": "unhandled_exception",
                        "error": type(exc).__name__,
                    },
                    ensure_ascii=False,
                ),
                exc_info=True,
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": {
                        "code": "UNHANDLED_ERROR",
                        "message": "Error interno no controlado",
                        "request_id": request_id,
                    }
                },
            )
        finally:
            _request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response
