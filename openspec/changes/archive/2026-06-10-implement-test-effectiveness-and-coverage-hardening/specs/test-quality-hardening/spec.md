## ADDED Requirements

### Requirement: Spec-to-test traceability matrix
The RTLS Analytics Platform SHALL maintain a formal traceability matrix mapping every normative requirement in the OpenSpec specifications to corresponding executable test cases.

#### Scenario: Criterion is mapped to existing tests
- **WHEN** the Administrator (Alex) reviews the traceability matrix
- **THEN** every normative criterion from active specs MUST be assigned a status of Covered, Partially Covered, or Uncovered with evidence of specific test files and line numbers

#### Scenario: Planned scenarios for uncovered criteria
- **WHEN** a criterion is marked as Partially Covered or Uncovered
- **THEN** the matrix SHALL include documented implementation plans for adding the missing test scenarios

### Requirement: Test effectiveness audit and refactoring
The system's test suite SHALL be audited for effectiveness to ensure that heavily mocked unit or UI tests are supplemented with real behavioral validation (integration or contract tests).

#### Scenario: Audit identifies mock-heavy tests
- **WHEN** a test effectiveness audit is performed
- **THEN** tests identified as "mock-heavy" MUST be tagged as Valid Mock, Needs Integration Companion, or Replace

#### Scenario: Critical path validation
- **WHEN** a regression is introduced into a critical system path (e.g., location ingestion, positioning logic)
- **THEN** at least one non-trivial integration or contract test MUST fail, demonstrating that the suite provides real behavioral protection

### Requirement: Negative path and failure mode coverage
The test suites SHALL include explicit coverage for negative paths, edge cases, and system failure modes.

#### Scenario: Invalid MQTT payload ingestion
- **WHEN** the ingestion pipeline receives a malformed or unauthorized MQTT payload
- **THEN** a corresponding negative-path test MUST verify that the system rejects the payload and logs the audit event without crashing

#### Scenario: WebSocket disconnection handling
- **WHEN** a live map client experiences a sudden WebSocket disconnection
- **THEN** the frontend test suite MUST verify that the client attempts a graceful reconnect and notifies the user (Carlos)

### Requirement: Coverage measurement and CI enforcement
The RTLS Analytics Platform SHALL measure code coverage for API, web, and mobile workspaces and enforce minimum quality gates in the CI pipeline.

#### Scenario: Pull request fails due to coverage drop
- **WHEN** a developer submits a pull request that drops code coverage below the defined line or branch thresholds
- **THEN** the CI gate MUST fail and block the merge until coverage is restored or the drop is justified

#### Scenario: Traceability gate enforcement
- **WHEN** a new feature is added without corresponding updates to the traceability matrix
- **THEN** the CI quality gate MUST fail, ensuring that documentation and testing remain in sync

### Requirement: Verification and residual risk reporting
The system SHALL generate a final verification report summarizing the results of the full test matrix execution and any residual test debt.

#### Scenario: Full test matrix execution
- **WHEN** the complete suite (API, web, mobile, workspace) is executed
- **THEN** a report MUST be published listing all added/updated tests, coverage deltas, and remaining risks with their rationale
