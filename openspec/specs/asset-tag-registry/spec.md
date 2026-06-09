# asset-tag-registry Specification

## Purpose
Define the Administrator-managed asset tag registry, policy metadata, and bulk onboarding workflow that later ingestion and operations features depend on.
## Requirements
### Requirement: Administrator-managed asset tag registry
The RTLS Analytics Platform SHALL allow authenticated Administrators to create and manage asset tag records with stable tag identity and operational metadata, utilizing "Command" style interaction standards including focus-responsive Cyan borders and real-time validation feedback.

#### Scenario: Administrator creates an asset tag record
- **WHEN** an authenticated Administrator submits a valid asset tag definition through a "Command" style form
- **THEN** the system SHALL persist the asset tag record and provide an `IconCheckCircle` feedback upon success

#### Scenario: Duplicate tag identity is submitted
- **WHEN** an authenticated Administrator enters an asset tag ID that already exists
- **THEN** the system SHALL provide real-time feedback with an `IconAlertCircle` and a human-readable message before the form is submitted

### Requirement: Asset update-rate and battery policy metadata
The RTLS Analytics Platform SHALL persist asset tag policy metadata including update-rate and battery profile settings needed for later operational workflows.

#### Scenario: Administrator saves policy metadata
- **WHEN** an authenticated Administrator creates or updates an asset tag with supported update-rate and battery profile values
- **THEN** the system SHALL persist those policy values with the asset tag record

#### Scenario: Unsupported policy value is submitted
- **WHEN** an authenticated Administrator submits an unsupported update-rate or battery profile value
- **THEN** the system SHALL reject the request with a validation error

### Requirement: CSV-based bulk asset tag import
The RTLS Analytics Platform SHALL support validated CSV import for bulk creation of asset tag records.

#### Scenario: Administrator uploads a valid CSV import
- **WHEN** an authenticated Administrator uploads a CSV file whose rows satisfy the asset tag import contract and confirms the reviewed import
- **THEN** the system SHALL create the validated asset tag records in bulk

#### Scenario: CSV import contains invalid rows
- **WHEN** an authenticated Administrator uploads a CSV file with invalid, duplicate, or unsupported asset tag data
- **THEN** the system SHALL return row-level validation errors before any invalid records are committed
