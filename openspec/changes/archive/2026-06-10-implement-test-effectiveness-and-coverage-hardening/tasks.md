## 1. Traceability and Inventory

- [x] 1.1 Read all active OpenSpec specifications and extract normative acceptance criteria.
- [x] 1.2 Initialize `TEST_TRACEABILITY.md` in the root directory with the extracted criteria.
- [x] 1.3 Map existing tests in `apps/api`, `apps/web`, and `apps/mobile` to the traceability matrix.
- [x] 1.4 Identify "Uncovered" and "Partially Covered" criteria for prioritization.

## 2. Effectiveness Audit

- [x] 2.1 Audit existing test suites for mock overuse and regression detection strength.
- [x] 2.2 Document audit findings in `TEST_AUDIT.md`, tagging tests for refactoring.
- [x] 2.3 Prioritize "Low Strength" tests affecting critical paths (Ingestion, Positioning, Auth).

## 3. Coverage and Quality Gate Setup

- [x] 3.1 Install and configure `pytest-cov` in `apps/api/pyproject.toml`.
- [x] 3.2 Configure `vitest` coverage (v8) in `apps/web/vite.config.ts`.
- [x] 3.3 Configure `vitest` coverage in `apps/mobile/package.json` or corresponding config.
- [x] 3.4 Define line and branch coverage thresholds for each workspace.
- [x] 3.5 Update GitHub Actions workflows to enforce coverage and traceability gates.

## 4. Test Hardening Implementation

- [x] 4.1 Refactor "Low Strength" tests identified in the audit into integration or contract tests.
- [x] 4.2 Implement missing test scenarios for uncovered acceptance criteria.
- [x] 4.3 Add negative-path tests for API boundaries and mobile hardware interactions.
- [x] 4.4 Implement at least one "Deep" integration test for the Location Ingestion to Positioning pipeline.

## 5. Verification and Reporting

- [x] 5.1 Execute the full test matrix across all workspaces (`make test`).
- [x] 5.2 Generate final coverage reports for all applications.
- [x] 5.3 Publish the `Final Verification Report` summarizing added tests, coverage deltas, and residual risks.
- [ ] 5.4 Archive the `implement-test-effectiveness-and-coverage-hardening` change after validation.
