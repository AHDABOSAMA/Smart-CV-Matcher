from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_list_cvs_endpoint():
    response = client.get("/cv/list")

    assert response.status_code == 200
