from __future__ import annotations

import math
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from rtls_api.audit import write_audit_event
from rtls_api.auth import get_current_user, require_role
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.models import (
    Floor,
    FloorPlanAsset,
    Site,
    SpatialArea,
    SpatialAreaType,
    User,
    UserRole,
    utc_now,
)
from rtls_api.schemas import (
    FloorCreateRequest,
    FloorDetailResponse,
    FloorPlanAssetResponse,
    FloorScaleResponse,
    FloorScaleUpdateRequest,
    FloorSummaryResponse,
    SiteCreateRequest,
    SiteResponse,
    SpatialAreaCreateRequest,
    SpatialAreaResponse,
    SpatialAreaUpdateRequest,
)
from rtls_api.storage import ObjectStorageService

SPATIAL_ADMIN_ROUTER = APIRouter(prefix="/api/admin", tags=["admin-spatial"])
SUPPORTED_FLOOR_PLAN_MIME_TYPES = {"image/png", "image/jpeg"}
SUPPORTED_FLOOR_PLAN_FORMATS = {"PNG": ".png", "JPEG": ".jpg"}


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_storage_service(request: Request) -> ObjectStorageService:
    return request.app.state.object_storage_service


def _ordered_floor_summary(floor: Floor) -> FloorSummaryResponse:
    return FloorSummaryResponse(
        id=floor.id,
        site_id=floor.site_id,
        name=floor.name,
        level_label=floor.level_label,
        has_floor_plan=floor.floor_plan_asset is not None,
        scale_configured=floor.scale_configured_at is not None,
    )


def serialize_site(site: Site) -> SiteResponse:
    ordered_floors = sorted(
        site.floors,
        key=lambda floor: ((floor.level_label or "").lower(), floor.name.lower()),
    )
    return SiteResponse(
        id=site.id,
        name=site.name,
        timezone_name=site.timezone_name,
        floors=[_ordered_floor_summary(floor) for floor in ordered_floors],
    )


def serialize_floor_plan(asset: FloorPlanAsset) -> FloorPlanAssetResponse:
    return FloorPlanAssetResponse(
        id=asset.id,
        floor_id=asset.floor_id,
        original_filename=asset.original_filename,
        mime_type=asset.mime_type,
        width_px=asset.width_px,
        height_px=asset.height_px,
        file_download_path=f"/api/admin/floors/{asset.floor_id}/floor-plan/file",
    )


def serialize_area(area: SpatialArea) -> SpatialAreaResponse:
    return SpatialAreaResponse(
        id=area.id,
        floor_id=area.floor_id,
        name=area.name,
        area_type=SpatialAreaType(area.area_type),
        points=area.geometry,
        sla_eligible=area.sla_eligible,
        alert_participation=area.alert_participation,
    )


def serialize_floor_detail(floor: Floor) -> FloorDetailResponse:
    scale = None
    if (
        floor.scale_configured_at
        and floor.scale_point_a
        and floor.scale_point_b
        and floor.scale_distance_m
    ):
        scale = FloorScaleResponse(
            point_a=floor.scale_point_a,
            point_b=floor.scale_point_b,
            real_world_distance_m=floor.scale_distance_m,
            pixels_per_meter=floor.scale_pixels_per_meter or 0,
            configured_at=floor.scale_configured_at,
        )

    ordered_areas = sorted(
        floor.areas,
        key=lambda area: (SpatialAreaType(area.area_type).value, area.name.lower()),
    )
    return FloorDetailResponse(
        id=floor.id,
        site_id=floor.site_id,
        name=floor.name,
        level_label=floor.level_label,
        scale_configured=floor.scale_configured_at is not None,
        floor_plan=serialize_floor_plan(floor.floor_plan_asset) if floor.floor_plan_asset else None,
        scale=scale,
        areas=[serialize_area(area) for area in ordered_areas],
    )


def get_floor_or_404(db: Session, floor_id: str) -> Floor:
    floor = db.scalar(
        select(Floor)
        .where(Floor.id == floor_id)
        .options(selectinload(Floor.floor_plan_asset), selectinload(Floor.areas))
    )
    if floor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found")
    return floor


def get_area_or_404(db: Session, area_id: str) -> SpatialArea:
    area = db.scalar(select(SpatialArea).where(SpatialArea.id == area_id))
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    return area


def _validate_floor_for_area_editing(floor: Floor) -> None:
    if floor.floor_plan_asset is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload a floor plan before editing operational areas",
        )


@SPATIAL_ADMIN_ROUTER.get("/sites", response_model=list[SiteResponse])
def list_sites(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SiteResponse]:
    sites = db.scalars(
        select(Site).options(selectinload(Site.floors)).order_by(Site.name.asc())
    ).all()
    return [serialize_site(site) for site in sites]


@SPATIAL_ADMIN_ROUTER.post(
    "/sites",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_site(
    payload: SiteCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> SiteResponse:
    site = Site(name=payload.name.strip(), timezone_name=payload.timezone_name)
    db.add(site)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Site already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="site.created",
        actor=admin_user,
        target_type="site",
        target_id=site.id,
        details={"name": site.name, "timezone_name": site.timezone_name},
    )
    db.commit()
    db.refresh(site)
    return serialize_site(site)


@SPATIAL_ADMIN_ROUTER.get("/sites/{site_id}/floors", response_model=list[FloorSummaryResponse])
def list_site_floors(
    site_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[FloorSummaryResponse]:
    site = db.scalar(select(Site).where(Site.id == site_id).options(selectinload(Site.floors)))
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    ordered_floors = sorted(
        site.floors,
        key=lambda floor: ((floor.level_label or "").lower(), floor.name.lower()),
    )
    return [_ordered_floor_summary(floor) for floor in ordered_floors]


@SPATIAL_ADMIN_ROUTER.post(
    "/sites/{site_id}/floors",
    response_model=FloorSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_floor(
    site_id: str,
    payload: FloorCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> FloorSummaryResponse:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    floor = Floor(site_id=site_id, name=payload.name.strip(), level_label=payload.level_label)
    db.add(floor)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Floor already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="floor.created",
        actor=admin_user,
        target_type="floor",
        target_id=floor.id,
        details={"site_id": site_id, "name": floor.name, "level_label": floor.level_label},
    )
    db.commit()
    db.refresh(floor)
    return _ordered_floor_summary(floor)


@SPATIAL_ADMIN_ROUTER.get("/floors/{floor_id}", response_model=FloorDetailResponse)
def get_floor_detail(
    floor_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FloorDetailResponse:
    return serialize_floor_detail(get_floor_or_404(db, floor_id))


@SPATIAL_ADMIN_ROUTER.post(
    "/floors/{floor_id}/floor-plan",
    response_model=FloorPlanAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_floor_plan(
    floor_id: str,
    floor_plan: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage_service: ObjectStorageService = Depends(get_storage_service),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> FloorPlanAssetResponse:
    floor = get_floor_or_404(db, floor_id)

    if floor_plan.content_type not in SUPPORTED_FLOOR_PLAN_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported floor-plan format",
        )

    file_bytes = await floor_plan.read()
    try:
        image = Image.open(BytesIO(file_bytes))
        image.load()
    except UnidentifiedImageError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid floor-plan image",
        ) from error

    if image.format not in SUPPORTED_FLOOR_PLAN_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported floor-plan format",
        )

    extension = SUPPORTED_FLOOR_PLAN_FORMATS[image.format]
    storage_key = f"floor-plans/{floor_id}/{uuid4()}{extension}"
    storage_service.put_object(
        key=storage_key,
        content=file_bytes,
        content_type=floor_plan.content_type,
    )

    if floor.floor_plan_asset is not None:
        previous_key = floor.floor_plan_asset.storage_key
        asset = floor.floor_plan_asset
        asset.storage_key = storage_key
        asset.original_filename = floor_plan.filename or f"floor-plan{extension}"
        asset.mime_type = floor_plan.content_type
        asset.width_px = image.width
        asset.height_px = image.height
        action_type = "floorplan.replaced"
        if previous_key != storage_key:
            storage_service.delete_object(key=previous_key)
    else:
        asset = FloorPlanAsset(
            floor_id=floor_id,
            storage_key=storage_key,
            original_filename=floor_plan.filename or f"floor-plan{extension}",
            mime_type=floor_plan.content_type,
            width_px=image.width,
            height_px=image.height,
        )
        db.add(asset)
        action_type = "floorplan.uploaded"

    db.flush()
    write_audit_event(
        db,
        action_category="configuration",
        action_type=action_type,
        actor=admin_user,
        target_type="floor_plan",
        target_id=asset.id,
        details={"floor_id": floor_id, "filename": asset.original_filename},
    )
    db.commit()
    db.refresh(asset)
    return serialize_floor_plan(asset)


@SPATIAL_ADMIN_ROUTER.get("/floors/{floor_id}/floor-plan/file")
def download_floor_plan_file(
    floor_id: str,
    db: Session = Depends(get_db),
    storage_service: ObjectStorageService = Depends(get_storage_service),
    _: User = Depends(get_current_user),
) -> Response:
    floor = get_floor_or_404(db, floor_id)
    if floor.floor_plan_asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor plan not found")

    stored_object = storage_service.get_object(key=floor.floor_plan_asset.storage_key)
    return Response(content=stored_object.content, media_type=floor.floor_plan_asset.mime_type)


@SPATIAL_ADMIN_ROUTER.put("/floors/{floor_id}/scale", response_model=FloorDetailResponse)
def configure_floor_scale(
    floor_id: str,
    payload: FloorScaleUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> FloorDetailResponse:
    floor = get_floor_or_404(db, floor_id)
    if floor.floor_plan_asset is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload a floor plan before configuring scale",
        )

    dx = payload.point_b.x - payload.point_a.x
    dy = payload.point_b.y - payload.point_a.y
    pixel_distance = math.hypot(
        dx * floor.floor_plan_asset.width_px,
        dy * floor.floor_plan_asset.height_px,
    )
    if pixel_distance <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid scale input",
        )

    floor.scale_point_a = payload.point_a.model_dump()
    floor.scale_point_b = payload.point_b.model_dump()
    floor.scale_distance_m = payload.real_world_distance_m
    floor.scale_pixels_per_meter = pixel_distance / payload.real_world_distance_m
    floor.scale_configured_at = utc_now()

    write_audit_event(
        db,
        action_category="configuration",
        action_type="floor.scale.updated",
        actor=admin_user,
        target_type="floor",
        target_id=floor.id,
        details={
            "point_a": floor.scale_point_a,
            "point_b": floor.scale_point_b,
            "real_world_distance_m": floor.scale_distance_m,
            "pixels_per_meter": floor.scale_pixels_per_meter,
        },
    )
    db.commit()
    db.refresh(floor)
    return serialize_floor_detail(get_floor_or_404(db, floor_id))


@SPATIAL_ADMIN_ROUTER.get("/floors/{floor_id}/areas", response_model=list[SpatialAreaResponse])
def list_floor_areas(
    floor_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SpatialAreaResponse]:
    floor = get_floor_or_404(db, floor_id)
    ordered_areas = sorted(
        floor.areas,
        key=lambda area: (SpatialAreaType(area.area_type).value, area.name.lower()),
    )
    return [serialize_area(area) for area in ordered_areas]


@SPATIAL_ADMIN_ROUTER.post(
    "/floors/{floor_id}/areas",
    response_model=SpatialAreaResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_area(
    floor_id: str,
    payload: SpatialAreaCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> SpatialAreaResponse:
    floor = get_floor_or_404(db, floor_id)
    _validate_floor_for_area_editing(floor)

    area = SpatialArea(
        floor_id=floor_id,
        name=payload.name.strip(),
        area_type=payload.area_type.value,
        geometry=[point.model_dump() for point in payload.points],
        sla_eligible=payload.sla_eligible,
        alert_participation=payload.alert_participation,
    )
    db.add(area)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Area already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="area.created",
        actor=admin_user,
        target_type="spatial_area",
        target_id=area.id,
        details={"floor_id": floor_id, "area_type": area.area_type, "name": area.name},
    )
    db.commit()
    db.refresh(area)
    return serialize_area(area)


@SPATIAL_ADMIN_ROUTER.patch("/areas/{area_id}", response_model=SpatialAreaResponse)
def update_area(
    area_id: str,
    payload: SpatialAreaUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> SpatialAreaResponse:
    area = get_area_or_404(db, area_id)
    floor = get_floor_or_404(db, area.floor_id)
    _validate_floor_for_area_editing(floor)

    changes: dict[str, object] = {}
    if payload.name is not None and payload.name.strip() != area.name:
        area.name = payload.name.strip()
        changes["name"] = area.name
    if payload.area_type is not None and payload.area_type.value != area.area_type:
        area.area_type = payload.area_type.value
        changes["area_type"] = area.area_type
    if payload.points is not None:
        next_points = [point.model_dump() for point in payload.points]
        if next_points != area.geometry:
            area.geometry = next_points
            changes["points"] = area.geometry
    if payload.sla_eligible is not None and payload.sla_eligible != area.sla_eligible:
        area.sla_eligible = payload.sla_eligible
        changes["sla_eligible"] = area.sla_eligible
    if (
        payload.alert_participation is not None
        and payload.alert_participation != area.alert_participation
    ):
        area.alert_participation = payload.alert_participation
        changes["alert_participation"] = area.alert_participation

    if not changes:
        return serialize_area(area)

    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Area already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="area.updated",
        actor=admin_user,
        target_type="spatial_area",
        target_id=area.id,
        details={"floor_id": area.floor_id, "changes": changes},
    )
    db.commit()
    db.refresh(area)
    return serialize_area(area)


@SPATIAL_ADMIN_ROUTER.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_area(
    area_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> None:
    area = get_area_or_404(db, area_id)
    write_audit_event(
        db,
        action_category="configuration",
        action_type="area.deleted",
        actor=admin_user,
        target_type="spatial_area",
        target_id=area.id,
        details={"floor_id": area.floor_id, "area_type": area.area_type, "name": area.name},
    )
    db.delete(area)
    db.commit()
