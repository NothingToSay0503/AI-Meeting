from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.summary import DraftStatus, TodoDraft
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskPatchRequest, TaskRead, TaskStatusUpdateRequest, TodoDraftConfirmRequest, TodoDraftRead
from app.services.auth_service import get_current_user
from app.services.task_service import ALLOWED_TASK_STATUSES, confirm_todo_draft, update_task_status

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Task]:
    statement = select(Task).order_by(Task.created_at.desc())
    if status_filter is not None:
        if status_filter not in ALLOWED_TASK_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task status")
        statement = statement.where(Task.status == TaskStatus(status_filter))
    return list(db.scalars(statement).all())


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def patch_task(
    task_id: int,
    payload: TaskPatchRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for field in ("title", "description", "assignee_id", "due_date"):
        value = getattr(payload, field)
        if value is not None:
            setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}/status", response_model=TaskRead)
def patch_task_status(
    task_id: int,
    payload: TaskStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    try:
        return update_task_status(db=db, task_id=task_id, to_status=payload.status, changed_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/todo-drafts/{draft_id}/confirm", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def confirm_draft(
    draft_id: int,
    payload: TodoDraftConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    try:
        return confirm_todo_draft(
            db=db,
            draft_id=draft_id,
            assignee_id=payload.assignee_id,
            confirmed_by=current_user.id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/todo-drafts/{draft_id}/discard", response_model=TodoDraftRead)
def discard_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TodoDraft:
    draft = db.get(TodoDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo draft not found")
    if draft.status != DraftStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Todo draft is not discardable")

    draft.status = DraftStatus.DISCARDED
    db.commit()
    db.refresh(draft)
    return draft
