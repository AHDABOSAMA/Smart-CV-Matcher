from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_expected_fields():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["llm_provider"], str)
    assert isinstance(data["chroma_docs"], int)
    assert isinstance(data["embedding_model"], str)