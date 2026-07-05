from datetime import date

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.summary import DraftStatus, TodoDraft
from app.models.task import Task, TaskStatus, TaskStatusLog
from app.services.event_service import create_outbox_event

ALLOWED_TASK_STATUSES = {status.value for status in TaskStatus}


def confirm_todo_draft(
    db: Session,
    *,
    draft_id: int,
    assignee_id: int,
    confirmed_by: int,
    title: str,
    description: str,
    due_date: date | None,
) -> Task:
    draft = db.get(TodoDraft, draft_id)
    if draft is None:
        raise ValueError("Todo draft not found")
    if draft.status != DraftStatus.DRAFT:
        raise ValueError("Todo draft is not confirmable")

    task = Task(
        meeting_id=draft.meeting_id,
        draft_id=draft.id,
        title=title,
        description=description,
        assignee_id=assignee_id,
        due_date=due_date,
        status=TaskStatus.TODO,
        confirmed_by=confirmed_by,
        confirmed_at=utc_now(),
    )
    db.add(task)
    db.flush()

    draft.status = DraftStatus.CONFIRMED
    draft.confirmed_task_id = task.id

    log = TaskStatusLog(task_id=task.id, from_status=None, to_status=TaskStatus.TODO.value, changed_by=confirmed_by)
    db.add(log)
    create_outbox_event(
        db,
        topic="todo.confirmed",
        aggregate_type="task",
        aggregate_id=task.id,
        payload={"task_id": task.id, "meeting_id": task.meeting_id, "assignee_id": assignee_id},
    )
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, *, task_id: int, to_status: str, changed_by: int) -> Task:
    if to_status not in ALLOWED_TASK_STATUSES:
        raise ValueError("Invalid task status")
    task = db.get(Task, task_id)
    if task is None:
        raise ValueError("Task not found")

    from_status = task.status.value
    task.status = TaskStatus(to_status)
    db.add(TaskStatusLog(task_id=task.id, from_status=from_status, to_status=to_status, changed_by=changed_by))
    create_outbox_event(
        db,
        topic="todo.status.changed",
        aggregate_type="task",
        aggregate_id=task.id,
        payload={"task_id": task.id, "from_status": from_status, "to_status": to_status},
    )
    db.commit()
    db.refresh(task)
    return task
