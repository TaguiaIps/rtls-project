from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import case, select
from sqlalchemy.orm import Session, joinedload

from rtls_api.models import (
    AssetTag,
    AssetZoneOccupancy,
    DerivedZoneDwellRecord,
    DerivedZoneEventType,
    DerivedZoneTransitionEvent,
    DwellClosureReason,
    Floor,
    SpatialArea,
    SpatialAreaType,
    TableServiceTimerState,
    TableServiceTimerStatus,
)


@dataclass(frozen=True)
class RoundTripMeasurement:
    asset_tag: AssetTag
    floor: Floor
    origin_zone: SpatialArea
    destination_zone: SpatialArea
    origin_entered_at: datetime
    destination_entered_at: datetime
    completed_at: datetime
    outbound_seconds: float
    return_seconds: float
    total_seconds: float


@dataclass(frozen=True)
class DerivedZoneSemanticsResult:
    entry_event: DerivedZoneTransitionEvent | None = None
    exit_event: DerivedZoneTransitionEvent | None = None


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def apply_derived_zone_semantics(
    *,
    db: Session,
    asset_tag_id: str,
    floor_id: str,
    zone_id: str | None,
    observed_at: datetime,
) -> DerivedZoneSemanticsResult:
    normalized_observed_at = ensure_utc(observed_at)
    occupancy = db.get(AssetZoneOccupancy, asset_tag_id)

    if occupancy is None:
        if zone_id is not None:
            entry_event = _open_occupancy(
                db=db,
                asset_tag_id=asset_tag_id,
                floor_id=floor_id,
                zone_id=zone_id,
                observed_at=normalized_observed_at,
                transition_boundary_id=str(uuid4()),
            )
            return DerivedZoneSemanticsResult(entry_event=entry_event)
        return DerivedZoneSemanticsResult()

    if occupancy.floor_id == floor_id and occupancy.zone_id == zone_id:
        return DerivedZoneSemanticsResult()

    closure_reason = _derive_closure_reason(
        occupancy=occupancy,
        next_floor_id=floor_id,
        next_zone_id=zone_id,
    )
    transition_boundary_id = str(uuid4())
    exit_event = _close_occupancy(
        db=db,
        occupancy=occupancy,
        observed_at=normalized_observed_at,
        closure_reason=closure_reason,
        transition_boundary_id=transition_boundary_id,
    )

    entry_event: DerivedZoneTransitionEvent | None = None
    if zone_id is not None:
        entry_event = _open_occupancy(
            db=db,
            asset_tag_id=asset_tag_id,
            floor_id=floor_id,
            zone_id=zone_id,
            observed_at=normalized_observed_at,
            transition_boundary_id=transition_boundary_id,
        )
    return DerivedZoneSemanticsResult(entry_event=entry_event, exit_event=exit_event)


def list_zone_transition_events(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
    zone_id: str | None = None,
    asset_tag_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[DerivedZoneTransitionEvent]:
    event_order = case(
        (DerivedZoneTransitionEvent.event_type == DerivedZoneEventType.EXIT.value, 0),
        else_=1,
    )
    query = (
        select(DerivedZoneTransitionEvent)
        .join(DerivedZoneTransitionEvent.asset_tag)
        .join(DerivedZoneTransitionEvent.floor)
        .options(
            joinedload(DerivedZoneTransitionEvent.asset_tag),
            joinedload(DerivedZoneTransitionEvent.floor).joinedload(Floor.site),
            joinedload(DerivedZoneTransitionEvent.zone),
        )
        .order_by(
            DerivedZoneTransitionEvent.observed_at.asc(),
            event_order.asc(),
            DerivedZoneTransitionEvent.created_at.asc(),
        )
    )
    if site_id is not None:
        query = query.where(Floor.site_id == site_id)
    if floor_id is not None:
        query = query.where(DerivedZoneTransitionEvent.floor_id == floor_id)
    if zone_id is not None:
        query = query.where(DerivedZoneTransitionEvent.zone_id == zone_id)
    if asset_tag_id is not None:
        query = query.where(DerivedZoneTransitionEvent.asset_tag_id == asset_tag_id)
    if start_at is not None:
        query = query.where(DerivedZoneTransitionEvent.observed_at >= start_at)
    if end_at is not None:
        query = query.where(DerivedZoneTransitionEvent.observed_at <= end_at)
    return db.scalars(query).all()


def list_zone_dwells(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
    zone_id: str | None = None,
    asset_tag_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[DerivedZoneDwellRecord]:
    query = (
        select(DerivedZoneDwellRecord)
        .join(DerivedZoneDwellRecord.asset_tag)
        .join(DerivedZoneDwellRecord.floor)
        .options(
            joinedload(DerivedZoneDwellRecord.asset_tag),
            joinedload(DerivedZoneDwellRecord.floor).joinedload(Floor.site),
            joinedload(DerivedZoneDwellRecord.zone),
        )
        .order_by(
            DerivedZoneDwellRecord.started_at.asc(),
            DerivedZoneDwellRecord.ended_at.asc(),
            DerivedZoneDwellRecord.created_at.asc(),
        )
    )
    if site_id is not None:
        query = query.where(Floor.site_id == site_id)
    if floor_id is not None:
        query = query.where(DerivedZoneDwellRecord.floor_id == floor_id)
    if zone_id is not None:
        query = query.where(DerivedZoneDwellRecord.zone_id == zone_id)
    if asset_tag_id is not None:
        query = query.where(DerivedZoneDwellRecord.asset_tag_id == asset_tag_id)
    if start_at is not None:
        query = query.where(DerivedZoneDwellRecord.ended_at >= start_at)
    if end_at is not None:
        query = query.where(DerivedZoneDwellRecord.started_at <= end_at)
    return db.scalars(query).all()


def list_table_timer_states(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
) -> list[TableServiceTimerState]:
    query = (
        select(TableServiceTimerState)
        .join(TableServiceTimerState.table_area)
        .join(TableServiceTimerState.floor)
        .options(
            joinedload(TableServiceTimerState.table_area),
            joinedload(TableServiceTimerState.floor).joinedload(Floor.site),
        )
        .where(
            SpatialArea.area_type == SpatialAreaType.TABLE.value,
            SpatialArea.sla_eligible.is_(True),
        )
        .order_by(Floor.name.asc(), SpatialArea.name.asc())
    )
    if site_id is not None:
        query = query.where(Floor.site_id == site_id)
    if floor_id is not None:
        query = query.where(TableServiceTimerState.floor_id == floor_id)
    return db.scalars(query).all()


def evaluate_round_trips(
    *,
    db: Session,
    origin_zone_id: str,
    destination_zone_id: str,
    site_id: str | None = None,
    floor_id: str | None = None,
    asset_tag_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[RoundTripMeasurement]:
    query = (
        select(DerivedZoneTransitionEvent)
        .join(DerivedZoneTransitionEvent.asset_tag)
        .join(DerivedZoneTransitionEvent.floor)
        .options(
            joinedload(DerivedZoneTransitionEvent.asset_tag),
            joinedload(DerivedZoneTransitionEvent.floor).joinedload(Floor.site),
            joinedload(DerivedZoneTransitionEvent.zone),
        )
        .where(
            DerivedZoneTransitionEvent.event_type == DerivedZoneEventType.ENTRY.value,
            DerivedZoneTransitionEvent.zone_id.in_([origin_zone_id, destination_zone_id]),
        )
        .order_by(
            DerivedZoneTransitionEvent.asset_tag_id.asc(),
            DerivedZoneTransitionEvent.observed_at.asc(),
            DerivedZoneTransitionEvent.created_at.asc(),
        )
    )
    if site_id is not None:
        query = query.where(Floor.site_id == site_id)
    if floor_id is not None:
        query = query.where(DerivedZoneTransitionEvent.floor_id == floor_id)
    if asset_tag_id is not None:
        query = query.where(DerivedZoneTransitionEvent.asset_tag_id == asset_tag_id)
    if start_at is not None:
        query = query.where(DerivedZoneTransitionEvent.observed_at >= start_at)
    if end_at is not None:
        query = query.where(DerivedZoneTransitionEvent.observed_at <= end_at)

    events = db.scalars(query).all()
    events_by_asset: dict[str, list[DerivedZoneTransitionEvent]] = defaultdict(list)
    for event in events:
        events_by_asset[event.asset_tag_id].append(event)

    measurements: list[RoundTripMeasurement] = []
    for asset_events in events_by_asset.values():
        origin_event: DerivedZoneTransitionEvent | None = None
        destination_event: DerivedZoneTransitionEvent | None = None

        for event in asset_events:
            if event.zone_id == origin_zone_id:
                if origin_event is None:
                    origin_event = event
                    destination_event = None
                    continue

                if destination_event is not None:
                    outbound_seconds = _seconds_between(
                        origin_event.observed_at,
                        destination_event.observed_at,
                    )
                    return_seconds = _seconds_between(
                        destination_event.observed_at,
                        event.observed_at,
                    )
                    measurements.append(
                        RoundTripMeasurement(
                            asset_tag=event.asset_tag,
                            floor=event.floor,
                            origin_zone=origin_event.zone,
                            destination_zone=destination_event.zone,
                            origin_entered_at=ensure_utc(origin_event.observed_at),
                            destination_entered_at=ensure_utc(destination_event.observed_at),
                            completed_at=ensure_utc(event.observed_at),
                            outbound_seconds=outbound_seconds,
                            return_seconds=return_seconds,
                            total_seconds=round(outbound_seconds + return_seconds, 3),
                        )
                    )

                origin_event = event
                destination_event = None
                continue

            if origin_event is not None and destination_event is None:
                destination_event = event

    return measurements


def serialize_zone_transition_event(event: DerivedZoneTransitionEvent) -> dict[str, object]:
    floor = event.floor
    site = floor.site
    return {
        "id": event.id,
        "asset_tag_id": event.asset_tag.id,
        "tag_identifier": event.asset_tag.tag_identifier,
        "display_name": event.asset_tag.display_name,
        "asset_category": event.asset_tag.asset_category,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "site_id": site.id,
        "site_name": site.name,
        "zone_id": event.zone.id,
        "zone_name": event.zone.name,
        "observed_at": ensure_utc(event.observed_at),
        "event_type": event.event_type,
        "transition_boundary_id": event.transition_boundary_id,
    }


def serialize_zone_dwell_record(record: DerivedZoneDwellRecord) -> dict[str, object]:
    floor = record.floor
    site = floor.site
    return {
        "id": record.id,
        "asset_tag_id": record.asset_tag.id,
        "tag_identifier": record.asset_tag.tag_identifier,
        "display_name": record.asset_tag.display_name,
        "asset_category": record.asset_tag.asset_category,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "site_id": site.id,
        "site_name": site.name,
        "zone_id": record.zone.id,
        "zone_name": record.zone.name,
        "started_at": ensure_utc(record.started_at),
        "ended_at": ensure_utc(record.ended_at),
        "duration_seconds": round(float(record.duration_seconds), 3),
        "closure_reason": record.closure_reason,
    }


def serialize_table_timer_state(
    timer_state: TableServiceTimerState,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    floor = timer_state.floor
    site = floor.site
    boundary_at = timer_state.active_since or timer_state.last_exit_at or timer_state.last_entry_at
    normalized_now = ensure_utc(now or datetime.now(timezone.utc))
    elapsed_seconds = 0.0
    if boundary_at is not None:
        elapsed_seconds = _seconds_between(boundary_at, normalized_now)

    return {
        "table_area_id": timer_state.table_area.id,
        "table_name": timer_state.table_area.name,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "site_id": site.id,
        "site_name": site.name,
        "status": timer_state.status,
        "active_visit_count": timer_state.active_visit_count,
        "boundary_at": ensure_utc(boundary_at) if boundary_at is not None else None,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "active_since": ensure_utc(timer_state.active_since),
        "last_entry_at": ensure_utc(timer_state.last_entry_at),
        "last_exit_at": ensure_utc(timer_state.last_exit_at),
        "last_visit_started_at": ensure_utc(timer_state.last_visit_started_at),
        "last_visit_ended_at": ensure_utc(timer_state.last_visit_ended_at),
        "last_visit_duration_seconds": (
            round(float(timer_state.last_visit_duration_seconds), 3)
            if timer_state.last_visit_duration_seconds is not None
            else None
        ),
    }


def serialize_round_trip_measurement(measurement: RoundTripMeasurement) -> dict[str, object]:
    floor = measurement.floor
    site = floor.site
    return {
        "asset_tag_id": measurement.asset_tag.id,
        "tag_identifier": measurement.asset_tag.tag_identifier,
        "display_name": measurement.asset_tag.display_name,
        "asset_category": measurement.asset_tag.asset_category,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "site_id": site.id,
        "site_name": site.name,
        "origin_zone_id": measurement.origin_zone.id,
        "origin_zone_name": measurement.origin_zone.name,
        "destination_zone_id": measurement.destination_zone.id,
        "destination_zone_name": measurement.destination_zone.name,
        "origin_entered_at": measurement.origin_entered_at,
        "destination_entered_at": measurement.destination_entered_at,
        "completed_at": measurement.completed_at,
        "outbound_seconds": round(measurement.outbound_seconds, 3),
        "return_seconds": round(measurement.return_seconds, 3),
        "total_seconds": round(measurement.total_seconds, 3),
    }


def _derive_closure_reason(
    *,
    occupancy: AssetZoneOccupancy,
    next_floor_id: str,
    next_zone_id: str | None,
) -> DwellClosureReason:
    if occupancy.floor_id != next_floor_id:
        return DwellClosureReason.FLOOR_CHANGE
    if next_zone_id is None:
        return DwellClosureReason.RESOLVED_PLACEMENT_LOST
    return DwellClosureReason.ZONE_CHANGE


def _open_occupancy(
    *,
    db: Session,
    asset_tag_id: str,
    floor_id: str,
    zone_id: str,
    observed_at: datetime,
    transition_boundary_id: str,
) -> DerivedZoneTransitionEvent:
    entry_event = DerivedZoneTransitionEvent(
        asset_tag_id=asset_tag_id,
        floor_id=floor_id,
        zone_id=zone_id,
        observed_at=observed_at,
        event_type=DerivedZoneEventType.ENTRY.value,
        transition_boundary_id=transition_boundary_id,
    )
    db.add(entry_event)
    db.flush()

    db.add(
        AssetZoneOccupancy(
            asset_tag_id=asset_tag_id,
            floor_id=floor_id,
            zone_id=zone_id,
            entered_at=observed_at,
            entry_event_id=entry_event.id,
        )
    )
    _update_table_timer_on_entry(
        db=db,
        table_area_id=zone_id,
        floor_id=floor_id,
        observed_at=observed_at,
    )
    return entry_event


def _close_occupancy(
    *,
    db: Session,
    occupancy: AssetZoneOccupancy,
    observed_at: datetime,
    closure_reason: DwellClosureReason,
    transition_boundary_id: str,
) -> DerivedZoneTransitionEvent:
    exit_event = DerivedZoneTransitionEvent(
        asset_tag_id=occupancy.asset_tag_id,
        floor_id=occupancy.floor_id,
        zone_id=occupancy.zone_id,
        observed_at=observed_at,
        event_type=DerivedZoneEventType.EXIT.value,
        transition_boundary_id=transition_boundary_id,
    )
    db.add(exit_event)
    db.flush()

    db.add(
        DerivedZoneDwellRecord(
            asset_tag_id=occupancy.asset_tag_id,
            floor_id=occupancy.floor_id,
            zone_id=occupancy.zone_id,
            started_at=occupancy.entered_at,
            ended_at=observed_at,
            duration_seconds=_seconds_between(occupancy.entered_at, observed_at),
            closure_reason=closure_reason.value,
            entry_event_id=occupancy.entry_event_id,
            exit_event_id=exit_event.id,
        )
    )
    _update_table_timer_on_exit(
        db=db,
        table_area_id=occupancy.zone_id,
        floor_id=occupancy.floor_id,
        entered_at=occupancy.entered_at,
        observed_at=observed_at,
    )
    db.delete(occupancy)
    return exit_event


def _update_table_timer_on_entry(
    *,
    db: Session,
    table_area_id: str,
    floor_id: str,
    observed_at: datetime,
) -> None:
    if not _is_sla_eligible_table(db=db, area_id=table_area_id):
        return

    timer_state = db.get(TableServiceTimerState, table_area_id)
    if timer_state is None:
        timer_state = TableServiceTimerState(
            table_area_id=table_area_id,
            floor_id=floor_id,
            status=TableServiceTimerStatus.IDLE.value,
            active_visit_count=0,
        )
        db.add(timer_state)

    timer_state.floor_id = floor_id
    timer_state.last_entry_at = observed_at
    if timer_state.active_visit_count == 0:
        timer_state.active_since = observed_at
    timer_state.active_visit_count += 1
    timer_state.status = TableServiceTimerStatus.ACTIVE.value


def _update_table_timer_on_exit(
    *,
    db: Session,
    table_area_id: str,
    floor_id: str,
    entered_at: datetime,
    observed_at: datetime,
) -> None:
    if not _is_sla_eligible_table(db=db, area_id=table_area_id):
        return

    timer_state = db.get(TableServiceTimerState, table_area_id)
    if timer_state is None:
        timer_state = TableServiceTimerState(
            table_area_id=table_area_id,
            floor_id=floor_id,
            status=TableServiceTimerStatus.IDLE.value,
            active_visit_count=0,
        )
        db.add(timer_state)

    timer_state.floor_id = floor_id
    timer_state.last_exit_at = observed_at
    if timer_state.active_visit_count > 0:
        timer_state.active_visit_count -= 1

    if timer_state.active_visit_count == 0:
        visit_started_at = timer_state.active_since or entered_at
        timer_state.status = TableServiceTimerStatus.IDLE.value
        timer_state.last_visit_started_at = visit_started_at
        timer_state.last_visit_ended_at = observed_at
        timer_state.last_visit_duration_seconds = _seconds_between(visit_started_at, observed_at)
        timer_state.active_since = None


def _is_sla_eligible_table(*, db: Session, area_id: str) -> bool:
    area = db.get(SpatialArea, area_id)
    return bool(
        area is not None
        and area.area_type == SpatialAreaType.TABLE.value
        and area.sla_eligible is True
    )


def _seconds_between(start_at: datetime, end_at: datetime) -> float:
    return round(
        max(
            0.0,
            (ensure_utc(end_at) - ensure_utc(start_at)).total_seconds(),
        ),
        3,
    )
