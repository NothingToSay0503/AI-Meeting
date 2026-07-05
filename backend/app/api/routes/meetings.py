from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.job import AiJob, AsrJob
from app.models.meeting import Meeting, MeetingTranscript
from app.models.summary import MeetingSummary, TodoDraft
from app.models.user import User
from app.schemas.meeting import (
    AiJobRead,
    AsrJobRead,
    AudioUploadResponse,
    ManualTranscriptCreate,
    ManualTranscriptJobResponse,
    MeetingRead,
    MeetingSummaryRead,
    TranscriptRead,
)
from app.schemas.task import TodoDraftRead
from app.services.auth_service import get_current_user
from app.services.meeting_service import create_audio_asr_job, create_manual_transcript_job

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/manual-transcripts", response_model=ManualTranscriptJobResponse, status_code=status.HTTP_201_CREATED)
def create_manual_transcript(
    payload: ManualTranscriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ManualTranscriptJobResponse:
    result = create_manual_transcript_job(
        db=db,
        meeting_title=payload.meeting_title,
        meeting_time=payload.meeting_time,
        transcript_content=payload.transcript_content,
        created_by=current_user.id,
    )
    return ManualTranscriptJobResponse(
        meeting_id=result.meeting.id,
        transcript_id=result.transcript.id,
        ai_job_id=result.ai_job.id,
    )


@router.post("/audio", response_model=AudioUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_audio(
    meeting_title: str = Form(...),
    meeting_time: datetime | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AudioUploadResponse:
    try:
        result = create_audio_asr_job(
            db=db,
            meeting_title=meeting_title,
            meeting_time=meeting_time,
            audio=file,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AudioUploadResponse(
        meeting_id=result.meeting.id,
        audio_file_id=result.audio_file.id,
        asr_job_id=result.asr_job.id,
    )


@router.get("", response_model=list[MeetingRead])
def list_meetings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Meeting]:
    return list(db.scalars(select(Meeting).order_by(Meeting.created_at.desc())).all())


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


@router.get("/{meeting_id}/transcripts", response_model=list[TranscriptRead])
def list_transcripts(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MeetingTranscript]:
    return list(
        db.scalars(
            select(MeetingTranscript)
            .where(MeetingTranscript.meeting_id == meeting_id)
            .order_by(MeetingTranscript.created_at.desc()),
        ).all(),
    )


@router.get("/{meeting_id}/summary", response_model=MeetingSummaryRead)
def get_meeting_summary(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MeetingSummary:
    summary = db.scalar(
        select(MeetingSummary)
        .where(MeetingSummary.meeting_id == meeting_id)
        .order_by(MeetingSummary.created_at.desc()),
    )
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting summary not found")
    return summary


@router.get("/{meeting_id}/todo-drafts", response_model=list[TodoDraftRead])
def list_meeting_todo_drafts(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TodoDraft]:
    return list(
        db.scalars(
            select(TodoDraft)
            .where(TodoDraft.meeting_id == meeting_id)
            .order_by(TodoDraft.created_at.desc()),
        ).all(),
    )


@router.get("/{meeting_id}/ai-jobs", response_model=list[AiJobRead])
def list_meeting_ai_jobs(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AiJob]:
    return list(
        db.scalars(
            select(AiJob)
            .where(AiJob.meeting_id == meeting_id)
            .order_by(AiJob.created_at.desc()),
        ).all(),
    )


@router.get("/{meeting_id}/asr-jobs", response_model=list[AsrJobRead])
def list_meeting_asr_jobs(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AsrJob]:
    return list(
        db.scalars(
            select(AsrJob)
            .where(AsrJob.meeting_id == meeting_id)
            .order_by(AsrJob.created_at.desc()),
        ).all(),
    )
