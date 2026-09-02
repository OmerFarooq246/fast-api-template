from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Self

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from starlette.requests import Request

from app.db.database import Database, get_db


class FakeTransaction:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def __aenter__(self) -> Self:
        self.events.append("begin")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.events.append("commit" if exc_type is None else "rollback")


class FakeSession:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self.events)


class FakeSessionFactory:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __call__(self) -> FakeSession:
        return FakeSession(self.events)


class FakeDatabase:
    def __init__(self, events: list[str]) -> None:
        self.session_factory = FakeSessionFactory(events)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[FakeSession]:
        async with self.session_factory() as session, session.begin():
            yield session


def build_request(events: list[str]) -> Request:
    application = FastAPI()
    application.state.database = FakeDatabase(events)
    return Request({"type": "http", "app": application})


async def test_application_owns_typed_async_database_resources(app: FastAPI) -> None:
    assert isinstance(app.state.database, Database)
    assert isinstance(app.state.database.engine, AsyncEngine)
    assert isinstance(app.state.database.session_factory, async_sessionmaker)

    session = app.state.database.session_factory()
    assert isinstance(session, AsyncSession)
    await session.close()


async def test_request_boundary_commits_on_success() -> None:
    events: list[str] = []
    dependency = get_db(build_request(events))

    await anext(dependency)
    with pytest.raises(StopAsyncIteration):
        await anext(dependency)

    assert events == ["begin", "commit"]


async def test_request_boundary_rolls_back_on_error() -> None:
    events: list[str] = []
    dependency = get_db(build_request(events))

    await anext(dependency)
    with pytest.raises(RuntimeError, match="operation failed"):
        await dependency.athrow(RuntimeError("operation failed"))

    assert events == ["begin", "rollback"]
