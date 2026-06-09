## ADDED Requirements

### Requirement: Durable radiomap artifact storage and versioning
The RTLS Analytics Platform SHALL store generated radiomap artifacts in a durable registry with support for versioning and floor-level association.

#### Scenario: New radiomap is generated
- **WHEN** the calibration engine produces a new radiomap artifact
- **THEN** the system SHALL store the artifact blob (e.g., in object storage) and create a new versioned entry in the metadata registry linked to the floor

#### Scenario: Multiple versions exist for the same floor
- **WHEN** multiple radiomap artifacts exist for a single floor
- **THEN** the system SHALL track which version is currently "active" for real-time positioning

### Requirement: Artifact lifecycle and metadata exposure
The artifact registry SHALL expose the status, lifecycle, and quality metadata for all calibration artifacts associated with a floor or gateway.

#### Scenario: Administrator views floor calibration status
- **WHEN** an Administrator (Alex) requests the calibration health or status for a floor
- **THEN** the system SHALL return metadata for the active radiomap, including generation time, coverage score, and used gateway offsets

### Requirement: Active artifact retrieval for estimators
The registry SHALL provide a high-performance retrieval mechanism for the active radiomap and offsets required by real-time positioning estimators.

#### Scenario: Estimator requests the active radiomap
- **WHEN** a positioning estimator requests the current calibration context for an active floor
- **THEN** the system SHALL return the active versioned radiomap and the associated gateway offset parameters
