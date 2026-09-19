from __future__ import annotations

import logging
import signal
import threading

from app.config import DB_PATH, setup_logging
from app.poller import run_loop as poller_loop
from app.store import db
from app.worker import run_loop as worker_loop


def main() -> None:
    setup_logging()
    log = logging.getLogger("run")

    # только для init schema
    boot_conn = db.connect(DB_PATH)
    db.init_schema(boot_conn)
    boot_conn.close()

    stop = threading.Event()

    def _on_signal(signum, frame):
        log.info("received signal %s, shutting down", signum)
        stop.set()

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    poller = threading.Thread(
        target=poller_loop, args=(DB_PATH, stop), name="poller", daemon=False
    )
    worker = threading.Thread(
        target=worker_loop, args=(DB_PATH, stop), name="worker", daemon=False
    )

    poller.start()
    worker.start()

    log.info("started (poller + worker)")
    stop.wait()

    poller.join(timeout=5)
    worker.join(timeout=5)

    log.info("stopped")


if __name__ == "__main__":
    main()
