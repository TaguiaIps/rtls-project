from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from rtls_api.config import get_settings
from rtls_api.db import create_session_factory
from rtls_api.ingestion import (
    TelemetryIngestionService,
    heartbeat_topic,
    telemetry_topic,
)
from rtls_api.ingestion_store import create_message_dedupe_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rtls-worker")


def build_subscription_topics() -> tuple[str, str]:
    settings = get_settings()
    return (telemetry_topic(settings), heartbeat_topic(settings))


def subscribe_to_topics(client: Any) -> None:
    for topic in build_subscription_topics():
        client.subscribe(topic, qos=1)


def create_ingestion_service() -> TelemetryIngestionService:
    settings = get_settings()
    return TelemetryIngestionService(
        session_factory=create_session_factory(settings),
        settings=settings,
        dedupe_store=create_message_dedupe_store(
            settings.redis_url,
            settings.ingestion_dedupe_key_prefix,
        ),
    )


def create_mqtt_client(ingestion_service: TelemetryIngestionService) -> Any:
    try:
        import paho.mqtt.client as mqtt
    except ImportError as error:  # pragma: no cover
        raise RuntimeError("paho-mqtt must be installed to run the worker") from error

    settings = get_settings()
    client = mqtt.Client(client_id=f"rtls-worker-{uuid4()}")
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    def on_connect(
        client: Any,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        del userdata, flags, properties
        if int(reason_code) != 0:
            logger.error("mqtt_connect_failed reason_code=%s", reason_code)
            return

        subscribe_to_topics(client)
        logger.info("mqtt_subscribed topics=%s", ",".join(build_subscription_topics()))

    def on_message(client: Any, userdata: Any, message: Any) -> None:
        del client, userdata
        result = ingestion_service.process_message(
            topic=message.topic,
            payload_bytes=message.payload,
        )
        log_level = logging.INFO if result.accepted else logging.WARNING
        logger.log(
            log_level,
            "ingestion_result topic=%s accepted=%s type=%s reason=%s raw_readings=%s",
            message.topic,
            result.accepted,
            result.message_type,
            result.reason,
            result.raw_reading_count,
        )

    client.on_connect = on_connect
    client.on_message = on_message
    return client


def main() -> None:
    settings = get_settings()
    ingestion_service = create_ingestion_service()
    client = create_mqtt_client(ingestion_service)
    logger.info(
        "worker_started env=%s mqtt=%s:%s redis=%s",
        settings.env,
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.redis_url,
    )
    client.connect(
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        keepalive=settings.mqtt_keepalive_seconds,
    )
    client.loop_forever()


if __name__ == "__main__":
    main()
