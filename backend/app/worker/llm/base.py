from typing import Protocol

from pydantic import BaseModel, Field


class ExtractedTodo(BaseModel):
    description: str
    assignee_name: str | None = None
    due_date: str | None = None
    source_sentence: str | None = None
    confidence: float = Field(default=0.8, ge=0, le=1)


class MinutesResult(BaseModel):
    topic: str
    participants: list[str]
    key_points: list[str]
    decisions: list[str]
    todos: list[ExtractedTodo]
    raw: dict = Field(default_factory=dict)


class MinutesProvider(Protocol):
    def summarize(self, transcript: str) -> MinutesResult:
        raise NotImplementedError
