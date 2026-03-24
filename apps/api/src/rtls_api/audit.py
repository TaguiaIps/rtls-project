from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from rtls_api.models import AuditEvent, User


def write_audit_event(
    db: Session,
    *,
    action_category: str,
    action_type: str,
    actor: User | None = None,
    actor_email: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=actor.id if actor else None,
            actor_email=actor.email if actor else actor_email,
            actor_role=actor.role if actor else None,
            action_category=action_category,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
    )
