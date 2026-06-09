## 1. Schema and Models

- [x] 1.1 Create `CalibrationSession` model to store mobile upload metadata and raw sample JSON
- [x] 1.2 Create `CalibrationArtifact` model for radiomap (blob key) and gateway offset metadata
- [x] 1.3 Add `status` (pending, processing, active, stale, invalid) and versioning to artifact model
- [x] 1.4 Generate and apply database migration for new calibration tables

## 2. API Endpoints

- [x] 2.1 Implement POST endpoint for mobile calibration session submission
- [x] 2.2 Implement GET/PATCH endpoints for artifact lifecycle management (list, active toggle, status)
- [x] 2.3 Implement GET endpoint for calibration health summary per floor
- [x] 2.4 Add request validation and RBAC enforcement (Alex/Administrator only)

## 3. Calibration Engine (Worker)

- [x] 3.1 Implement background task for processing submitted calibration sessions
- [x] 3.2 Implement radiomap grid generator with interpolation from walk-path samples
- [x] 3.3 Implement per-gateway offset calculation (coordinate and signal bias)
- [x] 3.4 Integrate object storage (MinIO/S3) for radiomap blob persistence

## 4. Lifecycle and Invalidation

- [x] 4.1 Add service-layer hooks to invalidate active artifacts when floor scale or plan changes
- [x] 4.2 Implement atomic "activation" logic to switch the active radiomap version for a floor
- [x] 4.3 Add backend validation to prevent activating artifacts with insufficient coverage

## 5. Estimator Integration

- [x] 5.1 Update `rtls_api.positioning` to fetch active calibration artifacts for the current floor
- [x] 5.2 Integrate radiomap data and gateway offsets into the Premium location estimator logic
- [x] 5.3 Implement caching for active artifacts in the positioning worker to minimize storage latency

## 6. Verification and Documentation

- [x] 6.1 Create end-to-end integration test: calibration submission -> processing -> estimator impact
- [x] 6.2 Update `docs/technical-specification-document.md` with calibration and radiomap architecture
- [x] 6.3 Update `docs/spatial-admin-workflow.md` with instructions for monitoring calibration health
