from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from pytest import approx
from sqlalchemy import select

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.ingestion import TelemetryIngestionService
from rtls_api.main import create_app
from rtls_api.models import (
    AssetBatteryProfile,
    AssetCurrentLocation,
    AssetLocationHistory,
    AssetTag,
    AssetUpdateRateProfile,
    Floor,
    FloorPlanAsset,
    Gateway,
    PremiumRawMeasurement,
    Site,
    SpatialArea,
    SpatialAreaType,
    UserRole,
    utc_now,
)
from rtls_api.positioning import PositioningService


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-premium.db'}",
        redis_url="memory://premium-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        positioning_recent_window_seconds=30,
        live_location_stream_poll_interval_ms=20,
        **overrides,
    )


def issue_access_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/token", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def make_png_bytes(width: int = 1000, height: int = 1000) -> bytes:
    image = Image.new("RGB", (width, height), color=(14, 23, 41))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def create_ingestion_service(app, settings: Settings) -> TelemetryIngestionService:
    return TelemetryIngestionService(
        session_factory=app.state.session_factory,
        settings=settings,
        dedupe_store=app.state.message_dedupe_store,
        positioning_service=PositioningService(settings),
    )


def seed_premium_tracking_environment(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Premium Site", timezone_name="America/Bahia")
        db.add(site)
        db.flush()

        floor = Floor(
            site_id=site.id,
            name="Dining Hall",
            level_label="L1",
            scale_pixels_per_meter=100,
            scale_distance_m=10,
            scale_point_a={"x": 0.0, "y": 0.0},
            scale_point_b={"x": 1.0, "y": 0.0},
            scale_configured_at=utc_now(),
        )
        db.add(floor)
        db.flush()

        db.add(
            FloorPlanAsset(
                floor_id=floor.id,
                storage_key=f"floor-plans/{floor.id}/premium.png",
                original_filename="premium.png",
                mime_type="image/png",
                width_px=1000,
                height_px=1000,
            )
        )
        db.add(
            SpatialArea(
                floor_id=floor.id,
                name="Dining Zone",
                area_type=SpatialAreaType.ZONE.value,
                geometry=[
                    {"x": 0.1, "y": 0.1},
                    {"x": 0.9, "y": 0.1},
                    {"x": 0.9, "y": 0.9},
                    {"x": 0.1, "y": 0.9},
                ],
                sla_eligible=False,
                alert_participation=True,
            )
        )

        gateways = [
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-econ-01",
                display_name="Economic 1",
                hardware_tier="Economic",
                placement_x=0.18,
                placement_y=0.22,
            ),
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-econ-02",
                display_name="Economic 2",
                hardware_tier="Economic",
                placement_x=0.32,
                placement_y=0.22,
            ),
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-premium-01",
                display_name="Premium 1",
                hardware_tier="Premium",
                placement_x=0.2,
                placement_y=0.2,
                premium_modality="UWB",
                premium_mounting_label="North wall",
                premium_mounting_angle_degrees=0,
                premium_calibration_status="calibrated",
                premium_calibration_updated_at=utc_now(),
            ),
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-premium-02",
                display_name="Premium 2",
                hardware_tier="Premium",
                placement_x=0.8,
                placement_y=0.2,
                premium_modality="UWB",
                premium_mounting_label="East wall",
                premium_mounting_angle_degrees=0,
                premium_calibration_status="calibrated",
                premium_calibration_updated_at=utc_now(),
            ),
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-premium-03",
                display_name="Premium 3",
                hardware_tier="Premium",
                placement_x=0.2,
                placement_y=0.8,
                premium_modality="UWB",
                premium_mounting_label="South wall",
                premium_mounting_angle_degrees=0,
                premium_calibration_status="calibrated",
                premium_calibration_updated_at=utc_now(),
            ),
        ]
        db.add_all(gateways)

        asset = AssetTag(
            tag_identifier="TAG-PRM-01",
            display_name="Waiter Tag Prime",
            asset_category="staff",
            update_rate_profile=AssetUpdateRateProfile.REALTIME.value,
            battery_profile=AssetBatteryProfile.PERFORMANCE.value,
        )
        db.add(asset)
        db.commit()

        return {
            "site_id": site.id,
            "floor_id": floor.id,
            "asset_tag_id": asset.id,
            "tag_identifier": asset.tag_identifier,
        }


def publish_economic_telemetry(
    service: TelemetryIngestionService,
    *,
    gateway_identifier: str,
    message_id: str,
    tag_identifier: str,
    rssi: int,
    broker_received_at: datetime,
) -> None:
    response = service.process_message(
        topic=f"rtls/data/{gateway_identifier}",
        payload_bytes=json.dumps(
            {
                "gateway_id": gateway_identifier,
                "message_id": message_id,
                "readings": [{"tag_id": tag_identifier, "rssi": rssi}],
            }
        ).encode("utf-8"),
        broker_received_at=broker_received_at,
    )
    assert response.accepted is True


def publish_premium_uwb(
    service: TelemetryIngestionService,
    *,
    gateway_identifier: str,
    message_id: str,
    tag_identifier: str,
    distance_m: float,
    quality_score: float,
    broker_received_at: datetime,
) -> None:
    response = service.process_message(
        topic=f"rtls/premium/{gateway_identifier}",
        payload_bytes=json.dumps(
            {
                "gateway_id": gateway_identifier,
                "message_id": message_id,
                "measurements": [
                    {
                        "tag_id": tag_identifier,
                        "modality": "UWB",
                        "sequence_id": message_id,
                        "quality_score": quality_score,
                        "distance_m": round(distance_m, 3),
                    }
                ],
            }
        ).encode("utf-8"),
        broker_received_at=broker_received_at,
    )
    assert response.accepted is True


def normalized_distance_meters(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
) -> float:
    return math.hypot((point_a[0] - point_b[0]) * 10, (point_a[1] - point_b[1]) * 10)


def test_premium_gateway_profile_validation_and_calibration_invalidation(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
                display_name="Admin",
            )
            db.commit()

        admin_token = issue_access_token(client, "admin@example.com", "StrongPass123")
        headers = {"Authorization": f"Bearer {admin_token}"}

        site = client.post(
            "/api/admin/sites",
            headers=headers,
            json={"name": "Premium Admin Site", "timezone_name": "America/Bahia"},
        ).json()
        floor = client.post(
            f"/api/admin/sites/{site['id']}/floors",
            headers=headers,
            json={"name": "Service Floor", "level_label": "L1"},
        ).json()
        floor_id = floor["id"]
        upload = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers=headers,
            files={"floor_plan": ("service-floor.png", make_png_bytes(), "image/png")},
        )
        assert upload.status_code == 201

        invalid = client.post(
            f"/api/admin/floors/{floor_id}/gateways",
            headers=headers,
            json={
                "gateway_identifier": "gw-premium-admin-01",
                "display_name": "Premium Admin Gateway",
                "hardware_tier": "Premium",
                "placement": {"x": 0.25, "y": 0.25},
            },
        )
        assert invalid.status_code == 422

        created = client.post(
            f"/api/admin/floors/{floor_id}/gateways",
            headers=headers,
            json={
                "gateway_identifier": "gw-premium-admin-01",
                "display_name": "Premium Admin Gateway",
                "hardware_tier": "Premium",
                "placement": {"x": 0.25, "y": 0.25},
                "premium_profile": {
                    "modality": "UWB",
                    "mounting_label": "Ceiling beam",
                    "mounting_angle_degrees": 15,
                    "calibration_status": "calibrated",
                },
            },
        )
        assert created.status_code == 201
        gateway_id = created.json()["id"]
        assert created.json()["premium_profile"]["calibration_status"] == "calibrated"

        replaced = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers=headers,
            files={"floor_plan": ("service-floor-v2.png", make_png_bytes(), "image/png")},
        )
        assert replaced.status_code == 201

        floor_detail = client.get(f"/api/admin/floors/{floor_id}", headers=headers)
        assert floor_detail.status_code == 200
        gateway_payload = floor_detail.json()["gateways"][0]
        assert gateway_payload["premium_profile"]["calibration_status"] == "stale"

        recalibrated = client.patch(
            f"/api/admin/gateways/{gateway_id}",
            headers=headers,
            json={
                "premium_profile": {
                    "modality": "UWB",
                    "mounting_label": "Ceiling beam",
                    "mounting_angle_degrees": 15,
                    "calibration_status": "calibrated",
                }
            },
        )
        assert recalibrated.status_code == 200
        assert recalibrated.json()["premium_profile"]["calibration_status"] == "calibrated"

        moved = client.patch(
            f"/api/admin/gateways/{gateway_id}",
            headers=headers,
            json={"placement": {"x": 0.35, "y": 0.3}},
        )
        assert moved.status_code == 200
        assert moved.json()["premium_profile"]["calibration_status"] == "stale"


def test_premium_uwb_ingestion_updates_live_location_contract(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        seeded = seed_premium_tracking_environment(app)
        with app.state.session_factory() as db:
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        service = create_ingestion_service(app, settings)
        target = (0.5, 0.5)
        base_time = datetime(2026, 3, 29, 12, 0, 0, tzinfo=timezone.utc)

        publish_premium_uwb(
            service,
            gateway_identifier="gw-premium-01",
            message_id="uwb-001",
            tag_identifier=seeded["tag_identifier"],
            distance_m=normalized_distance_meters((0.2, 0.2), target),
            quality_score=0.92,
            broker_received_at=base_time,
        )
        publish_premium_uwb(
            service,
            gateway_identifier="gw-premium-02",
            message_id="uwb-002",
            tag_identifier=seeded["tag_identifier"],
            distance_m=normalized_distance_meters((0.8, 0.2), target),
            quality_score=0.9,
            broker_received_at=base_time.replace(second=1),
        )
        publish_premium_uwb(
            service,
            gateway_identifier="gw-premium-03",
            message_id="uwb-003",
            tag_identifier=seeded["tag_identifier"],
            distance_m=normalized_distance_meters((0.2, 0.8), target),
            quality_score=0.89,
            broker_received_at=base_time.replace(second=2),
        )

        with app.state.session_factory() as db:
            current = db.get(AssetCurrentLocation, seeded["asset_tag_id"])
            measurements = db.scalars(select(PremiumRawMeasurement)).all()

        assert current is not None
        assert current.source_tier == "Premium"
        assert current.source_modality == "UWB"
        assert current.precision_meters is not None
        assert current.coordinate_x == approx(0.5, abs=0.03)
        assert current.coordinate_y == approx(0.5, abs=0.03)
        assert len(measurements) == 3

        access_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        response = client.get(
            f"/api/locations/live?floor_id={seeded['floor_id']}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json()[0]["source_tier"] == "Premium"
        assert response.json()[0]["source_modality"] == "UWB"
        assert response.json()[0]["precision_meters"] is not None


def test_premium_candidate_supersedes_recent_economic_location_and_preserves_history(
    tmp_path: Path,
) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app):
        seeded = seed_premium_tracking_environment(app)
        service = create_ingestion_service(app, settings)
        economic_time = datetime(2026, 3, 29, 12, 10, 0, tzinfo=timezone.utc)
        premium_time = datetime(2026, 3, 29, 12, 10, 5, tzinfo=timezone.utc)

        publish_economic_telemetry(
            service,
            gateway_identifier="gw-econ-01",
            message_id="econ-001",
            tag_identifier=seeded["tag_identifier"],
            rssi=-61,
            broker_received_at=economic_time,
        )
        publish_economic_telemetry(
            service,
            gateway_identifier="gw-econ-02",
            message_id="econ-002",
            tag_identifier=seeded["tag_identifier"],
            rssi=-60,
            broker_received_at=economic_time.replace(second=1),
        )

        with app.state.session_factory() as db:
            economic_current = db.get(AssetCurrentLocation, seeded["asset_tag_id"])

        assert economic_current is not None
        assert economic_current.source_tier == "Economic"

        target = (0.5, 0.5)
        publish_premium_uwb(
            service,
            gateway_identifier="gw-premium-01",
            message_id="uwb-101",
            tag_identifier=seeded["tag_identifier"],
            distance_m=normalized_distance_meters((0.2, 0.2), target),
            quality_score=0.93,
            broker_received_at=premium_time,
        )
        publish_premium_uwb(
            service,
            gateway_identifier="gw-premium-02",
            message_id="uwb-102",
            tag_identifier=seeded["tag_identifier"],
            distance_m=normalized_distance_meters((0.8, 0.2), target),
            quality_score=0.91,
            broker_received_at=premium_time.replace(second=6),
        )
        publish_premium_uwb(
            service,
            gateway_identifier="gw-premium-03",
            message_id="uwb-103",
            tag_identifier=seeded["tag_identifier"],
            distance_m=normalized_distance_meters((0.2, 0.8), target),
            quality_score=0.9,
            broker_received_at=premium_time.replace(second=7),
        )

        with app.state.session_factory() as db:
            current = db.get(AssetCurrentLocation, seeded["asset_tag_id"])
            history = db.scalars(
                select(AssetLocationHistory)
                .where(AssetLocationHistory.asset_tag_id == seeded["asset_tag_id"])
                .order_by(
                    AssetLocationHistory.observed_at.asc(),
                    AssetLocationHistory.created_at.asc(),
                )
            ).all()

        assert current is not None
        assert current.source_tier == "Premium"
        assert current.source_modality == "UWB"
        assert current.coordinate_x == approx(0.5, abs=0.03)
        assert current.coordinate_y == approx(0.5, abs=0.03)
        assert {entry.source_tier for entry in history} == {"Economic", "Premium"}
        assert history[-1].source_tier == "Premium"
