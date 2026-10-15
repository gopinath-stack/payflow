"""PayFlow - Notifier Worker
Background worker: waits for payment events on Redis and "sends" notifications.
No HTTP port - it only consumes a queue.
"""
import json
import logging
import os
import signal
import sys
import time

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EVENT_QUEUE = os.getenv("EVENT_QUEUE", "payment-events")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s notifier %(message)s")
log = logging.getLogger("notifier")

running = True


def stop(signum, frame):
    global running
    log.info("shutdown signal received")
    running = False


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def main() -> None:
    client = redis.Redis.from_url(REDIS_URL)
    log.info("notifier started, queue=%s", EVENT_QUEUE)
    while running:
        try:
            item = client.blpop(EVENT_QUEUE, timeout=5)
            if item is None:
                continue
            event = json.loads(item[1])
            log.info("NOTIFY: Rs %.2f sent from account %s to account %s (payment %s)",
                     event["amount"], event["from_account"], event["to_account"], event["id"])
        except redis.ConnectionError as exc:
            log.error("redis unavailable: %s - retrying in 3s", exc)
            time.sleep(3)
    log.info("notifier stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
