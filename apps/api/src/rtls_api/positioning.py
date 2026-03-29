from __future__ import annotations

import math
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
    GatewayHardwareTier,
    LocationConfidenceLevel,
    LocationSourceModality,
    PremiumCalibrationStatus,
    PremiumRawMeasurement,
    PremiumTelemetryModality,
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
    source_tier: GatewayHardwareTier
    source_modality: LocationSourceModality
    precision_meters: float | None
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
            candidate = self._select_best_candidate_for_tag(
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

    def _select_best_candidate_for_tag(
        self,
        *,
        db: Session,
        tag_identifier: str,
        observed_at: datetime,
    ) -> PositionCandidate | None:
        candidates = [
            candidate
            for candidate in [
                self._build_economic_position_candidate(
                    db=db,
                    tag_identifier=tag_identifier,
                    observed_at=observed_at,
                ),
                self._build_premium_position_candidate(
                    db=db,
                    tag_identifier=tag_identifier,
                    observed_at=observed_at,
                ),
            ]
            if candidate is not None
        ]
        if not candidates:
            return None
        return self._select_best_candidate(candidates)

    def _build_economic_position_candidate(
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
        floor = _load_floor_context(db=db, floor_id=floor_id)
        if floor is None:
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

        confidence_level = _derive_economic_confidence_level(floor_readings)
        confidence_score = _derive_economic_confidence_score(floor_readings)
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
            source_tier=GatewayHardwareTier.ECONOMIC,
            source_modality=LocationSourceModality.BLE_RSSI,
            precision_meters=None,
            source_gateway_count=len(floor_readings),
            source_reading_count=len(floor_readings),
        )

    def _build_premium_position_candidate(
        self,
        *,
        db: Session,
        tag_identifier: str,
        observed_at: datetime,
    ) -> PositionCandidate | None:
        cutoff = observed_at - timedelta(seconds=self._settings.positioning_recent_window_seconds)
        recent_measurements = db.scalars(
            select(PremiumRawMeasurement)
            .where(
                PremiumRawMeasurement.tag_identifier == tag_identifier,
                PremiumRawMeasurement.asset_tag_id.is_not(None),
                PremiumRawMeasurement.broker_received_at >= cutoff,
            )
            .options(joinedload(PremiumRawMeasurement.gateway))
            .order_by(PremiumRawMeasurement.broker_received_at.desc())
        ).all()
        if not recent_measurements:
            return None

        latest_measurements_by_gateway: dict[str, PremiumRawMeasurement] = {}
        for measurement in recent_measurements:
            if measurement.gateway_id not in latest_measurements_by_gateway:
                latest_measurements_by_gateway[measurement.gateway_id] = measurement

        candidate_measurements = [
            measurement
            for measurement in latest_measurements_by_gateway.values()
            if measurement.gateway.premium_calibration_status
            == PremiumCalibrationStatus.CALIBRATED.value
            and measurement.gateway.premium_modality == measurement.modality
        ]
        if not candidate_measurements:
            return None

        floor_counts: dict[str, int] = {}
        for measurement in candidate_measurements:
            floor_counts[measurement.gateway.floor_id] = (
                floor_counts.get(measurement.gateway.floor_id, 0) + 1
            )
        floor_id = max(floor_counts, key=floor_counts.__getitem__)
        floor = _load_floor_context(db=db, floor_id=floor_id)
        if floor is None:
            return None

        floor_measurements = [
            measurement
            for measurement in candidate_measurements
            if measurement.gateway.floor_id == floor_id
        ]
        if not floor_measurements:
            return None

        candidates: list[PositionCandidate] = []
        for modality in (
            PremiumTelemetryModality.UWB.value,
            PremiumTelemetryModality.BLE_AOA.value,
        ):
            modality_measurements = [
                measurement
                for measurement in floor_measurements
                if measurement.modality == modality
            ]
            if modality_measurements:
                candidate = _build_premium_candidate_for_modality(
                    floor=floor,
                    measurements=modality_measurements,
                )
                if candidate is not None:
                    candidates.append(candidate)

        if not candidates:
            return None
        return self._select_best_candidate(candidates)

    def _select_best_candidate(self, candidates: list[PositionCandidate]) -> PositionCandidate:
        return max(candidates, key=_candidate_sort_key)

    def _persist_position_candidate(
        self,
        *,
        db: Session,
        candidate: PositionCandidate,
    ) -> bool:
        current = db.get(AssetCurrentLocation, candidate.asset_tag_id)
        if current is not None and not _is_candidate_better_than_current(
            current=current,
            candidate=candidate,
        ):
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
        current.source_tier = candidate.source_tier.value
        current.source_modality = candidate.source_modality.value
        current.precision_meters = candidate.precision_meters
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
                source_tier=candidate.source_tier.value,
                source_modality=candidate.source_modality.value,
                precision_meters=candidate.precision_meters,
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
        "source_tier": current.source_tier,
        "source_modality": current.source_modality,
        "precision_meters": current.precision_meters,
        "source_gateway_count": current.source_gateway_count,
        "source_reading_count": current.source_reading_count,
    }


def serialize_asset_location_history(entry: AssetLocationHistory) -> dict[str, object]:
    payload = serialize_asset_current_location(entry)
    payload["id"] = entry.id
    return payload


def _load_floor_context(*, db: Session, floor_id: str) -> Floor | None:
    return db.scalar(
        select(Floor)
        .where(Floor.id == floor_id)
        .options(selectinload(Floor.areas), joinedload(Floor.floor_plan_asset))
    )


def _build_premium_candidate_for_modality(
    *,
    floor: Floor,
    measurements: list[PremiumRawMeasurement],
) -> PositionCandidate | None:
    if not measurements:
        return None
    asset_tag_id = measurements[0].asset_tag_id
    if asset_tag_id is None:
        return None

    if measurements[0].modality == PremiumTelemetryModality.UWB.value:
        solved = _solve_uwb_candidate(floor=floor, measurements=measurements)
        source_modality = LocationSourceModality.UWB
    else:
        solved = _solve_aoa_candidate(floor=floor, measurements=measurements)
        source_modality = LocationSourceModality.BLE_AOA

    if solved is None:
        return None

    coordinate_x, coordinate_y, confidence_level, confidence_score, precision_meters = solved
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
        floor_id=floor.id,
        observed_at=max(ensure_utc(measurement.broker_received_at) for measurement in measurements),
        location_type=location_type,
        coordinate_x=point_x,
        coordinate_y=point_y,
        zone_id=zone_id,
        confidence_level=confidence_level,
        confidence_score=confidence_score,
        source_tier=GatewayHardwareTier.PREMIUM,
        source_modality=source_modality,
        precision_meters=precision_meters,
        source_gateway_count=len({measurement.gateway_id for measurement in measurements}),
        source_reading_count=len(measurements),
    )


def _solve_uwb_candidate(
    *,
    floor: Floor,
    measurements: list[PremiumRawMeasurement],
) -> tuple[float, float, LocationConfidenceLevel, float, float | None] | None:
    if floor.floor_plan_asset is None or floor.scale_pixels_per_meter is None:
        return None

    anchors = [
        (
            measurement,
            _normalized_to_meters(
                floor=floor,
                x=measurement.gateway.placement_x,
                y=measurement.gateway.placement_y,
            ),
        )
        for measurement in measurements
        if measurement.distance_m is not None
    ]
    if len(anchors) < 2:
        return None

    reference_measurement, (x1, y1) = anchors[0]
    d1 = reference_measurement.distance_m or 0
    rows: list[tuple[float, float, float, float]] = []
    for measurement, (xi, yi) in anchors[1:]:
        distance = measurement.distance_m or 0
        weight = max(0.1, measurement.quality_score or 0.6)
        a = 2 * (xi - x1)
        b = 2 * (yi - y1)
        c = d1**2 - distance**2 - x1**2 + xi**2 - y1**2 + yi**2
        rows.append((a, b, c, weight))
    solved = _solve_weighted_linear_system(rows)
    if solved is None:
        return None

    x_m, y_m = solved
    coordinate_x, coordinate_y = _meters_to_normalized(floor=floor, x_m=x_m, y_m=y_m)
    if not _is_normalized_point_reasonable(coordinate_x, coordinate_y):
        return None

    residuals = [
        abs(math.hypot(x_m - xi, y_m - yi) - (measurement.distance_m or 0))
        for measurement, (xi, yi) in anchors
    ]
    precision_meters = round(sum(residuals) / len(residuals), 3)
    confidence_level = _derive_premium_confidence_level(
        measurement_count=len(anchors),
        quality_score=_average_quality_score([measurement for measurement, _ in anchors]),
        precision_meters=precision_meters,
    )
    confidence_score = _derive_premium_confidence_score(
        measurement_count=len(anchors),
        quality_score=_average_quality_score([measurement for measurement, _ in anchors]),
        precision_meters=precision_meters,
    )
    return coordinate_x, coordinate_y, confidence_level, confidence_score, precision_meters


def _solve_aoa_candidate(
    *,
    floor: Floor,
    measurements: list[PremiumRawMeasurement],
) -> tuple[float, float, LocationConfidenceLevel, float, float | None] | None:
    rays = [
        (
            measurement,
            measurement.gateway.placement_x,
            measurement.gateway.placement_y,
            math.radians(
                (measurement.gateway.premium_mounting_angle_degrees or 0)
                + (measurement.azimuth_degrees or 0)
            ),
        )
        for measurement in measurements
        if measurement.azimuth_degrees is not None
    ]
    if len(rays) < 2:
        return None

    intersections: list[tuple[float, float, float]] = []
    for index, (left_measurement, x1, y1, angle1) in enumerate(rays):
        direction_1 = (math.cos(angle1), math.sin(angle1))
        for right_measurement, x2, y2, angle2 in rays[index + 1 :]:
            direction_2 = (math.cos(angle2), math.sin(angle2))
            intersection = _line_intersection(
                point_a=(x1, y1),
                direction_a=direction_1,
                point_b=(x2, y2),
                direction_b=direction_2,
            )
            if intersection is None:
                continue
            point_x, point_y, t_a, t_b = intersection
            if t_a < 0 or t_b < 0:
                continue
            weight = max(
                0.1,
                ((left_measurement.quality_score or 0.6) + (right_measurement.quality_score or 0.6))
                / 2,
            )
            intersections.append((point_x, point_y, weight))
    if not intersections:
        return None

    total_weight = sum(weight for _, _, weight in intersections)
    coordinate_x = sum(point_x * weight for point_x, _, weight in intersections) / total_weight
    coordinate_y = sum(point_y * weight for _, point_y, weight in intersections) / total_weight
    if not _is_normalized_point_reasonable(coordinate_x, coordinate_y):
        return None

    spread = math.sqrt(
        sum(
            (((point_x - coordinate_x) ** 2) + ((point_y - coordinate_y) ** 2)) * weight
            for point_x, point_y, weight in intersections
        )
        / total_weight
    )
    precision_meters = (
        round(_normalized_distance_to_meters(floor=floor, distance=spread), 3)
        if floor.floor_plan_asset is not None and floor.scale_pixels_per_meter is not None
        else None
    )
    quality_score = _average_quality_score([measurement for measurement, *_ in rays])
    confidence_level = _derive_premium_confidence_level(
        measurement_count=len(rays),
        quality_score=quality_score,
        precision_meters=precision_meters,
    )
    confidence_score = _derive_premium_confidence_score(
        measurement_count=len(rays),
        quality_score=quality_score,
        precision_meters=precision_meters,
    )
    return coordinate_x, coordinate_y, confidence_level, confidence_score, precision_meters


def _candidate_sort_key(candidate: PositionCandidate) -> tuple[datetime, int, float, int, float]:
    precision_component = (
        -candidate.precision_meters if candidate.precision_meters is not None else -9999
    )
    return (
        candidate.observed_at,
        _confidence_rank(candidate.confidence_level),
        candidate.confidence_score,
        1 if candidate.source_tier == GatewayHardwareTier.PREMIUM else 0,
        precision_component,
    )


def _is_candidate_better_than_current(
    *,
    current: AssetCurrentLocation,
    candidate: PositionCandidate,
) -> bool:
    current_observed_at = ensure_utc(current.observed_at)
    if current_observed_at is None:
        return True
    if candidate.observed_at > current_observed_at:
        return True
    if candidate.observed_at < current_observed_at:
        return False

    current_precision_component = (
        -current.precision_meters if current.precision_meters is not None else -9999
    )
    current_key = (
        _confidence_rank(LocationConfidenceLevel(current.confidence_level)),
        current.confidence_score,
        1 if current.source_tier == GatewayHardwareTier.PREMIUM.value else 0,
        current_precision_component,
    )
    candidate_key = (
        _confidence_rank(candidate.confidence_level),
        candidate.confidence_score,
        1 if candidate.source_tier == GatewayHardwareTier.PREMIUM else 0,
        -candidate.precision_meters if candidate.precision_meters is not None else -9999,
    )
    return candidate_key > current_key


def _signal_weight(rssi: int) -> float:
    return max(1.0, float(110 + rssi))


def _derive_economic_confidence_level(readings: list[RawReading]) -> LocationConfidenceLevel:
    gateway_count = len(readings)
    strongest_rssi = max(reading.rssi for reading in readings)
    if gateway_count >= 3 and strongest_rssi >= -75:
        return LocationConfidenceLevel.HIGH
    if gateway_count >= 2 and strongest_rssi >= -85:
        return LocationConfidenceLevel.MEDIUM
    return LocationConfidenceLevel.LOW


def _derive_economic_confidence_score(readings: list[RawReading]) -> float:
    gateway_component = min(len(readings), 3) / 3 * 0.5
    strongest_rssi = max(reading.rssi for reading in readings)
    signal_component = min(max((strongest_rssi + 100) / 35, 0), 1) * 0.35
    average_rssi = sum(reading.rssi for reading in readings) / len(readings)
    stability_component = min(max((average_rssi + 100) / 45, 0), 1) * 0.15
    return round(min(1.0, gateway_component + signal_component + stability_component), 3)


def _derive_premium_confidence_level(
    *,
    measurement_count: int,
    quality_score: float,
    precision_meters: float | None,
) -> LocationConfidenceLevel:
    if (
        measurement_count >= 3
        and quality_score >= 0.8
        and (precision_meters is None or precision_meters <= 1.5)
    ):
        return LocationConfidenceLevel.HIGH
    if (
        measurement_count >= 2
        and quality_score >= 0.55
        and (precision_meters is None or precision_meters <= 3.0)
    ):
        return LocationConfidenceLevel.MEDIUM
    return LocationConfidenceLevel.LOW


def _derive_premium_confidence_score(
    *,
    measurement_count: int,
    quality_score: float,
    precision_meters: float | None,
) -> float:
    measurement_component = min(measurement_count, 4) / 4 * 0.35
    quality_component = min(max(quality_score, 0), 1) * 0.45
    if precision_meters is None:
        precision_component = 0.2
    else:
        precision_component = max(0.0, min(1.0, 1 - (precision_meters / 6))) * 0.2
    return round(min(1.0, measurement_component + quality_component + precision_component), 3)


def _average_quality_score(measurements: list[PremiumRawMeasurement]) -> float:
    if not measurements:
        return 0.0
    return sum(measurement.quality_score or 0.6 for measurement in measurements) / len(measurements)


def _confidence_rank(level: LocationConfidenceLevel) -> int:
    return {
        LocationConfidenceLevel.LOW: 0,
        LocationConfidenceLevel.MEDIUM: 1,
        LocationConfidenceLevel.HIGH: 2,
    }[level]


def _normalized_to_meters(*, floor: Floor, x: float, y: float) -> tuple[float, float]:
    if floor.floor_plan_asset is None or floor.scale_pixels_per_meter is None:
        return (x, y)
    return (
        x * floor.floor_plan_asset.width_px / floor.scale_pixels_per_meter,
        y * floor.floor_plan_asset.height_px / floor.scale_pixels_per_meter,
    )


def _meters_to_normalized(*, floor: Floor, x_m: float, y_m: float) -> tuple[float, float]:
    if floor.floor_plan_asset is None or floor.scale_pixels_per_meter is None:
        return (x_m, y_m)
    return (
        x_m * floor.scale_pixels_per_meter / floor.floor_plan_asset.width_px,
        y_m * floor.scale_pixels_per_meter / floor.floor_plan_asset.height_px,
    )


def _normalized_distance_to_meters(*, floor: Floor, distance: float) -> float:
    if floor.floor_plan_asset is None or floor.scale_pixels_per_meter is None:
        return distance
    pixel_distance = distance * (
        (floor.floor_plan_asset.width_px + floor.floor_plan_asset.height_px) / 2
    )
    return pixel_distance / floor.scale_pixels_per_meter


def _solve_weighted_linear_system(
    rows: list[tuple[float, float, float, float]]
) -> tuple[float, float] | None:
    if not rows:
        return None
    s_aa = 0.0
    s_ab = 0.0
    s_bb = 0.0
    s_ac = 0.0
    s_bc = 0.0
    for a, b, c, weight in rows:
        s_aa += weight * a * a
        s_ab += weight * a * b
        s_bb += weight * b * b
        s_ac += weight * a * c
        s_bc += weight * b * c
    determinant = (s_aa * s_bb) - (s_ab * s_ab)
    if abs(determinant) <= 1e-9:
        return None
    x = ((s_ac * s_bb) - (s_ab * s_bc)) / determinant
    y = ((s_aa * s_bc) - (s_ab * s_ac)) / determinant
    return (x, y)


def _line_intersection(
    *,
    point_a: tuple[float, float],
    direction_a: tuple[float, float],
    point_b: tuple[float, float],
    direction_b: tuple[float, float],
) -> tuple[float, float, float, float] | None:
    ax, ay = point_a
    adx, ady = direction_a
    bx, by = point_b
    bdx, bdy = direction_b
    determinant = (adx * -bdy) - (ady * -bdx)
    if abs(determinant) <= 1e-9:
        return None
    delta_x = bx - ax
    delta_y = by - ay
    t_a = ((delta_x * -bdy) - (delta_y * -bdx)) / determinant
    t_b = ((adx * delta_y) - (ady * delta_x)) / determinant
    return (ax + t_a * adx, ay + t_a * ady, t_a, t_b)


def _is_normalized_point_reasonable(x: float, y: float) -> bool:
    return -0.1 <= x <= 1.1 and -0.1 <= y <= 1.1


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
