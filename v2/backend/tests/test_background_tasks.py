import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_background_tasks_status():
    response = client.get("/api/v1/background-tasks/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any('task_name' in task for task in data)
