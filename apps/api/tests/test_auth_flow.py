from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from rtls_api.auth import create_user
from rtls_api.bootstrap_admin import run_bootstrap
from rtls_api.config import Settings
from rtls_api.main import create_app
from rtls_api.models import AuditEvent, User, UserRole, UserStatus


def build_settings(tmp_path: Path) -> Settings:
    return Settings(
        env="test",
        database_url=f"sqlite:///{tmp_path / 'rtls-test.db'}",
        redis_url="memory://auth-tests",
        web_origin="http://localhost:5173",
        jwt_secret_key="test-secret",
        object_storage_endpoint=f"file://{tmp_path / 'objects'}",
    )


def test_root_contains_service_inventory(tmp_path: Path) -> None:
    with TestClient(create_app(build_settings(tmp_path))) as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"] == "RTLS Analytics Platform"
    assert payload["security"]["auth"] == "local-jwt"


def test_authentication_refresh_logout_and_audit_events(tmp_path: Path) -> None:
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
            db.commit()

        login_response = client.post(
            "/api/auth/token",
            json={"email": "admin@example.com", "password": "StrongPass123"},
        )
        assert login_response.status_code == 200
        login_payload = login_response.json()

        me_response = client.get(
            "/api/me",
            headers={"Authorization": f"Bearer {login_payload['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["role"] == "Administrator"

        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": login_payload["refresh_token"]},
        )
        assert refresh_response.status_code == 200

        logout_response = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_response.json()["refresh_token"]},
        )
        assert logout_response.status_code == 204

        with app.state.session_factory() as db:
            audit_actions = db.scalars(select(AuditEvent.action_type)).all()

        assert "auth.login.success" in audit_actions
        assert "auth.refresh.success" in audit_actions
        assert "auth.logout" in audit_actions


def test_role_protection_and_admin_user_update_audit(tmp_path: Path) -> None:
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
            general = create_user(
                db,
                email="manager@example.com",
                password="StrongPass123",
                role=UserRole.GENERAL_USER,
                display_name="Carlos",
            )
            db.commit()
            general_id = general.id

        general_login = client.post(
            "/api/auth/token",
            json={"email": "manager@example.com", "password": "StrongPass123"},
        ).json()
        denied = client.get(
            "/api/admin/summary",
            headers={"Authorization": f"Bearer {general_login['access_token']}"},
        )
        assert denied.status_code == 403

        admin_login = client.post(
            "/api/auth/token",
            json={"email": "admin@example.com", "password": "StrongPass123"},
        ).json()
        updated = client.patch(
            f"/api/admin/users/{general_id}",
            headers={"Authorization": f"Bearer {admin_login['access_token']}"},
            json={"status": UserStatus.DISABLED.value},
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == UserStatus.DISABLED.value

        with app.state.session_factory() as db:
            stored_general = db.get(User, general_id)
            audit_events = db.scalars(
                select(AuditEvent).where(AuditEvent.action_type == "admin.user.updated")
            ).all()

        assert stored_general is not None
        assert stored_general.status == UserStatus.DISABLED.value
        assert len(audit_events) == 1


def test_bootstrap_admin_command_creates_first_administrator(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    exit_code = run_bootstrap(
        type(
            "Args",
            (),
            {
                "email": "bootstrap@example.com",
                "password": "StrongPass123",
                "display_name": "Bootstrap Admin",
            },
        )(),
        settings,
    )

    assert exit_code == 0

    app = create_app(settings)
    with TestClient(app):
        with app.state.session_factory() as db:
            admin = db.scalar(select(User).where(User.email == "bootstrap@example.com"))
            assert admin is not None
            assert admin.role == UserRole.ADMINISTRATOR.value
