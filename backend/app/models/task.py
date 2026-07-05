from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.time import utc_now
from app.models.user import enum_values


class TaskStatus(StrEnum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_tasks_assignee_status", "assignee_id", "status"),
        Index("idx_tasks_meeting_id", "meeting_id"),
        Index("idx_tasks_due_date", "due_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meetings.id"))
    draft_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("todo_drafts.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    assignee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, values_callable=enum_values, name="task_status"),
        default=TaskStatus.TODO,
    )
    confirmed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
    )
    status_logs: Mapped[list["TaskStatusLog"]] = relationship(
        back_populates="task",
        order_by="TaskStatusLog.changed_at",
    )


class TaskStatusLog(Base):
    __tablename__ = "task_status_logs"
    __table_args__ = (Index("idx_task_logs_task_id", "task_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"))
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32))
    changed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    task: Mapped[Task] = relationship(back_populates="status_logs")
