from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utc_now
from app.models.user import enum_values


class MeetingSourceType(StrEnum):
    AUDIO = "audio"
    MANUAL_TEXT = "manual_text"


class MeetingStatus(StrEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class TranscriptSourceType(StrEnum):
    AUDIO_ASR = "audio_asr"
    MANUAL_TEXT = "manual_text"


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        Index("idx_meetings_created_by", "created_by"),
        Index("idx_meetings_status", "status"),
        Index("idx_meetings_meeting_time", "meeting_time"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    meeting_time: Mapped[datetime] = mapped_column(DateTime)
    source_type: Mapped[MeetingSourceType] = mapped_column(
        Enum(
            MeetingSourceType, values_callable=enum_values, name="meeting_source_type"
        ),
    )
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, values_callable=enum_values, name="meeting_status"),
        default=MeetingStatus.DRAFT,
    )
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = (
        Index("idx_participants_meeting_id", "meeting_id"),
        Index("idx_participants_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    participant_name: Mapped[str] = mapped_column(String(64))
    is_ai_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class MeetingTranscript(Base):
    __tablename__ = "meeting_transcripts"
    __table_args__ = (
        Index("idx_transcripts_meeting_id", "meeting_id"),
        Index("idx_transcripts_source_type", "source_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    asr_job_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("asr_jobs.id"), nullable=True
    )
    source_type: Mapped[TranscriptSourceType] = mapped_column(
        Enum(
            TranscriptSourceType,
            values_callable=enum_values,
            name="transcript_source_type",
        ),
    )
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
