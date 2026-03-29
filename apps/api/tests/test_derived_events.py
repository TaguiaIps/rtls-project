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
    AssetTag,
    AssetUpdateRateProfile,
    DerivedZoneDwellRecord,
    DerivedZoneTransitionEvent,
    Floor,
    FloorPlanAsset,
    Gateway,
    Site,
    SpatialArea,
    SpatialAreaType,
    TableServiceTimerState,
    UserRole,
)
from rtls_api.positioning import PositioningService


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-derived-events.db'}",
        redis_url="memory://derived-event-tests",
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


def seed_tracking_environment(app) -> dict[str, str]:
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
                storage_key=f"floor-plans/{floor.id}/derived.png",
                original_filename="derived.png",
                mime_type="image/png",
                width_px=1200,
                height_px=800,
            )
        )

        areas = [
            SpatialArea(
                floor_id=floor.id,
                name="Kitchen Pass",
                area_type=SpatialAreaType.ZONE.value,
                geometry=[
                    {"x": 0.05, "y": 0.05},
                    {"x": 0.25, "y": 0.05},
                    {"x": 0.25, "y": 0.3},
                    {"x": 0.05, "y": 0.3},
                ],
                sla_eligible=False,
                alert_participation=True,
            ),
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
                name="Dining Exit",
                area_type=SpatialAreaType.ZONE.value,
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
            ("gw-kitchen-01", "Kitchen Gateway 1", 0.1, 0.1),
            ("gw-kitchen-02", "Kitchen Gateway 2", 0.2, 0.2),
            ("gw-table-01", "Table Gateway 1", 0.4, 0.1),
            ("gw-table-02", "Table Gateway 2", 0.5, 0.2),
            ("gw-exit-01", "Exit Gateway 1", 0.7, 0.1),
            ("gw-exit-02", "Exit Gateway 2", 0.8, 0.2),
            ("gw-unknown-01", "Unknown Gateway 1", 0.9, 0.8),
            ("gw-unknown-02", "Unknown Gateway 2", 0.95, 0.9),
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
            "asset_tag_id": asset.id,
            "kitchen_zone_id": area_ids["Kitchen Pass"],
            "table_zone_id": area_ids["Table 12"],
            "exit_zone_id": area_ids["Dining Exit"],
        }


def test_zone_events_and_dwell_records_follow_transition_rules(tmp_path: Path) -> None:
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

        seeded = seed_tracking_environment(app)
        service = create_ingestion_service(app, settings)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        base_time = datetime(2026, 3, 26, 12, 0, 0, tzinfo=timezone.utc)

        publish_telemetry(
            service,
            gateway_identifier="gw-kitchen-01",
            message_id="msg-001",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time,
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-kitchen-02",
            message_id="msg-002",
            tag_identifier="TAG-001",
            rssi=-61,
            broker_received_at=base_time + timedelta(seconds=2),
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-exit-01",
            message_id="msg-003",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time + timedelta(seconds=4),
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-unknown-01",
            message_id="msg-004",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time + timedelta(seconds=6),
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-unknown-02",
            message_id="msg-005",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time + timedelta(seconds=6, milliseconds=200),
        )

        with app.state.session_factory() as db:
            events = db.scalars(select(DerivedZoneTransitionEvent)).all()
            dwells = db.scalars(
                select(DerivedZoneDwellRecord).order_by(DerivedZoneDwellRecord.started_at.asc())
            ).all()

        assert len(events) == 4
        assert len(dwells) == 2
        assert dwells[0].closure_reason == "zone_change"
        assert dwells[0].duration_seconds == approx(4.0)
        assert dwells[1].closure_reason == "resolved_placement_lost"
        assert dwells[1].duration_seconds == approx(2.2)

        events_response = client.get(
            "/api/derived/zone-events",
            headers={"Authorization": f"Bearer {token}"},
            params={"floor_id": seeded["floor_id"]},
        )
        assert events_response.status_code == 200
        events_payload = events_response.json()
        assert [event["event_type"] for event in events_payload] == [
            "entry",
            "exit",
            "entry",
            "exit",
        ]
        assert [event["zone_id"] for event in events_payload] == [
            seeded["kitchen_zone_id"],
            seeded["kitchen_zone_id"],
            seeded["exit_zone_id"],
            seeded["exit_zone_id"],
        ]

        dwells_response = client.get(
            "/api/derived/dwells",
            headers={"Authorization": f"Bearer {token}"},
            params={"asset_tag_id": seeded["asset_tag_id"]},
        )
        assert dwells_response.status_code == 200
        dwells_payload = dwells_response.json()
        assert [record["closure_reason"] for record in dwells_payload] == [
            "zone_change",
            "resolved_placement_lost",
        ]


def test_round_trip_measurements_are_evaluated_from_entry_events(tmp_path: Path) -> None:
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

        seeded = seed_tracking_environment(app)
        service = create_ingestion_service(app, settings)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        base_time = datetime(2026, 3, 26, 13, 0, 0, tzinfo=timezone.utc)

        publish_telemetry(
            service,
            gateway_identifier="gw-kitchen-01",
            message_id="msg-101",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time,
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-exit-01",
            message_id="msg-102",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time + timedelta(seconds=2),
        )
        publish_telemetry(
            service,
            gateway_identifier="gw-kitchen-02",
            message_id="msg-103",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time + timedelta(seconds=4),
        )

        response = client.get(
            "/api/derived/round-trips",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "origin_zone_id": seeded["kitchen_zone_id"],
                "destination_zone_id": seeded["exit_zone_id"],
                "asset_tag_id": seeded["asset_tag_id"],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["origin_zone_id"] == seeded["kitchen_zone_id"]
        assert payload[0]["destination_zone_id"] == seeded["exit_zone_id"]
        assert payload[0]["outbound_seconds"] == approx(2.0)
        assert payload[0]["return_seconds"] == approx(2.0)
        assert payload[0]["total_seconds"] == approx(4.0)


def test_table_timer_state_tracks_only_sla_eligible_tables(tmp_path: Path) -> None:
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

        seeded = seed_tracking_environment(app)
        service = create_ingestion_service(app, settings)
        token = issue_access_token(client, "ops@example.com", "StrongPass123")
        base_time = datetime(2026, 3, 26, 14, 0, 0, tzinfo=timezone.utc)

        publish_telemetry(
            service,
            gateway_identifier="gw-table-01",
            message_id="msg-201",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time,
        )

        active_response = client.get(
            "/api/derived/table-timers",
            headers={"Authorization": f"Bearer {token}"},
            params={"floor_id": seeded["floor_id"]},
        )
        assert active_response.status_code == 200
        active_payload = active_response.json()
        assert len(active_payload) == 1
        assert active_payload[0]["table_area_id"] == seeded["table_zone_id"]
        assert active_payload[0]["status"] == "active"
        assert active_payload[0]["active_visit_count"] == 1

        publish_telemetry(
            service,
            gateway_identifier="gw-exit-01",
            message_id="msg-202",
            tag_identifier="TAG-001",
            rssi=-60,
            broker_received_at=base_time + timedelta(seconds=4),
        )

        idle_response = client.get(
            "/api/derived/table-timers",
            headers={"Authorization": f"Bearer {token}"},
            params={"floor_id": seeded["floor_id"]},
        )
        assert idle_response.status_code == 200
        idle_payload = idle_response.json()
        assert len(idle_payload) == 1
        assert idle_payload[0]["status"] == "idle"
        assert idle_payload[0]["active_visit_count"] == 0
        assert idle_payload[0]["last_visit_duration_seconds"] == approx(4.0)

        with app.state.session_factory() as db:
            timer_states = db.scalars(select(TableServiceTimerState)).all()
        assert len(timer_states) == 1
