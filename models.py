
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func

from database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    issue_date = Column(String, nullable=False)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, server_default=func.now())


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True, index=True)
    job_id = Column(
        String,
        ForeignKey("generation_jobs.id"),
        nullable=False
    )
    recipient_name = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    file_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)