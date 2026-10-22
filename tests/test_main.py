import sqlite3

import pytest
from fastapi.testclient import TestClient

from database import DEFAULT_DATABASE_PATH, initialize_database
from main import create_app


@pytest.fixture
def client(tmp_path) -> TestClient:
    return TestClient(create_app(tmp_path / "tasks.db"))


def test_root_returns_exact_service_information(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tasks_returns_three_sample_tasks(client: TestClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "title": "Buy groceries", "done": False},
        {"id": 2, "title": "Walk the dog", "done": True},
        {"id": 3, "title": "Read a book", "done": False},
    ]


def test_get_existing_task(client: TestClient) -> None:
    response = client.get("/tasks/2")

    assert response.status_code == 200
    assert response.json() == {"id": 2, "title": "Walk the dog", "done": True}


def test_get_unknown_task_returns_404(client: TestClient) -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_create_task_assigns_next_id_and_defaults_done(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Write tests"})

    assert response.status_code == 201
    assert response.json() == {"id": 4, "title": "Write tests", "done": False}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": 42},
        {"title": None},
    ],
)
def test_create_task_rejects_missing_blank_or_invalid_title(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.post("/tasks", json=body)

    assert response.status_code == 400
    assert "detail" in response.json()


def test_create_task_rejects_missing_body(client: TestClient) -> None:
    response = client.post("/tasks")

    assert response.status_code == 400
    assert "detail" in response.json()


def test_create_task_rejects_malformed_json(client: TestClient) -> None:
    response = client.post(
        "/tasks",
        content="{",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_update_title_only(client: TestClient) -> None:
    response = client.put("/tasks/1", json={"title": "Updated title"})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Updated title", "done": False}


def test_update_done_only(client: TestClient) -> None:
    response = client.put("/tasks/1", json={"done": True})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Buy groceries", "done": True}


def test_update_both_fields(client: TestClient) -> None:
    response = client.put(
        "/tasks/1", json={"title": "Updated title", "done": True}
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Updated title", "done": True}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"title": ""},
        {"title": "  "},
        {"title": None},
        {"done": None},
        {"done": "true"},
        {"other": "value"},
    ],
)
def test_update_rejects_empty_or_invalid_fields(
    client: TestClient, body: dict[str, object]
) -> None:
    response = client.put("/tasks/1", json=body)

    assert response.status_code == 400
    assert "detail" in response.json()


def test_update_rejects_missing_body(client: TestClient) -> None:
    response = client.put("/tasks/1")

    assert response.status_code == 400
    assert "detail" in response.json()


def test_update_unknown_task_returns_404(client: TestClient) -> None:
    response = client.put("/tasks/999", json={"done": True})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_existing_task_returns_empty_204(client: TestClient) -> None:
    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks/1").status_code == 404


def test_delete_unknown_task_returns_404(client: TestClient) -> None:
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_next_task_id_increments_after_deletion(client: TestClient) -> None:
    client.delete("/tasks/3")

    response = client.post("/tasks", json={"title": "New task"})

    assert response.status_code == 201
    assert response.json()["id"] == 4


def test_openapi_includes_task_endpoints(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert {
        "/",
        "/health",
        "/tasks",
        "/tasks/{task_id}",
    }.issubset(schema["paths"])
    assert "400" in schema["paths"]["/tasks"]["post"]["responses"]
    assert "404" in schema["paths"]["/tasks/{task_id}"]["get"]["responses"]


def test_swagger_docs_are_available(client: TestClient) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_each_app_starts_with_isolated_sample_data(tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "first.db"))
    client.delete("/tasks/1")

    fresh_client = TestClient(create_app(tmp_path / "second.db"))
    assert fresh_client.get("/tasks/1").status_code == 200


def test_database_initialization_creates_three_seed_tasks(tmp_path) -> None:
    database_path = tmp_path / "nested" / "tasks.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 3


def test_reinitializing_database_does_not_duplicate_seed_tasks(tmp_path) -> None:
    database_path = tmp_path / "tasks.db"

    initialize_database(database_path)
    initialize_database(database_path)
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 3


def test_default_database_path_is_next_to_application() -> None:
    assert DEFAULT_DATABASE_PATH.name == "tasks.db"
    assert DEFAULT_DATABASE_PATH.is_absolute()
