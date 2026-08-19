from typing import Any

from fastapi.testclient import TestClient

PROTECTED_OPERATIONS = {
    ("/auth/change-password", "post"),
    ("/auth/logout-all", "post"),
    ("/users/", "get"),
    ("/users/{user_id}", "delete"),
    ("/users/{user_id}", "get"),
    ("/users/{user_id}", "patch"),
}


def test_operation_ids_are_unique(client: TestClient) -> None:
    document: dict[str, Any] = client.get("/openapi.json").json()
    operation_ids = [
        operation["operationId"]
        for path in document["paths"].values()
        for method, operation in path.items()
        if method not in {"parameters", "summary", "description"}
    ]

    assert len(operation_ids) == len(set(operation_ids))


def test_protected_operations_declare_bearer_authentication(client: TestClient) -> None:
    document: dict[str, Any] = client.get("/openapi.json").json()

    for path, method in PROTECTED_OPERATIONS:
        assert document["paths"][path][method]["security"] == [{"HTTPBearer": []}]


def test_health_contract_documents_readiness_failure(client: TestClient) -> None:
    document: dict[str, Any] = client.get("/openapi.json").json()

    readiness_responses = document["paths"]["/health/ready"]["get"]["responses"]
    assert readiness_responses["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
    assert readiness_responses["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
