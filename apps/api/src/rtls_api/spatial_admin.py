from __future__ import annotations

import csv
import logging
import math
from io import BytesIO, StringIO
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
    AssetBatteryProfile,
    AssetTag,
    AssetTagImportSession,
    AssetUpdateRateProfile,
    Floor,
    FloorPlanAsset,
    Gateway,
    GatewayHardwareTier,
    PremiumCalibrationStatus,
    PremiumTelemetryModality,
    Site,
    SpatialArea,
    SpatialAreaType,
    User,
    UserRole,
    utc_now,
)
from rtls_api.schemas import (
    AssetTagCreateRequest,
    AssetTagImportConfirmRequest,
    AssetTagImportConfirmResponse,
    AssetTagImportPreviewRecord,
    AssetTagImportValidateResponse,
    AssetTagImportValidationRow,
    AssetTagResponse,
    AssetTagUpdateRequest,
    FloorCreateRequest,
    FloorDetailResponse,
    FloorPlanAssetResponse,
    FloorScaleResponse,
    FloorScaleUpdateRequest,
    FloorSummaryResponse,
    GatewayCreateRequest,
    GatewayResponse,
    GatewayUpdateRequest,
    PremiumGatewayProfileRequest,
    PremiumGatewayProfileResponse,
    SiteCreateRequest,
    SiteResponse,
    SpatialAreaCreateRequest,
    SpatialAreaResponse,
    SpatialAreaUpdateRequest,
)
from rtls_api.storage import (
    ObjectNotFoundError,
    ObjectStorageService,
    create_object_storage_service,
)

SPATIAL_ADMIN_ROUTER = APIRouter(prefix="/api/admin", tags=["admin-spatial"])
SUPPORTED_FLOOR_PLAN_MIME_TYPES = {"image/png", "image/jpeg"}
SUPPORTED_FLOOR_PLAN_FORMATS = {"PNG": ".png", "JPEG": ".jpg"}
ASSET_IMPORT_HEADERS = [
    "tag_identifier",
    "display_name",
    "asset_category",
    "update_rate_profile",
    "battery_profile",
]
logger = logging.getLogger("rtls-api")


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_storage_service(request: Request) -> ObjectStorageService:
    storage_service = getattr(request.app.state, "object_storage_service", None)
    if storage_service is None:
        storage_service = create_object_storage_service(get_settings(request))
        request.app.state.object_storage_service = storage_service
    return storage_service


def _delete_object_quietly(
    storage_service: ObjectStorageService,
    *,
    key: str,
    context: str,
) -> None:
    try:
        storage_service.delete_object(key=key)
    except Exception:
        logger.exception("Failed to delete floor-plan object during %s for %s", context, key)


def _ordered_floor_summary(floor: Floor) -> FloorSummaryResponse:
    return FloorSummaryResponse(
        id=floor.id,
        site_id=floor.site_id,
        name=floor.name,
        level_label=floor.level_label,
        has_floor_plan=floor.floor_plan_asset is not None,
        scale_configured=floor.scale_configured_at is not None,
    )


def _normalize_asset_import_cell(value: str | None) -> str:
    return (value or "").strip()


def _parse_asset_update_rate_profile(value: str) -> AssetUpdateRateProfile | None:
    normalized = value.strip().lower()
    try:
        return AssetUpdateRateProfile(normalized)
    except ValueError:
        return None


def _parse_asset_battery_profile(value: str) -> AssetBatteryProfile | None:
    normalized = value.strip().lower()
    try:
        return AssetBatteryProfile(normalized)
    except ValueError:
        return None


def _clear_floor_scale(floor: Floor) -> None:
    floor.scale_point_a = None
    floor.scale_point_b = None
    floor.scale_distance_m = None
    floor.scale_pixels_per_meter = None
    floor.scale_configured_at = None


def _serialize_premium_gateway_profile(gateway: Gateway) -> PremiumGatewayProfileResponse | None:
    if (
        gateway.premium_modality is None
        or gateway.premium_mounting_label is None
        or gateway.premium_mounting_angle_degrees is None
        or gateway.premium_calibration_status is None
    ):
        return None
    return PremiumGatewayProfileResponse(
        modality=PremiumTelemetryModality(gateway.premium_modality),
        mounting_label=gateway.premium_mounting_label,
        mounting_angle_degrees=gateway.premium_mounting_angle_degrees,
        calibration_status=PremiumCalibrationStatus(gateway.premium_calibration_status),
        calibration_updated_at=gateway.premium_calibration_updated_at,
    )


def _clear_gateway_premium_profile(gateway: Gateway) -> None:
    gateway.premium_modality = None
    gateway.premium_mounting_label = None
    gateway.premium_mounting_angle_degrees = None
    gateway.premium_calibration_status = None
    gateway.premium_calibration_updated_at = None


def _apply_premium_gateway_profile(
    gateway: Gateway,
    premium_profile: PremiumGatewayProfileRequest,
) -> None:
    gateway.premium_modality = premium_profile.modality.value
    gateway.premium_mounting_label = premium_profile.mounting_label.strip()
    gateway.premium_mounting_angle_degrees = premium_profile.mounting_angle_degrees
    gateway.premium_calibration_status = premium_profile.calibration_status.value
    gateway.premium_calibration_updated_at = utc_now()


def _mark_gateway_premium_calibration_stale(gateway: Gateway) -> None:
    if gateway.hardware_tier != GatewayHardwareTier.PREMIUM.value:
        return
    if gateway.premium_modality is None:
        return
    if gateway.premium_calibration_status == PremiumCalibrationStatus.STALE.value:
        return
    gateway.premium_calibration_status = PremiumCalibrationStatus.STALE.value
    gateway.premium_calibration_updated_at = utc_now()


def _validate_gateway_update_payload(gateway: Gateway, payload: GatewayUpdateRequest) -> None:
    next_tier = (
        payload.hardware_tier.value if payload.hardware_tier is not None else gateway.hardware_tier
    )
    if next_tier == GatewayHardwareTier.PREMIUM.value:
        if payload.premium_profile is None and gateway.premium_modality is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Premium gateways require a premium profile",
            )
    elif payload.premium_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Economic gateways cannot include a premium profile",
        )


def _mark_floor_premium_calibration_stale(floor: Floor) -> None:
    for gateway in floor.gateways:
        _mark_gateway_premium_calibration_stale(gateway)


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


def serialize_gateway(gateway: Gateway) -> GatewayResponse:
    return GatewayResponse(
        id=gateway.id,
        floor_id=gateway.floor_id,
        gateway_identifier=gateway.gateway_identifier,
        display_name=gateway.display_name,
        hardware_tier=GatewayHardwareTier(gateway.hardware_tier),
        placement={"x": gateway.placement_x, "y": gateway.placement_y},
        premium_profile=_serialize_premium_gateway_profile(gateway),
        notes=gateway.notes,
    )


def serialize_asset_tag(asset_tag: AssetTag) -> AssetTagResponse:
    return AssetTagResponse(
        id=asset_tag.id,
        tag_identifier=asset_tag.tag_identifier,
        display_name=asset_tag.display_name,
        asset_category=asset_tag.asset_category,
        update_rate_profile=AssetUpdateRateProfile(asset_tag.update_rate_profile),
        battery_profile=AssetBatteryProfile(asset_tag.battery_profile),
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
    ordered_gateways = sorted(
        floor.gateways,
        key=lambda gateway: (gateway.display_name.lower(), gateway.gateway_identifier.lower()),
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
        gateways=[serialize_gateway(gateway) for gateway in ordered_gateways],
    )


def get_floor_or_404(db: Session, floor_id: str) -> Floor:
    floor = db.scalar(
        select(Floor)
        .where(Floor.id == floor_id)
        .options(
            selectinload(Floor.floor_plan_asset),
            selectinload(Floor.areas),
            selectinload(Floor.gateways),
        )
    )
    if floor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Floor not found")
    return floor


def get_area_or_404(db: Session, area_id: str) -> SpatialArea:
    area = db.scalar(select(SpatialArea).where(SpatialArea.id == area_id))
    if area is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area not found")
    return area


def get_gateway_or_404(db: Session, gateway_id: str) -> Gateway:
    gateway = db.scalar(select(Gateway).where(Gateway.id == gateway_id))
    if gateway is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gateway not found")
    return gateway


def get_asset_tag_or_404(db: Session, asset_tag_id: str) -> AssetTag:
    asset_tag = db.scalar(select(AssetTag).where(AssetTag.id == asset_tag_id))
    if asset_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset tag not found")
    return asset_tag


def _validate_floor_for_area_editing(floor: Floor) -> None:
    if floor.floor_plan_asset is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload a floor plan before editing operational areas",
        )


def _validate_floor_for_gateway_placement(floor: Floor) -> None:
    if floor.floor_plan_asset is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload a floor plan before placing gateways",
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

    previous_key: str | None = None
    if floor.floor_plan_asset is not None:
        previous_key = floor.floor_plan_asset.storage_key
        asset = floor.floor_plan_asset
        asset.storage_key = storage_key
        asset.original_filename = floor_plan.filename or f"floor-plan{extension}"
        asset.mime_type = floor_plan.content_type
        asset.width_px = image.width
        asset.height_px = image.height
        _clear_floor_scale(floor)
        _mark_floor_premium_calibration_stale(floor)
        action_type = "floorplan.replaced"
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

    try:
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
    except Exception:
        db.rollback()
        _delete_object_quietly(
            storage_service,
            key=storage_key,
            context="rollback cleanup",
        )
        raise

    if previous_key is not None and previous_key != storage_key:
        _delete_object_quietly(
            storage_service,
            key=previous_key,
            context="post-commit replacement cleanup",
        )

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

    try:
        stored_object = storage_service.get_object(key=floor.floor_plan_asset.storage_key)
    except ObjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor plan file not found",
        ) from error
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


@SPATIAL_ADMIN_ROUTER.get("/floors/{floor_id}/gateways", response_model=list[GatewayResponse])
def list_floor_gateways(
    floor_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> list[GatewayResponse]:
    del admin_user
    floor = get_floor_or_404(db, floor_id)
    ordered_gateways = sorted(
        floor.gateways,
        key=lambda gateway: (gateway.display_name.lower(), gateway.gateway_identifier.lower()),
    )
    return [serialize_gateway(gateway) for gateway in ordered_gateways]


@SPATIAL_ADMIN_ROUTER.post(
    "/floors/{floor_id}/gateways",
    response_model=GatewayResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_gateway(
    floor_id: str,
    payload: GatewayCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> GatewayResponse:
    floor = get_floor_or_404(db, floor_id)
    _validate_floor_for_gateway_placement(floor)

    gateway = Gateway(
        floor_id=floor_id,
        gateway_identifier=payload.gateway_identifier.strip(),
        display_name=payload.display_name.strip(),
        hardware_tier=payload.hardware_tier.value,
        placement_x=payload.placement.x,
        placement_y=payload.placement.y,
        notes=payload.notes.strip() if payload.notes else None,
    )
    if payload.premium_profile is not None:
        _apply_premium_gateway_profile(gateway, payload.premium_profile)
    db.add(gateway)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gateway already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="gateway.created",
        actor=admin_user,
        target_type="gateway",
        target_id=gateway.id,
        details={
            "floor_id": floor_id,
            "gateway_identifier": gateway.gateway_identifier,
            "hardware_tier": gateway.hardware_tier,
            "premium_profile": (
                payload.premium_profile.model_dump(mode="json")
                if payload.premium_profile is not None
                else None
            ),
        },
    )
    db.commit()
    db.refresh(gateway)
    return serialize_gateway(gateway)


@SPATIAL_ADMIN_ROUTER.patch("/gateways/{gateway_id}", response_model=GatewayResponse)
def update_gateway(
    gateway_id: str,
    payload: GatewayUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> GatewayResponse:
    gateway = get_gateway_or_404(db, gateway_id)
    floor = get_floor_or_404(db, gateway.floor_id)
    _validate_floor_for_gateway_placement(floor)
    _validate_gateway_update_payload(gateway, payload)

    changes: dict[str, object] = {}
    if payload.display_name is not None and payload.display_name.strip() != gateway.display_name:
        gateway.display_name = payload.display_name.strip()
        changes["display_name"] = gateway.display_name
    if payload.hardware_tier is not None and payload.hardware_tier.value != gateway.hardware_tier:
        prior_tier = gateway.hardware_tier
        gateway.hardware_tier = payload.hardware_tier.value
        changes["hardware_tier"] = gateway.hardware_tier
        if (
            prior_tier == GatewayHardwareTier.PREMIUM.value
            and gateway.hardware_tier != GatewayHardwareTier.PREMIUM.value
        ):
            _clear_gateway_premium_profile(gateway)
            changes["premium_profile"] = None
    if payload.placement is not None:
        if (
            payload.placement.x != gateway.placement_x
            or payload.placement.y != gateway.placement_y
        ):
            gateway.placement_x = payload.placement.x
            gateway.placement_y = payload.placement.y
            changes["placement"] = {"x": gateway.placement_x, "y": gateway.placement_y}
            _mark_gateway_premium_calibration_stale(gateway)
            if gateway.hardware_tier == GatewayHardwareTier.PREMIUM.value:
                changes["premium_calibration_status"] = gateway.premium_calibration_status
    if payload.premium_profile is not None:
        _apply_premium_gateway_profile(gateway, payload.premium_profile)
        changes["premium_profile"] = payload.premium_profile.model_dump(mode="json")
    if payload.notes is not None:
        next_notes = payload.notes.strip() or None
        if next_notes != gateway.notes:
            gateway.notes = next_notes
            changes["notes"] = gateway.notes

    if not changes:
        return serialize_gateway(gateway)

    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gateway already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="gateway.updated",
        actor=admin_user,
        target_type="gateway",
        target_id=gateway.id,
        details={"floor_id": gateway.floor_id, "changes": changes},
    )
    db.commit()
    db.refresh(gateway)
    return serialize_gateway(gateway)


@SPATIAL_ADMIN_ROUTER.delete("/gateways/{gateway_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gateway(
    gateway_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> None:
    gateway = get_gateway_or_404(db, gateway_id)
    write_audit_event(
        db,
        action_category="configuration",
        action_type="gateway.deleted",
        actor=admin_user,
        target_type="gateway",
        target_id=gateway.id,
        details={
            "floor_id": gateway.floor_id,
            "gateway_identifier": gateway.gateway_identifier,
            "display_name": gateway.display_name,
        },
    )
    db.delete(gateway)
    db.commit()


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


@SPATIAL_ADMIN_ROUTER.get("/assets", response_model=list[AssetTagResponse])
def list_asset_tags(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> list[AssetTagResponse]:
    del admin_user
    asset_tags = db.scalars(select(AssetTag).order_by(AssetTag.display_name.asc())).all()
    return [serialize_asset_tag(asset_tag) for asset_tag in asset_tags]


@SPATIAL_ADMIN_ROUTER.post(
    "/assets",
    response_model=AssetTagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_asset_tag(
    payload: AssetTagCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AssetTagResponse:
    asset_tag = AssetTag(
        tag_identifier=payload.tag_identifier.strip(),
        display_name=payload.display_name.strip(),
        asset_category=payload.asset_category.strip(),
        update_rate_profile=payload.update_rate_profile.value,
        battery_profile=payload.battery_profile.value,
    )
    db.add(asset_tag)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset tag already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="asset.created",
        actor=admin_user,
        target_type="asset_tag",
        target_id=asset_tag.id,
        details={
            "tag_identifier": asset_tag.tag_identifier,
            "update_rate_profile": asset_tag.update_rate_profile,
            "battery_profile": asset_tag.battery_profile,
        },
    )
    db.commit()
    db.refresh(asset_tag)
    return serialize_asset_tag(asset_tag)


@SPATIAL_ADMIN_ROUTER.get("/assets/{asset_tag_id}", response_model=AssetTagResponse)
def get_asset_tag_detail(
    asset_tag_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AssetTagResponse:
    del admin_user
    return serialize_asset_tag(get_asset_tag_or_404(db, asset_tag_id))


@SPATIAL_ADMIN_ROUTER.patch("/assets/{asset_tag_id}", response_model=AssetTagResponse)
def update_asset_tag(
    asset_tag_id: str,
    payload: AssetTagUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AssetTagResponse:
    asset_tag = get_asset_tag_or_404(db, asset_tag_id)

    changes: dict[str, object] = {}
    if payload.display_name is not None and payload.display_name.strip() != asset_tag.display_name:
        asset_tag.display_name = payload.display_name.strip()
        changes["display_name"] = asset_tag.display_name
    if (
        payload.asset_category is not None
        and payload.asset_category.strip() != asset_tag.asset_category
    ):
        asset_tag.asset_category = payload.asset_category.strip()
        changes["asset_category"] = asset_tag.asset_category
    if (
        payload.update_rate_profile is not None
        and payload.update_rate_profile.value != asset_tag.update_rate_profile
    ):
        asset_tag.update_rate_profile = payload.update_rate_profile.value
        changes["update_rate_profile"] = asset_tag.update_rate_profile
    if (
        payload.battery_profile is not None
        and payload.battery_profile.value != asset_tag.battery_profile
    ):
        asset_tag.battery_profile = payload.battery_profile.value
        changes["battery_profile"] = asset_tag.battery_profile

    if not changes:
        return serialize_asset_tag(asset_tag)

    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset tag already exists",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="asset.updated",
        actor=admin_user,
        target_type="asset_tag",
        target_id=asset_tag.id,
        details={"changes": changes},
    )
    db.commit()
    db.refresh(asset_tag)
    return serialize_asset_tag(asset_tag)


@SPATIAL_ADMIN_ROUTER.delete("/assets/{asset_tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_tag(
    asset_tag_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> None:
    asset_tag = get_asset_tag_or_404(db, asset_tag_id)
    write_audit_event(
        db,
        action_category="configuration",
        action_type="asset.deleted",
        actor=admin_user,
        target_type="asset_tag",
        target_id=asset_tag.id,
        details={
            "tag_identifier": asset_tag.tag_identifier,
            "display_name": asset_tag.display_name,
        },
    )
    db.delete(asset_tag)
    db.commit()


@SPATIAL_ADMIN_ROUTER.post(
    "/assets/imports/validate",
    response_model=AssetTagImportValidateResponse,
)
async def validate_asset_tag_import(
    import_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AssetTagImportValidateResponse:
    if import_file.content_type not in {"text/csv", "application/vnd.ms-excel", "text/plain"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Upload a CSV file for asset import",
        )

    raw_bytes = await import_file.read()
    try:
        decoded = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="CSV import must be UTF-8 encoded",
        ) from error

    reader = csv.DictReader(StringIO(decoded))
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="CSV import is missing a header row",
        )

    missing_headers = [header for header in ASSET_IMPORT_HEADERS if header not in reader.fieldnames]
    if missing_headers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"CSV import is missing required columns: {', '.join(missing_headers)}",
        )

    existing_identifiers = set(
        db.scalars(select(AssetTag.tag_identifier)).all()
    )
    seen_identifiers: set[str] = set()
    valid_rows: list[AssetTagImportPreviewRecord] = []
    invalid_rows: list[AssetTagImportValidationRow] = []

    for row_number, row in enumerate(reader, start=2):
        values = {
            header: _normalize_asset_import_cell(row.get(header))
            for header in ASSET_IMPORT_HEADERS
        }
        errors: list[str] = []

        if not values["tag_identifier"]:
            errors.append("tag_identifier is required")
        if not values["display_name"]:
            errors.append("display_name is required")
        if not values["asset_category"]:
            errors.append("asset_category is required")

        update_rate_profile = _parse_asset_update_rate_profile(values["update_rate_profile"])
        if update_rate_profile is None:
            errors.append(
                "update_rate_profile must be one of: slow, balanced, realtime"
            )

        battery_profile = _parse_asset_battery_profile(values["battery_profile"])
        if battery_profile is None:
            errors.append(
                "battery_profile must be one of: long_life, standard, performance"
            )

        if values["tag_identifier"]:
            if values["tag_identifier"] in seen_identifiers:
                errors.append("tag_identifier is duplicated in this CSV file")
            elif values["tag_identifier"] in existing_identifiers:
                errors.append("tag_identifier already exists")
            seen_identifiers.add(values["tag_identifier"])

        if errors:
            invalid_rows.append(
                AssetTagImportValidationRow(
                    row_number=row_number,
                    values=values,
                    errors=errors,
                )
            )
            continue

        valid_rows.append(
            AssetTagImportPreviewRecord(
                tag_identifier=values["tag_identifier"],
                display_name=values["display_name"],
                asset_category=values["asset_category"],
                update_rate_profile=update_rate_profile,
                battery_profile=battery_profile,
            )
        )

    import_id: str | None = None
    if valid_rows and not invalid_rows:
        import_id = str(uuid4())
        db.add(
            AssetTagImportSession(
                id=import_id,
                created_by_user_id=admin_user.id,
                rows=[
                    {
                        "tag_identifier": row.tag_identifier,
                        "display_name": row.display_name,
                        "asset_category": row.asset_category,
                        "update_rate_profile": row.update_rate_profile.value,
                        "battery_profile": row.battery_profile.value,
                    }
                    for row in valid_rows
                ],
            )
        )
        db.commit()

    return AssetTagImportValidateResponse(
        import_id=import_id,
        total_rows=len(valid_rows) + len(invalid_rows),
        valid_row_count=len(valid_rows),
        invalid_row_count=len(invalid_rows),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
    )


@SPATIAL_ADMIN_ROUTER.post(
    "/assets/imports/confirm",
    response_model=AssetTagImportConfirmResponse,
)
def confirm_asset_tag_import(
    payload: AssetTagImportConfirmRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AssetTagImportConfirmResponse:
    import_session = db.scalar(
        select(AssetTagImportSession).where(
            AssetTagImportSession.id == payload.import_id,
            AssetTagImportSession.created_by_user_id == admin_user.id,
        )
    )
    if import_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import session not found",
        )

    created_assets: list[AssetTag] = []
    for row in import_session.rows:
        asset_tag = AssetTag(**row)
        db.add(asset_tag)
        created_assets.append(asset_tag)

    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more asset tags already exist",
        ) from error

    write_audit_event(
        db,
        action_category="configuration",
        action_type="asset.imported",
        actor=admin_user,
        target_type="asset_import",
        target_id=payload.import_id,
        details={
            "created_count": len(created_assets),
            "tag_identifiers": [asset.tag_identifier for asset in created_assets],
        },
    )
    db.delete(import_session)
    db.commit()
    for asset_tag in created_assets:
        db.refresh(asset_tag)

    return AssetTagImportConfirmResponse(
        created_count=len(created_assets),
        assets=[serialize_asset_tag(asset_tag) for asset_tag in created_assets],
    )
