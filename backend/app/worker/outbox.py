import json
import time
from typing import Any, Protocol

from kafka import KafkaProducer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.time import utc_now
from app.models.event import EventOutbox, OutboxStatus


class EventProducer(Protocol):
    def send(self, topic: str, value: dict[str, Any]) -> object:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError


def build_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )


def publish_pending_events_once(
    db: Session,
    *,
    producer: EventProducer | None = None,
    limit: int = 50,
) -> int:
    selected_producer = producer or build_kafka_producer()
    events = list(
        db.scalars(
            select(EventOutbox)
            .where(EventOutbox.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]))
            .order_by(EventOutbox.created_at)
            .limit(limit),
        ).all()
    )

    published_count = 0
    for event in events:
        try:
            selected_producer.send(event.topic, value=event.payload_json)
            event.status = OutboxStatus.PUBLISHED
            event.published_at = utc_now()
            event.error_message = None
            published_count += 1
        except Exception as exc:
            event.status = OutboxStatus.FAILED
            event.retry_count += 1
            event.error_message = str(exc)

    if published_count:
        selected_producer.flush()
    db.commit()
    return published_count


def run_outbox_publisher(poll_seconds: float = 2.0) -> None:
    producer = build_kafka_producer()
    while True:
        with SessionLocal() as db:
            publish_pending_events_once(db, producer=producer)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    run_outbox_publisher()
