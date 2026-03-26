## ADDED Requirements

### Requirement: Administrator-managed asset tag registry
The RTLS Analytics Platform SHALL allow authenticated Administrators to create and manage asset tag records with stable tag identity and operational metadata.

#### Scenario: Administrator creates an asset tag record
- **WHEN** an authenticated Administrator submits a valid asset tag definition with supported metadata fields
- **THEN** the system SHALL persist the asset tag record and make it available in the asset registry

#### Scenario: Duplicate tag identity is submitted
- **WHEN** an authenticated Administrator submits an asset tag whose unique tag identity already exists
- **THEN** the system SHALL reject the request with a validation error

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
