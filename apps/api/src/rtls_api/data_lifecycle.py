from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from rtls_api.analytics import _resolve_history_point
from rtls_api.config import Settings
from rtls_api.models import (
    AlertRule,
    AlertRuleType,
    AnalyticsHeatmapHourlyRollup,
    AnalyticsTableSlaHourlyRollup,
    AssetLocationHistory,
    DataLifecycleRun,
    DataLifecycleRunStatus,
    DerivedZoneDwellRecord,
    ExportJob,
    PremiumRawMeasurement,
    RawReading,
    SpatialArea,
    SpatialAreaType,
)
from rtls_api.positioning import ensure_utc
from rtls_api.storage import create_object_storage_service

HEATMAP_ROLLUP_COLUMNS = 12
HEATMAP_ROLLUP_ROWS = 8


def build_retention_policy_summary(settings: Settings) -> dict[str, int]:
    return {
        "raw_readings_days": settings.raw_reading_retention_days,
        "premium_measurements_days": settings.premium_measurement_retention_days,
        "location_history_days": settings.location_history_retention_days,
        "exports_days": settings.export_retention_days,
    }


def serialize_lifecycle_run(run: DataLifecycleRun) -> dict[str, object]:
    requested_by_email = getattr(getattr(run, "requested_by", None), "email", None)
    return {
        "id": run.id,
        "requested_by_user_id": run.requested_by_user_id,
        "requested_by_email": requested_by_email,
        "status": run.status,
        "retention_summary": run.retention_summary,
        "rollup_summary": run.rollup_summary,
        "error_message": run.error_message,
        "requested_at": ensure_utc(run.requested_at),
        "started_at": ensure_utc(run.started_at),
        "completed_at": ensure_utc(run.completed_at),
    }


def run_data_lifecycle_job(
    session_factory: sessionmaker[Session],
    settings: Settings,
    lifecycle_run_id: str,
) -> None:
    storage_service = create_object_storage_service(settings)
    with session_factory() as db:
        lifecycle_run = db.get(DataLifecycleRun, lifecycle_run_id)
        if lifecycle_run is None:
            return

        started_at = datetime.now(timezone.utc)
        lifecycle_run.status = DataLifecycleRunStatus.RUNNING.value
        lifecycle_run.started_at = started_at
        lifecycle_run.error_message = None
        db.commit()

        try:
            retention_summary = apply_retention_policies(
                db=db,
                settings=settings,
                now=started_at,
                storage_service=storage_service,
            )
            rollup_summary = refresh_rollups(db=db)
            lifecycle_run.retention_summary = retention_summary
            lifecycle_run.rollup_summary = rollup_summary
            lifecycle_run.status = DataLifecycleRunStatus.COMPLETED.value
            lifecycle_run.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as error:  # pragma: no cover - exercised via API state assertions
            db.rollback()
            failed_run = db.get(DataLifecycleRun, lifecycle_run_id)
            if failed_run is None:
                return
            failed_run.status = DataLifecycleRunStatus.FAILED.value
            failed_run.error_message = str(error)
            failed_run.completed_at = datetime.now(timezone.utc)
            db.commit()


def apply_retention_policies(
    *,
    db: Session,
    settings: Settings,
    now: datetime,
    storage_service,
) -> dict[str, int]:
    raw_cutoff = now - timedelta(days=settings.raw_reading_retention_days)
    premium_cutoff = now - timedelta(days=settings.premium_measurement_retention_days)
    location_cutoff = now - timedelta(days=settings.location_history_retention_days)
    export_cutoff = now - timedelta(days=settings.export_retention_days)

    raw_readings = db.scalars(
        select(RawReading).where(RawReading.broker_received_at < raw_cutoff)
    ).all()
    premium_measurements = db.scalars(
        select(PremiumRawMeasurement).where(
            PremiumRawMeasurement.broker_received_at < premium_cutoff
        )
    ).all()
    location_history = db.scalars(
        select(AssetLocationHistory).where(
            AssetLocationHistory.observed_at < location_cutoff
        )
    ).all()
    expired_exports = db.scalars(
        select(ExportJob).where(
            ExportJob.requested_at < export_cutoff,
        )
    ).all()

    for row in raw_readings:
        db.delete(row)
    for row in premium_measurements:
        db.delete(row)
    for row in location_history:
        db.delete(row)
    deleted_export_files = 0
    for job in expired_exports:
        if job.storage_key is not None:
            storage_service.delete_object(key=job.storage_key)
            deleted_export_files += 1
        db.delete(job)

    db.commit()
    return {
        "raw_readings_deleted": len(raw_readings),
        "premium_measurements_deleted": len(premium_measurements),
        "location_history_deleted": len(location_history),
        "export_jobs_deleted": len(expired_exports),
        "export_files_deleted": deleted_export_files,
    }


def refresh_rollups(*, db: Session) -> dict[str, int]:
    existing_heatmap_rollups = db.scalars(select(AnalyticsHeatmapHourlyRollup)).all()
    existing_sla_rollups = db.scalars(select(AnalyticsTableSlaHourlyRollup)).all()
    for row in existing_heatmap_rollups:
        db.delete(row)
    for row in existing_sla_rollups:
        db.delete(row)
    db.flush()

    heatmap_rollups = _build_heatmap_rollups(db=db)
    sla_rollups = _build_sla_rollups(db=db)
    db.add_all(heatmap_rollups)
    db.add_all(sla_rollups)
    db.commit()
    return {
        "heatmap_rollups_refreshed": len(heatmap_rollups),
        "sla_rollups_refreshed": len(sla_rollups),
    }


def _build_heatmap_rollups(*, db: Session) -> list[AnalyticsHeatmapHourlyRollup]:
    counts: dict[tuple[str, str | None, datetime, int, int], int] = defaultdict(int)
    history = db.scalars(
        select(AssetLocationHistory)
        .join(AssetLocationHistory.asset_tag)
        .options(joinedload(AssetLocationHistory.asset_tag), joinedload(AssetLocationHistory.zone))
    ).all()
    for record in history:
        point = _resolve_history_point(record)
        if point is None:
            continue
        bucket = _hour_bucket(record.observed_at)
        column = min(
            HEATMAP_ROLLUP_COLUMNS - 1,
            max(0, int(point["x"] * HEATMAP_ROLLUP_COLUMNS)),
        )
        row = min(
            HEATMAP_ROLLUP_ROWS - 1,
            max(0, int(point["y"] * HEATMAP_ROLLUP_ROWS)),
        )
        counts[
            (
                record.floor_id,
                record.asset_tag.asset_category,
                bucket,
                row,
                column,
            )
        ] += 1

    return [
        AnalyticsHeatmapHourlyRollup(
            floor_id=floor_id,
            asset_category=asset_category,
            bucket_started_at=bucket_started_at,
            grid_columns=HEATMAP_ROLLUP_COLUMNS,
            grid_rows=HEATMAP_ROLLUP_ROWS,
            row_index=row,
            column_index=column,
            sample_count=sample_count,
        )
        for (
            floor_id,
            asset_category,
            bucket_started_at,
            row,
            column,
        ), sample_count in counts.items()
    ]


def _build_sla_rollups(*, db: Session) -> list[AnalyticsTableSlaHourlyRollup]:
    table_thresholds = _resolve_table_thresholds(db=db)
    grouped: dict[
        tuple[str, str, datetime],
        dict[str, float | int | None],
    ] = defaultdict(
        lambda: {
            "completed_visit_count": 0,
            "breach_count": 0,
            "duration_total": 0.0,
            "max_duration_seconds": None,
        }
    )
    records = db.scalars(
        select(DerivedZoneDwellRecord)
        .join(DerivedZoneDwellRecord.zone)
        .options(joinedload(DerivedZoneDwellRecord.zone))
        .where(
            SpatialArea.area_type == SpatialAreaType.TABLE.value,
            SpatialArea.sla_eligible.is_(True),
        )
    ).all()
    for record in records:
        bucket = _hour_bucket(record.ended_at)
        key = (record.floor_id, record.zone_id, bucket)
        threshold_seconds = table_thresholds.get(record.zone_id)
        grouped[key]["completed_visit_count"] += 1
        grouped[key]["duration_total"] += float(record.duration_seconds)
        grouped[key]["max_duration_seconds"] = max(
            float(record.duration_seconds),
            float(grouped[key]["max_duration_seconds"] or 0),
        )
        if threshold_seconds is not None and record.duration_seconds > threshold_seconds:
            grouped[key]["breach_count"] += 1

    rollups: list[AnalyticsTableSlaHourlyRollup] = []
    for (floor_id, table_area_id, bucket_started_at), stats in grouped.items():
        completed_visit_count = int(stats["completed_visit_count"])
        duration_total = float(stats["duration_total"])
        rollups.append(
            AnalyticsTableSlaHourlyRollup(
                floor_id=floor_id,
                table_area_id=table_area_id,
                bucket_started_at=bucket_started_at,
                completed_visit_count=completed_visit_count,
                breach_count=int(stats["breach_count"]),
                avg_duration_seconds=(
                    duration_total / completed_visit_count
                    if completed_visit_count
                    else None
                ),
                max_duration_seconds=(
                    float(stats["max_duration_seconds"])
                    if stats["max_duration_seconds"] is not None
                    else None
                ),
                threshold_seconds=table_thresholds.get(table_area_id),
            )
        )
    return rollups


def _resolve_table_thresholds(*, db: Session) -> dict[str, float]:
    threshold_by_table: dict[str, float] = {}
    rules = db.scalars(
        select(AlertRule).where(AlertRule.rule_type == AlertRuleType.TABLE_SLA.value)
    ).all()
    for rule in rules:
        threshold_seconds = rule.config.get("threshold_seconds")
        table_area_ids = rule.config.get("table_area_ids") or []
        if not isinstance(threshold_seconds, (int, float)):
            continue
        for table_area_id in table_area_ids:
            threshold_by_table[str(table_area_id)] = float(threshold_seconds)
    return threshold_by_table


def _hour_bucket(value: datetime) -> datetime:
    normalized = ensure_utc(value)
    return normalized.replace(minute=0, second=0, microsecond=0)
