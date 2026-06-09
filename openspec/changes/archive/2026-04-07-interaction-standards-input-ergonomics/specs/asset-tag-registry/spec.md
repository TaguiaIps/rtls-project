## MODIFIED Requirements

### Requirement: Administrator-managed asset tag registry
The RTLS Analytics Platform SHALL allow authenticated Administrators to create and manage asset tag records with stable tag identity and operational metadata, utilizing "Command" style interaction standards including focus-responsive Cyan borders and real-time validation feedback.

#### Scenario: Administrator creates an asset tag record
- **WHEN** an authenticated Administrator submits a valid asset tag definition through a "Command" style form
- **THEN** the system SHALL persist the asset tag record and provide an `IconCheckCircle` feedback upon success

#### Scenario: Duplicate tag identity is submitted
- **WHEN** an authenticated Administrator enters an asset tag ID that already exists
- **THEN** the system SHALL provide real-time feedback with an `IconAlertCircle` and a human-readable message before the form is submitted
