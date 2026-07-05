from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utc_now
from app.models.user import enum_values


class DraftStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DISCARDED = "discarded"


class MeetingSummary(Base):
    __tablename__ = "meeting_summaries"
    __table_args__ = (
        Index("uk_summary_ai_job_id", "ai_job_id", unique=True),
        Index("idx_summaries_meeting_id", "meeting_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    ai_job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ai_jobs.id"))
    topic: Mapped[str] = mapped_column(String(200))
    participants_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    key_points_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    decisions_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    raw_model_output: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class TodoDraft(Base):
    __tablename__ = "todo_drafts"
    __table_args__ = (
        Index("idx_todo_drafts_meeting_id", "meeting_id"),
        Index("idx_todo_drafts_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    ai_job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ai_jobs.id"))
    description: Mapped[str] = mapped_column(Text)
    assignee_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus, values_callable=enum_values, name="draft_status"),
        default=DraftStatus.DRAFT,
    )
    confirmed_task_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", name="fk_todo_drafts_confirmed_task_id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
