
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Bulk Certificate Generator API is running"
    )


def test_job_not_found():
    response = client.get("/api/jobs/nonexistent-job/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_create_bulk_job():
    payload = {
        "event_name": "Python Workshop",
        "issue_date": "2026-10-09",
        "recipients": [
            {
                "name": "Test User",
                "email": "test@example.com"
            }
        ]
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 202

    data = response.json()
    assert data["total_count"] == 1
    assert data["status"] == "PENDING"
    assert "job_id" in data


def test_empty_recipients_rejected():
    payload = {
        "event_name": "Python Workshop",
        "issue_date": "2026-10-09",
        "recipients": []
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422