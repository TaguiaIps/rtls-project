from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from rtls_api.auth import get_current_user
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.ingestion import ensure_utc, gateway_health_status
from rtls_api.models import (
    AssetCurrentLocation,
    AssetTag,
    Floor,
    Gateway,
    GatewayHeartbeat,
    LocationConfidenceLevel,
    SpatialAreaType,
    User,
)
from rtls_api.positioning import serialize_asset_current_location
from rtls_api.schemas import (
    AssetLocationResponse,
    GatewayHealthResponse,
    OperationsMapPreviewResponse,
    OperationsOverviewKpisResponse,
    OperationsOverviewResponse,
    OperationsPriorityItemResponse,
)
from rtls_api.spatial_admin import serialize_area, serialize_floor_plan, serialize_gateway

OPERATIONS_OVERVIEW_ROUTER = APIRouter(prefix="/api/operations", tags=["operations"])


@dataclass(frozen=True)
class ResolvedOperationsContext:
    site_id: str | None
    site_name: str | None
    floor_id: str | None
    floor_name: str | None


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@OPERATIONS_OVERVIEW_ROUTER.get("/overview", response_model=OperationsOverviewResponse)
def get_operations_overview(
    site_id: str | None = None,
    floor_id: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
) -> OperationsOverviewResponse:
    context = _resolve_operations_context(db=db, site_id=site_id, floor_id=floor_id)
    locations = []
    if context.floor_id is not None:
        locations = _query_current_locations(db=db, floor_id=context.floor_id)
    stale_gateways = (
        _query_stale_gateways(db=db, settings=settings, floor_id=context.floor_id)
        if context.floor_id is not None
        else []
    )
    restricted_zone_assets = [
        location
        for location in locations
        if location.zone is not None
        and location.zone.area_type == SpatialAreaType.RESTRICTED_ZONE.value
    ]
    low_confidence_assets = [
        location
        for location in locations
        if location.confidence_level == LocationConfidenceLevel.LOW.value
    ]
    priority_items = _build_priority_items(
        locations=locations,
        stale_gateways=stale_gateways,
        settings=settings,
    )
    feed_updated_at = _derive_feed_updated_at(locations=locations, stale_gateways=stale_gateways)
    feed_status = _derive_feed_status(
        locations=locations,
        stale_gateways=stale_gateways,
        feed_updated_at=feed_updated_at,
        settings=settings,
    )
    map_preview = _build_map_preview(
        db=db,
        site_id=context.site_id,
        site_name=context.site_name,
        floor_id=context.floor_id,
        floor_name=context.floor_name,
        locations=locations[:6],
    )

    return OperationsOverviewResponse(
        site_id=context.site_id,
        site_name=context.site_name,
        floor_id=context.floor_id,
        floor_name=context.floor_name,
        feed_status=feed_status,
        feed_updated_at=feed_updated_at,
        kpis=OperationsOverviewKpisResponse(
            active_assets=len(locations),
            low_confidence_assets=len(low_confidence_assets),
            restricted_zone_assets=len(restricted_zone_assets),
            stale_gateways=len(stale_gateways),
        ),
        priority_items=priority_items[:5],
        gateway_snapshot=stale_gateways[:5],
        map_preview=map_preview,
    )


def _resolve_operations_context(
    *,
    db: Session,
    site_id: str | None,
    floor_id: str | None,
) -> ResolvedOperationsContext:
    selected_floor: Floor | None = None
    if floor_id is not None:
        selected_floor = db.scalar(
            select(Floor)
            .where(Floor.id == floor_id)
            .options(joinedload(Floor.site))
        )
    elif site_id is not None:
        site = db.scalar(
            select(Floor)
            .where(Floor.site_id == site_id)
            .options(joinedload(Floor.site))
            .order_by(Floor.level_label.asc().nullslast(), Floor.name.asc())
        )
        selected_floor = site

    if selected_floor is None:
        selected_floor = db.scalar(
            select(Floor)
            .options(joinedload(Floor.site))
            .order_by(Floor.level_label.asc().nullslast(), Floor.name.asc())
        )

    if selected_floor is None:
        return ResolvedOperationsContext(None, None, None, None)

    return ResolvedOperationsContext(
        site_id=selected_floor.site.id,
        site_name=selected_floor.site.name,
        floor_id=selected_floor.id,
        floor_name=selected_floor.name,
    )


def _query_current_locations(
    *,
    db: Session,
    floor_id: str,
) -> list[AssetCurrentLocation]:
    return db.scalars(
        select(AssetCurrentLocation)
        .join(AssetCurrentLocation.asset_tag)
        .join(AssetCurrentLocation.floor)
        .options(
            joinedload(AssetCurrentLocation.asset_tag),
            joinedload(AssetCurrentLocation.floor).joinedload(Floor.site),
            joinedload(AssetCurrentLocation.zone),
        )
        .where(AssetCurrentLocation.floor_id == floor_id)
        .order_by(AssetCurrentLocation.observed_at.desc(), AssetTag.display_name.asc())
    ).all()


def _query_stale_gateways(
    *,
    db: Session,
    settings: Settings,
    floor_id: str,
) -> list[GatewayHealthResponse]:
    now = datetime.now(timezone.utc)
    gateways = db.scalars(
        select(Gateway)
        .join(GatewayHeartbeat, GatewayHeartbeat.gateway_id == Gateway.id)
        .options(joinedload(Gateway.floor), joinedload(Gateway.latest_heartbeat))
        .where(Gateway.floor_id == floor_id)
        .order_by(Gateway.display_name.asc(), Gateway.gateway_identifier.asc())
    ).all()

    health_entries: list[GatewayHealthResponse] = []
    for gateway in gateways:
        heartbeat = gateway.latest_heartbeat
        if heartbeat is None:
            continue
        status = gateway_health_status(
            settings=settings,
            last_seen_at=heartbeat.last_seen_at,
            now=now,
        )
        if status.value != "stale":
            continue
        health_entries.append(
            GatewayHealthResponse(
                gateway_id=gateway.id,
                floor_id=gateway.floor_id,
                floor_name=gateway.floor.name,
                gateway_identifier=gateway.gateway_identifier,
                display_name=gateway.display_name,
                hardware_tier=gateway.hardware_tier,
                status=status,
                last_seen_at=ensure_utc(heartbeat.last_seen_at),
                gateway_timestamp=ensure_utc(heartbeat.gateway_timestamp),
                message_id=heartbeat.message_id,
                firmware_version=heartbeat.firmware_version,
                battery_level_percent=heartbeat.battery_level_percent,
            )
        )
    return health_entries


def _build_priority_items(
    *,
    locations: list[AssetCurrentLocation],
    stale_gateways: list[GatewayHealthResponse],
    settings: Settings,
) -> list[OperationsPriorityItemResponse]:
    items: list[OperationsPriorityItemResponse] = []
    for location in locations:
        if (
            location.zone is not None
            and location.zone.area_type == SpatialAreaType.RESTRICTED_ZONE.value
        ):
            items.append(
                OperationsPriorityItemResponse(
                    id=f"restricted-zone:{location.asset_tag_id}",
                    kind="restricted_zone_asset",
                    severity="critical",
                    title=f"{location.asset_tag.display_name} entered a restricted zone",
                    summary=f"Last known zone: {location.zone.name}.",
                    observed_at=ensure_utc(location.observed_at),
                    floor_id=location.floor_id,
                    asset_tag_id=location.asset_tag_id,
                    gateway_id=None,
                )
            )
        if location.confidence_level == LocationConfidenceLevel.LOW.value:
            zone_name = location.zone.name if location.zone is not None else location.floor.name
            items.append(
                OperationsPriorityItemResponse(
                    id=f"low-confidence:{location.asset_tag_id}",
                    kind="low_confidence_asset",
                    severity="warning",
                    title=f"{location.asset_tag.display_name} has degraded confidence",
                    summary=f"Last known context: {zone_name}.",
                    observed_at=ensure_utc(location.observed_at),
                    floor_id=location.floor_id,
                    asset_tag_id=location.asset_tag_id,
                    gateway_id=None,
                )
            )

    stale_after = settings.gateway_heartbeat_stale_after_seconds
    for gateway in stale_gateways:
        items.append(
            OperationsPriorityItemResponse(
                id=f"stale-gateway:{gateway.gateway_id}",
                kind="stale_gateway",
                severity="warning",
                title=f"{gateway.display_name} heartbeat is stale",
                summary=f"No heartbeat within the last {stale_after} seconds.",
                observed_at=gateway.last_seen_at,
                floor_id=gateway.floor_id,
                asset_tag_id=None,
                gateway_id=gateway.gateway_id,
            )
        )

    severity_rank = {"critical": 0, "warning": 1}
    return sorted(
        items,
        key=lambda item: (
            severity_rank[item.severity],
            -item.observed_at.timestamp(),
            item.title.lower(),
        ),
    )


def _derive_feed_updated_at(
    *,
    locations: list[AssetCurrentLocation],
    stale_gateways: list[GatewayHealthResponse],
) -> datetime | None:
    observed_times = [ensure_utc(location.observed_at) for location in locations]
    observed_times.extend(ensure_utc(entry.last_seen_at) for entry in stale_gateways)
    normalized_times = [value for value in observed_times if value is not None]
    if not normalized_times:
        return None
    return max(normalized_times)


def _derive_feed_status(
    *,
    locations: list[AssetCurrentLocation],
    stale_gateways: list[GatewayHealthResponse],
    feed_updated_at: datetime | None,
    settings: Settings,
) -> str:
    if not locations and not stale_gateways:
        return "empty"

    now = datetime.now(timezone.utc)
    stale_cutoff = timedelta(seconds=settings.positioning_recent_window_seconds * 2)
    if stale_gateways:
        return "degraded"
    if feed_updated_at is None or now - feed_updated_at > stale_cutoff:
        return "degraded"
    return "live"


def _build_map_preview(
    *,
    db: Session,
    site_id: str | None,
    site_name: str | None,
    floor_id: str | None,
    floor_name: str | None,
    locations: list[AssetCurrentLocation],
) -> OperationsMapPreviewResponse:
    if floor_id is None:
        return OperationsMapPreviewResponse(
            site_id=site_id,
            site_name=site_name,
            floor_id=None,
            floor_name=None,
            floor_plan=None,
            areas=[],
            gateways=[],
            locations=[],
        )

    floor = db.scalar(
        select(Floor)
        .where(Floor.id == floor_id)
        .options(
            joinedload(Floor.floor_plan_asset),
            selectinload(Floor.areas),
            selectinload(Floor.gateways),
        )
    )
    if floor is None:
        return OperationsMapPreviewResponse(
            site_id=site_id,
            site_name=site_name,
            floor_id=floor_id,
            floor_name=floor_name,
            floor_plan=None,
            areas=[],
            gateways=[],
            locations=[],
        )

    ordered_areas = sorted(
        floor.areas,
        key=lambda area: (area.area_type, area.name.lower()),
    )
    ordered_gateways = sorted(
        floor.gateways,
        key=lambda gateway: (gateway.display_name.lower(), gateway.gateway_identifier.lower()),
    )
    return OperationsMapPreviewResponse(
        site_id=site_id,
        site_name=site_name,
        floor_id=floor.id,
        floor_name=floor.name,
        floor_plan=serialize_floor_plan(floor.floor_plan_asset) if floor.floor_plan_asset else None,
        areas=[serialize_area(area) for area in ordered_areas],
        gateways=[serialize_gateway(gateway) for gateway in ordered_gateways],
        locations=[
            AssetLocationResponse.model_validate(serialize_asset_current_location(location))
            for location in locations
        ],
    )
