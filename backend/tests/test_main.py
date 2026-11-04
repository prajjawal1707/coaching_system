from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_get_students():
    response = client.get("/students")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_student_fees():
    response = client.get("/fees/FF-1001")

    assert response.status_code == 200
    assert response.json()["pending_fees"] == 30000