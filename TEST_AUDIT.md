# Test Effectiveness Audit

> Scores every existing test by its regression detection strength and identifies candidates for refactoring.
> **Strength levels:**
> - **High**: Integration or contract tests using real databases, real services, or real boundary models.
> - **Medium**: Pure unit tests that exercise real logic without mocks but lack cross-module coverage.
> - **Low**: Mock-heavy tests that only verify internal state transitions without exercising cross-module logic.

## Strength Distribution

| Workspace | Files | High | Medium | Low | Total |
|-----------|-------|------|--------|-----|-------|
| `apps/api` | 12 | 11 | 0 | 1 | 60 |
| `apps/web` | 4 | 0 | 0 | 4 | 9 |
| `apps/mobile` | 5 | 0 | 4 | 1 | 31 |
| **Total** | **21** | **11** | **4** | **6** | **100** |

## API Tests (`apps/api/tests/`)

### High Strength (11 files — real integration)

| File | Tests | Notes |
|------|-------|-------|
| `test_alerts.py` | 5 | Real SQLite, real ingestion, real alert pipeline. 1 monkeypatch for email sender. |
| `test_analytics.py` | 6 | Real DB, real rollup processing, real export job lifecycle. |
| `test_auth_flow.py` | 5 | Real JWT, real refresh rotation, real audit events, real bootstrap. |
| `test_calibration.py` | 7 | Real DB, real processing pipeline. MagicMock for object storage blob only. |
| `test_derived_events.py` | 3 | Real ingestion → positioning → derived events pipeline. |
| `test_ingestion.py` | 5 | Real DB, real heartbeat processing. 1 monkeypatch for MQTT client fake. |
| `test_live_locations.py` | 4 | Real DB, real WebSocket via FastAPI TestClient. |
| `test_mqtt_tls.py` | 5 | Real TLS sockets + running Mosquitto broker (4 tests). 1 unit test for TLS config. |
| `test_observability.py` | 4 | Real DB, real data lifecycle, real Prometheus metrics. |
| `test_operations_overview.py` | 5 | Real DB, real ingestion, real KPI computation. |
| `test_premium_tier.py` | 3 | Real DB, real UWB trilateration, real tier supersession. |

**Tag:** `Valid Mock` — The few monkeypatches (email sender, MQTT client, object storage, TLS context) are justified for isolating external side-effects while preserving real cross-module logic.

### Needs Attention

| File | Tests | Issue |
|------|-------|-------|
| `test_spatial_admin.py` | 8 | Primarily high strength. 1 monkeypatch for fault-injection rollback test — **Valid Mock**. |

## Web Tests (`apps/web/src/`)

### Low Strength (4 files — mock-heavy)

| File | Tests | Issue | Refactoring Tag |
|------|-------|-------|----------------|
| `App.test.tsx` | 1 | `globalThis.fetch` fully mocked. Tests only that unauthenticated state renders a sign-in screen. No real API interaction. | `Needs Integration Companion` |
| `auth.test.tsx` | 1 | `globalThis.fetch` replaced with stateful mock simulating token lifecycle. Tests refresh concurrency guard only — pure logic but no real server validation. | `Valid Mock` (pure concurrency logic) |
| `admin.test.tsx` | 2 | `globalThis.fetch` fully routed by URL pattern. Full `<App />` tree rendered against fake responses. No real backend validation. | `Needs Integration Companion` |
| `operations.test.tsx` | 5 | `globalThis.fetch` + custom `MockWebSocket` class. Full `<App />` tree. Tests UI behavior against fake data — no real API/WebSocket validation. | `Needs Integration Companion` |

**Critical path impact:** The operations.test.tsx covers Overview, Live Map, Alerts, and Analytics workspaces — all critical operational paths. If a backend endpoint shape changes, these mock-routed tests will still pass, providing false confidence.

### Refactoring Priority (Web)

1. **`operations.test.tsx`** — HIGH PRIORITY: Covers 5 critical operational routes. Should have at least one integration companion that hits real API endpoints (matching `test_operations_overview.py` and `test_alerts.py` patterns).
2. **`admin.test.tsx`** — MEDIUM PRIORITY: Covers Health and Audit workspaces. Backend counterparts exist (`test_observability.py`) but web-to-backend contract is not verified.
3. **`App.test.tsx`** — LOW PRIORITY: Minimal test surface (1 test), mostly covered by `test_auth_flow.py` on the backend.
4. **`auth.test.tsx`** — LOW PRIORITY: Tests a valid concurrency guard pattern. The mock is appropriate for this pure-logic test.

## Mobile Tests (`apps/mobile/test/`)

### Medium Strength (4 files — pure unit, no mocks)

| File | Tests | Notes |
|------|-------|-------|
| `smoke.test.ts` | 1 | Reads real `app.json` from disk. |
| `assetFinder.test.ts` | 6 | Pure unit tests against helper functions. Uses contract types. No mocks. |
| `commissioning.test.ts` | 6 | Pure unit tests against helper functions. Uses contract types. No mocks. |
| `selfLocation.test.ts` | 7 | Pure unit tests for Kalman filter and movement threshold. No mocks. |

**Tag:** `Valid Mock` — These are genuine unit tests for pure functions. They don't need integration companions.

### Low Strength (1 file — mock-heavy)

| File | Tests | Issue | Refactoring Tag |
|------|-------|-------|----------------|
| `useSelfLocation.test.ts` | 3 | `globalThis.WebSocket` fully replaced. React hooks (`useState`, `useEffect`, `useCallback`, `useRef`) all mocked. Tests imperative side effects without real React rendering. | `Replace` |

**Critical path impact:** The `useSelfLocation` hook is the core real-time location streaming mechanism for mobile. If WebSocket URL construction or message parsing changes, this test structure (mocking React internals) is fragile and may break on React version upgrades.

### Refactoring Priority (Mobile)

1. **`useSelfLocation.test.ts`** — HIGH PRIORITY: Should be rewritten to use `@testing-library/react` `renderHook` instead of mocking React internals. The WebSocket mock can remain but the React hook mocking should be eliminated.

## Cross-Cutting Findings

### 1. API test suite is high-quality (11/12 high strength)
The backend test suite is overwhelmingly integration-focused with real SQLite databases, real service instances, and real HTTP/WebSocket endpoints. This is a strong foundation. The few monkeypatches are justified.

### 2. Web test suite is entirely mock-dependent (4/4 low strength)
All web tests replace `globalThis.fetch` and render against fake data. While this provides fast UI-level regression detection, it creates a gap: if the backend API contract changes shape, the web tests will not catch it.

### 3. Mobile test suite has a good unit test core with one problematic hook test
4 out of 5 mobile test files are pure unit tests with no mocking — excellent. The `useSelfLocation.test.ts` file mocks React internals, which is fragile.

### 4. No negative-path tests for API boundaries
The API tests cover happy paths and validation errors, but there are no explicit tests for:
- Malformed MQTT payload rejection (covered implicitly in `test_ingestion.py`)
- WebSocket disconnection handling (not tested)
- Concurrent session conflicts
- Rate limiting behavior

### 5. No tests for shared packages
`packages/contracts` and `packages/config` have zero tests. These contain type definitions and configuration used by all three applications.

## Recommended Refactoring Actions

| Priority | File | Action | Rationale |
|----------|------|--------|-----------|
| P0 | `apps/web/src/operations.test.tsx` | Add integration companion: at least 1 test hitting real `/api/operations/overview` endpoint via a shared test harness | Critical path — if backend shape changes, all 5 tests give false confidence |
| P0 | `apps/mobile/test/useSelfLocation.test.ts` | Rewrite using `renderHook` instead of mocking React internals | Fragile mock structure, will break on React upgrades |
| P1 | `apps/web/src/admin.test.tsx` | Add integration companion for Health and Audit workspaces | Backend counterparts exist; web-to-backend contract unverified |
| P2 | `packages/contracts/` | Add basic type-validation or serialization tests | Zero coverage on shared types used across all apps |
| P2 | `apps/web/src/App.test.tsx` | Add minimal integration test verifying real 401 handling | Low priority — auth is well-tested on backend |
