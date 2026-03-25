from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from rtls_api import spatial_admin
from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.main import create_app
from rtls_api.models import (
    AssetTag,
    AssetTagImportSession,
    AuditEvent,
    FloorPlanAsset,
    Gateway,
    UserRole,
)


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-spatial.db'}",
        redis_url="memory://spatial-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
    )


def make_png_bytes(width: int = 1200, height: int = 800) -> bytes:
    image = Image.new("RGB", (width, height), color=(14, 23, 41))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def make_asset_csv(rows: list[dict[str, str]]) -> bytes:
    header = "tag_identifier,display_name,asset_category,update_rate_profile,battery_profile"
    lines = [
        ",".join(
            [
                row["tag_identifier"],
                row["display_name"],
                row["asset_category"],
                row["update_rate_profile"],
                row["battery_profile"],
            ]
        )
        for row in rows
    ]
    return "\n".join([header, *lines]).encode("utf-8")


def issue_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/token", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_spatial_crud_flow_records_audit_events(tmp_path: Path) -> None:
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
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Ops",
            )
            db.commit()

        admin_token = issue_token(client, "admin@example.com", "StrongPass123")
        user_token = issue_token(client, "ops@example.com", "StrongPass123")

        create_site = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Salvador Flagship", "timezone_name": "America/Bahia"},
        )
        assert create_site.status_code == 201
        site_id = create_site.json()["id"]

        forbidden = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "Blocked Site"},
        )
        assert forbidden.status_code == 403

        create_floor = client.post(
            f"/api/admin/sites/{site_id}/floors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Dining Room", "level_label": "L1"},
        )
        assert create_floor.status_code == 201
        floor_id = create_floor.json()["id"]
        assert create_floor.json()["has_floor_plan"] is False

        list_floors = client.get(
            f"/api/admin/sites/{site_id}/floors",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert list_floors.status_code == 200
        assert list_floors.json()[0]["name"] == "Dining Room"

        invalid_upload = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("plan.txt", b"not-an-image", "text/plain")},
        )
        assert invalid_upload.status_code == 422

        upload = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("dining-room.png", make_png_bytes(), "image/png")},
        )
        assert upload.status_code == 201
        floor_plan = upload.json()
        assert floor_plan["mime_type"] == "image/png"

        download = client.get(
            floor_plan["file_download_path"],
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("image/png")

        scale = client.put(
            f"/api/admin/floors/{floor_id}/scale",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "point_a": {"x": 0.1, "y": 0.2},
                "point_b": {"x": 0.6, "y": 0.2},
                "real_world_distance_m": 10,
            },
        )
        assert scale.status_code == 200
        scale_payload = scale.json()["scale"]
        assert scale_payload is not None
        assert scale_payload["real_world_distance_m"] == 10
        assert scale_payload["pixels_per_meter"] == pytest.approx(60.0)

        create_area = client.post(
            f"/api/admin/floors/{floor_id}/areas",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Kitchen Pass",
                "area_type": "zone",
                "points": [
                    {"x": 0.2, "y": 0.2},
                    {"x": 0.5, "y": 0.2},
                    {"x": 0.5, "y": 0.4},
                ],
                "sla_eligible": True,
                "alert_participation": True,
            },
        )
        assert create_area.status_code == 201
        area_id = create_area.json()["id"]

        patch_area = client.patch(
            f"/api/admin/areas/{area_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Kitchen Pass Updated",
                "area_type": "restricted_zone",
                "alert_participation": False,
            },
        )
        assert patch_area.status_code == 200
        assert patch_area.json()["area_type"] == "restricted_zone"
        assert patch_area.json()["alert_participation"] is False

        list_areas = client.get(
            f"/api/admin/floors/{floor_id}/areas",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert list_areas.status_code == 200
        assert len(list_areas.json()) == 1

        delete_area = client.delete(
            f"/api/admin/areas/{area_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert delete_area.status_code == 204

        floor_detail = client.get(
            f"/api/admin/floors/{floor_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert floor_detail.status_code == 200
        assert floor_detail.json()["areas"] == []

        with app.state.session_factory() as db:
            actions = db.scalars(
                select(AuditEvent.action_type).where(
                    AuditEvent.action_type.in_(
                        [
                            "site.created",
                            "floor.created",
                            "floorplan.uploaded",
                            "floor.scale.updated",
                            "area.created",
                            "area.updated",
                            "area.deleted",
                        ]
                    )
                ).order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
            ).all()

        assert actions == [
            "site.created",
            "floor.created",
            "floorplan.uploaded",
            "floor.scale.updated",
            "area.created",
            "area.updated",
            "area.deleted",
        ]


def test_area_creation_requires_floor_plan(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            admin = create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
            )
            db.commit()
            admin_email = admin.email

        admin_token = issue_token(client, admin_email, "StrongPass123")
        site = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "No Plan Site"},
        ).json()
        floor = client.post(
            f"/api/admin/sites/{site['id']}/floors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Service Floor"},
        ).json()

        create_area = client.post(
            f"/api/admin/floors/{floor['id']}/areas",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Tables",
                "area_type": "table",
                "points": [
                    {"x": 0.1, "y": 0.1},
                    {"x": 0.2, "y": 0.1},
                    {"x": 0.2, "y": 0.2},
                ],
            },
        )

        assert create_area.status_code == 409
        assert "floor plan" in create_area.json()["detail"].lower()


def test_floor_plan_replacement_keeps_existing_blob_when_transaction_rolls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(build_settings(tmp_path))
    objects_root = tmp_path / "objects"

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            admin = create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
            )
            db.commit()
            admin_email = admin.email

        admin_token = issue_token(client, admin_email, "StrongPass123")
        site = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Rollback Site"},
        ).json()
        floor = client.post(
            f"/api/admin/sites/{site['id']}/floors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Rollback Floor"},
        ).json()
        floor_id = floor["id"]

        first_upload = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("initial.png", make_png_bytes(), "image/png")},
        )
        assert first_upload.status_code == 201

        with app.state.session_factory() as db:
            asset = db.scalar(select(FloorPlanAsset).where(FloorPlanAsset.floor_id == floor_id))
            assert asset is not None
            original_key = asset.storage_key
            original_dimensions = (asset.width_px, asset.height_px)

        original_files = {
            path.relative_to(objects_root) for path in objects_root.rglob("*") if path.is_file()
        }
        assert Path(original_key) in original_files

        original_write_audit_event = spatial_admin.write_audit_event

        def failing_write_audit_event(*args, **kwargs) -> None:
            original_write_audit_event(*args, **kwargs)
            if kwargs.get("action_type") == "floorplan.replaced":
                raise RuntimeError("forced floor-plan replacement rollback")

        monkeypatch.setattr(spatial_admin, "write_audit_event", failing_write_audit_event)

        with pytest.raises(RuntimeError, match="forced floor-plan replacement rollback"):
            client.post(
                f"/api/admin/floors/{floor_id}/floor-plan",
                headers={"Authorization": f"Bearer {admin_token}"},
                files={"floor_plan": ("replacement.png", make_png_bytes(600, 400), "image/png")},
            )

        with app.state.session_factory() as db:
            asset = db.scalar(select(FloorPlanAsset).where(FloorPlanAsset.floor_id == floor_id))
            assert asset is not None
            assert asset.storage_key == original_key
            assert (asset.width_px, asset.height_px) == original_dimensions

        current_files = {
            path.relative_to(objects_root) for path in objects_root.rglob("*") if path.is_file()
        }
        assert current_files == original_files


def test_floor_plan_replacement_clears_existing_scale(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            admin = create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
            )
            db.commit()
            admin_email = admin.email

        admin_token = issue_token(client, admin_email, "StrongPass123")
        site = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Scale Reset Site"},
        ).json()
        floor = client.post(
            f"/api/admin/sites/{site['id']}/floors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Scale Reset Floor"},
        ).json()
        floor_id = floor["id"]

        upload = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("initial.png", make_png_bytes(1200, 800), "image/png")},
        )
        assert upload.status_code == 201

        scale = client.put(
            f"/api/admin/floors/{floor_id}/scale",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "point_a": {"x": 0.1, "y": 0.2},
                "point_b": {"x": 0.6, "y": 0.2},
                "real_world_distance_m": 10,
            },
        )
        assert scale.status_code == 200
        assert scale.json()["scale"] is not None

        replacement = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("replacement.png", make_png_bytes(600, 400), "image/png")},
        )
        assert replacement.status_code == 201

        floor_detail = client.get(
            f"/api/admin/floors/{floor_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert floor_detail.status_code == 200
        assert floor_detail.json()["scale_configured"] is False
        assert floor_detail.json()["scale"] is None


def test_missing_floor_plan_blob_returns_404(tmp_path: Path) -> None:
    app = create_app(build_settings(tmp_path))
    objects_root = tmp_path / "objects"

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            admin = create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
            )
            db.commit()
            admin_email = admin.email

        admin_token = issue_token(client, admin_email, "StrongPass123")
        site = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Missing Blob Site"},
        ).json()
        floor = client.post(
            f"/api/admin/sites/{site['id']}/floors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Missing Blob Floor"},
        ).json()

        upload = client.post(
            f"/api/admin/floors/{floor['id']}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("plan.png", make_png_bytes(), "image/png")},
        )
        assert upload.status_code == 201
        download_path = upload.json()["file_download_path"]

        with app.state.session_factory() as db:
            asset = db.scalar(select(FloorPlanAsset).where(FloorPlanAsset.floor_id == floor["id"]))
            assert asset is not None
            (objects_root / asset.storage_key).unlink()

        download = client.get(download_path, headers={"Authorization": f"Bearer {admin_token}"})
        assert download.status_code == 404
        assert download.json()["detail"] == "Floor plan file not found"


def test_healthcheck_does_not_require_object_storage_startup(tmp_path: Path) -> None:
    settings = build_settings(tmp_path).model_copy(
        update={"object_storage_endpoint": "http://127.0.0.1:9"}
    )
    app = create_app(settings)

    with TestClient(app) as client:
        assert not hasattr(app.state, "object_storage_service")
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert not hasattr(app.state, "object_storage_service")


def test_gateway_and_asset_registry_flow_records_audit_events(tmp_path: Path) -> None:
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
            create_user(
                db,
                email="ops@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Ops",
            )
            db.commit()

        admin_token = issue_token(client, "admin@example.com", "StrongPass123")
        user_token = issue_token(client, "ops@example.com", "StrongPass123")

        site = client.post(
            "/api/admin/sites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Gateway Site", "timezone_name": "America/Bahia"},
        ).json()
        floor = client.post(
            f"/api/admin/sites/{site['id']}/floors",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Service Floor", "level_label": "L1"},
        ).json()
        floor_id = floor["id"]

        upload = client.post(
            f"/api/admin/floors/{floor_id}/floor-plan",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"floor_plan": ("service-floor.png", make_png_bytes(), "image/png")},
        )
        assert upload.status_code == 201

        forbidden_gateway = client.post(
            f"/api/admin/floors/{floor_id}/gateways",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "gateway_identifier": "gw-dining-01",
                "display_name": "Dining Gateway",
                "hardware_tier": "Economic",
                "placement": {"x": 0.25, "y": 0.35},
            },
        )
        assert forbidden_gateway.status_code == 403

        create_gateway = client.post(
            f"/api/admin/floors/{floor_id}/gateways",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "gateway_identifier": "gw-dining-01",
                "display_name": "Dining Gateway",
                "hardware_tier": "Economic",
                "placement": {"x": 0.25, "y": 0.35},
                "notes": "South dining wall",
            },
        )
        assert create_gateway.status_code == 201
        gateway_id = create_gateway.json()["id"]
        assert create_gateway.json()["hardware_tier"] == "Economic"

        update_gateway = client.patch(
            f"/api/admin/gateways/{gateway_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "display_name": "Dining Gateway Updated",
                "hardware_tier": "Premium",
                "placement": {"x": 0.4, "y": 0.55},
                "notes": "Relocated near the kitchen pass",
            },
        )
        assert update_gateway.status_code == 200
        assert update_gateway.json()["hardware_tier"] == "Premium"
        assert update_gateway.json()["placement"] == {"x": 0.4, "y": 0.55}

        floor_detail = client.get(
            f"/api/admin/floors/{floor_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert floor_detail.status_code == 200
        assert len(floor_detail.json()["gateways"]) == 1

        create_asset = client.post(
            "/api/admin/assets",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tag_identifier": "waiter-tag-01",
                "display_name": "Waiter Tag 01",
                "asset_category": "staff",
                "update_rate_profile": "balanced",
                "battery_profile": "standard",
            },
        )
        assert create_asset.status_code == 201
        asset_id = create_asset.json()["id"]

        duplicate_asset = client.post(
            "/api/admin/assets",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "tag_identifier": "waiter-tag-01",
                "display_name": "Waiter Tag Duplicate",
                "asset_category": "staff",
                "update_rate_profile": "balanced",
                "battery_profile": "standard",
            },
        )
        assert duplicate_asset.status_code == 409

        update_asset = client.patch(
            f"/api/admin/assets/{asset_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "display_name": "Waiter Tag Prime",
                "asset_category": "service_staff",
                "update_rate_profile": "realtime",
                "battery_profile": "performance",
            },
        )
        assert update_asset.status_code == 200
        assert update_asset.json()["update_rate_profile"] == "realtime"

        forbidden_asset_list = client.get(
            "/api/admin/assets",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert forbidden_asset_list.status_code == 403

        invalid_import = client.post(
            "/api/admin/assets/imports/validate",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={
                "import_file": (
                    "asset-import-invalid.csv",
                    make_asset_csv(
                        [
                            {
                                "tag_identifier": "waiter-tag-02",
                                "display_name": "Waiter Tag 02",
                                "asset_category": "staff",
                                "update_rate_profile": "balanced",
                                "battery_profile": "standard",
                            },
                            {
                                "tag_identifier": "waiter-tag-01",
                                "display_name": "Duplicate Tag",
                                "asset_category": "staff",
                                "update_rate_profile": "turbo",
                                "battery_profile": "standard",
                            },
                        ]
                    ),
                    "text/csv",
                )
            },
        )
        assert invalid_import.status_code == 200
        assert invalid_import.json()["import_id"] is None
        assert invalid_import.json()["invalid_row_count"] == 1
        assert len(invalid_import.json()["invalid_rows"][0]["errors"]) == 2

        valid_import = client.post(
            "/api/admin/assets/imports/validate",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={
                "import_file": (
                    "asset-import-valid.csv",
                    make_asset_csv(
                        [
                            {
                                "tag_identifier": "tray-cart-01",
                                "display_name": "Tray Cart 01",
                                "asset_category": "equipment",
                                "update_rate_profile": "slow",
                                "battery_profile": "long_life",
                            },
                            {
                                "tag_identifier": "table-beacon-07",
                                "display_name": "Table Beacon 07",
                                "asset_category": "table",
                                "update_rate_profile": "balanced",
                                "battery_profile": "standard",
                            },
                        ]
                    ),
                    "text/csv",
                )
            },
        )
        assert valid_import.status_code == 200
        assert valid_import.json()["invalid_row_count"] == 0
        assert valid_import.json()["valid_row_count"] == 2
        import_id = valid_import.json()["import_id"]
        assert isinstance(import_id, str)

        confirm_import = client.post(
            "/api/admin/assets/imports/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"import_id": import_id},
        )
        assert confirm_import.status_code == 200
        assert confirm_import.json()["created_count"] == 2

        delete_asset = client.delete(
            f"/api/admin/assets/{asset_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert delete_asset.status_code == 204

        delete_gateway = client.delete(
            f"/api/admin/gateways/{gateway_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert delete_gateway.status_code == 204

        with app.state.session_factory() as db:
            gateways = db.scalars(select(Gateway)).all()
            asset_tags = db.scalars(select(AssetTag).order_by(AssetTag.tag_identifier.asc())).all()
            actions = db.scalars(
                select(AuditEvent.action_type).where(
                    AuditEvent.action_type.in_(
                        [
                            "gateway.created",
                            "gateway.updated",
                            "gateway.deleted",
                            "asset.created",
                            "asset.updated",
                            "asset.deleted",
                            "asset.imported",
                        ]
                    )
                ).order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
            ).all()

        assert gateways == []
        assert [asset.tag_identifier for asset in asset_tags] == ["table-beacon-07", "tray-cart-01"]
        assert actions == [
            "gateway.created",
            "gateway.updated",
            "asset.created",
            "asset.updated",
            "asset.imported",
            "asset.deleted",
            "gateway.deleted",
        ]


def test_asset_import_session_survives_app_restart(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        with app.state.session_factory() as db:
            admin = create_user(
                db,
                email="admin@example.com",
                password="StrongPass123",
                role=UserRole.ADMINISTRATOR,
            )
            db.commit()
            admin_email = admin.email

        admin_token = issue_token(client, admin_email, "StrongPass123")
        valid_import = client.post(
            "/api/admin/assets/imports/validate",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={
                "import_file": (
                    "asset-import-valid.csv",
                    make_asset_csv(
                        [
                            {
                                "tag_identifier": "cart-restart-01",
                                "display_name": "Cart Restart 01",
                                "asset_category": "equipment",
                                "update_rate_profile": "slow",
                                "battery_profile": "long_life",
                            }
                        ]
                    ),
                    "text/csv",
                )
            },
        )
        assert valid_import.status_code == 200
        import_id = valid_import.json()["import_id"]
        assert isinstance(import_id, str)

        with app.state.session_factory() as db:
            persisted_session = db.get(AssetTagImportSession, import_id)
            assert persisted_session is not None

    restarted_app = create_app(settings)
    with TestClient(restarted_app) as client:
        confirm_import = client.post(
            "/api/admin/assets/imports/confirm",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"import_id": import_id},
        )
        assert confirm_import.status_code == 200
        assert confirm_import.json()["created_count"] == 1

        with restarted_app.state.session_factory() as db:
            assert db.get(AssetTagImportSession, import_id) is None
