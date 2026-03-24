from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from rtls_api.audit import write_audit_event
from rtls_api.auth import require_role
from rtls_api.db import get_db
from rtls_api.models import User, UserRole
from rtls_api.schemas import AdminSummaryResponse, AdminUserUpdateRequest, CurrentUserResponse

ADMIN_ROUTER = APIRouter(prefix="/api/admin", tags=["admin"])


@ADMIN_ROUTER.get("/summary", response_model=AdminSummaryResponse)
def get_admin_summary(
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> AdminSummaryResponse:
    return AdminSummaryResponse(
        current_user=CurrentUserResponse.model_validate(admin_user),
        managed_roles=[UserRole.ADMINISTRATOR.value, UserRole.GENERAL_USER.value],
    )


@ADMIN_ROUTER.patch("/users/{user_id}", response_model=CurrentUserResponse)
def update_user_account(
    user_id: str,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMINISTRATOR)),
) -> CurrentUserResponse:
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes: dict[str, str] = {}
    if payload.display_name is not None and payload.display_name != target_user.display_name:
        target_user.display_name = payload.display_name
        changes["display_name"] = payload.display_name
    if payload.role is not None and payload.role.value != target_user.role:
        target_user.role = payload.role.value
        changes["role"] = payload.role.value
    if payload.status is not None and payload.status.value != target_user.status:
        target_user.status = payload.status.value
        changes["status"] = payload.status.value

    if changes:
        write_audit_event(
            db,
            action_category="configuration",
            action_type="admin.user.updated",
            actor=admin_user,
            target_type="user",
            target_id=target_user.id,
            details={"changes": changes},
        )
        db.commit()
        db.refresh(target_user)

    return CurrentUserResponse.model_validate(target_user)
