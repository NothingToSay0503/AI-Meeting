from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now
from app.models.audio import AudioFile
from app.models.job import AiJob, AsrJob, JobStatus
from app.models.meeting import Meeting, MeetingStatus, MeetingTranscript, TranscriptSourceType
from app.services.event_service import create_outbox_event
from app.worker.asr.base import AsrProvider
from app.worker.graphs.asr_graph import run_asr_graph
from app.worker.providers import build_asr_provider


def run_asr_job(db: Session, asr_job_id: int, provider: AsrProvider | None = None) -> AsrJob:
    job = db.get(AsrJob, asr_job_id)
    if job is None:
        raise ValueError(f"ASR job not found: {asr_job_id}")

    job.status = JobStatus.PROCESSING
    job.started_at = utc_now()
    job.error_message = None
    db.flush()

    try:
        audio_file = db.get(AudioFile, job.audio_file_id)
        if audio_file is None:
            raise ValueError(f"Audio file not found: {job.audio_file_id}")

        selected_provider = provider or build_asr_provider()
        result = run_asr_graph(Path(audio_file.file_path), selected_provider)

        transcript = MeetingTranscript(
            meeting_id=job.meeting_id,
            asr_job_id=job.id,
            source_type=TranscriptSourceType.AUDIO_ASR,
            content=result.text,
            language=settings.xfei_asr_language,
            created_by=audio_file.uploaded_by,
        )
        db.add(transcript)
        db.flush()

        ai_job = AiJob(
            meeting_id=job.meeting_id,
            transcript_id=transcript.id,
            provider=settings.llm_provider,
            model=settings.llm_model,
            status=JobStatus.PENDING,
            retry_count=0,
        )
        db.add(ai_job)
        db.flush()

        job.status = JobStatus.SUCCEEDED
        job.finished_at = utc_now()
        create_outbox_event(
            db,
            topic="asr.completed",
            aggregate_type="asr_job",
            aggregate_id=job.id,
            payload={
                "asr_job_id": job.id,
                "meeting_id": job.meeting_id,
                "audio_file_id": audio_file.id,
                "transcript_id": transcript.id,
                "ai_job_id": ai_job.id,
            },
        )
        db.commit()
        db.refresh(job)
        return job
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
        job.finished_at = utc_now()
        meeting = db.get(Meeting, job.meeting_id)
        if meeting is not None:
            meeting.status = MeetingStatus.FAILED
        db.commit()
        db.refresh(job)
        raise
