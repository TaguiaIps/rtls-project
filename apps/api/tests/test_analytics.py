from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.main import create_app
from rtls_api.models import (
    AlertRule,
    AlertRuleType,
    AlertSeverity,
    AssetBatteryProfile,
    AssetLocationHistory,
    AssetLocationType,
    AssetTag,
    AssetUpdateRateProfile,
    DerivedZoneDwellRecord,
    DerivedZoneEventType,
    DerivedZoneTransitionEvent,
    DwellClosureReason,
    Floor,
    Site,
    SpatialArea,
    SpatialAreaType,
    TableServiceTimerState,
    TableServiceTimerStatus,
    UserRole,
)


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-analytics.db'}",
        redis_url="memory://analytics-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        **overrides,
    )


def issue_access_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/token", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def seed_analytics_environment(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Salvador Flagship", timezone_name="America/Bahia")
        db.add(site)
        db.flush()

        floor = Floor(site_id=site.id, name="Dining Hall A", level_label="L1")
        db.add(floor)
        db.flush()

        kitchen = SpatialArea(
            floor_id=floor.id,
            name="Kitchen Pass",
            area_type=SpatialAreaType.ZONE.value,
            geometry=[
                {"x": 0.1, "y": 0.1},
                {"x": 0.35, "y": 0.1},
                {"x": 0.35, "y": 0.35},
                {"x": 0.1, "y": 0.35},
            ],
            sla_eligible=False,
            alert_participation=True,
        )
        dining = SpatialArea(
            floor_id=floor.id,
            name="Dining Hall",
            area_type=SpatialAreaType.ZONE.value,
            geometry=[
                {"x": 0.5, "y": 0.1},
                {"x": 0.85, "y": 0.1},
                {"x": 0.85, "y": 0.45},
                {"x": 0.5, "y": 0.45},
            ],
            sla_eligible=False,
            alert_participation=True,
        )
        table = SpatialArea(
            floor_id=floor.id,
            name="Table 12",
            area_type=SpatialAreaType.TABLE.value,
            geometry=[
                {"x": 0.3, "y": 0.55},
                {"x": 0.4, "y": 0.55},
                {"x": 0.4, "y": 0.7},
                {"x": 0.3, "y": 0.7},
            ],
            sla_eligible=True,
            alert_participation=True,
        )
        db.add_all([kitchen, dining, table])
        db.flush()

        waiter = AssetTag(
            tag_identifier="TAG-881",
            display_name="Waiter Tag 881",
            asset_category="staff",
            update_rate_profile=AssetUpdateRateProfile.REALTIME.value,
            battery_profile=AssetBatteryProfile.PERFORMANCE.value,
        )
        cart = AssetTag(
            tag_identifier="TAG-440",
            display_name="Tray Cart 09",
            asset_category="equipment",
            update_rate_profile=AssetUpdateRateProfile.BALANCED.value,
            battery_profile=AssetBatteryProfile.STANDARD.value,
        )
        db.add_all([waiter, cart])
        db.flush()

        base = datetime(2026, 3, 29, 12, 0, 0, tzinfo=timezone.utc)
        db.add_all(
            [
                AssetLocationHistory(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=kitchen.id,
                    observed_at=base,
                    location_type=AssetLocationType.POINT.value,
                    coordinate_x=0.2,
                    coordinate_y=0.2,
                    confidence_level="high",
                    confidence_score=0.91,
                    source_gateway_count=3,
                    source_reading_count=3,
                ),
                AssetLocationHistory(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=dining.id,
                    observed_at=base + timedelta(minutes=5),
                    location_type=AssetLocationType.POINT.value,
                    coordinate_x=0.65,
                    coordinate_y=0.2,
                    confidence_level="high",
                    confidence_score=0.88,
                    source_gateway_count=3,
                    source_reading_count=3,
                ),
                AssetLocationHistory(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=kitchen.id,
                    observed_at=base + timedelta(minutes=10),
                    location_type=AssetLocationType.POINT.value,
                    coordinate_x=0.22,
                    coordinate_y=0.24,
                    confidence_level="medium",
                    confidence_score=0.7,
                    source_gateway_count=2,
                    source_reading_count=2,
                ),
                AssetLocationHistory(
                    asset_tag_id=cart.id,
                    floor_id=floor.id,
                    zone_id=table.id,
                    observed_at=base + timedelta(minutes=12),
                    location_type=AssetLocationType.POINT.value,
                    coordinate_x=0.34,
                    coordinate_y=0.62,
                    confidence_level="medium",
                    confidence_score=0.72,
                    source_gateway_count=2,
                    source_reading_count=2,
                ),
            ]
        )

        db.add_all(
            [
                DerivedZoneTransitionEvent(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=kitchen.id,
                    observed_at=base,
                    event_type=DerivedZoneEventType.ENTRY.value,
                    transition_boundary_id="boundary-1",
                ),
                DerivedZoneTransitionEvent(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=dining.id,
                    observed_at=base + timedelta(minutes=5),
                    event_type=DerivedZoneEventType.ENTRY.value,
                    transition_boundary_id="boundary-2",
                ),
                DerivedZoneTransitionEvent(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=kitchen.id,
                    observed_at=base + timedelta(minutes=10),
                    event_type=DerivedZoneEventType.ENTRY.value,
                    transition_boundary_id="boundary-3",
                ),
                DerivedZoneDwellRecord(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=dining.id,
                    started_at=base + timedelta(minutes=5),
                    ended_at=base + timedelta(minutes=10),
                    duration_seconds=300.0,
                    closure_reason=DwellClosureReason.ZONE_CHANGE.value,
                ),
                DerivedZoneDwellRecord(
                    asset_tag_id=waiter.id,
                    floor_id=floor.id,
                    zone_id=table.id,
                    started_at=base + timedelta(minutes=15),
                    ended_at=base + timedelta(minutes=27),
                    duration_seconds=720.0,
                    closure_reason=DwellClosureReason.ZONE_CHANGE.value,
                ),
                TableServiceTimerState(
                    table_area_id=table.id,
                    floor_id=floor.id,
                    status=TableServiceTimerStatus.IDLE.value,
                    active_visit_count=0,
                    last_entry_at=base + timedelta(minutes=15),
                    last_exit_at=base + timedelta(minutes=27),
                    last_visit_started_at=base + timedelta(minutes=15),
                    last_visit_ended_at=base + timedelta(minutes=27),
                    last_visit_duration_seconds=720.0,
                ),
                AlertRule(
                    name="Dining Table SLA",
                    rule_type=AlertRuleType.TABLE_SLA.value,
                    severity=AlertSeverity.WARNING.value,
                    enabled=True,
                    site_id=site.id,
                    floor_id=floor.id,
                    config={
                        "threshold_seconds": 600,
                        "table_area_ids": [table.id],
                    },
                    delivery={"in_app": True, "email": False, "email_recipients": []},
                ),
            ]
        )
        db.commit()

        return {
            "site_id": site.id,
            "floor_id": floor.id,
            "kitchen_id": kitchen.id,
            "dining_id": dining.id,
            "table_id": table.id,
            "waiter_id": waiter.id,
        }


def test_analytics_endpoints_require_auth_and_validate_bounds(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        seeded = seed_analytics_environment(app)
        response = client.get(
            "/api/analytics/trajectory",
            params={
                "asset_tag_id": seeded["waiter_id"],
                "floor_id": seeded["floor_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T13:00:00Z",
            },
        )
        assert response.status_code == 401

        with app.state.session_factory() as db:
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()

        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        heatmap_response = client.get(
            "/api/analytics/heatmap",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "start_at": "2026-03-28T00:00:00Z",
                "end_at": "2026-03-29T12:00:00Z",
            },
        )
        assert heatmap_response.status_code == 422

        sla_response = client.get(
            "/api/analytics/sla-trends",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "table_area_id": seeded["table_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T13:00:00Z",
                "bucket_minutes": 30,
            },
        )
        assert sla_response.status_code == 422


def test_trajectory_and_heatmap_reports_return_history_and_density(tmp_path: Path) -> None:
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
        seeded = seed_analytics_environment(app)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")

        trajectory_response = client.get(
            "/api/analytics/trajectory",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "asset_tag_id": seeded["waiter_id"],
                "floor_id": seeded["floor_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T12:20:00Z",
            },
        )
        assert trajectory_response.status_code == 200
        trajectory_payload = trajectory_response.json()
        assert trajectory_payload["asset_tag_id"] == seeded["waiter_id"]
        assert len(trajectory_payload["points"]) == 3

        heatmap_response = client.get(
            "/api/analytics/heatmap",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T12:20:00Z",
            },
        )
        assert heatmap_response.status_code == 200
        heatmap_payload = heatmap_response.json()
        assert heatmap_payload["total_samples"] == 4
        assert heatmap_payload["max_density"] >= 1
        assert len(heatmap_payload["cells"]) >= 2


def test_dwell_and_round_trip_reports_use_derived_events(tmp_path: Path) -> None:
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
        seeded = seed_analytics_environment(app)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")

        dwell_response = client.get(
            "/api/analytics/dwells",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "zone_id": seeded["dining_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T12:20:00Z",
            },
        )
        assert dwell_response.status_code == 200
        dwell_payload = dwell_response.json()
        assert dwell_payload["summary"]["sample_count"] == 1
        assert dwell_payload["records"][0]["zone_id"] == seeded["dining_id"]

        round_trip_response = client.get(
            "/api/analytics/round-trips",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "origin_zone_id": seeded["kitchen_id"],
                "destination_zone_id": seeded["dining_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T12:20:00Z",
            },
        )
        assert round_trip_response.status_code == 200
        round_trip_payload = round_trip_response.json()
        assert round_trip_payload["summary"]["sample_count"] == 1
        assert round_trip_payload["records"][0]["origin_zone_id"] == seeded["kitchen_id"]


def test_sla_trends_use_alert_rule_thresholds_and_return_empty_buckets(tmp_path: Path) -> None:
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
        seeded = seed_analytics_environment(app)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")

        trend_response = client.get(
            "/api/analytics/sla-trends",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "table_area_id": seeded["table_id"],
                "start_at": "2026-03-29T12:00:00Z",
                "end_at": "2026-03-29T13:00:00Z",
                "bucket_minutes": 60,
            },
        )
        assert trend_response.status_code == 200
        trend_payload = trend_response.json()
        assert trend_payload["threshold_source"] == "alert_rule"
        assert trend_payload["threshold_seconds"] == 600
        assert trend_payload["current_timer"]["table_area_id"] == seeded["table_id"]
        assert trend_payload["buckets"][0]["breach_count"] == 1

        empty_response = client.get(
            "/api/analytics/sla-trends",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "floor_id": seeded["floor_id"],
                "table_area_id": seeded["table_id"],
                "start_at": "2026-03-29T14:00:00Z",
                "end_at": "2026-03-29T15:00:00Z",
                "bucket_minutes": 60,
            },
        )
        assert empty_response.status_code == 200
        empty_payload = empty_response.json()
        assert empty_payload["threshold_source"] == "alert_rule"
        assert all(bucket["completed_visit_count"] == 0 for bucket in empty_payload["buckets"])
