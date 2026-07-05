from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.job import AiJob, JobStatus
from app.models.user import User
from app.schemas.meeting import AiJobRead
from app.services.auth_service import get_current_user
from app.services.event_service import create_outbox_event

router = APIRouter(prefix="/ai-jobs", tags=["ai-jobs"])


@router.get("/{job_id}", response_model=AiJobRead)
def get_ai_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AiJob:
    job = db.get(AiJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
    return job


@router.post("/{job_id}/retry", response_model=AiJobRead)
def retry_ai_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AiJob:
    job = db.get(AiJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
    if job.status != JobStatus.FAILED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only failed AI jobs can be retried")

    job.status = JobStatus.PENDING
    job.retry_count += 1
    job.error_message = None
    create_outbox_event(
        db,
        topic="transcript.created",
        aggregate_type="ai_job",
        aggregate_id=job.id,
        payload={"ai_job_id": job.id, "meeting_id": job.meeting_id, "transcript_id": job.transcript_id},
    )
    db.commit()
    db.refresh(job)
    return job
