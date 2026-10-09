
from uuid import uuid4
from pathlib import Path
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import date

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    TypeAdapter,
    EmailStr,
    ValidationError,
)
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal, get_db
from models import GenerationJob, Certificate
from certificate import generate_certificate


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator",
    description="Generate and retrieve certificates in bulk",
    version="1.0.0"
)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecipientInput(BaseModel):
    name: str
    email: str


class BulkCertificateRequest(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    issue_date: str = Field(min_length=1, max_length=30)
    recipients: list[RecipientInput] = Field(min_length=1, max_length=500)

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Event name cannot be empty or whitespace")

        return value

    @field_validator("issue_date")
    @classmethod
    def validate_issue_date(cls, value: str) -> str:
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            raise ValueError(
                "Issue date must use YYYY-MM-DD format"
            )

        if parsed_date.isoformat() != value:
            raise ValueError(
                "Issue date must use YYYY-MM-DD format"
            )

        return value

def process_job(job_id: str):
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if not job:
            return

        job.status = "PROCESSING"
        db.commit()

        recipients = db.query(Certificate).filter(
            Certificate.job_id == job_id
        ).all()

        for recipient in recipients:
            try:
                name = recipient.recipient_name.strip()
                email = recipient.recipient_email.strip()

                if not name:
                    raise ValueError("Recipient name is required")
                try:
                    TypeAdapter(EmailStr).validate_python(email)
                except ValidationError:
                    raise ValueError("Invalid email address")

                recipient.file_path = generate_certificate(
                    certificate_id=recipient.id,
                    recipient_name=name,
                    event_name=job.event_name,
                    issue_date=job.issue_date
                )
                recipient.status = "SUCCESS"
                recipient.error_message = None

            except Exception as exc:
                recipient.status = "FAILED"
                recipient.error_message = str(exc)[:500]

            # Persist after every item: completed items survive a later failure
            # and status polling exposes accurate in-flight progress.
            job.success_count = db.query(Certificate).filter(
                Certificate.job_id == job_id,
                Certificate.status == "SUCCESS"
            ).count()
            job.failed_count = db.query(Certificate).filter(
                Certificate.job_id == job_id,
                Certificate.status == "FAILED"
            ).count()
            db.commit()

        # Recalculate from committed rows before completing the job. This also
        # guards against a session seeing stale state after a per-item commit.
        job.success_count = db.query(Certificate).filter(
            Certificate.job_id == job_id,
            Certificate.status == "SUCCESS"
        ).count()
        job.failed_count = db.query(Certificate).filter(
            Certificate.job_id == job_id,
            Certificate.status == "FAILED"
        ).count()
        job.status = "COMPLETED"
        db.commit()

    except Exception:
        db.rollback()
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()
        if job:
            job.status = "FAILED"
            db.commit()
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Bulk Certificate Generator API is running"}


@app.post("/api/jobs/", status_code=202)
def create_job(
    request: BulkCertificateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job_id = str(uuid4())

    job = GenerationJob(
        id=job_id,
        event_name=request.event_name,
        issue_date=request.issue_date,
        total_count=len(request.recipients),
        status="PENDING"
    )
    db.add(job)

    for item in request.recipients:
        recipient = Certificate(
            id=str(uuid4()),
            job_id=job_id,
            recipient_name=item.name,
            recipient_email=item.email,
            status="PENDING"
        )
        db.add(recipient)

    db.commit()

    background_tasks.add_task(process_job, job_id)

    return {
        "job_id": job_id,
        "status": "PENDING",
        "total_count": len(request.recipients),
        "message": "Certificate generation job submitted"
    }


@app.get("/api/jobs/{job_id}/")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "status": job.status,
        "total_count": job.total_count,
        "success_count": job.success_count,
        "failed_count": job.failed_count,
        "created_at": job.created_at
    }


@app.get("/api/certificates/{certificate_id}/")
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    certificate = db.query(Certificate).filter(
        Certificate.id == certificate_id
    ).first()

    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if certificate.status != "SUCCESS" or not certificate.file_path:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available yet"
        )

    from pathlib import Path
    file_path = Path(certificate.file_path)

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{certificate.id}.pdf"
    )


@app.get("/api/jobs/{job_id}/certificates/")
def list_job_certificates(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    recipients = db.query(Certificate).filter(
        Certificate.job_id == job_id
    ).all()

    return [
        {
            "certificate_id": item.id,
            "recipient_name": item.recipient_name,
            "recipient_email": item.recipient_email,
            "status": item.status,
            "error_message": item.error_message,
            "download_url": (
                f"/api/certificates/{item.id}/"
                if item.status == "SUCCESS"
                else None
            )
        }
        for item in recipients
    ]


# The optional browser client is served by the same process as the API, so no
# separate Live Server or CORS configuration is required for normal use.
app.mount(
    "/app",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend",
)
