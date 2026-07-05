import threading

from app.worker.events import run_worker
from app.worker.outbox import run_outbox_publisher


def run_worker_process() -> None:
    publisher_thread = threading.Thread(
        target=run_outbox_publisher,
        daemon=True,
        name="outbox-publisher",
    )
    publisher_thread.start()
    run_worker()


if __name__ == "__main__":
    run_worker_process()
