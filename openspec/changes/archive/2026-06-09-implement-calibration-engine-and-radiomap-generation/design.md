## Context

The platform is moving towards supporting high-precision positioning (Premium Tier), which depends on environmental calibration. Mobile commissioning tools are already capable of collecting calibration walks (checkpoints and signal samples), but the backend lacks the logic to turn these sessions into actionable "Radiomap" artifacts that the positioning estimators can use.

## Goals / Non-Goals

**Goals:**
- Implement a backend pipeline to process calibration sessions.
- Generate and store versioned Radiomap and Gateway Offset artifacts.
- Provide a mechanism for positioning estimators to fetch active artifacts.
- Automatically invalidate artifacts when floor plans or scale changes.

**Non-Goals:**
- Real-time "auto-calibration" during positioning (calibration remains a discrete administrative step).
- Processing economic-tier (BLE RSSI fingerprinting) calibration in this phase (focus is on Premium Tier).

## Decisions

### 1. Asynchronous Calibration Processing in Worker
Calibration processing involves heavy geometric calculations and radiomap interpolation.
- **Decision**: Offload processing to the backend worker using the existing background task infrastructure.
- **Rationale**: Keeps the API responsive while handling long-running computational tasks.

### 2. Artifact Storage: PostgreSQL + Object Storage
Radiomaps can be large binary blobs (grids of signal expectations).
- **Decision**: Store metadata (version, status, coverage) in PostgreSQL and the actual radiomap data in Object Storage (e.g., MinIO/S3).
- **Rationale**: Efficiently handles large blobs while keeping metadata queryable and relational.

### 3. Versioning and "Active" State
A floor can have multiple calibration attempts.
- **Decision**: Implement a `status` field (`pending`, `processing`, `active`, `stale`, `invalid`) and ensure only one `active` artifact exists per floor.
- **Rationale**: Allows Alex (Administrator) to review new calibrations before they impact real-time positioning, and provides a clear audit trail.

### 4. Automatic Invalidation on Floor Plan Change
Physical changes to the floor plan (uploading a new image or changing the scale) render existing calibration invalid.
- **Decision**: Add database triggers or service-layer hooks to mark all calibration artifacts for a floor as `invalid` when the `Floor`'s `scale_configured_at` or `FloorPlanAsset`'s `updated_at` changes.
- **Rationale**: Prevents misleading "high-precision" results based on outdated environmental data.

## Risks / Trade-offs

- **[Risk] Resource Exhaustion** → **Mitigation**: Implement concurrency limits for calibration tasks in the worker.
- **[Risk] Estimator Latency** → **Mitigation**: Cache active radiomaps in the positioning service's memory or a fast cache (Redis) to avoid frequent object storage lookups.
- **[Risk] Data Consistency** → **Mitigation**: Use atomic transitions when switching the "active" radiomap for a floor.

## Migration Plan

1. **Schema Migration**: Add `calibration_sessions` and `calibration_artifacts` tables.
2. **Worker Update**: Implement the calibration engine logic (interpolation, offset calculation).
3. **API Update**: Add endpoints for session upload and artifact management.
4. **Estimator Update**: Update `positioning.py` to fetch and apply artifacts.

## Open Questions

- What is the optimal grid resolution for the initial radiomap implementation? (Likely 0.5m to 1.0m based on catering environment constraints).
