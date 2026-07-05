from dataclasses import dataclass
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.models.audio import AudioFile
from app.models.event import EventOutbox
from app.models.job import AiJob, AsrJob, JobStatus
from app.models.meeting import Meeting, MeetingSourceType, MeetingStatus, MeetingTranscript, TranscriptSourceType
from app.services.event_service import create_outbox_event
from app.services.storage_service import save_audio_file


@dataclass
class ManualTranscriptJobResult:
    meeting: Meeting
    transcript: MeetingTranscript
    ai_job: AiJob
    event: EventOutbox


@dataclass
class AudioAsrJobResult:
    meeting: Meeting
    audio_file: AudioFile
    asr_job: AsrJob
    event: EventOutbox


def create_manual_transcript_job(
    db: Session,
    *,
    meeting_title: str,
    meeting_time: datetime | None,
    transcript_content: str,
    created_by: int,
) -> ManualTranscriptJobResult:
    meeting = Meeting(
        title=meeting_title,
        meeting_time=meeting_time or utc_now(),
        source_type=MeetingSourceType.MANUAL_TEXT,
        status=MeetingStatus.PROCESSING,
        created_by=created_by,
    )
    db.add(meeting)
    db.flush()

    transcript = MeetingTranscript(
        meeting_id=meeting.id,
        source_type=TranscriptSourceType.MANUAL_TEXT,
        content=transcript_content,
        created_by=created_by,
    )
    db.add(transcript)
    db.flush()

    ai_job = AiJob(
        meeting_id=meeting.id,
        transcript_id=transcript.id,
        provider=settings.llm_provider,
        model=settings.llm_model,
        status=JobStatus.PENDING,
        retry_count=0,
    )
    db.add(ai_job)
    db.flush()

    event = create_outbox_event(
        db,
        topic="transcript.created",
        aggregate_type="ai_job",
        aggregate_id=ai_job.id,
        payload={"ai_job_id": ai_job.id, "meeting_id": meeting.id, "transcript_id": transcript.id},
    )
    db.flush()
    db.commit()
    db.refresh(meeting)
    db.refresh(transcript)
    db.refresh(ai_job)
    db.refresh(event)
    return ManualTranscriptJobResult(meeting=meeting, transcript=transcript, ai_job=ai_job, event=event)


def create_audio_asr_job(
    db: Session,
    *,
    meeting_title: str,
    meeting_time: datetime | None,
    audio: UploadFile,
    created_by: int,
) -> AudioAsrJobResult:
    file_path, size_bytes = save_audio_file(audio)

    meeting = Meeting(
        title=meeting_title,
        meeting_time=meeting_time or utc_now(),
        source_type=MeetingSourceType.AUDIO,
        status=MeetingStatus.PROCESSING,
        created_by=created_by,
    )
    db.add(meeting)
    db.flush()

    audio_file = AudioFile(
        meeting_id=meeting.id,
        original_name=audio.filename or "audio.mp3",
        file_path=file_path,
        mime_type=audio.content_type or "audio/mpeg",
        size_bytes=size_bytes,
        uploaded_by=created_by,
    )
    db.add(audio_file)
    db.flush()

    asr_job = AsrJob(
        meeting_id=meeting.id,
        audio_file_id=audio_file.id,
        provider=settings.asr_provider,
        model=settings.asr_provider,
        status=JobStatus.PENDING,
    )
    db.add(asr_job)
    db.flush()

    event = create_outbox_event(
        db,
        topic="audio.uploaded",
        aggregate_type="asr_job",
        aggregate_id=asr_job.id,
        payload={"asr_job_id": asr_job.id, "meeting_id": meeting.id, "audio_file_id": audio_file.id},
    )
    db.flush()
    db.commit()
    db.refresh(meeting)
    db.refresh(audio_file)
    db.refresh(asr_job)
    db.refresh(event)
    return AudioAsrJobResult(meeting=meeting, audio_file=audio_file, asr_job=asr_job, event=event)
