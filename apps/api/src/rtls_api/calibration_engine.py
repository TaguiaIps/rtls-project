from __future__ import annotations

import json
import logging
import math
from typing import Any

from rtls_api.config import Settings
from rtls_api.models import (
    CalibrationArtifact,
    CalibrationArtifactStatus,
    CalibrationSession,
    CalibrationSessionStatus,
    Floor,
    Gateway,
    utc_now,
)
from rtls_api.storage import ObjectStorageService

logger = logging.getLogger("rtls-calibration")

GRID_RESOLUTION_M = 0.5


def process_calibration_session(
    *,
    db_session: Any,
    session_id: str,
    settings: Settings,
    storage: ObjectStorageService,
) -> None:
    session = db_session.get(CalibrationSession, session_id)
    if session is None:
        logger.error("calibration_session_not_found id=%s", session_id)
        return

    if session.status == CalibrationSessionStatus.PROCESSING.value:
        logger.warning("calibration_session_already_processing id=%s", session_id)
        return

    session.status = CalibrationSessionStatus.PROCESSING.value
    session.processing_started_at = utc_now()
    db_session.flush()

    try:
        floor = db_session.get(Floor, session.floor_id)
        if floor is None:
            raise ValueError(f"Floor {session.floor_id} not found")

        gateways = {
            g.id: g
            for g in db_session.scalars(
                Gateway.__table__.select().where(Gateway.floor_id == session.floor_id)
            ).all()
        }
        if not gateways:
            raise ValueError("No gateways found on this floor")

        checkpoints = session.raw_samples.get("checkpoints", [])
        if not checkpoints:
            raise ValueError("No checkpoint data in session")

        radiomap, grid_cols, grid_rows = _generate_radiomap_grid(
            checkpoints=checkpoints,
            gateways=gateways,
        )

        gateway_offsets = _calculate_gateway_offsets(
            checkpoints=checkpoints,
            gateways=gateways,
        )

        coverage_score = _calculate_coverage_score(radiomap, grid_cols, grid_rows)

        next_version = _next_artifact_version(db_session, session.floor_id)

        artifact = CalibrationArtifact(
            floor_id=session.floor_id,
            version=next_version,
            status=CalibrationArtifactStatus.PENDING.value,
            radiomap_storage_key=f"radiomaps/{session.floor_id}/v{next_version}.json",
            gateway_offsets=gateway_offsets,
            coverage_score=coverage_score,
            grid_resolution_m=GRID_RESOLUTION_M,
        )
        db_session.add(artifact)
        db_session.flush()

        radiomap_blob = json.dumps(
            {
                "grid_cols": grid_cols,
                "grid_rows": grid_rows,
                "resolution_m": GRID_RESOLUTION_M,
                "gateway_ids": list(gateways.keys()),
                "grid": radiomap,
            }
        ).encode("utf-8")
        storage.put_object(
            key=artifact.radiomap_storage_key,
            content=radiomap_blob,
            content_type="application/json",
        )

        session.status = CalibrationSessionStatus.COMPLETED.value
        session.processing_completed_at = utc_now()
        session.artifact_id = artifact.id

        logger.info(
            "calibration_processed session=%s artifact=%s version=%s coverage=%.2f",
            session_id,
            artifact.id,
            next_version,
            coverage_score,
        )

    except Exception as exc:
        session.status = CalibrationSessionStatus.FAILED.value
        session.error_message = str(exc)
        session.processing_completed_at = utc_now()
        logger.error("calibration_processing_failed session=%s error=%s", session_id, exc)

    db_session.commit()


def _generate_radiomap_grid(
    *,
    checkpoints: list[dict],
    gateways: dict[str, Gateway],
    grid_resolution_m: float = GRID_RESOLUTION_M,
) -> tuple[dict[str, list[float]], int, int]:
    if not checkpoints:
        return {}, 0, 0

    min_x = min(cp["x"] for cp in checkpoints)
    max_x = max(cp["x"] for cp in checkpoints)
    min_y = min(cp["y"] for cp in checkpoints)
    max_y = max(cp["y"] for cp in checkpoints)

    span_x = max(max_x - min_x, grid_resolution_m)
    span_y = max(max_y - min_y, grid_resolution_m)
    grid_cols = max(1, int(math.ceil(span_x / grid_resolution_m)))
    grid_rows = max(1, int(math.ceil(span_y / grid_resolution_m)))

    gateway_ids = sorted(gateways.keys())
    radiomap: dict[str, list[float]] = {
        gid: [float("nan")] * (grid_cols * grid_rows) for gid in gateway_ids
    }

    for checkpoint in checkpoints:
        cx, cy = checkpoint["x"], checkpoint["y"]
        readings = checkpoint.get("readings", [])
        for reading in readings:
            gw_id = reading["gateway_id"]
            if gw_id not in radiomap:
                continue
            rssi = reading["rssi"]

            col = min(int((cx - min_x) / grid_resolution_m), grid_cols - 1)
            row = min(int((cy - min_y) / grid_resolution_m), grid_rows - 1)
            idx = row * grid_cols + col

            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < grid_rows and 0 <= nc < grid_cols:
                        n_idx = nr * grid_cols + nc
                        dist = math.sqrt(dr * dr + dc * dc)
                        weight = max(0.0, 1.0 / (1.0 + dist))
                        existing = radiomap[gw_id][n_idx]
                        if math.isnan(existing):
                            radiomap[gw_id][n_idx] = rssi * weight
                        else:
                            alpha = 0.3
                            radiomap[gw_id][n_idx] = (1 - alpha) * existing + alpha * rssi * weight

    return radiomap, grid_cols, grid_rows


def _calculate_gateway_offsets(
    *,
    checkpoints: list[dict],
    gateways: dict[str, Gateway],
) -> dict[str, dict[str, float]]:
    offsets: dict[str, dict[str, float]] = {}

    for gw_id, gateway in gateways.items():
        rssi_values = []
        for cp in checkpoints:
            for reading in cp.get("readings", []):
                if reading["gateway_id"] == gw_id:
                    rssi_values.append(reading["rssi"])

        if not rssi_values:
            continue

        avg_rssi = sum(rssi_values) / len(rssi_values)
        distance = max(1.0, float(110 + avg_rssi))

        offsets[gw_id] = {
            "signal_bias_db": round(avg_rssi, 2),
            "estimated_distance_m": round(distance, 2),
            "sample_count": len(rssi_values),
            "coordinate_offset_x": 0.0,
            "coordinate_offset_y": 0.0,
        }

    return offsets


def _calculate_coverage_score(
    radiomap: dict[str, list[float]],
    grid_cols: int,
    grid_rows: int,
) -> float:
    if grid_cols == 0 or grid_rows == 0:
        return 0.0

    total_cells = grid_cols * grid_rows
    covered_cells = 0
    for values in radiomap.values():
        for v in values:
            if not math.isnan(v):
                covered_cells += 1
                break

    return round(covered_cells / total_cells, 3)


def _next_artifact_version(db_session: Any, floor_id: str) -> int:
    from sqlalchemy import func, select

    max_version = db_session.scalar(
        select(func.max(CalibrationArtifact.version)).where(
            CalibrationArtifact.floor_id == floor_id
        )
    )
    return (max_version or 0) + 1
