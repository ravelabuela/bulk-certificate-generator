# Bulk Certificate Generator

A FastAPI service that accepts one request containing many recipients,
generates a personalized PDF certificate for every valid recipient, and keeps
a durable record of job and item status.

## Features

- Submit up to 500 recipients in one request.
- Generate a PDF from one predefined ReportLab certificate template.
- Track a job's `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED` status.
- Isolate recipient failures: one bad recipient does not stop the batch.
- List individual results and download successful PDFs.
- Includes API and PDF-generation tests.

## Technology

Python, FastAPI, SQLAlchemy, SQLite, ReportLab, and pytest.

## Setup and Run

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

The interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

The browser client is available at `http://127.0.0.1:8000/app/`.

## Submit a Job

`POST /api/jobs/` returns `202 Accepted` because the work starts in a FastAPI
background task.

```json
{
  "event_name": "Python Workshop",
  "issue_date": "2026-10-09",
  "recipients": [
    {"name": "Ravela Buela", "email": "ravela@example.com"},
    {"name": "Priya", "email": "priya@example.com"}
  ]
}
```

Example response:

```json
{
  "job_id": "4c1a...",
  "status": "PENDING",
  "total_count": 2,
  "message": "Certificate generation job submitted"
}
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Health check |
| POST | `/api/jobs/` | Submit a bulk generation job |
| GET | `/api/jobs/{job_id}/` | Get job status and progress counts |
| GET | `/api/jobs/{job_id}/certificates/` | List every recipient result |
| GET | `/api/certificates/{certificate_id}/` | Download a generated PDF |

Poll the job endpoint until its status is `COMPLETED` or `FAILED`. During
`PROCESSING`, `success_count + failed_count` is the number of recipients
already processed. List the job's certificates next; successful entries expose
a `download_url`, which can be requested to retrieve the PDF.

## Validation and Failure Handling

The API validates required fields, non-empty event names, ISO dates in
`YYYY-MM-DD` format, a non-empty recipient list, and the 500-recipient limit.
Email validation occurs per recipient during background processing. This is
deliberate: an invalid email is stored as a failed item with an error message,
rather than rejecting the whole bulk request. Any PDF-generation exception is
handled the same way.

## Tests

```powershell
python -m pytest -v
```

Tests use an in-memory SQLite database and cover job creation, validation, PDF
creation, status/progress results, individual failures, and retrieval.

## Design Decisions

`BackgroundTasks` is a good lightweight fit for this assignment: the client
gets a job ID immediately and can observe progress while the request's items
are processed one at a time. Each item is committed independently, so results
already created remain recorded if a later item fails. SQLite and local PDF
storage make the project self-contained. In production, use a durable queue
and workers (such as Celery or RQ), a production relational database, and
object storage for PDFs.

The optional browser client lives in `frontend/index.html` and is served at
`/app/` by the FastAPI process. It can also be opened from a separate static
server; in that case it falls back to `http://127.0.0.1:8000` for API calls.
