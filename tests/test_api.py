
from fastapi.testclient import TestClient
from pathlib import Path
import main

client = TestClient(main.app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Bulk Certificate Generator API is running"
    )


def test_browser_client_is_served():
    response = client.get("/app/")

    assert response.status_code == 200
    assert "Bulk Certificate Generator" in response.text


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


def test_one_invalid_recipient_does_not_stop_others(monkeypatch):
    # Replace PDF generation with a lightweight test function.
    # This test focuses on recipient processing and job counts.
    def fake_generate_certificate(
        certificate_id,
        recipient_name,
        event_name,
        issue_date
    ):
        return f"fake_certificates/{certificate_id}.pdf"

    monkeypatch.setattr(
        main,
        "generate_certificate",
        fake_generate_certificate
    )

    payload = {
        "event_name": "Python Workshop",
        "issue_date": "2026-10-09",
        "recipients": [
            {
                "name": "Ravela Buela",
                "email": "ravela@example.com"
            },
            {
                "name": "Invalid Recipient",
                "email": "not-an-email"
            },
            {
                "name": "Priya",
                "email": "priya@example.com"
            }
        ]
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 202

    job_id = response.json()["job_id"]

    # The test client waits for background tasks to finish.
    status_response = client.get(f"/api/jobs/{job_id}/")

    assert status_response.status_code == 200

    job = status_response.json()
    assert job["status"] == "COMPLETED"
    assert job["total_count"] == 3
    assert job["success_count"] == 2
    assert job["failed_count"] == 1

    # Check the result for every recipient.
    list_response = client.get(
        f"/api/jobs/{job_id}/certificates/"
    )

    assert list_response.status_code == 200

    certificates = list_response.json()

    assert len(certificates) == 3

    assert certificates[0]["status"] == "SUCCESS"
    assert certificates[1]["status"] == "FAILED"
    assert certificates[2]["status"] == "SUCCESS"

    assert certificates[1]["error_message"] == "Invalid email address"
    assert certificates[1]["download_url"] is None
    assert certificates[0]["download_url"] is not None
    assert certificates[2]["download_url"] is not None


def test_one_pdf_generation_failure_does_not_stop_other_recipients(
    monkeypatch,
):
    def selective_generator(certificate_id, recipient_name, event_name, issue_date):
        if recipient_name == "Cannot Generate":
            raise RuntimeError("Template rendering failed")
        return f"fake_certificates/{certificate_id}.pdf"

    monkeypatch.setattr(main, "generate_certificate", selective_generator)

    response = client.post(
        "/api/jobs/",
        json={
            "event_name": "Python Workshop",
            "issue_date": "2026-10-09",
            "recipients": [
                {"name": "Working Recipient", "email": "one@example.com"},
                {"name": "Cannot Generate", "email": "two@example.com"},
            ],
        },
    )

    assert response.status_code == 202
    job_id = response.json()["job_id"]

    job = client.get(f"/api/jobs/{job_id}/").json()
    assert job["status"] == "COMPLETED"
    assert job["success_count"] == 1
    assert job["failed_count"] == 1

    certificates = client.get(
        f"/api/jobs/{job_id}/certificates/"
    ).json()
    results = {item["recipient_name"]: item for item in certificates}
    assert results["Working Recipient"]["status"] == "SUCCESS"
    assert results["Cannot Generate"]["status"] == "FAILED"
    assert results["Cannot Generate"]["error_message"] == (
        "Template rendering failed"
    )


def test_certificate_pdf_is_created(tmp_path, monkeypatch):
    import certificate

    monkeypatch.setattr(certificate, "OUTPUT_DIR", tmp_path)

    file_path = certificate.generate_certificate(
        certificate_id="test-pdf-001",
        recipient_name="Ravela Buela",
        event_name="Python Workshop",
        issue_date="2026-10-09",
    )

    pdf_file = Path(file_path)

    assert pdf_file.exists()
    assert pdf_file.suffix == ".pdf"
    assert pdf_file.stat().st_size > 0


def test_download_generated_certificate():
    # Create a job; TestClient runs its background task.
    payload = {
        "event_name": "Python Workshop",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Download Test User", "email": "download@example.com"}
        ],
    }

    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Find the generated certificate ID.
    list_response = client.get(
        f"/api/jobs/{job_id}/certificates/"
    )
    assert list_response.status_code == 200

    certificate_id = list_response.json()[0]["certificate_id"]

    # Download the PDF.
    download_response = client.get(
        f"/api/certificates/{certificate_id}/"
    )

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF")


def test_download_unknown_certificate():
    response = client.get("/api/certificates/unknown-certificate/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate not found"


def test_download_certificate_not_available_yet():
    # Create a job with an invalid email so generation fails.
    payload = {
        "event_name": "Python Workshop",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Pending User", "email": "invalid-email"}
        ],
    }

    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 202

    job_id = response.json()["job_id"]

    # Find the failed certificate.
    list_response = client.get(
        f"/api/jobs/{job_id}/certificates/"
    )
    assert list_response.status_code == 200

    certificate_id = list_response.json()[0]["certificate_id"]
    assert list_response.json()[0]["status"] == "FAILED"

    # Downloading an unavailable certificate should return HTTP 409.
    download_response = client.get(
        f"/api/certificates/{certificate_id}/"
    )

    assert download_response.status_code == 409
    assert download_response.json()["detail"] == (
        "Certificate is not available yet"
    )


def test_whitespace_event_name_rejected():
    payload = {
        "event_name": "   ",
        "issue_date": "2026-10-09",
        "recipients": [
            {"name": "Test User", "email": "test@example.com"}
        ],
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_invalid_issue_date_rejected():
    payload = {
        "event_name": "Python Workshop",
        "issue_date": "not-a-date",
        "recipients": [
            {"name": "Test User", "email": "test@example.com"}
        ],
    }

    response = client.post("/api/jobs/", json=payload)

    assert response.status_code == 422


def test_missing_recipient_name_rejected():
    response = client.post(
        "/api/jobs/",
        json={
            "event_name": "Python Workshop",
            "issue_date": "2026-10-09",
            "recipients": [
                {"email": "test@example.com"}
            ],
        },
    )

    assert response.status_code == 422


def test_missing_recipient_email_rejected():
    response = client.post(
        "/api/jobs/",
        json={
            "event_name": "Python Workshop",
            "issue_date": "2026-10-09",
            "recipients": [
                {"name": "Ravi"}
            ],
        },
    )

    assert response.status_code == 422
