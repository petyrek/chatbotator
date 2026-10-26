from fastapi.testclient import TestClient

from chatbotator.main import create_app

client = TestClient(create_app())


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "chatbotator-api",
        "aiConnected": False,
    }
    assert response.headers["cache-control"] == "no-store"


def test_chat_not_implemented_yet() -> None:
    response = client.post("/api/chat")
    assert response.status_code == 501
    assert response.json()["error"] == "NOT_IMPLEMENTED"
