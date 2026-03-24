from __future__ import annotations

import logging
import time

from rtls_api.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rtls-worker")


def main() -> None:
    settings = get_settings()
    logger.info(
        "worker_started env=%s mqtt=%s:%s redis=%s",
        settings.env,
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.redis_url,
    )

    while True:
        logger.info("worker_heartbeat")
        time.sleep(30)


if __name__ == "__main__":
    main()
