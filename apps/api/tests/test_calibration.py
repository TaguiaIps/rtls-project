from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from rtls_api.calibration_engine import (
    _calculate_coverage_score,
    _calculate_gateway_offsets,
    _generate_radiomap_grid,
    process_calibration_session,
)
from rtls_api.config import Settings
from rtls_api.main import create_app
from rtls_api.models import (
    CalibrationArtifact,
    CalibrationArtifactStatus,
    CalibrationSession,
    CalibrationSessionStatus,
    Floor,
    Gateway,
    Site,
)


def build_settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-calibration.db'}",
        redis_url="memory://calibration-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
        **overrides,
    )


def seed_floor_with_gateway(app) -> tuple[str, str, str]:
    with app.state.session_factory() as db:
        site = Site(name="Calibration Test Site")
        db.add(site)
        db.flush()
        floor = Floor(site_id=site.id, name="Test Floor")
        db.add(floor)
        db.flush()
        gateway = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-cal-01",
            display_name="Cal Gateway",
            hardware_tier="Premium",
            placement_x=0.5,
            placement_y=0.5,
        )
        db.add(gateway)
        db.commit()
        return site.id, floor.id, gateway.id


def test_submit_calibration_session_and_list_artifacts(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app):
        _, floor_id, gw_id = seed_floor_with_gateway(app)

        payload = {
            "floor_id": floor_id,
            "samples": [
                {
                    "checkpoint_x": 0.2,
                    "checkpoint_y": 0.3,
                    "gateway_id": gw_id,
                    "rssi": -60,
                },
                {
                    "checkpoint_x": 0.5,
                    "checkpoint_y": 0.5,
                    "gateway_id": gw_id,
                    "rssi": -45,
                },
                {
                    "checkpoint_x": 0.8,
                    "checkpoint_y": 0.7,
                    "gateway_id": gw_id,
                    "rssi": -55,
                },
            ],
        }

        from rtls_api.auth import create_user

        with app.state.session_factory() as db:
            create_user(
                db,
                email="admin@test.com",
                password="AdminPass123",
                role="Administrator",
                display_name="Admin",
            )
            db.commit()

        response = TestClient(app).post(
            "/api/auth/token",
            json={"email": "admin@test.com", "password": "AdminPass123"},
        )
        token = response.json()["access_token"]

        response = TestClient(app).post(
            "/api/admin/calibration/sessions",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["checkpoint_count"] == 3
        assert data["sample_count"] == 3


def test_calibration_health_endpoint(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app):
        _, floor_id, _ = seed_floor_with_gateway(app)

        response = TestClient(app).get(f"/api/admin/floors/{floor_id}/calibration/health")
        assert response.status_code == 200
        data = response.json()
        assert data["floor_id"] == floor_id
        assert data["has_active_calibration"] is False
        assert data["total_sessions"] == 0


def test_calibration_processing_generates_artifact(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with app.state.session_factory() as db:
        site = Site(name="Processing Test")
        db.add(site)
        db.flush()
        floor = Floor(site_id=site.id, name="Proc Floor")
        db.add(floor)
        db.flush()
        gw = Gateway(
            floor_id=floor.id,
            gateway_identifier="gw-proc-01",
            display_name="Proc GW",
            hardware_tier="Premium",
            placement_x=0.5,
            placement_y=0.5,
        )
        db.add(gw)
        db.commit()

        session = CalibrationSession(
            floor_id=floor.id,
            status=CalibrationSessionStatus.PENDING.value,
            checkpoint_count=2,
            sample_count=4,
            raw_samples={
                "checkpoints": [
                    {
                        "x": 0.2,
                        "y": 0.3,
                        "readings": [
                            {"gateway_id": gw.id, "rssi": -60},
                            {"gateway_id": gw.id, "rssi": -62},
                        ],
                    },
                    {
                        "x": 0.7,
                        "y": 0.8,
                        "readings": [
                            {"gateway_id": gw.id, "rssi": -48},
                            {"gateway_id": gw.id, "rssi": -50},
                        ],
                    },
                ]
            },
        )
        db.add(session)
        db.flush()
        session_id = session.id

    mock_storage = MagicMock()
    mock_storage.put_object = MagicMock()

    process_calibration_session(
        db_session=app.state.session_factory(),
        session_id=session_id,
        settings=settings,
        storage=mock_storage,
    )

    with app.state.session_factory() as db:
        session = db.get(CalibrationSession, session_id)
        assert session.status == CalibrationSessionStatus.COMPLETED.value
        assert session.artifact_id is not None

        artifact = db.get(CalibrationArtifact, session.artifact_id)
        assert artifact is not None
        assert artifact.floor_id == floor.id
        assert artifact.version == 1
        assert artifact.coverage_score is not None
        assert artifact.coverage_score > 0
        assert artifact.gateway_offsets is not None
        assert gw.id in artifact.gateway_offsets


def test_radiomap_grid_generation() -> None:
    checkpoints = [
        {"x": 0.0, "y": 0.0, "readings": [{"gateway_id": "gw1", "rssi": -50}]},
        {"x": 1.0, "y": 1.0, "readings": [{"gateway_id": "gw1", "rssi": -70}]},
    ]
    gateways = {"gw1": MagicMock(placement_x=0.5, placement_y=0.5)}

    radiomap, cols, rows = _generate_radiomap_grid(
        checkpoints=checkpoints, gateways=gateways, grid_resolution_m=0.5
    )
    assert "gw1" in radiomap
    assert cols > 0
    assert rows > 0


def test_gateway_offset_calculation() -> None:
    checkpoints = [
        {"x": 0.0, "y": 0.0, "readings": [{"gateway_id": "gw1", "rssi": -60}]},
        {"x": 1.0, "y": 0.0, "readings": [{"gateway_id": "gw1", "rssi": -50}]},
    ]
    gateways = {"gw1": MagicMock(placement_x=0.5, placement_y=0.5)}

    offsets = _calculate_gateway_offsets(checkpoints=checkpoints, gateways=gateways)
    assert "gw1" in offsets
    assert "signal_bias_db" in offsets["gw1"]


def test_coverage_score_calculation() -> None:
    radiomap = {"gw1": [-50.0, float("nan"), -55.0]}
    score = _calculate_coverage_score(radiomap, 3, 1)
    assert score == 0.667

    empty = {"gw1": [float("nan"), float("nan")]}
    score_empty = _calculate_coverage_score(empty, 2, 1)
    assert score_empty == 0.0


def test_activate_artifact_sets_others_stale(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with app.state.session_factory() as db:
        site = Site(name="Activate Test")
        db.add(site)
        db.flush()
        floor = Floor(site_id=site.id, name="Activate Floor")
        db.add(floor)
        db.flush()

        from rtls_api.auth import create_user

        user = create_user(
            db,
            email="admin2@test.com",
            password="AdminPass123",
            role="Administrator",
            display_name="Admin2",
        )
        db.commit()

        active = CalibrationArtifact(
            floor_id=floor.id,
            version=1,
            status=CalibrationArtifactStatus.ACTIVE.value,
            coverage_score=0.8,
            activated_at=db.scalar("SELECT datetime('now')"),
        )
        pending = CalibrationArtifact(
            floor_id=floor.id,
            version=2,
            status=CalibrationArtifactStatus.PENDING.value,
            coverage_score=0.9,
        )
        db.add(active)
        db.add(pending)
        db.flush()
        pending_id = pending.id

        from rtls_api.calibration import activate_calibration_artifact

        result = activate_calibration_artifact(
            artifact_id=pending_id,
            db=db,
            current_user=user,
        )
        assert result.status == "active"

        db.refresh(active)
        assert active.status == CalibrationArtifactStatus.STALE.value
