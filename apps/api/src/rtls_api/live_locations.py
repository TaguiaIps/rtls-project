from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from rtls_api.auth import get_current_user
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.models import (
    AssetCurrentLocation,
    AssetLocationHistory,
    AssetLocationType,
    AssetTag,
    Floor,
    LocationConfidenceLevel,
    User,
    UserStatus,
)
from rtls_api.positioning import serialize_asset_current_location, serialize_asset_location_history
from rtls_api.schemas import (
    AssetLocationHistoryResponse,
    AssetLocationResponse,
    LiveLocationStreamEvent,
)
from rtls_api.security import TokenError, decode_token

LIVE_LOCATION_ROUTER = APIRouter(tags=["locations"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@LIVE_LOCATION_ROUTER.get("/api/locations/live", response_model=list[AssetLocationResponse])
def list_live_locations(
    site_id: str | None = None,
    floor_id: str | None = None,
    asset_tag_id: str | None = None,
    asset_category: str | None = None,
    search: str | None = None,
    confidence_level: LocationConfidenceLevel | None = None,
    location_type: AssetLocationType | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AssetLocationResponse]:
    locations = _query_current_locations(
        db=db,
        site_id=site_id,
        floor_id=floor_id,
        asset_tag_id=asset_tag_id,
        asset_category=asset_category,
        search=search,
        confidence_level=confidence_level,
        location_type=location_type,
    )
    return [
        AssetLocationResponse.model_validate(serialize_asset_current_location(location))
        for location in locations
    ]


@LIVE_LOCATION_ROUTER.get("/api/locations/search", response_model=list[AssetLocationResponse])
def search_live_locations(
    query: str = Query(min_length=1),
    site_id: str | None = None,
    floor_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AssetLocationResponse]:
    locations = _query_current_locations(
        db=db,
        site_id=site_id,
        floor_id=floor_id,
        search=query,
    )
    return [
        AssetLocationResponse.model_validate(serialize_asset_current_location(location))
        for location in locations
    ]


@LIVE_LOCATION_ROUTER.get(
    "/api/locations/assets/{asset_tag_id}/history",
    response_model=list[AssetLocationHistoryResponse],
)
def get_asset_location_history(
    asset_tag_id: str,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AssetLocationHistoryResponse]:
    query = (
        select(AssetLocationHistory)
        .join(AssetLocationHistory.asset_tag)
        .join(AssetLocationHistory.floor)
        .options(
            joinedload(AssetLocationHistory.asset_tag),
            joinedload(AssetLocationHistory.floor).joinedload(Floor.site),
            joinedload(AssetLocationHistory.zone),
        )
        .where(AssetLocationHistory.asset_tag_id == asset_tag_id)
        .order_by(AssetLocationHistory.observed_at.asc(), AssetLocationHistory.created_at.asc())
    )
    if start_at is not None:
        query = query.where(AssetLocationHistory.observed_at >= start_at)
    if end_at is not None:
        query = query.where(AssetLocationHistory.observed_at <= end_at)

    history = db.scalars(query).all()
    return [
        AssetLocationHistoryResponse.model_validate(serialize_asset_location_history(entry))
        for entry in history
    ]


@LIVE_LOCATION_ROUTER.websocket("/ws/locations")
async def stream_live_locations(websocket: WebSocket) -> None:
    if not await _authenticate_websocket(websocket):
        return

    await websocket.accept()
    site_id = websocket.query_params.get("site_id")
    floor_id = websocket.query_params.get("floor_id")
    search = websocket.query_params.get("search")
    asset_category = websocket.query_params.get("asset_category")
    last_seen_update = datetime.now(timezone.utc)
    settings: Settings = websocket.app.state.settings
    session_factory: sessionmaker[Session] = websocket.app.state.session_factory

    try:
        while True:
            await asyncio.sleep(settings.live_location_stream_poll_interval_ms / 1000)
            with session_factory() as db:
                updates = _query_current_locations(
                    db=db,
                    site_id=site_id,
                    floor_id=floor_id,
                    asset_category=asset_category,
                    search=search,
                    updated_after=last_seen_update,
                    order_by_updated_at=True,
                )

            for update in updates:
                await websocket.send_json(
                    LiveLocationStreamEvent(
                        location=AssetLocationResponse.model_validate(
                            serialize_asset_current_location(update)
                        )
                    ).model_dump(mode="json")
                )

            if updates:
                last_seen_update = max(
                    update.updated_at.astimezone(timezone.utc) for update in updates
                )
    except (RuntimeError, WebSocketDisconnect):
        return


async def _authenticate_websocket(websocket: WebSocket) -> bool:
    access_token = websocket.query_params.get("access_token")
    if not access_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False

    settings: Settings = websocket.app.state.settings
    session_factory: sessionmaker[Session] = websocket.app.state.session_factory
    try:
        payload = decode_token(access_token, settings, expected_type="access")
    except TokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return False

    with session_factory() as db:
        user = db.get(User, str(payload["sub"]))
        if user is None or user.status != UserStatus.ACTIVE.value:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False
    return True


def _query_current_locations(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
    asset_tag_id: str | None = None,
    asset_category: str | None = None,
    search: str | None = None,
    confidence_level: LocationConfidenceLevel | None = None,
    location_type: AssetLocationType | None = None,
    updated_after: datetime | None = None,
    order_by_updated_at: bool = False,
) -> list[AssetCurrentLocation]:
    query = (
        select(AssetCurrentLocation)
        .join(AssetCurrentLocation.asset_tag)
        .join(AssetCurrentLocation.floor)
        .options(
            joinedload(AssetCurrentLocation.asset_tag),
            joinedload(AssetCurrentLocation.floor).joinedload(Floor.site),
            joinedload(AssetCurrentLocation.zone),
        )
    )
    if site_id is not None:
        query = query.where(Floor.site_id == site_id)
    if floor_id is not None:
        query = query.where(AssetCurrentLocation.floor_id == floor_id)
    if asset_tag_id is not None:
        query = query.where(AssetCurrentLocation.asset_tag_id == asset_tag_id)
    if asset_category is not None:
        query = query.where(AssetTag.asset_category == asset_category)
    if search is not None:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(AssetTag.display_name.ilike(pattern), AssetTag.tag_identifier.ilike(pattern))
        )
    if confidence_level is not None:
        query = query.where(AssetCurrentLocation.confidence_level == confidence_level.value)
    if location_type is not None:
        query = query.where(AssetCurrentLocation.location_type == location_type.value)
    if updated_after is not None:
        query = query.where(AssetCurrentLocation.updated_at > updated_after)

    if order_by_updated_at:
        query = query.order_by(AssetCurrentLocation.updated_at.asc(), AssetTag.display_name.asc())
    else:
        query = query.order_by(AssetTag.display_name.asc(), AssetTag.tag_identifier.asc())

    return db.scalars(query).all()
