from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from rtls_api.auth import get_current_user
from rtls_api.db import get_db
from rtls_api.derived_events import (
    evaluate_round_trips,
    list_table_timer_states,
    list_zone_dwells,
    list_zone_transition_events,
    serialize_round_trip_measurement,
    serialize_table_timer_state,
    serialize_zone_dwell_record,
    serialize_zone_transition_event,
)
from rtls_api.models import User
from rtls_api.schemas import (
    DerivedZoneDwellRecordResponse,
    DerivedZoneTransitionEventResponse,
    RoundTripMeasurementResponse,
    TableServiceTimerStateResponse,
)

DERIVED_EVENT_ROUTER = APIRouter(prefix="/api/derived", tags=["derived-events"])


@DERIVED_EVENT_ROUTER.get("/zone-events", response_model=list[DerivedZoneTransitionEventResponse])
def get_zone_transition_events(
    site_id: str | None = None,
    floor_id: str | None = None,
    zone_id: str | None = None,
    asset_tag_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DerivedZoneTransitionEventResponse]:
    events = list_zone_transition_events(
        db=db,
        site_id=site_id,
        floor_id=floor_id,
        zone_id=zone_id,
        asset_tag_id=asset_tag_id,
        start_at=start_at,
        end_at=end_at,
    )
    return [
        DerivedZoneTransitionEventResponse.model_validate(serialize_zone_transition_event(event))
        for event in events
    ]


@DERIVED_EVENT_ROUTER.get("/dwells", response_model=list[DerivedZoneDwellRecordResponse])
def get_zone_dwells(
    site_id: str | None = None,
    floor_id: str | None = None,
    zone_id: str | None = None,
    asset_tag_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DerivedZoneDwellRecordResponse]:
    dwells = list_zone_dwells(
        db=db,
        site_id=site_id,
        floor_id=floor_id,
        zone_id=zone_id,
        asset_tag_id=asset_tag_id,
        start_at=start_at,
        end_at=end_at,
    )
    return [
        DerivedZoneDwellRecordResponse.model_validate(serialize_zone_dwell_record(record))
        for record in dwells
    ]


@DERIVED_EVENT_ROUTER.get("/table-timers", response_model=list[TableServiceTimerStateResponse])
def get_table_timer_states(
    site_id: str | None = None,
    floor_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TableServiceTimerStateResponse]:
    timer_states = list_table_timer_states(db=db, site_id=site_id, floor_id=floor_id)
    return [
        TableServiceTimerStateResponse.model_validate(serialize_table_timer_state(timer_state))
        for timer_state in timer_states
    ]


@DERIVED_EVENT_ROUTER.get("/round-trips", response_model=list[RoundTripMeasurementResponse])
def get_round_trip_measurements(
    origin_zone_id: str,
    destination_zone_id: str,
    site_id: str | None = None,
    floor_id: str | None = None,
    asset_tag_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RoundTripMeasurementResponse]:
    if origin_zone_id == destination_zone_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Origin and destination must differ",
        )

    measurements = evaluate_round_trips(
        db=db,
        origin_zone_id=origin_zone_id,
        destination_zone_id=destination_zone_id,
        site_id=site_id,
        floor_id=floor_id,
        asset_tag_id=asset_tag_id,
        start_at=start_at,
        end_at=end_at,
    )
    return [
        RoundTripMeasurementResponse.model_validate(
            serialize_round_trip_measurement(measurement)
        )
        for measurement in measurements
    ]
