from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from rtls_api.audit import write_audit_event
from rtls_api.auth import get_current_user, require_role
from rtls_api.db import get_db
from rtls_api.models import (
    CalibrationArtifact,
    CalibrationArtifactStatus,
    CalibrationSession,
    CalibrationSessionStatus,
    Floor,
    Gateway,
    User,
    utc_now,
)
from rtls_api.schemas import (
    CalibrationArtifactResponse,
    CalibrationHealthResponse,
    CalibrationSample,
    CalibrationSessionRequest,
    CalibrationSessionResponse,
)

logger = logging.getLogger("rtls-api")

CALIBRATION_ROUTER = APIRouter(prefix="/api/admin", tags=["admin-calibration"])


def _session_to_response(session: CalibrationSession) -> CalibrationSessionResponse:
    return CalibrationSessionResponse(
        id=session.id,
        floor_id=session.floor_id,
        status=session.status,
        checkpoint_count=session.checkpoint_count,
        sample_count=session.sample_count,
        error_message=session.error_message,
        artifact_id=session.artifact_id,
        created_at=session.created_at,
        processing_started_at=session.processing_started_at,
        processing_completed_at=session.processing_completed_at,
    )


def _artifact_to_response(artifact: CalibrationArtifact) -> CalibrationArtifactResponse:
    return CalibrationArtifactResponse(
        id=artifact.id,
        floor_id=artifact.floor_id,
        version=artifact.version,
        status=artifact.status,
        coverage_score=artifact.coverage_score,
        grid_resolution_m=artifact.grid_resolution_m,
        activated_at=artifact.activated_at,
        created_at=artifact.created_at,
    )


def _group_samples_by_checkpoint(
    samples: list[CalibrationSample],
) -> list[dict]:
    checkpoints: dict[tuple[float, float], list[dict]] = {}
    for sample in samples:
        key = (round(sample.checkpoint_x, 4), round(sample.checkpoint_y, 4))
        checkpoints.setdefault(key, []).append(
            {"gateway_id": sample.gateway_id, "rssi": sample.rssi, "tx_power": sample.tx_power}
        )
    return [{"x": k[0], "y": k[1], "readings": v} for k, v in sorted(checkpoints.items())]


@CALIBRATION_ROUTER.post(
    "/calibration/sessions",
    response_model=CalibrationSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_calibration_session(
    body: CalibrationSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator")),
) -> CalibrationSessionResponse:
    floor = db.get(Floor, body.floor_id)
    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    gateways_on_floor = {
        g.id for g in db.scalars(select(Gateway).where(Gateway.floor_id == body.floor_id)).all()
    }
    sample_gateway_ids = {s.gateway_id for s in body.samples}
    if not sample_gateway_ids.issubset(gateways_on_floor):
        raise HTTPException(
            status_code=400,
            detail="One or more sample gateway_ids do not belong to this floor",
        )

    checkpoints = _group_samples_by_checkpoint(body.samples)
    session = CalibrationSession(
        floor_id=body.floor_id,
        submitted_by_user_id=current_user.id,
        status=CalibrationSessionStatus.PENDING.value,
        checkpoint_count=len(checkpoints),
        sample_count=len(body.samples),
        raw_samples={"checkpoints": checkpoints},
    )
    db.add(session)
    db.flush()

    write_audit_event(
        db,
        action_category="calibration",
        action_type="session_submitted",
        actor=current_user,
        target_type="calibration_session",
        target_id=session.id,
        details={"floor_id": body.floor_id, "checkpoint_count": len(checkpoints)},
    )

    db.commit()
    return _session_to_response(session)


@CALIBRATION_ROUTER.get(
    "/floors/{floor_id}/calibration/artifacts",
    response_model=list[CalibrationArtifactResponse],
)
def list_calibration_artifacts(
    floor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CalibrationArtifactResponse]:
    floor = db.get(Floor, floor_id)
    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    artifacts = db.scalars(
        select(CalibrationArtifact)
        .where(CalibrationArtifact.floor_id == floor_id)
        .order_by(CalibrationArtifact.version.desc())
    ).all()
    return [_artifact_to_response(a) for a in artifacts]


@CALIBRATION_ROUTER.patch(
    "/calibration/artifacts/{artifact_id}/activate",
    response_model=CalibrationArtifactResponse,
)
def activate_calibration_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator")),
) -> CalibrationArtifactResponse:
    artifact = db.get(CalibrationArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if artifact.status == CalibrationArtifactStatus.ACTIVE.value:
        return _artifact_to_response(artifact)

    if artifact.status not in {
        CalibrationArtifactStatus.PENDING.value,
        CalibrationArtifactStatus.STALE.value,
    }:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot activate artifact with status '{artifact.status}'",
        )

    if artifact.coverage_score is not None and artifact.coverage_score < 0.3:
        raise HTTPException(
            status_code=400,
            detail="Cannot activate artifact with insufficient coverage (< 30%)",
        )

    existing_active = db.scalars(
        select(CalibrationArtifact).where(
            CalibrationArtifact.floor_id == artifact.floor_id,
            CalibrationArtifact.status == CalibrationArtifactStatus.ACTIVE.value,
        )
    ).first()
    if existing_active is not None:
        existing_active.status = CalibrationArtifactStatus.STALE.value
        existing_active.activated_at = None

    artifact.status = CalibrationArtifactStatus.ACTIVE.value
    artifact.activated_at = utc_now()
    artifact.activated_by_user_id = current_user.id

    write_audit_event(
        db,
        action_category="calibration",
        action_type="artifact_activated",
        actor=current_user,
        target_type="calibration_artifact",
        target_id=artifact.id,
        details={"floor_id": artifact.floor_id, "version": artifact.version},
    )

    db.commit()
    return _artifact_to_response(artifact)


@CALIBRATION_ROUTER.get(
    "/floors/{floor_id}/calibration/health",
    response_model=CalibrationHealthResponse,
)
def get_calibration_health(
    floor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalibrationHealthResponse:
    floor = db.get(Floor, floor_id)
    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found")

    total_sessions = (
        db.scalar(select(func.count()).where(CalibrationSession.floor_id == floor_id)) or 0
    )
    total_artifacts = (
        db.scalar(select(func.count()).where(CalibrationArtifact.floor_id == floor_id)) or 0
    )

    active_artifact = db.scalars(
        select(CalibrationArtifact).where(
            CalibrationArtifact.floor_id == floor_id,
            CalibrationArtifact.status == CalibrationArtifactStatus.ACTIVE.value,
        )
    ).first()

    return CalibrationHealthResponse(
        floor_id=floor_id,
        floor_name=floor.name,
        active_artifact=(_artifact_to_response(active_artifact) if active_artifact else None),
        total_sessions=total_sessions,
        total_artifacts=total_artifacts,
        has_active_calibration=active_artifact is not None,
    )
