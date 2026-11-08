import logging
import signal
import threading

from app.config import config
from app.logger import setup_logging
from app.poller import run_loop as poller_loop
from app.store import database
from app.worker import run_loop as worker_loop


def _init_database_schema() -> None:
    connection = database.connect(config.DATABASE_PATH)
    database.init_schema(connection)
    connection.close()


def main() -> None:
    setup_logging(config.LOGGING_LEVEL)
    log = logging.getLogger(__name__)

    _init_database_schema()
    log.info("Database schema created")

    stop = threading.Event()

    def _on_signal(signum, _):
        log.info("received signal %s, shutting down", signum)
        stop.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    poller = threading.Thread(target=poller_loop, args=(config.DATABASE_PATH, stop), name="poller", daemon=False)
    worker = threading.Thread(target=worker_loop, args=(config.DATABASE_PATH, stop), name="worker", daemon=False)

    poller.start()
    worker.start()

    log.info("started (poller + worker)")
    stop.wait()

    poller.join(timeout=5)
    worker.join(timeout=5)

    log.info("stopped")


if __name__ == "__main__":
    main()
