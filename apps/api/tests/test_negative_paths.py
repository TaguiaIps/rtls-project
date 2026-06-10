from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.ingestion import TelemetryIngestionService
from rtls_api.main import create_app
from rtls_api.models import (
    AssetBatteryProfile,
    AssetTag,
    AssetUpdateRateProfile,
    Floor,
    FloorPlanAsset,
    Gateway,
    Site,
    SpatialArea,
    UserRole,
)
from rtls_api.positioning import PositioningService


def make_png_bytes(width: int = 1200, height: int = 800) -> bytes:
    image = Image.new("RGB", (width, height), color=(14, 23, 41))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-negative-paths.db'}",
        redis_url="memory://negative-path-tests",
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
    )


def seed_full_environment(app, **kwargs) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Test Site")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Test Floor")
        db.add(floor)
        db.flush()

        plan_asset = FloorPlanAsset(
            floor_id=floor.id,
            storage_key=f"floor-plans/{floor.id}/test.png",
            original_filename="test.png",
            mime_type="image/png",
            width_px=1000,
            height_px=1000,
        )
        db.add(plan_asset)
        db.flush()

        gateway = Gateway(
            floor_id=floor.id,
            gateway_identifier=kwargs.get("gateway_identifier", "gw-test-01"),
            display_name="Test Gateway",
            hardware_tier="Economic",
            placement_x=0.5,
            placement_y=0.5,
        )
        db.add(gateway)
        db.flush()

        area = SpatialArea(
            floor_id=floor.id,
            name="Test Zone",
            area_type="zone",
            geometry=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0}, {"x": 0.0, "y": 0.0}],
        )

        table_area = SpatialArea(
            floor_id=floor.id,
            name="Test Table",
            area_type="table",
            geometry=[{"x": 0.3, "y": 0.3}, {"x": 0.7, "y": 0.3}, {"x": 0.7, "y": 0.7}, {"x": 0.3, "y": 0.7}, {"x": 0.3, "y": 0.3}],
            sla_eligible=True,
        )
        db.add(table_area)
        db.flush()
        db.add(area)
        db.flush()

        tag = AssetTag(
            tag_identifier=kwargs.get("tag_identifier", "TAG-001"),
            display_name="Test Tag",
            asset_category="Tray Cart",
            battery_profile="standard",
            update_rate_profile="balanced",
        )
        db.add(tag)
        db.commit()

        return {
            "site_id": str(site.id),
            "floor_id": str(floor.id),
            "gateway_id": str(gateway.id),
            "area_id": str(area.id),
            "table_area_id": str(table_area.id),
            "tag_id": str(tag.id),
        }


def test_audit_events_exclude_password_and_token_values(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(db, email="admin@example.com", password="SecretPass123!", role=UserRole.ADMINISTRATOR)
            db.commit()

        token = issue_access_token(client, "admin@example.com", "SecretPass123!")

        response = client.get(
            "/api/admin/audit-events",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        events = response.json()["items"]

        for event in events:
            detail_str = json.dumps(event)
            assert "SecretPass123!" not in detail_str, f"Audit event contains raw password: {event['action_type']}"
            assert "eyJ" not in detail_str, f"Audit event contains raw token: {event['action_type']}"


def test_maintenance_alert_rules_not_exposed_as_editable(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        ids = seed_full_environment(app)
        with app.state.session_factory() as db:
            create_user(db, email="admin@example.com", password="Pass123!", role=UserRole.ADMINISTRATOR)
            db.commit()

        token = issue_access_token(client, "admin@example.com", "Pass123!")

        response = client.post(
            "/api/alerts/rules",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Table SLA Rule",
                "rule_type": "table_sla",
                "floor_id": ids["floor_id"],
                "table_area_ids": [ids["table_area_id"]],
                "threshold_seconds": 600,
                "enabled": True,
            },
        )
        assert response.status_code in (200, 201)

        response = client.get(
            "/api/alerts/rules",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        rules = response.json()
        assert len(rules) >= 1

        for rule in rules:
            assert rule["rule_type"] not in ("gateway_stale", "gateway_low_battery"), "System-managed maintenance rule exposed as editable"


def test_area_creation_rejects_invalid_area_type(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(db, email="admin@example.com", password="Pass123!", role=UserRole.ADMINISTRATOR)
            db.commit()

        token = issue_access_token(client, "admin@example.com", "Pass123!")

        response = client.post("/api/admin/sites", headers={"Authorization": f"Bearer {token}"}, json={"name": "Test Site"})
        assert response.status_code == 201
        site_id = response.json()["id"]

        response = client.post(
            f"/api/admin/sites/{site_id}/floors",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Floor", "level_label": "L1"},
        )
        assert response.status_code == 201
        floor_id = response.json()["id"]

        response = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {token}"},
            files={"floor_plan": ("plan.png", make_png_bytes(), "image/png")},
        )
        assert response.status_code == 201

        response = client.post(
            f"/api/admin/floors/{floor_id}/areas",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Bad Type",
                "area_type": "invalid_type",
                "points": [{"x": 0.0, "y": 0.0}, {"x": 0.5, "y": 0.0}, {"x": 0.5, "y": 0.5}, {"x": 0.0, "y": 0.5}],
            },
        )
        assert response.status_code in (422, 400), "Should reject unsupported area type"


def test_general_user_cannot_access_admin_routes(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(db, email="admin@example.com", password="Pass123!", role=UserRole.ADMINISTRATOR)
            create_user(db, email="user@example.com", password="Pass123!", role=UserRole.GENERAL_USER)
            db.commit()

        admin_token = issue_access_token(client, "admin@example.com", "Pass123!")
        user_token = issue_access_token(client, "user@example.com", "Pass123!")

        for route in ["/api/admin/summary", "/api/admin/observability/summary", "/api/admin/audit-events", "/api/admin/gateway-health"]:
            assert client.get(route, headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
            assert client.get(route, headers={"Authorization": f"Bearer {user_token}"}).status_code == 403


def test_unauthenticated_requests_rejected(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        for route in ["/api/me", "/api/locations/live", "/api/alerts/summary", "/api/operations/overview", "/api/admin/summary"]:
            assert client.get(route).status_code == 401


def test_ingestion_rejects_malformed_payloads(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app):
        ids = seed_full_environment(app)
        service = create_ingestion_service(app, settings)

        # Negative RSSI — accepted
        result = publish_telemetry(service, gateway_id="gw-test-01", message_id="msg-neg-rssi", readings=[{"tag_id": "TAG-001", "rssi": -85}])
        assert result.accepted is True

        # Missing readings — rejected
        result = service.process_message(
            topic="rtls/data/gw-test-01",
            payload_bytes=json.dumps({"gateway_id": "gw-test-01", "message_id": "msg-no-readings", "timestamp": "2026-06-09T12:00:01Z"}).encode("utf-8"),
        )
        assert result.accepted is False

        # Invalid JSON — rejected
        result = service.process_message(
            topic="rtls/data/gw-test-01",
            payload_bytes=b"{broken json",
        )
        assert result.accepted is False


def test_refresh_with_replayed_tokens_is_rejected(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(db, email="admin@example.com", password="Pass123!", role=UserRole.ADMINISTRATOR)
            db.commit()

        response = client.post("/api/auth/token", json={"email": "admin@example.com", "password": "Pass123!"})
        assert response.status_code == 200
        refresh_token_1 = response.json()["refresh_token"]

        # Refresh — get rotated token
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token_1})
        assert response.status_code == 200
        refresh_token_2 = response.json()["refresh_token"]

        # Replay old token — rejected
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token_1})
        assert response.status_code == 401, "Replayed refresh token should be rejected"

        # Rotated token was already consumed by the refresh above,
        # so it's also now stale — the system rotates on every use
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token_2})
        assert response.status_code == 401, "Already-rotated refresh token should be rejected"
