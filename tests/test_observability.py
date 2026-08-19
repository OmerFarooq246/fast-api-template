import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.logging import JsonFormatter, request_id_context


class FakeConnection:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.execute = AsyncMock(side_effect=error)


class FakeEngine:
    def __init__(self, error: Exception | None = None) -> None:
        self.connection = FakeConnection(error)
        self.dispose = AsyncMock()

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[FakeConnection]:
        yield self.connection


def test_request_id_is_preserved_and_returned(client: TestClient) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "upstream-request-42"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "upstream-request-42"


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "invalid request id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "invalid request id"
    assert response.headers["X-Request-ID"]


def test_json_formatter_emits_structured_request_context() -> None:
    formatter = JsonFormatter()
    token = request_id_context.set("request-123")
    try:
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Request handled",
            args=(),
            exc_info=None,
        )
        record.request_id = request_id_context.get()
        record.status_code = 200
        output: dict[str, Any] = json.loads(formatter.format(record))
    finally:
        request_id_context.reset(token)

    assert output["level"] == "INFO"
    assert output["message"] == "Request handled"
    assert output["request_id"] == "request-123"
    assert output["status_code"] == 200
    assert "timestamp" in output


def test_liveness_does_not_require_the_database(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_succeeds_when_database_is_available(app: FastAPI) -> None:
    engine = FakeEngine()
    app.state.db_engine = engine

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    engine.connection.execute.assert_awaited_once()


def test_readiness_is_unavailable_when_database_fails(app: FastAPI) -> None:
    error = OperationalError("SELECT 1", {}, RuntimeError("database unavailable"))
    app.state.db_engine = FakeEngine(error)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
