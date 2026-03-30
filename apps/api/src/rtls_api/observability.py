from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from rtls_api.auth import require_role
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.ingestion import ensure_utc, gateway_health_status
from rtls_api.models import (
    AlertInstance,
    AlertSeverity,
    AlertStatus,
    AuditEvent,
    Gateway,
    GatewayHeartbeat,
    PremiumRawMeasurement,
    RawReading,
    User,
    UserRole,
)
from rtls_api.schemas import (
    AuditEventListResponse,
    AuditEventResponse,
    HealthRiskResponse,
    ObservabilityAlertTotalsResponse,
    ObservabilityAuditTotalsResponse,
    ObservabilityGatewayTotalsResponse,
    ObservabilityServiceResponse,
    ObservabilitySummaryResponse,
    ObservabilityTelemetryTotalsResponse,
)

OBSERVABILITY_ROUTER = APIRouter(prefix="/api/admin", tags=["admin-observability"])
METRICS_ROUTER = APIRouter(tags=["metrics"])

LOW_BATTERY_WARNING_PERCENT = 20.0
CRITICAL_BATTERY_PERCENT = 10.0

SERVICE_DETAILS: Sequence[tuple[str, str, str]] = (
    (
        "web",
        "baseline",
        "The web console renders admin health, audit, and operations surfaces.",
    ),
    (
        "api",
        "healthy",
        "Health summary, audit queries, and request identifiers are served by the API.",
    ),
    (
        "worker",
        "baseline",
        "Background processing owns telemetry ingestion and derived-state updates.",
    ),
    (
        "mqtt-broker",
        "baseline",
        "Gateway heartbeat and telemetry visibility depends on the broker path.",
    ),
    (
        "redis",
        "baseline",
        "Redis remains part of the dedupe and session-control baseline.",
    ),
    (
        "timescaledb",
        "baseline",
        "Operational counts and projections are derived from the primary data store.",
    ),
    (
        "object-storage",
        "baseline",
        "Object storage retains floor plans and future calibration artifacts.",
    ),
)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@OBSERVABILITY_ROUTER.get("/audit-events", response_model=AuditEventListResponse)
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=100),
    actor_email: str | None = None,
    action_category: str | None = None,
    action_type: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AuditEventListResponse:
    base_query = _apply_audit_filters(
        select(AuditEvent),
        actor_email=actor_email,
        action_category=action_category,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        created_after=created_after,
        created_before=created_before,
    )
    items = db.scalars(
        base_query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit)
    ).all()
    total_count = db.scalar(
        _apply_audit_filters(
            select(func.count()).select_from(AuditEvent),
            actor_email=actor_email,
            action_category=action_category,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            created_after=created_after,
            created_before=created_before,
        )
    )
    return AuditEventListResponse(
        items=[serialize_audit_event(item) for item in items],
        total_count=total_count or 0,
    )


@OBSERVABILITY_ROUTER.get(
    "/observability/summary",
    response_model=ObservabilitySummaryResponse,
)
def get_observability_summary(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> ObservabilitySummaryResponse:
    now = datetime.now(timezone.utc)
    gateways = db.scalars(
        select(Gateway)
        .options(joinedload(Gateway.floor), joinedload(Gateway.latest_heartbeat))
        .order_by(Gateway.display_name.asc(), Gateway.gateway_identifier.asc())
    ).all()

    raw_readings_total = db.scalar(select(func.count()).select_from(RawReading)) or 0
    premium_measurements_total = db.scalar(
        select(func.count()).select_from(PremiumRawMeasurement)
    ) or 0
    heartbeat_snapshots_total = db.scalar(
        select(func.count()).select_from(GatewayHeartbeat)
    ) or 0
    active_alert_count = db.scalar(
        select(func.count()).select_from(AlertInstance).where(
            AlertInstance.status.in_(
                [AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value]
            )
        )
    ) or 0
    active_critical_alert_count = db.scalar(
        select(func.count()).select_from(AlertInstance).where(
            AlertInstance.status.in_(
                [AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value]
            ),
            AlertInstance.severity == AlertSeverity.CRITICAL.value,
        )
    ) or 0
    active_warning_alert_count = db.scalar(
        select(func.count()).select_from(AlertInstance).where(
            AlertInstance.status.in_(
                [AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value]
            ),
            AlertInstance.severity == AlertSeverity.WARNING.value,
        )
    ) or 0
    total_audit_events = db.scalar(select(func.count()).select_from(AuditEvent)) or 0
    audit_events_last_24h = db.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.created_at >= now - timedelta(hours=24)
        )
    ) or 0
    latest_audit_event_at = db.scalar(select(func.max(AuditEvent.created_at)))

    gateway_summary = summarize_gateway_risks(
        gateways,
        settings=settings,
        now=now,
    )

    return ObservabilitySummaryResponse(
        generated_at=now,
        gateway_totals=ObservabilityGatewayTotalsResponse(
            total=len(gateways),
            healthy=gateway_summary["healthy"],
            stale=gateway_summary["stale"],
            low_battery=gateway_summary["low_battery"],
            without_heartbeat=gateway_summary["without_heartbeat"],
        ),
        telemetry_totals=ObservabilityTelemetryTotalsResponse(
            raw_readings=raw_readings_total,
            premium_measurements=premium_measurements_total,
            heartbeat_snapshots=heartbeat_snapshots_total,
        ),
        alert_totals=ObservabilityAlertTotalsResponse(
            active=active_alert_count,
            critical=active_critical_alert_count,
            warning=active_warning_alert_count,
        ),
        audit_totals=ObservabilityAuditTotalsResponse(
            total=total_audit_events,
            last_24h=audit_events_last_24h,
            latest_at=ensure_utc(latest_audit_event_at),
        ),
        risk_items=gateway_summary["risk_items"][:8],
        services=[
            ObservabilityServiceResponse(name=name, status=status, detail=detail)
            for name, status, detail in SERVICE_DETAILS
        ],
        healthcheck_path="/health",
        metrics_path="/metrics",
        request_id_header="X-Request-ID",
        tracing_status=(
            "Request identifiers are attached to every API response "
            "for operational tracing."
        ),
    )


@METRICS_ROUTER.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def get_metrics(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> str:
    now = datetime.now(timezone.utc)
    gateways = db.scalars(select(Gateway).options(joinedload(Gateway.latest_heartbeat))).all()
    gateway_summary = summarize_gateway_risks(
        gateways,
        settings=settings,
        now=now,
    )

    metrics = {
        "rtls_gateways_total": len(gateways),
        "rtls_gateways_stale_total": gateway_summary["stale"],
        "rtls_gateways_low_battery_total": gateway_summary["low_battery"],
        "rtls_audit_events_total": db.scalar(select(func.count()).select_from(AuditEvent)) or 0,
        "rtls_alert_instances_open_total": db.scalar(
            select(func.count()).select_from(AlertInstance).where(
                AlertInstance.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
            )
        )
        or 0,
        "rtls_raw_readings_total": db.scalar(select(func.count()).select_from(RawReading)) or 0,
        "rtls_premium_measurements_total": db.scalar(
            select(func.count()).select_from(PremiumRawMeasurement)
        )
        or 0,
        "rtls_gateway_heartbeat_snapshots_total": db.scalar(
            select(func.count()).select_from(GatewayHeartbeat)
        )
        or 0,
        "rtls_request_id_header_enabled": 1,
    }

    lines = []
    for metric_name, metric_value in metrics.items():
        lines.append(f"# TYPE {metric_name} gauge")
        lines.append(f"{metric_name} {metric_value}")
    return "\n".join(lines) + "\n"


def summarize_gateway_risks(
    gateways: Sequence[Gateway],
    *,
    settings: Settings,
    now: datetime,
) -> dict[str, int | list[HealthRiskResponse]]:
    healthy_gateways = 0
    stale_gateways = 0
    low_battery_gateways = 0
    gateways_without_heartbeat = 0
    risk_items: list[HealthRiskResponse] = []

    for gateway in gateways:
        heartbeat = gateway.latest_heartbeat
        if heartbeat is None:
            gateways_without_heartbeat += 1
            stale_gateways += 1
            risk_items.append(
                HealthRiskResponse(
                    id=f"stale:{gateway.id}",
                    kind="stale_gateway",
                    severity="critical",
                    gateway_id=gateway.id,
                    gateway_identifier=gateway.gateway_identifier,
                    display_name=gateway.display_name,
                    floor_id=gateway.floor_id,
                    floor_name=gateway.floor.name,
                    summary="No heartbeat has been recorded for this gateway yet.",
                    observed_at=None,
                    battery_level_percent=None,
                )
            )
            continue

        status = gateway_health_status(
            settings=settings,
            last_seen_at=heartbeat.last_seen_at,
            now=now,
        )
        if status.value == "stale":
            stale_gateways += 1
            risk_items.append(
                HealthRiskResponse(
                    id=f"stale:{gateway.id}",
                    kind="stale_gateway",
                    severity="warning",
                    gateway_id=gateway.id,
                    gateway_identifier=gateway.gateway_identifier,
                    display_name=gateway.display_name,
                    floor_id=gateway.floor_id,
                    floor_name=gateway.floor.name,
                    summary=(
                        f"No heartbeat within the last "
                        f"{settings.gateway_heartbeat_stale_after_seconds} seconds."
                    ),
                    observed_at=ensure_utc(heartbeat.last_seen_at),
                    battery_level_percent=heartbeat.battery_level_percent,
                )
            )
        else:
            healthy_gateways += 1

        if (
            heartbeat.battery_level_percent is not None
            and heartbeat.battery_level_percent <= LOW_BATTERY_WARNING_PERCENT
        ):
            low_battery_gateways += 1
            risk_items.append(
                HealthRiskResponse(
                    id=f"battery:{gateway.id}",
                    kind="low_battery_gateway",
                    severity=(
                        "critical"
                        if heartbeat.battery_level_percent <= CRITICAL_BATTERY_PERCENT
                        else "warning"
                    ),
                    gateway_id=gateway.id,
                    gateway_identifier=gateway.gateway_identifier,
                    display_name=gateway.display_name,
                    floor_id=gateway.floor_id,
                    floor_name=gateway.floor.name,
                    summary=(
                        f"Battery dropped to {heartbeat.battery_level_percent:.0f}% "
                        "on the latest heartbeat."
                    ),
                    observed_at=ensure_utc(heartbeat.last_seen_at),
                    battery_level_percent=heartbeat.battery_level_percent,
                )
            )

    risk_items.sort(
        key=lambda item: (
            0 if item.severity == "critical" else 1,
            -(item.observed_at.timestamp() if item.observed_at is not None else 0),
            item.display_name.lower(),
        )
    )
    return {
        "healthy": healthy_gateways,
        "stale": stale_gateways,
        "low_battery": low_battery_gateways,
        "without_heartbeat": gateways_without_heartbeat,
        "risk_items": risk_items,
    }


def _apply_audit_filters(
    statement,
    *,
    actor_email: str | None,
    action_category: str | None,
    action_type: str | None,
    target_type: str | None,
    target_id: str | None,
    created_after: datetime | None,
    created_before: datetime | None,
):
    if actor_email:
        like_value = f"%{actor_email.strip()}%"
        statement = statement.where(AuditEvent.actor_email.ilike(like_value))
    if action_category:
        statement = statement.where(AuditEvent.action_category == action_category.strip())
    if action_type:
        statement = statement.where(AuditEvent.action_type == action_type.strip())
    if target_type:
        statement = statement.where(AuditEvent.target_type == target_type.strip())
    if target_id:
        statement = statement.where(AuditEvent.target_id == target_id.strip())
    if created_after is not None:
        statement = statement.where(AuditEvent.created_at >= created_after)
    if created_before is not None:
        statement = statement.where(AuditEvent.created_at <= created_before)
    return statement


def serialize_audit_event(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        actor_user_id=event.actor_user_id,
        actor_email=event.actor_email,
        actor_role=event.actor_role,
        action_category=event.action_category,
        action_type=event.action_type,
        target_type=event.target_type,
        target_id=event.target_id,
        details=event.details,
        created_at=ensure_utc(event.created_at),
    )
