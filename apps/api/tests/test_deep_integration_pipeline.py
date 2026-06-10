from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

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
    DerivedZoneDwellRecord,
    DerivedZoneTransitionEvent,
    Floor,
    FloorPlanAsset,
    Gateway,
    Site,
    SpatialArea,
    UserRole,
)
from rtls_api.positioning import PositioningService


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-deep-integration.db'}",
        redis_url="memory://deep-integration-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret-key-that-is-long-enough-for-hmac-sha256",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
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


def publish_telemetry(service, *, gateway_id, message_id, readings, timestamp="2026-06-09T12:00:00Z"):
    return service.process_message(
        topic=f"rtls/data/{gateway_id}",
        payload_bytes=json.dumps({
            "gateway_id": gateway_id,
            "message_id": message_id,
            "timestamp": timestamp,
            "readings": readings,
        }).encode("utf-8"),
        broker_received_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
    )


def seed_pipeline_environment(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Restaurant HQ")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Main Dining")
        db.add(floor)
        db.flush()

        plan_asset = FloorPlanAsset(
            floor_id=floor.id,
            storage_key=f"floor-plans/{floor.id}/dining.png",
            original_filename="dining.png",
            mime_type="image/png",
            width_px=1000,
            height_px=1000,
        )
        db.add(plan_asset)
        db.flush()

        gw_kitchen = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-kitchen-01",
            display_name="Kitchen Gateway",
            hardware_tier="Economic",
            placement_x=0.15,
            placement_y=0.15,
        )
        gw_exit = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-exit-01",
            display_name="Exit Gateway",
            hardware_tier="Economic",
            placement_x=0.85,
            placement_y=0.85,
        )
        db.add_all([gw_kitchen, gw_exit])
        db.flush()

        kitchen_zone = SpatialArea(
            floor_id=floor.id,
            name="Kitchen",
            area_type="zone",
            geometry=[{"x": 0.0, "y": 0.0}, {"x": 0.3, "y": 0.0}, {"x": 0.3, "y": 0.3}, {"x": 0.0, "y": 0.3}, {"x": 0.0, "y": 0.0}],
        )
        exit_zone = SpatialArea(
            floor_id=floor.id,
            name="Exit",
            area_type="zone",
            geometry=[{"x": 0.7, "y": 0.7}, {"x": 1, "y": 0.7}, {"x": 1, "y": 1}, {"x": 0.7, "y": 1}, {"x": 0.7, "y": 0.7}],
        )
        db.add_all([kitchen_zone, exit_zone])
        db.flush()

        table_area = SpatialArea(
            floor_id=floor.id,
            name="Table 12",
            area_type="table",
            geometry=[{"x": 0.1, "y": 0.1}, {"x": 0.3, "y": 0.1}, {"x": 0.3, "y": 0.3}, {"x": 0.1, "y": 0.3}, {"x": 0.1, "y": 0.1}],
            sla_eligible=True,
        )
        db.add(table_area)
        db.flush()

        tag = AssetTag(
            tag_identifier="WAITER-001",
            display_name="Waiter Tag 001",
            asset_category="Staff",
            battery_profile="standard",
            update_rate_profile="balanced",
        )
        db.add(tag)
        db.commit()

        return {
            "site_id": str(site.id),
            "floor_id": str(floor.id),
            "kitchen_zone_id": str(kitchen_zone.id),
            "exit_zone_id": str(exit_zone.id),
            "table_area_id": str(table_area.id),
            "tag_id": str(tag.id),
        }


def test_full_pipeline_ingestion_to_positioning_to_derived_events(tmp_path: Path) -> None:
    """Deep integration: MQTT ingestion -> positioning -> zone transitions -> dwell records -> live locations.

    Simulates a waiter moving Kitchen -> Exit -> Kitchen and verifies the full pipeline.
    """
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        ids = seed_pipeline_environment(app)
        service = create_ingestion_service(app, settings)

        with app.state.session_factory() as db:
            create_user(db, email="admin@example.com", password="Pass123!", role=UserRole.ADMINISTRATOR)
            create_user(db, email="ops@example.com", password="Pass123!", role=UserRole.GENERAL_USER)
            db.commit()

        token = issue_access_token(client, "ops@example.com", "Pass123!")

        # Ingest readings near kitchen gateway
        for i in range(3):
            result = publish_telemetry(service, gateway_id="gw-kitchen-01", message_id=f"msg-kitchen-{i}", readings=[{"tag_id": "WAITER-001", "rssi": -50 + i * 5}])
            assert result.accepted is True, f"Kitchen reading {i} should be accepted"

        # Verify location was produced (in some zone on the floor)
        with app.state.session_factory() as db:
            current = db.query(AssetCurrentLocation).filter_by(asset_tag_id=ids["tag_id"]).first()
            assert current is not None, "Should have a current location"
            assert current.zone_id is not None, "Should be in a zone"
            first_zone_id = current.zone_id

        # Verify zone entry event
        with app.state.session_factory() as db:
            events = db.query(DerivedZoneTransitionEvent).order_by(DerivedZoneTransitionEvent.created_at).all()
            entry_events = [e for e in events if e.event_type == "entry" and e.zone_id == first_zone_id]
            assert len(entry_events) >= 1, "Should have at least one entry event"

        # Move to exit (30s after kitchen, outside the 20s positioning window)
        for i in range(3):
            result = publish_telemetry(service, gateway_id="gw-exit-01", message_id=f"msg-exit-{i}", readings=[{"tag_id": "WAITER-001", "rssi": -55 + i * 3}], timestamp=f"2026-06-09T12:00:{30 + i}Z")
            assert result.accepted is True

        # Verify now in exit zone (or at least a different zone from initial)
        with app.state.session_factory() as db:
            current = db.query(AssetCurrentLocation).filter_by(asset_tag_id=ids["tag_id"]).first()
            assert current is not None
            assert current.zone_id is not None, "Should have a zone after moving to exit"
            assert current.zone_id != first_zone_id, "Should have transitioned to a different zone"
            exit_zone_id = current.zone_id

        # Verify kitchen dwell closed
        with app.state.session_factory() as db:
            dwells = db.query(DerivedZoneDwellRecord).filter_by(zone_id=first_zone_id).all()
            assert len(dwells) >= 1, "Should have dwell record for initial zone"
            assert any(d.ended_at is not None for d in dwells), "Dwell in initial zone should be closed"

        # Return to kitchen (round trip, 30s after exit readings)
        for i in range(3):
            result = publish_telemetry(service, gateway_id="gw-kitchen-01", message_id=f"msg-return-{i}", readings=[{"tag_id": "WAITER-001", "rssi": -48 + i * 2}], timestamp=f"2026-06-09T12:01:{i:02d}Z")
            assert result.accepted is True

        # Verify round trip
        response = client.get(
            "/api/derived/round-trips",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": ids["floor_id"],
                "origin_zone_id": first_zone_id,
                "destination_zone_id": exit_zone_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        trips = data if isinstance(data, list) else data["items"]
        assert len(trips) >= 1, "Should have a round trip"
        assert trips[0]["total_seconds"] > 0

        # Verify live locations
        response = client.get(
            "/api/locations/live",
            headers={"Authorization": f"Bearer {token}"},
            params={"floor_id": ids["floor_id"]},
        )
        assert response.status_code == 200
        live_data = response.json()
        live_items = live_data if isinstance(live_data, list) else live_data["items"]
        waiter = next((l for l in live_items if l["tag_identifier"] == "WAITER-001"), None)
        assert waiter is not None
        assert waiter["zone_name"] in ("Kitchen", "Table 12", "Exit"), f"Unexpected zone: {waiter['zone_name']}"

        # Verify audit trail
        admin_token = issue_access_token(client, "admin@example.com", "Pass123!")
        response = client.get("/api/admin/audit-events", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        audit_data = response.json()
        audit_items = audit_data if isinstance(audit_data, list) else audit_data["items"]
        assert len(audit_items) > 0


def test_pipeline_positioning_degrades_without_spatial_context(tmp_path: Path) -> None:
    """Verify positioning degrades gracefully with no spatial zones."""
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app):
        with app.state.session_factory() as db:
            site = Site(name="Empty Site")
            db.add(site)
            db.flush()

            floor = Floor(site_id=site.id, name="Empty Floor")
            db.add(floor)
            db.flush()

            FloorPlanAsset(
                floor_id=floor.id,
                storage_key=f"floor-plans/{floor.id}/empty.png",
                original_filename="empty.png",
                mime_type="image/png",
                width_px=1000,
                height_px=1000,
            )
            db.add(
                Gateway(
                    floor_id=floor.id,
                    gateway_identifier="gw-isolated-01",
                    display_name="Isolated Gateway",
                    hardware_tier="Economic",
                    placement_x=0.5,
                    placement_y=0.5,
                )
            )
            db.add(
                AssetTag(
                    tag_identifier="ISOLATED-001",
                    display_name="Isolated Tag",
                    asset_category="Equipment",
                    battery_profile="standard",
                    update_rate_profile="balanced",
                )
            )
            db.commit()

        service = create_ingestion_service(app, settings)

        result = publish_telemetry(service, gateway_id="gw-isolated-01", message_id="msg-isolated", readings=[{"tag_id": "ISOLATED-001", "rssi": -60}])
        assert result.accepted is True

        with app.state.session_factory() as db:
            assert db.query(AssetCurrentLocation).first() is None

        publish_telemetry(service, gateway_id="gw-isolated-01", message_id="msg-isolated-2", readings=[{"tag_id": "ISOLATED-001", "rssi": -58}], timestamp="2026-06-09T12:00:01Z")

        with app.state.session_factory() as db:
            assert db.query(AssetCurrentLocation).first() is None
            assert db.query(AssetLocationHistory).count() == 0
