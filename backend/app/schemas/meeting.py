from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_serializer

from app.schemas.datetime import serialize_utc_datetime


class ManualTranscriptCreate(BaseModel):
    meeting_title: str
    transcript_content: str
    meeting_time: datetime | None = None


class ManualTranscriptJobResponse(BaseModel):
    meeting_id: int
    transcript_id: int
    ai_job_id: int


class AudioUploadResponse(BaseModel):
    meeting_id: int
    audio_file_id: int
    asr_job_id: int


class MeetingRead(BaseModel):
    id: int
    title: str
    meeting_time: datetime
    source_type: str
    status: str
    created_by: int

    model_config = {"from_attributes": True}

    @field_serializer("meeting_time")
    def serialize_meeting_time(self, value: datetime) -> str:
        return serialize_utc_datetime(value) or ""


class TranscriptRead(BaseModel):
    id: int
    meeting_id: int
    source_type: str
    content: str
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value) or ""


class MeetingSummaryRead(BaseModel):
    id: int
    meeting_id: int
    ai_job_id: int
    topic: str
    participants_json: dict[str, Any]
    key_points_json: dict[str, Any]
    decisions_json: dict[str, Any]
    raw_model_output: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value) or ""


class AsrJobRead(BaseModel):
    id: int
    meeting_id: int
    audio_file_id: int
    provider: str
    model: str
    status: str
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}

    @field_serializer("started_at", "finished_at")
    def serialize_optional_datetime(self, value: datetime | None) -> str | None:
        return serialize_utc_datetime(value)


class AiJobRead(BaseModel):
    id: int
    meeting_id: int
    transcript_id: int
    provider: str
    model: str
    status: str
    retry_count: int
    error_message: str | None

    model_config = {"from_attributes": True}
