from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RTLS_", extra="ignore")

    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    web_origin: str = "http://localhost:5173"
    jwt_secret_key: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 10
    refresh_token_ttl_days: int = 7
    refresh_session_key_prefix: str = "rtls:auth:refresh"
    database_url: str = "postgresql://rtls:rtls@timescaledb:5432/rtls"
    redis_url: str = "redis://redis:6379/0"
    mqtt_broker_host: str = "mqtt-broker"
    mqtt_broker_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_keepalive_seconds: int = 60
    mqtt_topic_prefix: str = "rtls"
    ingestion_dedupe_key_prefix: str = "rtls:ingest:message"
    ingestion_dedupe_ttl_seconds: int = 10
    positioning_recent_window_seconds: int = 20
    live_location_stream_poll_interval_ms: int = 500
    gateway_heartbeat_stale_after_seconds: int = 120
    object_storage_endpoint: str = "http://object-storage:9000"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    object_storage_bucket: str = "rtls-floor-plans"
    object_storage_region: str = "us-east-1"
    raw_reading_retention_days: int = 90
    premium_measurement_retention_days: int = 90
    location_history_retention_days: int = 30
    export_retention_days: int = 7
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    alert_email_from_address: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
