from typing import Any

from sqlalchemy.orm import Session

from app.models.event import EventOutbox, OutboxStatus


def create_outbox_event(
    db: Session,
    *,
    topic: str,
    aggregate_type: str,
    aggregate_id: int,
    payload: dict[str, Any],
) -> EventOutbox:
    event = EventOutbox(
        topic=topic,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload_json=payload,
        status=OutboxStatus.PENDING,
        retry_count=0,
    )
    db.add(event)
    return event
