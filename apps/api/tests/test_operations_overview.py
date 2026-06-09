from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.ingestion import TelemetryIngestionService
from rtls_api.main import create_app
from rtls_api.models import (
    AlertInstance,
    AlertSeverity,
    AlertStatus,
    AssetBatteryProfile,
    AssetTag,
    AssetUpdateRateProfile,
    DerivedZoneDwellRecord,
    Floor,
    FloorPlanAsset,
    Gateway,
    GatewayHeartbeat,
    Site,
    SpatialArea,
    SpatialAreaType,
    UserRole,
)
from rtls_api.positioning import PositioningService


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-operations-overview.db'}",
        redis_url="memory://operations-overview-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        positioning_recent_window_seconds=30,
        gateway_heartbeat_stale_after_seconds=60,
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


def seed_environment(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Salvador Flagship", timezone_name="America/Bahia")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Dining Hall A", level_label="L1")
        db.add(floor)
        db.flush()

        db.add(
            FloorPlanAsset(
                floor_id=floor.id,
                storage_key=f"floor-plans/{floor.id}/overview.png",
                original_filename="overview.png",
                mime_type="image/png",
                width_px=1280,
                height_px=720,
            )
        )

        db.add_all(
            [
                SpatialArea(
                    floor_id=floor.id,
                    name="Kitchen Pass",
                    area_type=SpatialAreaType.ZONE.value,
                    geometry=[
                        {"x": 0.1, "y": 0.1},
                        {"x": 0.35, "y": 0.1},
                        {"x": 0.35, "y": 0.35},
                        {"x": 0.1, "y": 0.35},
                    ],
                    sla_eligible=True,
                    alert_participation=True,
                ),
                SpatialArea(
                    floor_id=floor.id,
                    name="Cold Storage",
                    area_type=SpatialAreaType.RESTRICTED_ZONE.value,
                    geometry=[
                        {"x": 0.55, "y": 0.1},
                        {"x": 0.85, "y": 0.1},
                        {"x": 0.85, "y": 0.4},
                        {"x": 0.55, "y": 0.4},
                    ],
                    sla_eligible=False,
                    alert_participation=True,
                ),
            ]
        )

        db.add_all(
            [
                Gateway(
                    floor_id=floor.id,
                    gateway_identifier="gw-overview-01",
                    display_name="Dining Gateway 1",
                    hardware_tier="Economic",
                    placement_x=0.2,
                    placement_y=0.2,
                ),
                Gateway(
                    floor_id=floor.id,
                    gateway_identifier="gw-overview-02",
                    display_name="Dining Gateway 2",
                    hardware_tier="Economic",
                    placement_x=0.4,
                    placement_y=0.2,
                ),
                Gateway(
                    floor_id=floor.id,
                    gateway_identifier="gw-overview-03",
                    display_name="Cold Storage Gateway",
                    hardware_tier="Economic",
                    placement_x=0.7,
                    placement_y=0.2,
                ),
            ]
        )

        db.add_all(
            [
                AssetTag(
                    tag_identifier="TAG-OV-001",
                    display_name="Tray Cart 09",
                    asset_category="equipment",
                    update_rate_profile=AssetUpdateRateProfile.BALANCED.value,
                    battery_profile=AssetBatteryProfile.STANDARD.value,
                ),
                AssetTag(
                    tag_identifier="TAG-OV-002",
                    display_name="Waiter Tag 881",
                    asset_category="staff",
                    update_rate_profile=AssetUpdateRateProfile.REALTIME.value,
                    battery_profile=AssetBatteryProfile.PERFORMANCE.value,
                ),
            ]
        )
        db.commit()

        return {"site_id": site.id, "floor_id": floor.id}


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


def test_operations_overview_supports_general_users_and_returns_summary(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
                display_name="Alex",
            )
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        seeded = seed_environment(app)
        service = create_ingestion_service(app, settings)
        observed_at = datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc)

        publish_telemetry(
            service,
            gateway_identifier="gw-overview-01",
            message_id="msg-001",
            tag_identifier="TAG-OV-001",
            rssi=-62,
            broker_received_at=observed_at,
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-overview-03",
            message_id="msg-002",
            tag_identifier="TAG-OV-002",
            rssi=-67,
            broker_received_at=observed_at + timedelta(seconds=1),
        )

        with app.state.session_factory() as db:
            stale_gateway = db.scalar(
                select(Gateway).where(Gateway.gateway_identifier == "gw-overview-02")
            )
            assert stale_gateway is not None
            db.add(
                GatewayHeartbeat(
                    gateway_id=stale_gateway.id,
                    last_seen_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
                    message_id="hb-001",
                    firmware_version="1.2.3",
                    battery_level_percent=82,
                )
            )
            db.commit()

        user_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        response = client.get(
            "/api/operations/overview",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"site_id": seeded["site_id"], "floor_id": seeded["floor_id"]},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["site_id"] == seeded["site_id"]
        assert payload["floor_id"] == seeded["floor_id"]
        assert payload["feed_status"] == "degraded"
        assert payload["kpis"]["active_assets"] == 2
        assert payload["kpis"]["low_confidence_assets"] == 2
        assert payload["kpis"]["restricted_zone_assets"] == 1
        assert payload["kpis"]["stale_gateways"] == 1
        assert len(payload["priority_items"]) >= 2
        assert payload["priority_items"][0]["severity"] == "critical"
        assert payload["gateway_snapshot"][0]["gateway_identifier"] == "gw-overview-02"
        assert payload["map_preview"]["floor_plan"]["mime_type"] == "image/png"
        assert len(payload["map_preview"]["locations"]) == 2


def test_operations_overview_returns_empty_state_without_spatial_context(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        user_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        response = client.get(
            "/api/operations/overview",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["feed_status"] == "empty"
        assert payload["site_id"] is None
        assert payload["floor_id"] is None
        assert payload["priority_items"] == []
        assert payload["gateway_snapshot"] == []
        assert payload["map_preview"]["locations"] == []


def test_operations_overview_includes_alert_kpis(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        seeded = seed_environment(app)

        with app.state.session_factory() as db:
            db.add_all(
                [
                    AlertInstance(
                        rule_id="rule-c1",
                        rule_type="table_sla",
                        severity=AlertSeverity.CRITICAL.value,
                        status=AlertStatus.OPEN.value,
                        title="SLA breach Table 5",
                        summary="Table 5 exceeded 30min SLA",
                        scope_key="table:area-5",
                        scope_label="Table 5",
                        site_id=seeded["site_id"],
                        floor_id=seeded["floor_id"],
                        first_triggered_at=datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc),
                        last_triggered_at=datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc),
                    ),
                    AlertInstance(
                        rule_id="rule-w1",
                        rule_type="gateway_stale",
                        severity=AlertSeverity.WARNING.value,
                        status=AlertStatus.OPEN.value,
                        title="Gateway stale",
                        summary="Gateway 1 is stale",
                        scope_key="gateway:gw-1",
                        scope_label="GW 1",
                        site_id=seeded["site_id"],
                        floor_id=seeded["floor_id"],
                        first_triggered_at=datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc),
                        last_triggered_at=datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc),
                    ),
                    AlertInstance(
                        rule_id="rule-w2",
                        rule_type="gateway_stale",
                        severity=AlertSeverity.WARNING.value,
                        status=AlertStatus.RESOLVED.value,
                        title="Old warning",
                        summary="Already resolved",
                        scope_key="gateway:gw-2",
                        scope_label="GW 2",
                        site_id=seeded["site_id"],
                        floor_id=seeded["floor_id"],
                        first_triggered_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
                        last_triggered_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
                        resolved_at=datetime(2026, 3, 26, tzinfo=timezone.utc),
                    ),
                ]
            )
            db.commit()

        user_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        response = client.get(
            "/api/operations/overview",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"floor_id": seeded["floor_id"]},
        )

        assert response.status_code == 200
        kpis = response.json()["kpis"]
        assert kpis["alerts"]["total_active"] == 2
        assert kpis["alerts"]["critical"] == 1
        assert kpis["alerts"]["warning"] == 1


def test_operations_overview_includes_sla_kpis(tmp_path: Path) -> None:
    settings = build_settings(tmp_path, sla_threshold_seconds=600)
    app = create_app(settings)

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        seeded = seed_environment(app)
        now = datetime.now(timezone.utc)

        with app.state.session_factory() as db:
            tag = db.scalar(select(AssetTag).where(AssetTag.tag_identifier == "TAG-OV-001"))
            zone = db.scalar(select(SpatialArea).where(SpatialArea.name == "Kitchen Pass"))
            assert tag is not None and zone is not None

            db.add_all(
                [
                    DerivedZoneDwellRecord(
                        asset_tag_id=tag.id,
                        floor_id=seeded["floor_id"],
                        zone_id=zone.id,
                        started_at=now - timedelta(minutes=30),
                        ended_at=now - timedelta(minutes=25),
                        duration_seconds=300,
                        closure_reason="exit",
                    ),
                    DerivedZoneDwellRecord(
                        asset_tag_id=tag.id,
                        floor_id=seeded["floor_id"],
                        zone_id=zone.id,
                        started_at=now - timedelta(minutes=20),
                        ended_at=now - timedelta(minutes=10),
                        duration_seconds=700,
                        closure_reason="exit",
                    ),
                    DerivedZoneDwellRecord(
                        asset_tag_id=tag.id,
                        floor_id=seeded["floor_id"],
                        zone_id=zone.id,
                        started_at=now - timedelta(minutes=90),
                        ended_at=now - timedelta(minutes=70),
                        duration_seconds=1200,
                        closure_reason="exit",
                    ),
                ]
            )
            db.commit()

        user_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        response = client.get(
            "/api/operations/overview",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"floor_id": seeded["floor_id"]},
        )

        assert response.status_code == 200
        kpis = response.json()["kpis"]
        assert kpis["sla"]["breach_count"] == 1
        assert 40.0 <= kpis["sla"]["success_rate_pct"] <= 60.0
        assert kpis["sla"]["trend_pct"] is not None


def test_operations_overview_alert_kpis_default_zero(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        user_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        response = client.get(
            "/api/operations/overview",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        kpis = response.json()["kpis"]
        assert kpis["alerts"]["total_active"] == 0
        assert kpis["alerts"]["critical"] == 0
        assert kpis["alerts"]["warning"] == 0
        assert kpis["sla"]["breach_count"] == 0
        assert kpis["sla"]["success_rate_pct"] == 100.0
        assert kpis["sla"]["trend_pct"] is None
