import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_context

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def resolve_request_id(scope: Scope) -> str:
    supplied_request_id = Headers(scope=scope).get(REQUEST_ID_HEADER)
    if supplied_request_id and REQUEST_ID_PATTERN.fullmatch(supplied_request_id):
        return supplied_request_id
    return str(uuid4())


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = resolve_request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id
        context_token = request_id_context.set(request_id)
        started_at = perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            logger.info(
                "HTTP request completed",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
            request_id_context.reset(context_token)
