from __future__ import annotations

from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

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
from rtls_api.audit import write_audit_event
from rtls_api.auth import get_current_user
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.exports import (
    get_accessible_export_job,
    get_download_payload,
    normalize_export_request,
    process_export_job,
    serialize_export_job,
)
from rtls_api.models import ExportJob, ExportJobStatus, User, UserRole
from rtls_api.schemas import (
    AnalyticsDwellReportResponse,
    AnalyticsExportJobResponse,
    AnalyticsExportRequest,
    AnalyticsHeatmapResponse,
    AnalyticsRoundTripReportResponse,
    AnalyticsSlaTrendResponse,
    AnalyticsTrajectoryResponse,
)

ANALYTICS_ROUTER = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


@ANALYTICS_ROUTER.get("/trajectory", response_model=AnalyticsTrajectoryResponse)
def read_trajectory_report(
    asset_tag_id: str,
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AnalyticsTrajectoryResponse:
    start_at, end_at = validate_time_window(
        start_at=start_at,
        end_at=end_at,
        max_window=MAX_TRAJECTORY_WINDOW,
        label="Trajectory report",
    )
    return AnalyticsTrajectoryResponse.model_validate(
        get_trajectory_report(
            db=db,
            asset_tag_id=asset_tag_id,
            floor_id=floor_id,
            start_at=start_at,
            end_at=end_at,
        )
    )


@ANALYTICS_ROUTER.get("/heatmap", response_model=AnalyticsHeatmapResponse)
def read_heatmap_report(
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    asset_category: str | None = None,
    grid_columns: int = 12,
    grid_rows: int = 8,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AnalyticsHeatmapResponse:
    start_at, end_at = validate_time_window(
        start_at=start_at,
        end_at=end_at,
        max_window=MAX_HEATMAP_WINDOW,
        label="Heatmap report",
    )
    if grid_columns < 4 or grid_columns > 24 or grid_rows < 4 or grid_rows > 24:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Heatmap grid must stay within 4..24 columns and rows",
        )
    return AnalyticsHeatmapResponse.model_validate(
        get_heatmap_report(
            db=db,
            floor_id=floor_id,
            start_at=start_at,
            end_at=end_at,
            asset_category=asset_category,
            grid_columns=grid_columns,
            grid_rows=grid_rows,
        )
    )


@ANALYTICS_ROUTER.get("/dwells", response_model=AnalyticsDwellReportResponse)
def read_dwell_report(
    floor_id: str,
    start_at: datetime,
    end_at: datetime,
    zone_id: str | None = None,
    asset_category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AnalyticsDwellReportResponse:
    start_at, end_at = validate_time_window(
        start_at=start_at,
        end_at=end_at,
        max_window=MAX_DERIVED_REPORT_WINDOW,
        label="Dwell report",
    )
    return AnalyticsDwellReportResponse.model_validate(
        get_dwell_report(
            db=db,
            floor_id=floor_id,
            start_at=start_at,
            end_at=end_at,
            zone_id=zone_id,
            asset_category=asset_category,
        )
    )


@ANALYTICS_ROUTER.get("/round-trips", response_model=AnalyticsRoundTripReportResponse)
def read_round_trip_report(
    floor_id: str,
    origin_zone_id: str,
    destination_zone_id: str,
    start_at: datetime,
    end_at: datetime,
    asset_category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AnalyticsRoundTripReportResponse:
    if origin_zone_id == destination_zone_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Origin and destination must differ",
        )
    start_at, end_at = validate_time_window(
        start_at=start_at,
        end_at=end_at,
        max_window=MAX_DERIVED_REPORT_WINDOW,
        label="Round-trip report",
    )
    return AnalyticsRoundTripReportResponse.model_validate(
        get_round_trip_report(
            db=db,
            floor_id=floor_id,
            start_at=start_at,
            end_at=end_at,
            origin_zone_id=origin_zone_id,
            destination_zone_id=destination_zone_id,
            asset_category=asset_category,
        )
    )


@ANALYTICS_ROUTER.get("/sla-trends", response_model=AnalyticsSlaTrendResponse)
def read_sla_trend_report(
    floor_id: str,
    table_area_id: str,
    start_at: datetime,
    end_at: datetime,
    bucket_minutes: int = 60,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AnalyticsSlaTrendResponse:
    start_at, end_at = validate_time_window(
        start_at=start_at,
        end_at=end_at,
        max_window=MAX_DERIVED_REPORT_WINDOW,
        label="SLA trend report",
    )
    return AnalyticsSlaTrendResponse.model_validate(
        get_sla_trend_report(
            db=db,
            floor_id=floor_id,
            table_area_id=table_area_id,
            start_at=start_at,
            end_at=end_at,
            bucket_minutes=bucket_minutes,
        )
    )


@ANALYTICS_ROUTER.post("/exports", response_model=AnalyticsExportJobResponse)
def create_analytics_export(
    payload: AnalyticsExportRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsExportJobResponse:
    normalized_payload, site_id = normalize_export_request(
        payload=payload.model_dump(),
        db=db,
    )
    export_job = ExportJob(
        requested_by_user_id=current_user.id,
        report_kind=payload.report_kind,
        export_format=payload.export_format.value,
        status=ExportJobStatus.PENDING.value,
        floor_id=payload.floor_id,
        site_id=site_id,
        report_params=normalized_payload,
    )
    db.add(export_job)
    write_audit_event(
        db,
        action_category="analytics",
        action_type="analytics.export.requested",
        actor=current_user,
        target_type="export_job",
        target_id=export_job.id,
        details={
            "report_kind": payload.report_kind,
            "floor_id": payload.floor_id,
        },
    )
    db.commit()
    db.refresh(export_job)
    background_tasks.add_task(
        process_export_job,
        request.app.state.session_factory,
        request.app.state.settings,
        export_job.id,
    )
    return AnalyticsExportJobResponse.model_validate(serialize_export_job(export_job))


@ANALYTICS_ROUTER.get("/exports", response_model=list[AnalyticsExportJobResponse])
def list_analytics_exports(
    floor_id: str | None = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalyticsExportJobResponse]:
    query = db.query(ExportJob).order_by(ExportJob.requested_at.desc())
    if current_user.role != UserRole.ADMINISTRATOR.value:
        query = query.filter(ExportJob.requested_by_user_id == current_user.id)
    if floor_id is not None:
        query = query.filter(ExportJob.floor_id == floor_id)
    jobs = query.limit(min(max(limit, 1), 25)).all()
    return [AnalyticsExportJobResponse.model_validate(serialize_export_job(job)) for job in jobs]


@ANALYTICS_ROUTER.get("/exports/{job_id}", response_model=AnalyticsExportJobResponse)
def read_analytics_export(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsExportJobResponse:
    job = get_accessible_export_job(db=db, job_id=job_id, current_user=current_user)
    return AnalyticsExportJobResponse.model_validate(serialize_export_job(job))


@ANALYTICS_ROUTER.get("/exports/{job_id}/file")
def download_analytics_export(
    job_id: str,
    settings=Depends(get_settings),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    job = get_accessible_export_job(db=db, job_id=job_id, current_user=current_user)
    content, content_type = get_download_payload(db=db, job=job, settings=settings)
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{job.file_name or "analytics-export.csv"}"'
            ),
        },
    )
