# exports-retention-and-rollups Specification

## Purpose
Define the delivered baseline for async analytics exports, administrator-triggered lifecycle runs, and hourly rollups that accelerate compatible analytics queries.

## Requirements
### Requirement: Authorized users can request async analytics exports
The RTLS Analytics Platform SHALL let authenticated users create durable analytics export jobs for supported report types.

#### Scenario: User queues a CSV export
- **WHEN** an authenticated user submits an export request for a supported analytics report scope
- **THEN** the system SHALL create an export job, process it asynchronously, and expose status until the artifact is ready or fails

#### Scenario: User downloads a completed export
- **WHEN** an authenticated user requests the file for a completed export job they are allowed to access
- **THEN** the system SHALL return the generated artifact instead of recomputing the report inline

### Requirement: Administrators can run and review data lifecycle jobs
The RTLS Analytics Platform SHALL expose a supported lifecycle run that refreshes rollups and applies retention windows.

#### Scenario: Administrator starts a lifecycle run
- **WHEN** an authenticated Administrator triggers the delivered lifecycle action
- **THEN** the system SHALL create a lifecycle run record and report its progress and latest outcome through a supported status surface

#### Scenario: Lifecycle run applies retention windows
- **WHEN** a lifecycle run completes successfully
- **THEN** the system SHALL purge records and artifacts older than the configured retention windows for the delivered data classes

### Requirement: The platform maintains hourly analytics rollups for supported reports
The RTLS Analytics Platform SHALL refresh reusable hourly rollups that accelerate compatible analytics requests.

#### Scenario: Lifecycle refresh rebuilds rollups
- **WHEN** the delivered lifecycle job runs
- **THEN** it SHALL recompute the supported hourly rollups from durable source data and persist their coverage metadata

#### Scenario: Compatible analytics query uses rollups
- **WHEN** an authorized analytics request matches the delivered rollup shape
- **THEN** the system SHALL prefer the refreshed rollup data instead of scanning only raw historical rows
