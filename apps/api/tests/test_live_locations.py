from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
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
    Site,
    SpatialArea,
    SpatialAreaType,
    UserRole,
)
from rtls_api.positioning import PositioningService


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-live-locations.db'}",
        redis_url="memory://live-location-tests",
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


def create_ingestion_service(app, settings: Settings) -> TelemetryIngestionService:
    return TelemetryIngestionService(
        session_factory=app.state.session_factory,
        settings=settings,
        dedupe_store=app.state.message_dedupe_store,
        positioning_service=PositioningService(settings),
    )


def seed_tracking_environment(
    app,
    *,
    include_zone: bool = True,
) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Flagship Site", timezone_name="America/Bahia")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Dining Room", level_label="L1")
        db.add(floor)
        db.flush()

        db.add(
            FloorPlanAsset(
                floor_id=floor.id,
                storage_key=f"floor-plans/{floor.id}/seed.png",
                original_filename="seed.png",
                mime_type="image/png",
                width_px=1000,
                height_px=600,
            )
        )

        if include_zone:
            db.add(
                SpatialArea(
                    floor_id=floor.id,
                    name="Dining Zone",
                    area_type=SpatialAreaType.ZONE.value,
                    geometry=[
                        {"x": 0.1, "y": 0.1},
                        {"x": 0.6, "y": 0.1},
                        {"x": 0.6, "y": 0.5},
                        {"x": 0.1, "y": 0.5},
                    ],
                    sla_eligible=False,
                    alert_participation=True,
                )
            )

        gateways = [
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-dining-01",
                display_name="Dining Gateway 1",
                hardware_tier="Economic",
                placement_x=0.2,
                placement_y=0.2,
            ),
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-dining-02",
                display_name="Dining Gateway 2",
                hardware_tier="Economic",
                placement_x=0.4,
                placement_y=0.2,
            ),
            Gateway(
                floor_id=floor.id,
                gateway_identifier="gw-dining-03",
                display_name="Dining Gateway 3",
                hardware_tier="Economic",
                placement_x=0.3,
                placement_y=0.4,
            ),
        ]
        db.add_all(gateways)

        assets = [
            AssetTag(
                tag_identifier="TAG-001",
                display_name="Cart 1",
                asset_category="cart",
                update_rate_profile=AssetUpdateRateProfile.BALANCED.value,
                battery_profile=AssetBatteryProfile.STANDARD.value,
            ),
            AssetTag(
                tag_identifier="TAG-002",
                display_name="Waiter 7",
                asset_category="staff",
                update_rate_profile=AssetUpdateRateProfile.REALTIME.value,
                battery_profile=AssetBatteryProfile.PERFORMANCE.value,
            ),
        ]
        db.add_all(assets)
        db.commit()

        zone = db.scalar(select(SpatialArea).where(SpatialArea.floor_id == floor.id))
        asset_ids = {
            asset.tag_identifier: asset.id
            for asset in db.scalars(select(AssetTag).order_by(AssetTag.tag_identifier.asc())).all()
        }
        return {
            "site_id": site.id,
            "floor_id": floor.id,
            "zone_id": zone.id if zone is not None else "",
            "asset_tag_1_id": asset_ids["TAG-001"],
            "asset_tag_2_id": asset_ids["TAG-002"],
        }


def publish_telemetry(
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


def test_positioning_persists_zone_fallback_then_point_location_and_history(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app):
        seeded = seed_tracking_environment(app)
        service = create_ingestion_service(app, settings)
        first_seen = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)
        second_seen = first_seen + timedelta(seconds=2)

        publish_telemetry(
            service,
            gateway_identifier="gw-dining-01",
            message_id="msg-001",
            tag_identifier="TAG-001",
            rssi=-62,
            broker_received_at=first_seen,
        )

        with app.state.session_factory() as db:
            current = db.get(AssetCurrentLocation, seeded["asset_tag_1_id"])
            history = db.scalars(
                select(AssetLocationHistory).where(
                    AssetLocationHistory.asset_tag_id == seeded["asset_tag_1_id"]
                )
            ).all()

        assert current is not None
        assert current.location_type == "zone"
        assert current.zone_id == seeded["zone_id"]
        assert current.coordinate_x is None
        assert current.coordinate_y is None
        assert current.confidence_level == "low"
        assert len(history) == 1

        publish_telemetry(
            service,
            gateway_identifier="gw-dining-02",
            message_id="msg-002",
            tag_identifier="TAG-001",
            rssi=-64,
            broker_received_at=second_seen,
        )

        with app.state.session_factory() as db:
            current = db.get(AssetCurrentLocation, seeded["asset_tag_1_id"])
            history = db.scalars(
                select(AssetLocationHistory)
                .where(AssetLocationHistory.asset_tag_id == seeded["asset_tag_1_id"])
                .order_by(AssetLocationHistory.observed_at.asc())
            ).all()

        assert current is not None
        assert current.location_type == "point"
        assert current.coordinate_x is not None
        assert current.coordinate_y is not None
        assert 0.2 < current.coordinate_x < 0.4
        assert current.coordinate_y == approx(0.2)
        assert current.zone_id == seeded["zone_id"]
        assert current.confidence_level == "medium"
        assert len(history) == 2
        assert history[0].location_type == "zone"
        assert history[1].location_type == "point"


def test_positioning_skips_low_confidence_updates_without_known_zone(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app):
        seeded = seed_tracking_environment(app, include_zone=False)
        service = create_ingestion_service(app, settings)
        publish_telemetry(
            service,
            gateway_identifier="gw-dining-01",
            message_id="msg-001",
            tag_identifier="TAG-001",
            rssi=-61,
            broker_received_at=datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc),
        )

        with app.state.session_factory() as db:
            current = db.get(AssetCurrentLocation, seeded["asset_tag_1_id"])
            history = db.scalars(
                select(AssetLocationHistory).where(
                    AssetLocationHistory.asset_tag_id == seeded["asset_tag_1_id"]
                )
            ).all()

        assert current is None
        assert history == []


def test_live_location_endpoints_support_filters_search_and_history(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        seeded = seed_tracking_environment(app)
        with app.state.session_factory() as db:
            create_user(
                db,
                email="manager@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        service = create_ingestion_service(app, settings)
        base_time = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc)
        publish_telemetry(
            service,
            gateway_identifier="gw-dining-01",
            message_id="msg-001",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time,
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-dining-02",
            message_id="msg-002",
            tag_identifier="TAG-001",
            rssi=-64,
            broker_received_at=base_time + timedelta(seconds=1),
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-dining-02",
            message_id="msg-003",
            tag_identifier="TAG-002",
            rssi=-63,
            broker_received_at=base_time + timedelta(seconds=2),
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-dining-03",
            message_id="msg-004",
            tag_identifier="TAG-002",
            rssi=-65,
            broker_received_at=base_time + timedelta(seconds=3),
        )

        access_token = issue_access_token(client, "manager@example.com", "StrongPass123")
        headers = {"Authorization": f"Bearer {access_token}"}

        live_response = client.get(
            f"/api/locations/live?floor_id={seeded['floor_id']}&asset_category=cart",
            headers=headers,
        )
        assert live_response.status_code == 200
        assert [record["tag_identifier"] for record in live_response.json()] == ["TAG-001"]
        assert live_response.json()[0]["location_type"] == "point"

        search_response = client.get(
            "/api/locations/search",
            params={"query": "Waiter"},
            headers=headers,
        )
        assert search_response.status_code == 200
        assert [record["tag_identifier"] for record in search_response.json()] == ["TAG-002"]

        history_response = client.get(
            f"/api/locations/assets/{seeded['asset_tag_1_id']}/history",
            params={
                "start_at": base_time.isoformat().replace("+00:00", "Z"),
                "end_at": (base_time + timedelta(seconds=10)).isoformat().replace("+00:00", "Z"),
            },
            headers=headers,
        )
        assert history_response.status_code == 200
        assert [entry["location_type"] for entry in history_response.json()] == ["zone", "point"]


def test_websocket_stream_publishes_new_location_updates(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        seed_tracking_environment(app)
        with app.state.session_factory() as db:
            create_user(
                db,
                email="manager@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        access_token = issue_access_token(client, "manager@example.com", "StrongPass123")
        service = create_ingestion_service(app, settings)

        with client.websocket_connect(f"/ws/locations?access_token={access_token}") as websocket:
            publish_telemetry(
                service,
                gateway_identifier="gw-dining-01",
                message_id="msg-001",
                tag_identifier="TAG-001",
                rssi=-61,
                broker_received_at=datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone.utc),
            )
            event = websocket.receive_json()

        assert event["event"] == "location.updated"
        assert event["location"]["tag_identifier"] == "TAG-001"
        assert event["location"]["location_type"] == "zone"
