## Why

The platform supports high-precision "Premium Tier" positioning (AoA/UWB), which requires precise gateway calibration and environmental radiomaps to achieve advertised accuracy. Currently, while mobile commissioning tools exist to collect calibration data, there is no backend engine to process these sessions into reusable artifacts, manage their lifecycle, or provide them to the positioning estimators.

This change is critical to bridge the gap between data collection and real-time positioning, ensuring that estimators have access to the latest, most accurate environmental data while maintaining system integrity when physical floor plans are updated.

## What Changes

- **Calibration Processing Pipeline**: A backend service that consumes mobile calibration session data and performs the necessary geometric and signal-strength calculations.
- **Radiomap & Offset Artifact Generation**: Automated generation of radiomap artifacts (for fingerprinting/IPS) and per-gateway offset corrections.
- **Artifact Registry & Versioning**: A durable storage and metadata layer to track artifact versions, association with floors/gateways, and "active" status.
- **Automatic Invalidation Logic**: Logic to mark calibration artifacts as stale or invalid whenever the associated floor plan's geometry or scale is modified.
- **Estimator Integration**: Updates to the premium positioning path to fetch and apply active calibration artifacts during real-time processing.

## Capabilities

### New Capabilities
- `calibration-engine`: Processing raw mobile calibration sessions into normalized positioning artifacts.
- `radiomap-artifact-registry`: Lifecycle management, versioning, and storage of radiomaps and gateway offsets.

### Modified Capabilities
- `premium-tier-position-estimation`: Consumption of radiomap and offset artifacts for high-fidelity location calculation.
- `floor-plan-management`: Invalidation triggers for calibration data when spatial boundaries or scale are redefined.
- `mobile-commissioning-and-calibration`: Backend handshake to confirm successful session ingestion and transition to processing.

## Impact

- **Backend (API/Worker)**: New service layer for processing; new database tables for artifact metadata; updates to positioning logic.
- **Persistence**: Storage of large radiomap blobs (likely in object storage) with metadata in PostgreSQL.
- **Performance**: High-computational load for radiomap generation (asynchronous processing in worker).
- **Security**: Ensures that only authorized calibration sessions (from Alex/Administrator) can generate system-wide positioning artifacts.
