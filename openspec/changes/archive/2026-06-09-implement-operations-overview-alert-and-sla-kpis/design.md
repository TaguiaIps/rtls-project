## Context

The Operations Overview currently focuses on site and floor inventory health (active assets, stale gateways, restricted zone entries). However, Carlos Mendes needs to see the status of higher-level operational events like Alerts and SLA compliance to effectively manage the floor. This design extends the overview to include these signals, leveraging existing Alert and SLA data structures.

## Goals / Non-Goals

**Goals:**
- Add Alert and SLA KPIs to the Operations Overview.
- Provide trend analysis for SLA performance.
- Implement efficient backend aggregations for these new KPIs.
- Enable direct navigation from KPI cards to detailed views with pre-applied filters.

**Non-Goals:**
- Creating new types of alerts or SLA measurements.
- Redesigning the entire Operations Overview layout (focus on adding new sections).

## Decisions

### 1. Unified KPI Aggregation Service
We will implement a new internal service method in the `OperationsOverview` module to handle the aggregation of Alerts and SLA metrics.
- **Rationale**: Keeps the `get_operations_overview` endpoint clean and allows for reuse of aggregation logic.
- **Implementation**: This service will perform lightweight counts on `alert_instances` and `analytics_table_sla_hourly_rollups`.

### 2. Time Window for SLA Trends
SLA trends will be calculated by comparing the "Current Window" (e.g., last 1 hour) with the "Previous Window" (e.g., the hour before that).
- **Rationale**: Provides immediate operational context for performance degradation or improvement.
- **Decision**: The default window for the overview will be the last 60 minutes.

### 3. KPI Drilldown Protocol
Drilldown will be handled via URL parameters in the frontend.
- **Alerts**: Navigate to `/alerts` with `status=unresolved` and `severity=critical` (or other).
- **SLA**: Navigate to `/analytics/sla` with site/floor context and timeframe.

### 4. Efficient Database Queries
To avoid performance hits on the overview, we will:
- Use indexes on `alert_instances` (site_id, status, severity).
- Query `analytics_table_sla_hourly_rollups` for SLA history rather than re-calculating from raw events.

## Risks / Trade-offs

- **[Risk] High Query Latency on Large Datasets** → **Mitigation**: Ensure proper indexing on `alert_instances` and use rollup tables for SLA metrics.
- **[Risk] Drifting SLA Definitions** → **Mitigation**: Use a shared constant for SLA threshold calculations across Analytics and Overview.
- **[Trade-off] Real-time vs. Periodic Rollups** → **Decision**: Alerts will be real-time (total count), while SLA metrics will use the latest available hourly rollups + partial current hour from the `table_service_timers` state.

## Migration Plan

1. **Contract Update**: Add new fields to `OperationsOverviewKpisResponse` in `packages/contracts`.
2. **Backend**: Implement the aggregation logic and update the `/api/operations/overview` endpoint.
3. **Frontend**: Add new KPI card components and update the dashboard layout.
4. **Validation**: Verify counts match the Alerts Center and Analytics reports.
