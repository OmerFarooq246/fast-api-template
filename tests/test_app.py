from fastapi.testclient import TestClient

from app.core.config import Environment, Settings
from app.main import create_app


def test_openapi_document_is_available(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == "fast-api-template"
    assert {
        "/auth/change-password",
        "/auth/login",
        "/auth/logout",
        "/auth/logout-all",
        "/auth/refresh",
        "/users/",
        "/users/{user_id}",
    } <= set(document["paths"])


def test_application_factory_uses_injected_settings() -> None:
    application = create_app(
        Settings(
            environment=Environment.TEST,
            project_name="test-application",
            database_uri="postgresql+asyncpg://postgres:postgres@localhost/test_unused",
            secret_key="test-secret",  # noqa: S106
        )
    )

    assert application.title == "test-application"
    assert application.state.settings.environment is Environment.TEST
