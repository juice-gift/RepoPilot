"""Bounded operational metadata only; never log prompts, arguments or exceptions."""

import json
import logging
import re
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from time import monotonic
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
logger = logging.getLogger("repopilot.operations")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "time": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "event": record.msg,
                **getattr(record, "operation", {}),
            },
            separators=(",", ":"),
        )


def configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def event(name: str, **metadata: str | float | bool | None) -> None:
    logger.info(name, extra={"operation": {"request_id": request_id.get(), **metadata}})


@contextmanager
def operation(name: str):
    started = monotonic()
    outcome = "ok"
    try:
        yield
    except Exception:
        outcome = "failed"
        raise
    finally:
        event(
            name, outcome=outcome, elapsed_ms=round((monotonic() - started) * 1000, 3)
        )


class RequestDiagnostics:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        supplied = dict(scope.get("headers", [])).get(b"x-request-id", b"")
        correlation = supplied.decode("ascii", errors="ignore")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", correlation):
            correlation = uuid4().hex
        token = request_id.set(correlation)
        started, status = monotonic(), 500
        response_started = False

        async def observed_send(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                message["headers"] = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != b"x-request-id"
                ] + [(b"x-request-id", correlation.encode())]
            await send(message)

        try:
            await self.app(scope, receive, observed_send)
        except Exception:
            # Do not send exception messages or SDK/database details to logs/client.
            if response_started:
                raise
            await observed_send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Internal server error"}',
                }
            )
        finally:
            route = scope.get("route")
            event(
                "http.request",
                method=scope["method"],
                route=getattr(route, "path", "unmatched"),
                status=status,
                failure="server_error"
                if status >= 500
                else "request_rejected"
                if status >= 400
                else None,
                elapsed_ms=round((monotonic() - started) * 1000, 3),
            )
            request_id.reset(token)
