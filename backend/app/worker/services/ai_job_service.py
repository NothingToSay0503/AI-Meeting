import re
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.job import AiJob, JobStatus
from app.models.meeting import Meeting, MeetingStatus, MeetingTranscript
from app.models.summary import DraftStatus, MeetingSummary, TodoDraft
from app.services.event_service import create_outbox_event
from app.worker.graphs.minutes_graph import run_minutes_graph
from app.worker.llm.base import MinutesProvider
from app.worker.providers import build_minutes_provider


WEEKDAY_INDEX = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}


def parse_due_date(value: str | None, *, reference_date: date) -> date | None:
    if not value:
        return None
    normalized = value.strip()
    try:
        return date.fromisoformat(normalized[:10])
    except ValueError:
        pass

    if "后天" in normalized:
        return reference_date + timedelta(days=2)
    if "明天" in normalized or "明日" in normalized:
        return reference_date + timedelta(days=1)
    if "今天" in normalized or "今日" in normalized:
        return reference_date

    weekday_match = re.search(r"(?:(本周|这周|下周)([一二三四五六日天])|(?:周|星期)([一二三四五六日天]))", normalized)
    if weekday_match:
        prefix = weekday_match.group(1) or "本周"
        weekday = WEEKDAY_INDEX[weekday_match.group(2) or weekday_match.group(3)]
        start_of_week = reference_date - timedelta(days=reference_date.weekday())
        if prefix == "下周":
            start_of_week += timedelta(days=7)
        return start_of_week + timedelta(days=weekday)

    return None


def run_ai_job(db: Session, ai_job_id: int, provider: MinutesProvider | None = None) -> AiJob:
    job = db.get(AiJob, ai_job_id)
    if job is None:
        raise ValueError(f"AI job not found: {ai_job_id}")
    if job.status == JobStatus.SUCCEEDED:
        return job

    job.status = JobStatus.PROCESSING
    job.started_at = utc_now()
    job.error_message = None
    db.flush()

    try:
        transcript = db.get(MeetingTranscript, job.transcript_id)
        if transcript is None:
            raise ValueError(f"Meeting transcript not found: {job.transcript_id}")
        meeting = db.get(Meeting, job.meeting_id)
        reference_date = meeting.meeting_time.date() if meeting is not None else utc_now().date()

        selected_provider = provider or build_minutes_provider()
        result = run_minutes_graph(transcript.content, selected_provider)

        existing_summary = db.scalar(select(MeetingSummary).where(MeetingSummary.ai_job_id == job.id))
        if existing_summary is not None:
            db.delete(existing_summary)
        for existing_draft in db.scalars(select(TodoDraft).where(TodoDraft.ai_job_id == job.id)).all():
            db.delete(existing_draft)
        db.flush()

        summary = MeetingSummary(
            meeting_id=job.meeting_id,
            ai_job_id=job.id,
            topic=result.topic,
            participants_json={"items": result.participants},
            key_points_json={"items": result.key_points},
            decisions_json={"items": result.decisions},
            raw_model_output=result.model_dump(mode="json"),
        )
        db.add(summary)

        for todo in result.todos:
            db.add(
                TodoDraft(
                    meeting_id=job.meeting_id,
                    ai_job_id=job.id,
                    description=todo.description,
                    assignee_name=todo.assignee_name,
                    due_date=parse_due_date(todo.due_date, reference_date=reference_date),
                    source_sentence=todo.source_sentence,
                    confidence=Decimal(str(todo.confidence)),
                    status=DraftStatus.DRAFT,
                )
            )

        if meeting is not None:
            meeting.status = MeetingStatus.READY

        job.status = JobStatus.SUCCEEDED
        job.finished_at = utc_now()
        create_outbox_event(
            db,
            topic="ai.summary.completed",
            aggregate_type="ai_job",
            aggregate_id=job.id,
            payload={"ai_job_id": job.id, "meeting_id": job.meeting_id, "transcript_id": job.transcript_id},
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
