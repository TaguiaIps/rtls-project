## Why

The current Operations Overview provides a summary of site and floor health but lacks immediate visibility into critical operational performance indicators, specifically active alerts and SLA compliance. Carlos Mendes (Operations Manager) currently needs to navigate to the separate Alerts Center or Analytics reports to understand if the service is meeting targets. Integrating these KPIs directly into the overview enables faster triage and provides a unified "pulse" of the operation.

## What Changes

- **Alert KPIs**: Integration of high-level alert counts (Total Active, Critical, and Warning) into the dashboard.
- **SLA Performance KPIs**: Visualization of current SLA breach counts and success rates for the selected timeframe.
- **Trend Analysis**: Visual indicators showing whether SLA performance is improving or degrading compared to the previous period.
- **Integrated Drilldowns**: Actionable links on KPI cards that navigate users directly to the filtered Alerts Center queue or specific Analytics reports.
- **Backend Aggregations**: New efficient database queries to provide real-time KPI summaries without full report generation overhead.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `operations-overview-dashboard`: Extend the overview data contract and UI to include alert and SLA performance summaries with drilldown support.

## Impact

- **Backend (API)**: New aggregation logic in the operations overview service to query alert and event tables.
- **Frontend (Web)**: New KPI card components and updated layout for the Operations Overview page.
- **Contracts**: Update `OperationsOverviewResponse` in `packages/contracts` to include the new KPI structures.
- **Performance**: Requires optimized queries on `alerts` and `event_derived_sla` tables to maintain dashboard responsiveness.
