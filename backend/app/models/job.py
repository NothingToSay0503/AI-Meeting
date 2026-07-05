from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utc_now
from app.models.user import enum_values


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AsrJob(Base):
    __tablename__ = "asr_jobs"
    __table_args__ = (
        Index("idx_asr_jobs_status", "status"),
        Index("idx_asr_jobs_meeting_id", "meeting_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    audio_file_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("audio_files.id"))
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, values_callable=enum_values, name="asr_job_status"),
        default=JobStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class AiJob(Base):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("idx_ai_jobs_status", "status"),
        Index("idx_ai_jobs_meeting_id", "meeting_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    transcript_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("meeting_transcripts.id")
    )
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, values_callable=enum_values, name="ai_job_status"),
        default=JobStatus.PENDING,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
