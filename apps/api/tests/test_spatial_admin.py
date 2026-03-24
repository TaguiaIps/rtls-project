from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from rtls_api.auth import create_user
from rtls_api.config import Settings
from rtls_api.main import create_app
from rtls_api.models import AuditEvent, UserRole


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
