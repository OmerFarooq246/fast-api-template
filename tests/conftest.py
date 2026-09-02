from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Environment, Settings
from app.main import create_app


@pytest.fixture(scope="session")
def app() -> FastAPI:
    return create_app(
        Settings(
            environment=Environment.TEST,
            project_name="test-application",
            database_uri="postgresql+asyncpg://postgres:postgres@localhost/test_unused",
            secret_key="test-secret",  # noqa: S106
        )
    )


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
