import json
import logging
from typing import Any

from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.worker.asr.base import AsrProvider
from app.worker.llm.base import MinutesProvider
from app.worker.services.ai_job_service import run_ai_job
from app.worker.services.asr_job_service import run_asr_job

logger = logging.getLogger(__name__)


def dispatch_event(
    *,
    db: Session,
    topic: str,
    payload: dict[str, Any],
    asr_provider: AsrProvider | None = None,
    minutes_provider: MinutesProvider | None = None,
) -> object | None:
    if topic == "audio.uploaded":
        return run_asr_job(db, int(payload["asr_job_id"]), provider=asr_provider)
    if topic in {"transcript.created", "asr.completed"}:
        return run_ai_job(db, int(payload["ai_job_id"]), provider=minutes_provider)
    return None


def process_worker_message(topic: str, payload: dict[str, Any]) -> None:
    try:
        with SessionLocal() as db:
            dispatch_event(db=db, topic=topic, payload=payload)
    except Exception:
        logger.exception("Worker failed to process topic=%s payload=%s", topic, payload)


def run_worker() -> None:
    consumer = KafkaConsumer(
        "audio.uploaded",
        "asr.completed",
        "transcript.created",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="meeting-minutes-ai-worker",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
    try:
        for message in consumer:
            process_worker_message(message.topic, message.value)
    finally:
        consumer.close()
