## Why

Recent development waves have significantly increased the application's surface area, but the current test suite relies heavily on mocked unit and UI tests. This creates a risk of shallow confidence where tests pass but real-world behavioral regressions could still occur. Hardening test effectiveness and coverage ensures the platform remains stable as it approaches production-grade maturity.

## What Changes

- **Traceability Matrix**: Establish a formal mapping between OpenSpec acceptance criteria and executable tests across all active specifications.
- **Effectiveness Audit**: Audit the existing test suite to identify "mock-heavy" tests that lack real behavioral validation and refactor them into integration or contract tests where necessary.
- **Coverage Hardening**: Implement mandatory coverage reporting and quality gates (line and branch thresholds) in the CI pipeline for API, web, and mobile workspaces.
- **Scenario Expansion**: Add missing test scenarios for previously unverified criteria, including negative paths and complex failure modes.
- **Cross-Layer Validation**: Standardize a testing strategy that includes unit (logic), integration (module interactions), contract (boundaries), and end-to-end (user journeys) validation.

## Capabilities

### New Capabilities
- `test-quality-hardening`: Defines the requirements for test effectiveness, coverage thresholds, traceability mapping, and the execution of the full test matrix.

### Modified Capabilities
- None

## Impact

- **CI/CD Pipeline**: New quality gates will be integrated to enforce coverage and traceability.
- **Developer Workflow**: Developers will be required to maintain traceability between new features and tests.
- **Test Suites**: Significant updates to existing tests in `apps/api`, `apps/web`, and `apps/mobile`.
