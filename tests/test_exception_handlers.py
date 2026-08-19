from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import ResourceNotFoundError


def test_expected_application_error_has_stable_response(app: FastAPI) -> None:
    @app.get("/_test/not-found")
    async def not_found() -> None:
        raise ResourceNotFoundError("User", 42)

    with TestClient(app) as client:
        response = client.get("/_test/not-found")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "resource_not_found",
            "message": "User 42 was not found",
        }
    }


def test_unexpected_error_does_not_leak_details(app: FastAPI) -> None:
    @app.get("/_test/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("sensitive database detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/_test/unexpected")

    assert response.status_code == 500
    assert response.headers["X-Request-ID"]
    assert response.json() == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected error occurred",
        }
    }
