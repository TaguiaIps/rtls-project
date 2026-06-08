from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from rtls_api.auth import require_role
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.ingestion import ensure_utc, gateway_health_status
from rtls_api.models import Gateway, GatewayHeartbeat, User, UserRole
from rtls_api.schemas import GatewayHealthResponse

GATEWAY_HEALTH_ROUTER = APIRouter(prefix="/api/admin", tags=["admin-gateway-health"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@GATEWAY_HEALTH_ROUTER.get("/gateway-health", response_model=list[GatewayHealthResponse])
def list_gateway_health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> list[GatewayHealthResponse]:
    now = datetime.now(timezone.utc)
    gateways = db.scalars(
        select(Gateway)
        .join(GatewayHeartbeat, GatewayHeartbeat.gateway_id == Gateway.id)
        .options(joinedload(Gateway.floor), joinedload(Gateway.latest_heartbeat))
        .order_by(Gateway.display_name.asc(), Gateway.gateway_identifier.asc())
    ).all()
    return [
        GatewayHealthResponse(
            gateway_id=gateway.id,
            floor_id=gateway.floor_id,
            floor_name=gateway.floor.name,
            gateway_identifier=gateway.gateway_identifier,
            display_name=gateway.display_name,
            hardware_tier=gateway.hardware_tier,
            status=gateway_health_status(
                settings=settings,
                last_seen_at=gateway.latest_heartbeat.last_seen_at,
                now=now,
            ),
            last_seen_at=ensure_utc(gateway.latest_heartbeat.last_seen_at),
            gateway_timestamp=ensure_utc(gateway.latest_heartbeat.gateway_timestamp),
            message_id=gateway.latest_heartbeat.message_id,
            firmware_version=gateway.latest_heartbeat.firmware_version,
            battery_level_percent=gateway.latest_heartbeat.battery_level_percent,
        )
        for gateway in gateways
        if gateway.latest_heartbeat is not None
    ]
