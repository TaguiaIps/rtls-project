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
    AlertAction,
    AlertNotificationDelivery,
    AlertRule,
    AlertStatus,
    AssetBatteryProfile,
    AssetTag,
    AssetUpdateRateProfile,
    AuditEvent,
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
        database_url=f"sqlite:///{tmp_path / 'rtls-alerts.db'}",
        redis_url="memory://alert-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        positioning_recent_window_seconds=1,
        **overrides,
    )


def create_ingestion_service(app, settings: Settings) -> TelemetryIngestionService:
    return TelemetryIngestionService(
        session_factory=app.state.session_factory,
        settings=settings,
        dedupe_store=app.state.message_dedupe_store,
        positioning_service=PositioningService(settings),
    )


def issue_access_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/token", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


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


def publish_gateway_pair(
    service: TelemetryIngestionService,
    *,
    gateway_identifiers: tuple[str, str],
    tag_identifier: str,
    message_prefix: str,
    observed_at: datetime,
) -> None:
    publish_telemetry(
        service,
        gateway_identifier=gateway_identifiers[0],
        message_id=f"{message_prefix}-1",
        tag_identifier=tag_identifier,
        rssi=-60,
        broker_received_at=observed_at,
    )
    publish_telemetry(
        service,
        gateway_identifier=gateway_identifiers[1],
        message_id=f"{message_prefix}-2",
        tag_identifier=tag_identifier,
        rssi=-61,
        broker_received_at=observed_at + timedelta(milliseconds=200),
    )


def seed_alert_environment(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Flagship Dining", timezone_name="America/Bahia")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Dining Hall", level_label="L1")
        db.add(floor)
        db.flush()

        db.add(
            FloorPlanAsset(
                floor_id=floor.id,
                storage_key=f"floor-plans/{floor.id}/alerts.png",
                original_filename="alerts.png",
                mime_type="image/png",
                width_px=1200,
                height_px=800,
            )
        )

        areas = [
            SpatialArea(
                floor_id=floor.id,
                name="Table 12",
                area_type=SpatialAreaType.TABLE.value,
                geometry=[
                    {"x": 0.35, "y": 0.05},
                    {"x": 0.55, "y": 0.05},
                    {"x": 0.55, "y": 0.3},
                    {"x": 0.35, "y": 0.3},
                ],
                sla_eligible=True,
                alert_participation=True,
            ),
            SpatialArea(
                floor_id=floor.id,
                name="Cold Storage",
                area_type=SpatialAreaType.RESTRICTED_ZONE.value,
                geometry=[
                    {"x": 0.65, "y": 0.05},
                    {"x": 0.85, "y": 0.05},
                    {"x": 0.85, "y": 0.3},
                    {"x": 0.65, "y": 0.3},
                ],
                sla_eligible=False,
                alert_participation=True,
            ),
        ]
        db.add_all(areas)
        db.flush()

        gateways = [
            ("gw-table-01", "Table Gateway 1", 0.4, 0.1),
            ("gw-table-02", "Table Gateway 2", 0.5, 0.2),
            ("gw-restricted-01", "Restricted Gateway 1", 0.7, 0.1),
            ("gw-restricted-02", "Restricted Gateway 2", 0.8, 0.2),
            ("gw-unknown-01", "Unknown Gateway 1", 0.93, 0.78),
            ("gw-unknown-02", "Unknown Gateway 2", 0.97, 0.86),
        ]
        for gateway_identifier, display_name, placement_x, placement_y in gateways:
            db.add(
                Gateway(
                    floor_id=floor.id,
                    gateway_identifier=gateway_identifier,
                    display_name=display_name,
                    hardware_tier="Economic",
                    placement_x=placement_x,
                    placement_y=placement_y,
                )
            )

        asset = AssetTag(
            tag_identifier="TAG-001",
            display_name="Waiter Tag 7",
            asset_category="staff",
            update_rate_profile=AssetUpdateRateProfile.REALTIME.value,
            battery_profile=AssetBatteryProfile.PERFORMANCE.value,
        )
        db.add(asset)
        db.commit()

        area_ids = {
            area.name: area.id
            for area in db.scalars(
                select(SpatialArea).where(SpatialArea.floor_id == floor.id)
            ).all()
        }
        return {
            "site_id": site.id,
            "floor_id": floor.id,
            "table_area_id": area_ids["Table 12"],
            "restricted_area_id": area_ids["Cold Storage"],
            "asset_tag_id": asset.id,
        }


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_alert_rule_validation_and_summary_queries(tmp_path: Path) -> None:
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

        seeded = seed_alert_environment(app)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")

        invalid_rule = client.post(
            "/api/alerts/rules",
            headers=auth_headers(token),
            json={
                "name": "Broken table rule",
                "rule_type": "table_sla",
                "enabled": True,
                "threshold_seconds": 60,
                "table_area_ids": [seeded["restricted_area_id"]],
                "notify_in_app": True,
                "notify_email": False,
                "email_recipients": [],
            },
        )
        assert invalid_rule.status_code == 422

        create_response = client.post(
            "/api/alerts/rules",
            headers=auth_headers(token),
            json={
                "name": "Dining Table SLA",
                "rule_type": "table_sla",
                "enabled": True,
                "threshold_seconds": 120,
                "table_area_ids": [seeded["table_area_id"]],
                "notify_in_app": True,
                "notify_email": False,
                "email_recipients": [],
            },
        )
        assert create_response.status_code == 200
        created_rule = create_response.json()
        assert created_rule["severity"] == "warning"
        assert created_rule["config"]["table_area_ids"] == [seeded["table_area_id"]]

        rules_response = client.get(
            f"/api/alerts/rules?floor_id={seeded['floor_id']}",
            headers=auth_headers(token),
        )
        assert rules_response.status_code == 200
        assert len(rules_response.json()) == 1

        summary_response = client.get(
            f"/api/alerts/summary?floor_id={seeded['floor_id']}",
            headers=auth_headers(token),
        )
        assert summary_response.status_code == 200
        assert summary_response.json()["unresolved_count"] == 0


def test_alert_summary_and_list_include_gateway_maintenance_alerts(tmp_path: Path) -> None:
    settings = build_settings(tmp_path, gateway_heartbeat_stale_after_seconds=60)
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

        seeded = seed_alert_environment(app)
        now = datetime.now(timezone.utc)
        with app.state.session_factory() as db:
            gateways = {
                gateway.gateway_identifier: gateway
                for gateway in db.scalars(select(Gateway)).all()
            }
            db.add_all(
                [
                    GatewayHeartbeat(
                        gateway_id=gateways["gw-table-01"].id,
                        last_seen_at=now - timedelta(minutes=5),
                        message_id="hb-stale-01",
                        firmware_version="1.0.0",
                        battery_level_percent=9,
                    ),
                    GatewayHeartbeat(
                        gateway_id=gateways["gw-table-02"].id,
                        last_seen_at=now,
                        message_id="hb-healthy-01",
                        firmware_version="1.0.0",
                        battery_level_percent=82,
                    ),
                ]
            )
            db.commit()

        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        summary_response = client.get(
            "/api/alerts/summary",
            headers=auth_headers(token),
            params={"floor_id": seeded["floor_id"]},
        )
        assert summary_response.status_code == 200
        assert summary_response.json()["active_critical_count"] == 1
        assert summary_response.json()["active_warning_count"] == 1

        list_response = client.get(
            "/api/alerts",
            headers=auth_headers(token),
            params={"floor_id": seeded["floor_id"]},
        )
        assert list_response.status_code == 200
        rule_types = {item["rule_type"] for item in list_response.json()}
        assert "gateway_stale" in rule_types
        assert "gateway_low_battery" in rule_types


def test_table_sla_alerts_deduplicate_and_clear(tmp_path: Path) -> None:
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

        seeded = seed_alert_environment(app)
        service = create_ingestion_service(app, settings)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        base_time = datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc)

        create_rule = client.post(
            "/api/alerts/rules",
            headers=auth_headers(token),
            json={
                "name": "Dining Table SLA",
                "rule_type": "table_sla",
                "enabled": True,
                "threshold_seconds": 2,
                "table_area_ids": [seeded["table_area_id"]],
                "notify_in_app": True,
                "notify_email": False,
                "email_recipients": [],
            },
        )
        assert create_rule.status_code == 200

        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-table-01", "gw-table-02"),
            tag_identifier="TAG-001",
            message_prefix="table-start",
            observed_at=base_time,
        )
        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-table-01", "gw-table-02"),
            tag_identifier="TAG-001",
            message_prefix="table-threshold",
            observed_at=base_time + timedelta(seconds=3),
        )
        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-table-01", "gw-table-02"),
            tag_identifier="TAG-001",
            message_prefix="table-repeat",
            observed_at=base_time + timedelta(seconds=5),
        )
        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-unknown-01", "gw-unknown-02"),
            tag_identifier="TAG-001",
            message_prefix="table-clear",
            observed_at=base_time + timedelta(seconds=7),
        )

        alerts_response = client.get(
            f"/api/alerts?floor_id={seeded['floor_id']}",
            headers=auth_headers(token),
        )
        assert alerts_response.status_code == 200
        alerts = alerts_response.json()
        assert len(alerts) == 1
        assert alerts[0]["status"] == AlertStatus.CLEARED.value

        with app.state.session_factory() as db:
            alert = db.scalar(select(AlertRule))
            assert alert is not None
            instances = db.scalars(select(AlertNotificationDelivery)).all()
            assert len(instances) == 1
            actions = db.scalars(select(AlertAction).order_by(AlertAction.created_at.asc())).all()
            assert [action.action_type for action in actions] == ["triggered", "cleared"]


def test_geofence_alerts_support_triage_actions_and_audit(tmp_path: Path) -> None:
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

        seeded = seed_alert_environment(app)
        service = create_ingestion_service(app, settings)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        base_time = datetime(2026, 3, 26, 13, 0, 0, tzinfo=timezone.utc)

        create_rule = client.post(
            "/api/alerts/rules",
            headers=auth_headers(token),
            json={
                "name": "Restricted Entry",
                "rule_type": "unauthorized_geofence",
                "enabled": True,
                "area_ids": [seeded["restricted_area_id"]],
                "trigger_on": "entry",
                "asset_category": "staff",
                "notify_in_app": True,
                "notify_email": False,
                "email_recipients": [],
            },
        )
        assert create_rule.status_code == 200

        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-restricted-01", "gw-restricted-02"),
            tag_identifier="TAG-001",
            message_prefix="restricted-entry",
            observed_at=base_time,
        )
        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-restricted-01", "gw-restricted-02"),
            tag_identifier="TAG-001",
            message_prefix="restricted-repeat",
            observed_at=base_time + timedelta(seconds=2),
        )

        alerts_response = client.get(
            f"/api/alerts?floor_id={seeded['floor_id']}&status_value=open",
            headers=auth_headers(token),
        )
        assert alerts_response.status_code == 200
        alerts = alerts_response.json()
        assert len(alerts) == 1
        alert_id = alerts[0]["id"]

        acknowledge_response = client.post(
            f"/api/alerts/{alert_id}/acknowledge",
            headers=auth_headers(token),
            json={"notes": "Investigating with floor lead"},
        )
        assert acknowledge_response.status_code == 200
        assert acknowledge_response.json()["status"] == "acknowledged"

        resolve_response = client.post(
            f"/api/alerts/{alert_id}/resolve",
            headers=auth_headers(token),
            json={"notes": "Asset escorted out"},
        )
        assert resolve_response.status_code == 200
        resolved_alert = resolve_response.json()
        assert resolved_alert["status"] == "resolved"
        assert [action["action_type"] for action in resolved_alert["actions"]] == [
            "triggered",
            "acknowledged",
            "resolved",
        ]

        with app.state.session_factory() as db:
            audit_types = [
                event.action_type
                for event in db.scalars(
                    select(AuditEvent).order_by(AuditEvent.created_at.asc())
                ).all()
            ]
            assert "alert.rule.created" in audit_types
            assert "alert.instance.acknowledged" in audit_types
            assert "alert.instance.resolved" in audit_types


def test_email_delivery_attempts_are_recorded(tmp_path: Path, monkeypatch) -> None:
    settings = build_settings(
        tmp_path,
        smtp_host="smtp.test",
        alert_email_from_address="alerts@example.com",
    )
    app = create_app(settings)

    sent_messages: list[str] = []

    def fake_send_email(*, settings: Settings, message) -> None:
        sent_messages.append(str(message["To"]))

    monkeypatch.setattr("rtls_api.alerts._send_email_message", fake_send_email)

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

        seeded = seed_alert_environment(app)
        service = create_ingestion_service(app, settings)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        base_time = datetime(2026, 3, 26, 14, 0, 0, tzinfo=timezone.utc)

        create_rule = client.post(
            "/api/alerts/rules",
            headers=auth_headers(token),
            json={
                "name": "Restricted Entry Email",
                "rule_type": "unauthorized_geofence",
                "enabled": True,
                "area_ids": [seeded["restricted_area_id"]],
                "trigger_on": "entry",
                "notify_in_app": True,
                "notify_email": True,
                "email_recipients": ["ops@example.com"],
            },
        )
        assert create_rule.status_code == 200

        publish_gateway_pair(
            service,
            gateway_identifiers=("gw-restricted-01", "gw-restricted-02"),
            tag_identifier="TAG-001",
            message_prefix="restricted-email",
            observed_at=base_time,
        )

        with app.state.session_factory() as db:
            deliveries = db.scalars(
                select(AlertNotificationDelivery).order_by(AlertNotificationDelivery.created_at.asc())
            ).all()
            assert [delivery.channel for delivery in deliveries] == ["in_app", "email"]
            assert deliveries[1].status == "delivered"
            assert sent_messages == ["ops@example.com"]
