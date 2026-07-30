from fastapi.testclient import TestClient


def test_openapi_document_is_available(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"] == "fast-api-template"
    assert {"/auth/login", "/auth/referesh", "/users/", "/users/{user_id}"} <= set(
        document["paths"]
    )
