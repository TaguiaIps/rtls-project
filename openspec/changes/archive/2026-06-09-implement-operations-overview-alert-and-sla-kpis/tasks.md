## 1. Contracts and Schemas

- [x] 1.1 Update `OperationsOverviewKpisResponse` in `apps/api/src/rtls_api/schemas.py` with Alert and SLA fields
- [x] 1.2 Update shared contracts in `packages/contracts` if applicable (mirroring schema changes)

## 2. Backend Implementation: Aggregations

- [x] 2.1 Implement `_query_active_alert_counts` in `apps/api/src/rtls_api/operations_overview.py`
- [x] 2.2 Implement `_query_sla_performance_stats` for current and previous monitoring windows
- [x] 2.3 Add logic to calculate SLA success rate trend (+/- percentage)
- [x] 2.4 Update `get_operations_overview` to populate the new KPI fields using the aggregation methods

## 3. Frontend Implementation: UI Components

- [x] 3.1 Create `AlertKpiCard` component with severity-based coloring and counts
- [x] 3.2 Create `SlaPerformanceKpiCard` component with success rate and trend indicator
- [x] 3.3 Update `OperationsOverview` dashboard layout to include the new Alert and SLA KPI sections
- [x] 3.4 Implement drilldown navigation logic (e.g., clicking Alert card redirects to `/alerts?severity=critical`)

## 4. Verification and Testing

- [x] 4.1 Add backend unit tests for alert and SLA aggregation logic
- [x] 4.2 Add integration tests for the updated `/api/operations/overview` endpoint
- [x] 4.3 Add frontend component tests for the new KPI cards
- [x] 4.4 Verify drilldown links navigate to correctly filtered detailed views
