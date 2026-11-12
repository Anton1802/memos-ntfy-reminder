import signal
import threading

from app.config import config
from app.logger import get_logger
from app.poller import run_loop as poller_loop
from app.store import database
from app.worker import run_loop as worker_loop


def _init_database() -> None:
    connection = database.connect(config.DATABASE_PATH)
    database.init_schema(connection)
    connection.close()


def main() -> None:
    log = get_logger(__name__)

    _init_database()
    log.info("Database initialized")

    stop_event = threading.Event()

    def _on_signal(signum, _) -> None:
        log.info("Received signal %s, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    poller = threading.Thread(target=poller_loop, args=(config.DATABASE_PATH, stop_event), name="poller", daemon=False)
    worker = threading.Thread(target=worker_loop, args=(config.DATABASE_PATH, stop_event), name="worker", daemon=False)

    poller.start()
    worker.start()

    log.info("Ntfy reminder started")
    stop_event.wait()

    poller.join(timeout=5)
    worker.join(timeout=5)

    log.info("Ntfy reminder stopped")


if __name__ == "__main__":
    main()
