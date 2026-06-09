## Context

The current test suite across `apps/api`, `apps/web`, and `apps/mobile` primarily focuses on isolated unit tests with significant mocking of external dependencies (e.g., database, MQTT broker, hardware APIs). While this ensures fast execution, it leaves a gap in validating the real integration between modules and system boundaries. This design addresses the need for behavioral hardening through better traceability, effectiveness auditing, and enforced coverage gates.

## Goals / Non-Goals

**Goals:**
- Implement a spec-to-test traceability matrix.
- Establish a "Behavioral Validation First" policy for critical paths.
- Enforce coverage thresholds in CI.
- Expand test coverage to include negative paths and complex failure modes.

**Non-Goals:**
- Complete removal of mocks (mocks are still essential for isolation).
- Full end-to-end automation of every possible UI state.
- Performance profiling of the production system.

## Decisions

### 1. Spec-to-Test Traceability Matrix
We will establish a root-level `TEST_TRACEABILITY.md` file that maps every requirement ID from OpenSpec specifications (e.g., `FR-ADM-001`) to specific test files and scenario names.

- **Format**: A Markdown table with columns: `Spec ID`, `Requirement`, `Test File`, `Scenario`, `Status` (Covered/Partial/Uncovered).
- **Maintenance**: Developers must update this matrix as part of any feature implementation or test hardening task.

### 2. Test Effectiveness Scoring (Audit)
Existing tests will be audited and scored based on their "Regression Detection Strength."
- **High Strength**: Integration or contract tests using real/ephemeral databases (Postgres/Redis) or real boundary models.
- **Low Strength**: Mock-heavy unit tests that only verify internal state transitions without exercising cross-module logic.
- **Outcome**: Tests scored as "Needs Integration Companion" will be prioritized for refactoring.

### 3. Coverage Enforcement Strategy
We will utilize the following tools to measure and enforce coverage:
- **Backend (apps/api)**: `pytest-cov` with a target threshold of 80% line coverage and 70% branch coverage.
- **Frontend (apps/web & apps/mobile)**: `vitest` coverage (via `v8`) with a target threshold of 75% line coverage.
- **CI Integration**: GitHub Actions will be configured to fail if a pull request reduces coverage or fails to update the traceability matrix for new requirements.

### 4. Cross-Layer Testing Tiers
We will standardize on a 4-tier testing hierarchy:
1. **Unit (Vitest/Pytest)**: Fast logic validation.
2. **Integration (Pytest + Ephemeral DB)**: Validates database interactions and complex business logic.
3. **Contract/Boundary (Httpx/Supertest)**: Verifies API request/response compliance against `packages/contracts`.
4. **End-to-End (Critical Flows)**: Verifies the "Happy Path" of core user journeys (e.g., Asset Search to Selection).

## Risks / Trade-offs

- **[Risk] Test Runtime Growth** → Mitigation: Use parallel test execution in CI and isolate heavy integration tests to a "Pre-Merge" gate instead of every commit.
- **[Risk] Brittle Integration Tests** → Mitigation: Use database migrations and seed data scripts to ensure a consistent test environment for every run.
- **[Risk] Maintenance Overhead of Traceability Matrix** → Mitigation: The matrix is required for project governance; the benefit of clear gap analysis outweighs the manual update cost.
