from datetime import date, datetime

from pydantic import BaseModel, field_serializer

from app.schemas.datetime import serialize_utc_datetime


class TodoDraftConfirmRequest(BaseModel):
    assignee_id: int
    title: str
    description: str
    due_date: date | None = None


class TaskPatchRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None


class TaskStatusUpdateRequest(BaseModel):
    status: str


class TaskRead(BaseModel):
    id: int
    meeting_id: int
    draft_id: int | None
    title: str
    description: str
    assignee_id: int
    due_date: date | None
    status: str
    confirmed_by: int
    confirmed_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("confirmed_at")
    def serialize_confirmed_at(self, value: datetime) -> str:
        return serialize_utc_datetime(value) or ""


class TodoDraftRead(BaseModel):
    id: int
    meeting_id: int
    ai_job_id: int
    description: str
    assignee_name: str | None
    assignee_id: int | None
    due_date: date | None
    source_sentence: str | None
    confidence: float | None
    status: str
    confirmed_task_id: int | None

    model_config = {"from_attributes": True}
