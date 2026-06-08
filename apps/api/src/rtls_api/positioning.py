from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from rtls_api.alerts import evaluate_alerts_for_position_update
from rtls_api.config import Settings
from rtls_api.derived_events import apply_derived_zone_semantics
from rtls_api.models import (
    AssetCurrentLocation,
    AssetLocationHistory,
    AssetLocationType,
    Floor,
    LocationConfidenceLevel,
    RawReading,
    SpatialArea,
    SpatialAreaType,
)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class PositionCandidate:
    asset_tag_id: str
    floor_id: str
    observed_at: datetime
    location_type: AssetLocationType
    coordinate_x: float | None
    coordinate_y: float | None
    zone_id: str | None
    confidence_level: LocationConfidenceLevel
    confidence_score: float
    source_gateway_count: int
    source_reading_count: int


class PositioningService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def update_positions_for_tags(
        self,
        *,
        db: Session,
        tag_identifiers: set[str],
        observed_at: datetime,
    ) -> list[PositionCandidate]:
        updates: list[PositionCandidate] = []
        for tag_identifier in sorted(tag_identifiers):
            candidate = self._build_position_candidate(
                db=db,
                tag_identifier=tag_identifier,
                observed_at=observed_at,
            )
            if candidate is None:
                continue
            persisted = self._persist_position_candidate(db=db, candidate=candidate)
            if persisted:
                updates.append(candidate)
        return updates

    def _build_position_candidate(
        self,
        *,
        db: Session,
        tag_identifier: str,
        observed_at: datetime,
    ) -> PositionCandidate | None:
        cutoff = observed_at - timedelta(seconds=self._settings.positioning_recent_window_seconds)
        recent_readings = db.scalars(
            select(RawReading)
            .where(
                RawReading.tag_identifier == tag_identifier,
                RawReading.asset_tag_id.is_not(None),
                RawReading.broker_received_at >= cutoff,
            )
            .options(joinedload(RawReading.gateway))
            .order_by(RawReading.broker_received_at.desc())
        ).all()
        if not recent_readings:
            return None

        latest_readings_by_gateway: dict[str, RawReading] = {}
        for reading in recent_readings:
            if reading.gateway_id not in latest_readings_by_gateway:
                latest_readings_by_gateway[reading.gateway_id] = reading

        latest_readings = list(latest_readings_by_gateway.values())
        if not latest_readings:
            return None

        asset_tag_id = latest_readings[0].asset_tag_id
        if asset_tag_id is None:
            return None

        floor_weight_totals: dict[str, float] = {}
        for reading in latest_readings:
            floor_weight_totals[reading.gateway.floor_id] = floor_weight_totals.get(
                reading.gateway.floor_id,
                0.0,
            ) + _signal_weight(reading.rssi)

        floor_id = max(floor_weight_totals, key=floor_weight_totals.__getitem__)
        floor = db.scalar(
            select(Floor)
            .where(Floor.id == floor_id)
            .options(selectinload(Floor.areas), joinedload(Floor.floor_plan_asset))
        )
        if floor is None or floor.floor_plan_asset is None:
            return None

        floor_readings = [
            reading for reading in latest_readings if reading.gateway.floor_id == floor_id
        ]
        if not floor_readings:
            return None

        total_weight = sum(_signal_weight(reading.rssi) for reading in floor_readings)
        if total_weight <= 0:
            return None

        coordinate_x = sum(
            reading.gateway.placement_x * _signal_weight(reading.rssi) for reading in floor_readings
        ) / total_weight
        coordinate_y = sum(
            reading.gateway.placement_y * _signal_weight(reading.rssi) for reading in floor_readings
        ) / total_weight

        confidence_level = _derive_confidence_level(floor_readings)
        confidence_score = _derive_confidence_score(floor_readings)
        zone = _find_best_zone(floor.areas, coordinate_x, coordinate_y)

        location_type = AssetLocationType.POINT
        point_x: float | None = coordinate_x
        point_y: float | None = coordinate_y
        zone_id: str | None = zone.id if zone is not None else None

        if confidence_level == LocationConfidenceLevel.LOW:
            if zone is None:
                return None
            location_type = AssetLocationType.ZONE
            point_x = None
            point_y = None

        return PositionCandidate(
            asset_tag_id=asset_tag_id,
            floor_id=floor_id,
            observed_at=max(ensure_utc(reading.broker_received_at) for reading in floor_readings),
            location_type=location_type,
            coordinate_x=point_x,
            coordinate_y=point_y,
            zone_id=zone_id,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            source_gateway_count=len(floor_readings),
            source_reading_count=len(floor_readings),
        )

    def _persist_position_candidate(
        self,
        *,
        db: Session,
        candidate: PositionCandidate,
    ) -> bool:
        current = db.get(AssetCurrentLocation, candidate.asset_tag_id)
        if current is not None and ensure_utc(current.observed_at) > candidate.observed_at:
            return False

        if current is None:
            current = AssetCurrentLocation(asset_tag_id=candidate.asset_tag_id)
            db.add(current)

        current.floor_id = candidate.floor_id
        current.zone_id = candidate.zone_id
        current.observed_at = candidate.observed_at
        current.location_type = candidate.location_type.value
        current.coordinate_x = candidate.coordinate_x
        current.coordinate_y = candidate.coordinate_y
        current.confidence_level = candidate.confidence_level.value
        current.confidence_score = candidate.confidence_score
        current.source_gateway_count = candidate.source_gateway_count
        current.source_reading_count = candidate.source_reading_count

        db.add(
            AssetLocationHistory(
                asset_tag_id=candidate.asset_tag_id,
                floor_id=candidate.floor_id,
                zone_id=candidate.zone_id,
                observed_at=candidate.observed_at,
                location_type=candidate.location_type.value,
                coordinate_x=candidate.coordinate_x,
                coordinate_y=candidate.coordinate_y,
                confidence_level=candidate.confidence_level.value,
                confidence_score=candidate.confidence_score,
                source_gateway_count=candidate.source_gateway_count,
                source_reading_count=candidate.source_reading_count,
            )
        )
        semantics = apply_derived_zone_semantics(
            db=db,
            asset_tag_id=candidate.asset_tag_id,
            floor_id=candidate.floor_id,
            zone_id=candidate.zone_id,
            observed_at=candidate.observed_at,
        )
        floor_ids = {candidate.floor_id}
        if semantics.exit_event is not None:
            floor_ids.add(semantics.exit_event.floor_id)
        evaluate_alerts_for_position_update(
            db=db,
            settings=self._settings,
            floor_ids=floor_ids,
            semantics=semantics,
            observed_at=candidate.observed_at,
        )
        return True


def serialize_asset_current_location(current: AssetCurrentLocation) -> dict[str, object]:
    asset_tag = current.asset_tag
    floor = current.floor
    site = floor.site
    zone = current.zone
    return {
        "asset_tag_id": asset_tag.id,
        "tag_identifier": asset_tag.tag_identifier,
        "display_name": asset_tag.display_name,
        "asset_category": asset_tag.asset_category,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "site_id": site.id,
        "site_name": site.name,
        "observed_at": ensure_utc(current.observed_at),
        "location_type": current.location_type,
        "point": (
            {"x": current.coordinate_x, "y": current.coordinate_y}
            if current.coordinate_x is not None and current.coordinate_y is not None
            else None
        ),
        "zone_id": zone.id if zone is not None else None,
        "zone_name": zone.name if zone is not None else None,
        "confidence_level": current.confidence_level,
        "confidence_score": current.confidence_score,
        "source_gateway_count": current.source_gateway_count,
        "source_reading_count": current.source_reading_count,
    }


def serialize_asset_location_history(entry: AssetLocationHistory) -> dict[str, object]:
    payload = serialize_asset_current_location(entry)
    payload["id"] = entry.id
    return payload


def _signal_weight(rssi: int) -> float:
    return max(1.0, float(110 + rssi))


def _derive_confidence_level(readings: list[RawReading]) -> LocationConfidenceLevel:
    gateway_count = len(readings)
    strongest_rssi = max(reading.rssi for reading in readings)
    if gateway_count >= 3 and strongest_rssi >= -75:
        return LocationConfidenceLevel.HIGH
    if gateway_count >= 2 and strongest_rssi >= -85:
        return LocationConfidenceLevel.MEDIUM
    return LocationConfidenceLevel.LOW


def _derive_confidence_score(readings: list[RawReading]) -> float:
    gateway_component = min(len(readings), 3) / 3 * 0.5
    strongest_rssi = max(reading.rssi for reading in readings)
    signal_component = min(max((strongest_rssi + 100) / 35, 0), 1) * 0.35
    average_rssi = sum(reading.rssi for reading in readings) / len(readings)
    stability_component = min(max((average_rssi + 100) / 45, 0), 1) * 0.15
    return round(min(1.0, gateway_component + signal_component + stability_component), 3)


def _find_best_zone(
    areas: list[SpatialArea],
    coordinate_x: float,
    coordinate_y: float,
) -> SpatialArea | None:
    candidate_areas = [
        area
        for area in areas
        if area.area_type != SpatialAreaType.POI.value
        and _point_in_polygon(coordinate_x, coordinate_y, area.geometry)
    ]
    if not candidate_areas:
        return None

    # Prefer the smallest containing polygon so nested operational areas win over broad shells.
    return min(candidate_areas, key=lambda area: _polygon_area(area.geometry))


def _polygon_area(points: list[dict[str, float]]) -> float:
    area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        area += point["x"] * next_point["y"] - next_point["x"] * point["y"]
    return abs(area) / 2


def _point_in_polygon(x: float, y: float, polygon: list[dict[str, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, point in enumerate(polygon):
        xi = point["x"]
        yi = point["y"]
        xj = polygon[j]["x"]
        yj = polygon[j]["y"]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside
