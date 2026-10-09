# Bulk Certificate Generator

A Python-based REST API that generates PDF certificates for multiple recipients in a single request. It tracks job progress, stores recipient details in SQLite, and handles individual recipient failures without stopping the entire batch.

## Features

* Generate certificates in bulk using a single API request.
* Create personalized PDF certificates using ReportLab.
* Store job and recipient information in SQLite.
* Track job status, total recipients, successful certificates, and failures.
* Handle invalid recipient data independently.
* Download generated certificates using their certificate IDs.
* Test API endpoints using Pytest.

## Technology Stack

* **Language:** Python
* **API Framework:** FastAPI
* **Database:** SQLite
* **ORM:** SQLAlchemy
* **PDF Generation:** ReportLab
* **Testing:** Pytest, FastAPI TestClient

## Project Structure

```text
bulk-certificate-generator/
├── main.py
├── database.py
├── models.py
├── certificate.py
├── requirements.txt
├── README.md
├── tests/
│   └── test_api.py
└── certificates/
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/bulk-certificate-generator.git
cd bulk-certificate-generator
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create and activate a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the application

```bash
uvicorn main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint                              | Description                    |
| ------ | ------------------------------------- | ------------------------------ |
| GET    | `/`                                   | Check API status               |
| POST   | `/api/jobs/`                          | Submit a bulk certificate job  |
| GET    | `/api/jobs/{job_id}/`                 | Retrieve job status and counts |
| GET    | `/api/jobs/{job_id}/certificates/`    | List certificates for a job    |
| GET    | `/api/certificates/{certificate_id}/` | Download a certificate PDF     |

## Example Request

Send a POST request to `/api/jobs/` with this JSON body:

```json
{
  "event_name": "Python Workshop",
  "issue_date": "2026-10-09",
  "recipients": [
    {
      "name": "Ravela Buela",
      "email": "ravela@example.com"
    },
    {
      "name": "Priya",
      "email": "priya@example.com"
    }
  ]
}
```

The API returns a job ID that can be used to check the job status and retrieve individual certificate IDs.

## Example Job Status

```json
{
  "job_id": "your-job-id",
  "event_name": "Python Workshop",
  "status": "COMPLETED",
  "total_count": 2,
  "success_count": 2,
  "failed_count": 0
}
```

## Run Tests

From the project root directory, execute:

```bash
python -m pytest -v
```

The initial automated test suite contains four tests covering the home endpoint, unknown jobs, job creation, and empty recipient validation.

## Error Handling

Each recipient is processed independently. Invalid recipient data is marked as failed, while other valid recipients can still receive certificates.

## Future Improvements

* Add isolated test database fixtures.
* Improve input validation and issue-date validation.
* Add authentication and authorization.
* Use a dedicated background task queue for production workloads.
* Add a downloadable ZIP archive for completed certificate batches.
* Add configurable certificate templates.

## Author

**Ravela Buela**

GitHub: https://github.com/buela-ravela

---

*This project was developed as a Python backend assignment to demonstrate REST API development, database integration, PDF generation, and automated testing.*
