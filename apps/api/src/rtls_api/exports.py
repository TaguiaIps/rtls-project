from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from rtls_api.analytics import (
    MAX_DERIVED_REPORT_WINDOW,
    MAX_HEATMAP_WINDOW,
    MAX_TRAJECTORY_WINDOW,
    get_dwell_report,
    get_heatmap_report,
    get_round_trip_report,
    get_sla_trend_report,
    get_trajectory_report,
    validate_time_window,
)
from rtls_api.config import Settings
from rtls_api.models import (
    ExportJob,
    ExportJobFormat,
    ExportJobStatus,
    Floor,
    User,
    UserRole,
)
from rtls_api.positioning import ensure_utc
from rtls_api.storage import ObjectNotFoundError, create_object_storage_service


def serialize_export_job(job: ExportJob) -> dict[str, object]:
    return {
        "id": job.id,
        "report_kind": job.report_kind,
        "export_format": job.export_format,
        "status": job.status,
        "floor_id": job.floor_id,
        "site_id": job.site_id,
        "file_name": job.file_name,
        "row_count": job.row_count,
        "error_message": job.error_message,
        "requested_at": ensure_utc(job.requested_at),
        "started_at": ensure_utc(job.started_at),
        "completed_at": ensure_utc(job.completed_at),
        "expires_at": ensure_utc(job.expires_at),
    }


def process_export_job(
    session_factory: sessionmaker[Session],
    settings: Settings,
    export_job_id: str,
) -> None:
    storage_service = create_object_storage_service(settings)
    with session_factory() as db:
        job = db.get(ExportJob, export_job_id)
        if job is None:
            return

        job.status = ExportJobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None
        db.commit()

        try:
            csv_content, row_count = _build_export_csv(db=db, job=job)
            completed_at = datetime.now(timezone.utc)
            file_name = _build_export_file_name(job=job, completed_at=completed_at)
            storage_key = f"exports/{job.id}/{file_name}"
            storage_service.put_object(
                key=storage_key,
                content=csv_content.encode("utf-8"),
                content_type="text/csv",
            )
            job.status = ExportJobStatus.COMPLETED.value
            job.file_name = file_name
            job.storage_key = storage_key
            job.content_type = "text/csv"
            job.row_count = row_count
            job.completed_at = completed_at
            job.expires_at = completed_at + timedelta(days=settings.export_retention_days)
            db.commit()
        except Exception as error:  # pragma: no cover - exercised via status assertions
            db.rollback()
            failed_job = db.get(ExportJob, export_job_id)
            if failed_job is None:
                return
            failed_job.status = ExportJobStatus.FAILED.value
            failed_job.error_message = str(error)
            failed_job.completed_at = datetime.now(timezone.utc)
            db.commit()


def get_download_payload(*, db: Session, job: ExportJob, settings: Settings) -> tuple[bytes, str]:
    if job.storage_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export artifact not found",
        )
    if (
        job.expires_at is not None
        and ensure_utc(job.expires_at) < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Export artifact expired")

    try:
        stored = create_object_storage_service(settings).get_object(key=job.storage_key)
    except ObjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export artifact not found",
        ) from error
    return stored.content, job.content_type or stored.content_type


def get_accessible_export_job(*, db: Session, job_id: str, current_user: User) -> ExportJob:
    query = (
        select(ExportJob)
        .options(joinedload(ExportJob.requested_by))
        .where(ExportJob.id == job_id)
    )
    if current_user.role != UserRole.ADMINISTRATOR.value:
        query = query.where(ExportJob.requested_by_user_id == current_user.id)
    job = db.scalar(query)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")
    return job


def normalize_export_request(
    *,
    payload: dict[str, object],
    db: Session,
) -> tuple[dict[str, object], str | None]:
    report_kind = str(payload["report_kind"])
    floor_id = str(payload["floor_id"])
    floor = db.scalar(select(Floor).options(joinedload(Floor.site)).where(Floor.id == floor_id))
    if floor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found")

    start_at = payload["start_at"]
    end_at = payload["end_at"]
    if not isinstance(start_at, datetime) or not isinstance(end_at, datetime):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Export request requires start_at and end_at",
        )

    if report_kind == "trajectory":
        start_at, end_at = validate_time_window(
            start_at=start_at,
            end_at=end_at,
            max_window=MAX_TRAJECTORY_WINDOW,
            label="Trajectory export",
        )
        if not payload.get("asset_tag_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="asset_tag_id is required for trajectory exports",
            )
    elif report_kind == "heatmap":
        start_at, end_at = validate_time_window(
            start_at=start_at,
            end_at=end_at,
            max_window=MAX_HEATMAP_WINDOW,
            label="Heatmap export",
        )
    elif report_kind == "dwell":
        start_at, end_at = validate_time_window(
            start_at=start_at,
            end_at=end_at,
            max_window=MAX_DERIVED_REPORT_WINDOW,
            label="Dwell export",
        )
    elif report_kind == "round_trip":
        start_at, end_at = validate_time_window(
            start_at=start_at,
            end_at=end_at,
            max_window=MAX_DERIVED_REPORT_WINDOW,
            label="Round-trip export",
        )
        if not payload.get("origin_zone_id") or not payload.get("destination_zone_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "origin_zone_id and destination_zone_id are required "
                    "for round-trip exports"
                ),
            )
    elif report_kind == "sla":
        start_at, end_at = validate_time_window(
            start_at=start_at,
            end_at=end_at,
            max_window=MAX_DERIVED_REPORT_WINDOW,
            label="SLA trend export",
        )
        if not payload.get("table_area_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="table_area_id is required for SLA exports",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported export report_kind",
        )

    normalized_payload = {
        **payload,
        "floor_id": floor_id,
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "export_format": ExportJobFormat.CSV.value,
    }
    return normalized_payload, floor.site.id


def _build_export_csv(*, db: Session, job: ExportJob) -> tuple[str, int]:
    report_payload = _resolve_report_payload(db=db, job=job)
    headers, rows = _rows_for_report(job.report_kind, report_payload)
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue(), len(rows)


def _resolve_report_payload(*, db: Session, job: ExportJob) -> dict[str, object]:
    params = job.report_params
    start_at = datetime.fromisoformat(str(params["start_at"]))
    end_at = datetime.fromisoformat(str(params["end_at"]))
    if job.report_kind == "trajectory":
        return get_trajectory_report(
            db=db,
            asset_tag_id=str(params["asset_tag_id"]),
            floor_id=str(params["floor_id"]),
            start_at=start_at,
            end_at=end_at,
        )
    if job.report_kind == "heatmap":
        return get_heatmap_report(
            db=db,
            floor_id=str(params["floor_id"]),
            start_at=start_at,
            end_at=end_at,
            asset_category=_optional_string(params.get("asset_category")),
            grid_columns=12,
            grid_rows=8,
        )
    if job.report_kind == "dwell":
        return get_dwell_report(
            db=db,
            floor_id=str(params["floor_id"]),
            start_at=start_at,
            end_at=end_at,
            zone_id=_optional_string(params.get("zone_id")),
            asset_category=_optional_string(params.get("asset_category")),
        )
    if job.report_kind == "round_trip":
        return get_round_trip_report(
            db=db,
            floor_id=str(params["floor_id"]),
            start_at=start_at,
            end_at=end_at,
            origin_zone_id=str(params["origin_zone_id"]),
            destination_zone_id=str(params["destination_zone_id"]),
            asset_category=_optional_string(params.get("asset_category")),
        )
    return get_sla_trend_report(
        db=db,
        floor_id=str(params["floor_id"]),
        table_area_id=str(params["table_area_id"]),
        start_at=start_at,
        end_at=end_at,
        bucket_minutes=int(params.get("bucket_minutes") or 60),
    )


def _rows_for_report(
    report_kind: str,
    report_payload: dict[str, object],
) -> tuple[list[str], list[dict[str, object]]]:
    if report_kind == "trajectory":
        headers = ["observed_at", "zone_name", "floor_name", "confidence_level", "confidence_score"]
        rows = [
            {
                "observed_at": point["observed_at"],
                "zone_name": point["zone_name"],
                "floor_name": point["floor_name"],
                "confidence_level": point["confidence_level"],
                "confidence_score": point["confidence_score"],
            }
            for point in report_payload["points"]  # type: ignore[index]
        ]
        return headers, rows
    if report_kind == "heatmap":
        headers = ["row", "column", "sample_count", "intensity", "center_x", "center_y"]
        rows = [
            {
                "row": cell["row"],
                "column": cell["column"],
                "sample_count": cell["sample_count"],
                "intensity": cell["intensity"],
                "center_x": cell["center"]["x"],
                "center_y": cell["center"]["y"],
            }
            for cell in report_payload["cells"]  # type: ignore[index]
        ]
        return headers, rows
    if report_kind == "dwell":
        headers = [
            "started_at",
            "ended_at",
            "duration_seconds",
            "zone_name",
            "asset_label",
            "threshold_seconds",
            "threshold_breached",
        ]
        rows = [
            {
                "started_at": record["started_at"],
                "ended_at": record["ended_at"],
                "duration_seconds": record["duration_seconds"],
                "zone_name": report_payload["zone_name"],
                "asset_label": record["display_name"],
                "threshold_seconds": record["threshold_seconds"],
                "threshold_breached": record["threshold_breached"],
            }
            for record in report_payload["records"]  # type: ignore[index]
        ]
        return headers, rows
    if report_kind == "round_trip":
        headers = [
            "completed_at",
            "asset_label",
            "origin_zone_name",
            "destination_zone_name",
            "outbound_seconds",
            "return_seconds",
            "total_seconds",
        ]
        rows = [
            {
                "completed_at": record["completed_at"],
                "asset_label": record["display_name"],
                "origin_zone_name": record["origin_zone_name"],
                "destination_zone_name": record["destination_zone_name"],
                "outbound_seconds": record["outbound_seconds"],
                "return_seconds": record["return_seconds"],
                "total_seconds": record["total_seconds"],
            }
            for record in report_payload["records"]  # type: ignore[index]
        ]
        return headers, rows
    headers = [
        "bucket_started_at",
        "completed_visit_count",
        "breach_count",
        "avg_duration_seconds",
        "max_duration_seconds",
    ]
    rows = [
        {
            "bucket_started_at": bucket["bucket_started_at"],
            "completed_visit_count": bucket["completed_visit_count"],
            "breach_count": bucket["breach_count"],
            "avg_duration_seconds": bucket["avg_duration_seconds"],
            "max_duration_seconds": bucket["max_duration_seconds"],
        }
        for bucket in report_payload["buckets"]  # type: ignore[index]
    ]
    return headers, rows


def _build_export_file_name(*, job: ExportJob, completed_at: datetime) -> str:
    timestamp = completed_at.strftime("%Y%m%dT%H%M%SZ")
    return f"{job.report_kind}-{timestamp}.csv"


def _optional_string(value: object) -> str | None:
    if value in {None, ""}:
        return None
    return str(value)
