from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.data_lifecycle import run_data_lifecycle_job
from rtls_api.main import create_app
from rtls_api.models import (
    AlertInstance,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    AssetBatteryProfile,
    AssetTag,
    AssetUpdateRateProfile,
    AuditEvent,
    Floor,
    Gateway,
    GatewayHeartbeat,
    PremiumRawMeasurement,
    RawReading,
    Site,
    UserRole,
)


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-observability.db'}",
        redis_url="memory://observability-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        gateway_heartbeat_stale_after_seconds=60,
    )


def issue_access_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/token", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def seed_observability_state(app) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    with app.state.session_factory() as db:
        site = Site(name="Salvador Flagship", timezone_name="America/Bahia")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Dining Hall A", level_label="L1")
        db.add(floor)
        db.flush()

        healthy_gateway = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-health-01",
            display_name="North Dining Gateway",
            hardware_tier="Economic",
            placement_x=0.2,
            placement_y=0.2,
        )
        stale_gateway = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-health-02",
            display_name="South Dining Gateway",
            hardware_tier="Economic",
            placement_x=0.6,
            placement_y=0.2,
        )
        silent_gateway = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-health-03",
            display_name="Kitchen Gateway",
            hardware_tier="Premium",
            placement_x=0.8,
            placement_y=0.4,
        )
        db.add_all([healthy_gateway, stale_gateway, silent_gateway])

        asset = AssetTag(
            tag_identifier="TAG-HEALTH-001",
            display_name="Tray Cart 12",
            asset_category="equipment",
            update_rate_profile=AssetUpdateRateProfile.BALANCED.value,
            battery_profile=AssetBatteryProfile.STANDARD.value,
        )
        db.add(asset)
        db.flush()

        db.add_all(
            [
                GatewayHeartbeat(
                    gateway_id=healthy_gateway.id,
                    last_seen_at=now,
                    message_id="hb-healthy",
                    firmware_version="1.0.0",
                    battery_level_percent=88,
                ),
                GatewayHeartbeat(
                    gateway_id=stale_gateway.id,
                    last_seen_at=now - timedelta(minutes=5),
                    message_id="hb-stale",
                    firmware_version="1.0.1",
                    battery_level_percent=9,
                ),
            ]
        )
        db.add(
            RawReading(
                gateway_id=healthy_gateway.id,
                asset_tag_id=asset.id,
                tag_identifier=asset.tag_identifier,
                message_id="reading-001",
                broker_received_at=now,
                gateway_timestamp=now,
                firmware_version="1.0.0",
                rssi=-61,
                tx_power=-4,
                channel=37,
            )
        )
        db.add(
            PremiumRawMeasurement(
                gateway_id=silent_gateway.id,
                asset_tag_id=asset.id,
                tag_identifier=asset.tag_identifier,
                message_id="premium-001",
                sequence_id="seq-001",
                broker_received_at=now,
                gateway_timestamp=now,
                firmware_version="2.0.0",
                modality="UWB",
                quality_score=0.93,
                azimuth_degrees=13.0,
                elevation_degrees=2.5,
                distance_m=4.1,
            )
        )

        rule = AlertRule(
            name="Gateway Stale Warning",
            rule_type="unauthorized_geofence",
            severity=AlertSeverity.CRITICAL.value,
            enabled=True,
            site_id=site.id,
            floor_id=floor.id,
            config={"area_ids": [], "trigger_on": "entry", "asset_category": None},
            delivery={"in_app": True, "email": False, "email_recipients": []},
        )
        db.add(rule)
        db.flush()

        db.add(
            AlertInstance(
                rule_id=rule.id,
                rule_type=rule.rule_type,
                severity=rule.severity,
                status=AlertStatus.OPEN.value,
                title="Gateway stale",
                summary="South Dining Gateway is stale.",
                scope_key=f"gateway:{stale_gateway.id}",
                scope_label=stale_gateway.display_name,
                site_id=site.id,
                floor_id=floor.id,
                area_id=None,
                asset_tag_id=None,
                condition_key="heartbeat",
                context_payload={"gateway_id": stale_gateway.id},
                first_triggered_at=now - timedelta(minutes=4),
                last_triggered_at=now - timedelta(minutes=1),
            )
        )

        db.add_all(
            [
                AuditEvent(
                    actor_email="admin@example.com",
                    actor_role=UserRole.ADMINISTRATOR.value,
                    action_category="configuration",
                    action_type="admin.gateway.updated",
                    target_type="gateway",
                    target_id=stale_gateway.id,
                    details={"field": "display_name"},
                    created_at=now - timedelta(hours=2),
                ),
                AuditEvent(
                    actor_email="admin@example.com",
                    actor_role=UserRole.ADMINISTRATOR.value,
                    action_category="security",
                    action_type="auth.login.success",
                    target_type="refresh_session",
                    target_id="session-001",
                    details={"ip": "127.0.0.1"},
                    created_at=now - timedelta(minutes=15),
                ),
            ]
        )
        db.commit()

        return {
            "floor_id": floor.id,
            "healthy_gateway_id": healthy_gateway.id,
            "silent_gateway_id": silent_gateway.id,
            "stale_gateway_id": stale_gateway.id,
        }


def test_observability_summary_returns_health_and_audit_totals(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
                display_name="Alex",
            )
            db.commit()

        seeded = seed_observability_state(app)
        access_token = issue_access_token(client, "admin@example.com", "StrongPass123")

        response = client.get(
            "/api/admin/observability/summary",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["gateway_totals"] == {
        "total": 3,
        "healthy": 1,
        "stale": 2,
        "low_battery": 1,
        "without_heartbeat": 1,
    }
    assert payload["telemetry_totals"] == {
        "raw_readings": 1,
        "premium_measurements": 1,
        "heartbeat_snapshots": 2,
    }
    assert payload["alert_totals"] == {"active": 1, "critical": 1, "warning": 0}
    assert payload["audit_totals"]["total"] >= 3
    assert payload["audit_totals"]["last_24h"] >= 3
    assert payload["lifecycle"]["policies"] == {
        "raw_readings_days": 90,
        "premium_measurements_days": 90,
        "location_history_days": 30,
        "exports_days": 7,
    }
    assert payload["lifecycle"]["latest_run"] is None
    assert payload["metrics_path"] == "/metrics"
    assert payload["request_id_header"] == "X-Request-ID"
    assert len(payload["services"]) == 7
    risk_gateway_ids = {item["gateway_id"] for item in payload["risk_items"]}
    assert seeded["silent_gateway_id"] in risk_gateway_ids
    assert seeded["stale_gateway_id"] in risk_gateway_ids


def test_audit_events_support_filtering_and_admin_protection(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

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
                display_name="Casey",
            )
            db.commit()

        seeded = seed_observability_state(app)
        general_token = issue_access_token(client, "ops@example.com", "StrongPass123")
        denied = client.get(
            "/api/admin/audit-events",
            headers={"Authorization": f"Bearer {general_token}"},
        )
        assert denied.status_code == 403

        admin_token = issue_access_token(client, "admin@example.com", "StrongPass123")
        response = client.get(
            "/api/admin/audit-events",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "actor_email": "admin@",
                "action_category": "configuration",
                "target_type": "gateway",
                "target_id": seeded["stale_gateway_id"],
                "limit": 10,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] == 1
    assert payload["items"][0]["action_type"] == "admin.gateway.updated"
    assert payload["items"][0]["target_id"] == seeded["stale_gateway_id"]


def test_metrics_and_request_id_headers_are_exposed(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
                display_name="Alex",
            )
            db.commit()

        seed_observability_state(app)

        metrics_response = client.get("/metrics", headers={"X-Request-ID": "req-123"})
        health_response = client.get("/health")

    assert metrics_response.status_code == 200
    assert metrics_response.headers["X-Request-ID"] == "req-123"
    assert "rtls_gateways_total 3" in metrics_response.text
    assert "rtls_gateways_stale_total 2" in metrics_response.text
    assert "rtls_request_id_header_enabled 1" in metrics_response.text
    assert health_response.headers["X-Request-ID"]


def test_admin_can_trigger_lifecycle_run_and_summary_exposes_latest_run(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
                display_name="Alex",
            )
            db.commit()

        seed_observability_state(app)
        access_token = issue_access_token(client, "admin@example.com", "StrongPass123")

        trigger_response = client.post(
            "/api/admin/observability/lifecycle-runs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert trigger_response.status_code == 200
        trigger_payload = trigger_response.json()
        assert trigger_payload["status"] == "pending"

        run_data_lifecycle_job(
            app.state.session_factory,
            app.state.settings,
            trigger_payload["id"],
        )

        run_detail_response = client.get(
            "/api/admin/observability/summary",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert run_detail_response.status_code == 200
        latest_run = run_detail_response.json()["lifecycle"]["latest_run"]
        assert latest_run["id"] == trigger_payload["id"]
        assert latest_run["status"] == "completed"
        assert latest_run["retention_summary"] == {
            "raw_readings_deleted": 0,
            "premium_measurements_deleted": 0,
            "location_history_deleted": 0,
            "export_jobs_deleted": 0,
            "export_files_deleted": 0,
        }
        assert latest_run["rollup_summary"] == {
            "heatmap_rollups_refreshed": 0,
            "sla_rollups_refreshed": 0,
        }
