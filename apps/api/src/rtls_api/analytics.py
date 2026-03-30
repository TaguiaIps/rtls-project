from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from rtls_api.derived_events import (
    evaluate_round_trips,
    list_zone_dwells,
    serialize_round_trip_measurement,
    serialize_table_timer_state,
    serialize_zone_dwell_record,
)
from rtls_api.models import (
    AlertRule,
    AlertRuleType,
    AnalyticsHeatmapHourlyRollup,
    AnalyticsTableSlaHourlyRollup,
    AssetLocationHistory,
    AssetTag,
    Floor,
    SpatialArea,
    SpatialAreaType,
    TableServiceTimerState,
)
from rtls_api.positioning import ensure_utc, serialize_asset_location_history

MAX_TRAJECTORY_WINDOW = timedelta(hours=24)
MAX_HEATMAP_WINDOW = timedelta(hours=24)
MAX_DERIVED_REPORT_WINDOW = timedelta(days=7)
SUPPORTED_SLA_BUCKET_MINUTES = {15, 60}


def validate_time_window(
    *,
    start_at: datetime,
    end_at: datetime,
    max_window: timedelta,
    label: str,
) -> tuple[datetime, datetime]:
    normalized_start = ensure_utc(start_at)
    normalized_end = ensure_utc(end_at)
    if normalized_end <= normalized_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{label} end_at must be after start_at",
        )
    if normalized_end - normalized_start > max_window:
        max_hours = int(max_window.total_seconds() // 3600)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{label} supports at most {max_hours} hours per request",
        )
    return normalized_start, normalized_end


def get_trajectory_report(
    *,
    db: Session,
    asset_tag_id: str,
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
) -> dict[str, object]:
    floor = _get_floor(db=db, floor_id=floor_id)
    asset = db.get(AssetTag, asset_tag_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    history = db.scalars(
        select(AssetLocationHistory)
        .join(AssetLocationHistory.asset_tag)
        .join(AssetLocationHistory.floor)
        .options(
            joinedload(AssetLocationHistory.asset_tag),
            joinedload(AssetLocationHistory.floor).joinedload(Floor.site),
            joinedload(AssetLocationHistory.zone),
        )
        .where(
            AssetLocationHistory.asset_tag_id == asset_tag_id,
            AssetLocationHistory.floor_id == floor_id,
            AssetLocationHistory.observed_at >= start_at,
            AssetLocationHistory.observed_at <= end_at,
        )
        .order_by(AssetLocationHistory.observed_at.asc(), AssetLocationHistory.created_at.asc())
    ).all()

    return {
        "asset_tag_id": asset.id,
        "tag_identifier": asset.tag_identifier,
        "display_name": asset.display_name,
        "asset_category": asset.asset_category,
        "site_id": floor.site.id,
        "site_name": floor.site.name,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "start_at": start_at,
        "end_at": end_at,
        "points": [serialize_asset_location_history(entry) for entry in history],
    }


def get_heatmap_report(
    *,
    db: Session,
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    asset_category: str | None,
    grid_columns: int,
    grid_rows: int,
) -> dict[str, object]:
    floor = _get_floor(db=db, floor_id=floor_id)
    counts: dict[tuple[int, int], int] = defaultdict(int)
    used_rollups = False

    if grid_columns == 12 and grid_rows == 8:
        rollup_start = _ceil_hour(start_at)
        rollup_end = _floor_hour(end_at)
        if rollup_start < rollup_end:
            query = select(AnalyticsHeatmapHourlyRollup).where(
                AnalyticsHeatmapHourlyRollup.floor_id == floor_id,
                AnalyticsHeatmapHourlyRollup.grid_columns == grid_columns,
                AnalyticsHeatmapHourlyRollup.grid_rows == grid_rows,
                AnalyticsHeatmapHourlyRollup.bucket_started_at >= rollup_start,
                AnalyticsHeatmapHourlyRollup.bucket_started_at < rollup_end,
            )
            if asset_category is not None:
                query = query.where(AnalyticsHeatmapHourlyRollup.asset_category == asset_category)
            rollup_rows = db.scalars(query).all()
            if rollup_rows:
                used_rollups = True
                for row in rollup_rows:
                    counts[(row.row_index, row.column_index)] += row.sample_count
                _accumulate_heatmap_counts(
                    counts=counts,
                    history=_list_location_history(
                        db=db,
                        floor_id=floor_id,
                        start_at=start_at,
                        end_at=rollup_start,
                        asset_category=asset_category,
                    ),
                    grid_columns=grid_columns,
                    grid_rows=grid_rows,
                )
                _accumulate_heatmap_counts(
                    counts=counts,
                    history=_list_location_history(
                        db=db,
                        floor_id=floor_id,
                        start_at=rollup_end,
                        end_at=end_at,
                        asset_category=asset_category,
                    ),
                    grid_columns=grid_columns,
                    grid_rows=grid_rows,
                )

    if not used_rollups:
        history = _list_location_history(
            db=db,
            floor_id=floor_id,
            start_at=start_at,
            end_at=end_at,
            asset_category=asset_category,
        )
        _accumulate_heatmap_counts(
            counts=counts,
            history=history,
            grid_columns=grid_columns,
            grid_rows=grid_rows,
        )

    max_density = max(counts.values(), default=0)
    cells = [
        {
            "row": row,
            "column": column,
            "center": {
                "x": (column + 0.5) / grid_columns,
                "y": (row + 0.5) / grid_rows,
            },
            "sample_count": count,
            "intensity": round(count / max_density, 4) if max_density else 0.0,
        }
        for (row, column), count in sorted(counts.items())
    ]
    return {
        "site_id": floor.site.id,
        "site_name": floor.site.name,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "asset_category": asset_category,
        "start_at": start_at,
        "end_at": end_at,
        "grid_columns": grid_columns,
        "grid_rows": grid_rows,
        "total_samples": sum(counts.values()),
        "max_density": max_density,
        "cells": cells,
    }


def get_dwell_report(
    *,
    db: Session,
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    zone_id: str | None,
    asset_category: str | None,
) -> dict[str, object]:
    floor = _get_floor(db=db, floor_id=floor_id)
    zone = _get_zone(db=db, zone_id=zone_id) if zone_id is not None else None
    records = list_zone_dwells(
        db=db,
        floor_id=floor_id,
        zone_id=zone_id,
        start_at=start_at,
        end_at=end_at,
    )
    if asset_category is not None:
        records = [
            record for record in records if record.asset_tag.asset_category == asset_category
        ]

    threshold_seconds = None
    threshold_source = "unavailable"
    if zone is not None and zone.area_type == SpatialAreaType.TABLE.value and zone.sla_eligible:
        threshold_seconds = _resolve_table_sla_threshold(
            db=db,
            floor_id=floor_id,
            table_area_id=zone.id,
        )
        if threshold_seconds is not None:
            threshold_source = "alert_rule"

    serialized_records = []
    threshold_breach_count = 0
    for record in records:
        payload = serialize_zone_dwell_record(record)
        threshold_breached = bool(
            threshold_seconds is not None and payload["duration_seconds"] > threshold_seconds
        )
        if threshold_breached:
            threshold_breach_count += 1
        serialized_records.append(
            {
                **payload,
                "threshold_seconds": threshold_seconds,
                "threshold_breached": threshold_breached,
            }
        )

    durations = [float(record["duration_seconds"]) for record in serialized_records]
    return {
        "site_id": floor.site.id,
        "site_name": floor.site.name,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "zone_id": zone.id if zone is not None else None,
        "zone_name": zone.name if zone is not None else None,
        "asset_category": asset_category,
        "start_at": start_at,
        "end_at": end_at,
        "summary": {
            "sample_count": len(serialized_records),
            "avg_duration_seconds": _average(durations),
            "max_duration_seconds": max(durations, default=None),
            "threshold_seconds": threshold_seconds,
            "threshold_source": threshold_source,
            "threshold_breach_count": threshold_breach_count,
        },
        "records": serialized_records,
    }


def get_round_trip_report(
    *,
    db: Session,
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    origin_zone_id: str,
    destination_zone_id: str,
    asset_category: str | None,
) -> dict[str, object]:
    floor = _get_floor(db=db, floor_id=floor_id)
    origin_zone = _get_zone(db=db, zone_id=origin_zone_id)
    destination_zone = _get_zone(db=db, zone_id=destination_zone_id)
    measurements = evaluate_round_trips(
        db=db,
        floor_id=floor_id,
        origin_zone_id=origin_zone_id,
        destination_zone_id=destination_zone_id,
        start_at=start_at,
        end_at=end_at,
    )
    if asset_category is not None:
        measurements = [
            measurement
            for measurement in measurements
            if measurement.asset_tag.asset_category == asset_category
        ]
    serialized_records = [
        serialize_round_trip_measurement(measurement) for measurement in measurements
    ]
    totals = [float(record["total_seconds"]) for record in serialized_records]
    outbounds = [float(record["outbound_seconds"]) for record in serialized_records]
    returns = [float(record["return_seconds"]) for record in serialized_records]
    return {
        "site_id": floor.site.id,
        "site_name": floor.site.name,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "origin_zone_id": origin_zone.id,
        "origin_zone_name": origin_zone.name,
        "destination_zone_id": destination_zone.id,
        "destination_zone_name": destination_zone.name,
        "asset_category": asset_category,
        "start_at": start_at,
        "end_at": end_at,
        "summary": {
            "sample_count": len(serialized_records),
            "avg_duration_seconds": _average(totals),
            "max_duration_seconds": max(totals, default=None),
            "avg_outbound_seconds": _average(outbounds),
            "avg_return_seconds": _average(returns),
        },
        "records": serialized_records,
    }


def get_sla_trend_report(
    *,
    db: Session,
    floor_id: str,
    table_area_id: str,
    start_at: datetime,
    end_at: datetime,
    bucket_minutes: int,
) -> dict[str, object]:
    if bucket_minutes not in SUPPORTED_SLA_BUCKET_MINUTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="bucket_minutes must be one of 15 or 60",
        )

    floor = _get_floor(db=db, floor_id=floor_id)
    table_area = _get_zone(db=db, zone_id=table_area_id)
    if (
        table_area.area_type != SpatialAreaType.TABLE.value
        or table_area.sla_eligible is not True
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selected area is not an SLA-eligible table",
        )

    threshold_seconds = _resolve_table_sla_threshold(
        db=db,
        floor_id=floor_id,
        table_area_id=table_area_id,
    )
    threshold_source = "alert_rule" if threshold_seconds is not None else "unavailable"

    records = list_zone_dwells(
        db=db,
        floor_id=floor_id,
        zone_id=table_area_id,
        start_at=start_at,
        end_at=end_at,
    )

    buckets: dict[datetime, list[float]] = defaultdict(list)
    used_rollups = False
    if bucket_minutes == 60 and _is_hour_aligned(start_at, end_at):
        rollup_rows = db.scalars(
            select(AnalyticsTableSlaHourlyRollup).where(
                AnalyticsTableSlaHourlyRollup.floor_id == floor_id,
                AnalyticsTableSlaHourlyRollup.table_area_id == table_area_id,
                AnalyticsTableSlaHourlyRollup.bucket_started_at >= start_at,
                AnalyticsTableSlaHourlyRollup.bucket_started_at <= _bucket_start(end_at, 60),
            )
        ).all()
        if rollup_rows:
            used_rollups = True

    if used_rollups:
        serialized_buckets = []
        current_bucket = _bucket_start(start_at, bucket_minutes)
        final_bucket = _bucket_start(end_at, bucket_minutes)
        bucket_delta = timedelta(minutes=bucket_minutes)
        rollup_map = {ensure_utc(row.bucket_started_at): row for row in rollup_rows}
        while current_bucket <= final_bucket:
            row = rollup_map.get(current_bucket)
            serialized_buckets.append(
                {
                    "bucket_started_at": current_bucket,
                    "completed_visit_count": row.completed_visit_count if row is not None else 0,
                    "breach_count": row.breach_count if row is not None else 0,
                    "avg_duration_seconds": row.avg_duration_seconds if row is not None else None,
                    "max_duration_seconds": row.max_duration_seconds if row is not None else None,
                }
            )
            current_bucket += bucket_delta
    else:
        for record in records:
            bucket = _bucket_start(record.ended_at, bucket_minutes)
            buckets[bucket].append(float(record.duration_seconds))

        serialized_buckets = []
        current_bucket = _bucket_start(start_at, bucket_minutes)
        final_bucket = _bucket_start(end_at, bucket_minutes)
        bucket_delta = timedelta(minutes=bucket_minutes)
        while current_bucket <= final_bucket:
            durations = buckets.get(current_bucket, [])
            serialized_buckets.append(
                {
                    "bucket_started_at": current_bucket,
                    "completed_visit_count": len(durations),
                    "breach_count": sum(
                        1
                        for duration in durations
                        if threshold_seconds is not None and duration > threshold_seconds
                    ),
                    "avg_duration_seconds": _average(durations),
                    "max_duration_seconds": max(durations, default=None),
                }
            )
            current_bucket += bucket_delta

    timer_state = db.get(TableServiceTimerState, table_area_id)
    serialized_timer = (
        serialize_table_timer_state(timer_state)
        if timer_state is not None
        else None
    )
    return {
        "site_id": floor.site.id,
        "site_name": floor.site.name,
        "floor_id": floor.id,
        "floor_name": floor.name,
        "table_area_id": table_area.id,
        "table_name": table_area.name,
        "start_at": start_at,
        "end_at": end_at,
        "bucket_minutes": bucket_minutes,
        "threshold_source": threshold_source,
        "threshold_seconds": threshold_seconds,
        "current_timer": serialized_timer,
        "buckets": serialized_buckets,
    }


def _get_floor(*, db: Session, floor_id: str) -> Floor:
    floor = db.scalar(
        select(Floor)
        .options(joinedload(Floor.site))
        .where(Floor.id == floor_id)
    )
    if floor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found")
    return floor


def _get_zone(*, db: Session, zone_id: str) -> SpatialArea:
    zone = db.scalar(
        select(SpatialArea)
        .options(joinedload(SpatialArea.floor).joinedload(Floor.site))
        .where(SpatialArea.id == zone_id)
    )
    if zone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    return zone


def _list_location_history(
    *,
    db: Session,
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    asset_category: str | None = None,
) -> list[AssetLocationHistory]:
    query = (
        select(AssetLocationHistory)
        .join(AssetLocationHistory.asset_tag)
        .join(AssetLocationHistory.floor)
        .options(
            joinedload(AssetLocationHistory.asset_tag),
            joinedload(AssetLocationHistory.floor).joinedload(Floor.site),
            joinedload(AssetLocationHistory.zone),
        )
        .where(
            AssetLocationHistory.floor_id == floor_id,
            AssetLocationHistory.observed_at >= start_at,
            AssetLocationHistory.observed_at <= end_at,
        )
        .order_by(AssetLocationHistory.observed_at.asc(), AssetLocationHistory.created_at.asc())
    )
    if asset_category is not None:
        query = query.where(AssetTag.asset_category == asset_category)
    return db.scalars(query).all()


def _resolve_history_point(entry: AssetLocationHistory) -> dict[str, float] | None:
    if entry.coordinate_x is not None and entry.coordinate_y is not None:
        return {"x": entry.coordinate_x, "y": entry.coordinate_y}
    zone = entry.zone
    if zone is None or not zone.geometry:
        return None
    x_total = sum(float(point["x"]) for point in zone.geometry)
    y_total = sum(float(point["y"]) for point in zone.geometry)
    count = len(zone.geometry)
    if count == 0:
        return None
    return {"x": x_total / count, "y": y_total / count}


def _resolve_table_sla_threshold(
    *,
    db: Session,
    floor_id: str,
    table_area_id: str,
) -> float | None:
    floor = _get_floor(db=db, floor_id=floor_id)
    rules = db.scalars(
        select(AlertRule).where(
            AlertRule.rule_type == AlertRuleType.TABLE_SLA.value,
            AlertRule.enabled.is_(True),
            or_(AlertRule.floor_id == floor_id, AlertRule.floor_id.is_(None)),
        )
    ).all()
    thresholds = []
    for rule in rules:
        if rule.site_id is not None and rule.site_id != floor.site_id:
            continue
        table_area_ids = [
            str(area_id) for area_id in rule.config.get("table_area_ids", [])
        ]
        if table_area_id not in table_area_ids:
            continue
        threshold_seconds = rule.config.get("threshold_seconds")
        if isinstance(threshold_seconds, (int, float)):
            thresholds.append(float(threshold_seconds))
    return min(thresholds) if thresholds else None


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _bucket_start(value: datetime, bucket_minutes: int) -> datetime:
    normalized = ensure_utc(value)
    minute = (normalized.minute // bucket_minutes) * bucket_minutes
    return normalized.replace(minute=minute, second=0, microsecond=0)


def _ceil_hour(value: datetime) -> datetime:
    normalized = ensure_utc(value)
    bucket = normalized.replace(minute=0, second=0, microsecond=0)
    if bucket == normalized:
        return bucket
    return bucket + timedelta(hours=1)


def _floor_hour(value: datetime) -> datetime:
    normalized = ensure_utc(value)
    return normalized.replace(minute=0, second=0, microsecond=0)


def _is_hour_aligned(start_at: datetime, end_at: datetime) -> bool:
    normalized_start = ensure_utc(start_at)
    normalized_end = ensure_utc(end_at)
    return (
        normalized_start.minute == 0
        and normalized_start.second == 0
        and normalized_start.microsecond == 0
        and normalized_end.minute == 0
        and normalized_end.second == 0
        and normalized_end.microsecond == 0
    )


def _accumulate_heatmap_counts(
    *,
    counts: dict[tuple[int, int], int],
    history: list[AssetLocationHistory],
    grid_columns: int,
    grid_rows: int,
) -> None:
    for entry in history:
        point = _resolve_history_point(entry)
        if point is None:
            continue
        column = min(grid_columns - 1, max(0, int(point["x"] * grid_columns)))
        row = min(grid_rows - 1, max(0, int(point["y"] * grid_rows)))
        counts[(row, column)] += 1
