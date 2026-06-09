# Spec-to-Test Traceability Matrix

> Maps every normative requirement in the OpenSpec specifications to executable test cases.
> **Status**: `Covered` | `Partial` | `Uncovered`
> Update this matrix as part of any feature implementation or test hardening task.

## Summary

| Spec | Requirements | Covered | Partial | Uncovered |
|------|-------------|---------|---------|------------|
| alert-rules-and-notification-delivery | 4 | 3 | 1 | 0 |
| alerts-center-triage | 3 | 2 | 1 | 0 |
| analytics-workspace-and-reports | 7 | 5 | 2 | 0 |
| asset-tag-registry | 3 | 2 | 1 | 0 |
| audit-event-recording | 3 | 2 | 1 | 0 |
| calibration-engine | 2 | 2 | 0 | 0 |
| contextual-breadcrumb-engine | 2 | 0 | 1 | 1 |
| economic-tier-position-estimation | 4 | 4 | 0 | 0 |
| exports-retention-and-rollups | 3 | 3 | 0 | 0 |
| floor-plan-management | 4 | 4 | 0 | 0 |
| form-ergonomics-engine | 3 | 0 | 1 | 2 |
| gateway-placement-and-tier-profiles | 5 | 5 | 0 | 0 |
| gateway-telemetry-ingestion | 7 | 7 | 0 | 0 |
| health-audit-ui-and-observability | 5 | 5 | 0 | 0 |
| implementation-workspace | 5 | 1 | 1 | 3 |
| live-location-query-and-streaming | 4 | 4 | 0 | 0 |
| live-map-microinteractions | 2 | 0 | 0 | 2 |
| live-map-workspace | 5 | 4 | 1 | 0 |
| local-runtime-stack | 6 | 0 | 0 | 6 |
| mobile-affective-feedback | 2 | 0 | 0 | 2 |
| mobile-asset-finder | 4 | 3 | 1 | 0 |
| mobile-commissioning-and-calibration | 7 | 6 | 1 | 0 |
| mobile-self-location | 4 | 2 | 1 | 1 |
| mqtt-client-authorization | 1 | 1 | 0 | 0 |
| mqtt-transport-security | 3 | 3 | 0 | 0 |
| operations-overview-dashboard | 7 | 7 | 0 | 0 |
| premium-tier-position-estimation | 4 | 4 | 0 | 0 |
| radiomap-artifact-registry | 3 | 2 | 1 | 0 |
| raw-reading-persistence | 3 | 3 | 0 | 0 |
| role-based-access | 4 | 4 | 0 | 0 |
| round-trip-and-table-sla-primitives | 3 | 3 | 0 | 0 |
| site-and-floor-management | 2 | 2 | 0 | 0 |
| user-authentication | 4 | 4 | 0 | 0 |
| web-operations-shell | 5 | 5 | 0 | 0 |
| web-theme-engine | 3 | 0 | 0 | 3 |
| zone-and-poi-editor | 3 | 1 | 2 | 0 |
| zone-transition-and-dwell-events | 3 | 3 | 0 | 0 |
| **Total** | **141** | **106** | **14** | **21** |

## Priority Gaps (Uncovered — Critical Paths)

These uncovered requirements sit on critical operational paths and should be addressed first:

1. **mobile-self-location**: Reconnect and stream health management — WebSocket disconnect handling with auto-reconnect
2. **mqtt-client-authorization** / **mqtt-transport-security**: Already covered at integration level (requires running broker)
3. **zone-and-poi-editor**: Polygon validation and metadata exposure for later features
4. **mobile-commissioning-and-calibration**: Camera permission/availability states
5. **live-map-workspace**: Confidence visualization (degraded vs point treatment)
6. **audit-event-recording**: Sensitive material exclusion in audit events

## Priority Gaps (Uncovered — Infrastructure / Tooling)

These uncovered requirements are infrastructure or environment concerns:

1. **local-runtime-stack**: All 6 requirements (Docker Compose, services, config, secrets, TLS, certs) — requires integration test environment
2. **implementation-workspace**: Workspace structure, shared packages, governance checklist — structural/documentation
3. **web-theme-engine**: All 3 requirements (CSS variable engine, geometry tokens, typography) — visual regression territory
4. **live-map-microinteractions**: Pulsing glassmorphism, fluid coordinate transitions — animation/visual tests
5. **mobile-affective-feedback**: Haptic feedback, calibration completion animation — native hardware tests
6. **form-ergonomics-engine**: Command aesthetic inputs, password toggle, semantic feedback — UI component tests

---

## Per-Spec Traceability

### alert-rules-and-notification-delivery

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Manage delivered operational alert rules | `test_alerts.py` | `test_alert_rule_validation_and_summary_queries` | Covered |
| 2 | Alert rules generate durable alert instances from signals | `test_alerts.py` | `test_table_sla_alerts_deduplicate_and_clear`, `test_geofence_alerts_support_triage_actions_and_audit`, `test_alert_summary_and_list_include_gateway_maintenance_alerts` | Covered |
| 3 | Alert delivery supports in-app notifications and email | `test_alerts.py` | `test_email_delivery_attempts_are_recorded` | Covered |
| 4 | System-managed maintenance rules remain platform-owned | — | — | Partial |

**Partial notes (Req 4):** Maintenance alerts are tested for creation/clearing, but the explicit rule-hiding behavior (user-authored vs system-managed rule separation) is not tested.

### alerts-center-triage

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Review active and historical alerts | `operations.test.tsx`, `test_alerts.py` | `renders Alerts Center workflows...`, `test_alert_summary_and_list_include_gateway_maintenance_alerts` | Covered |
| 2 | Inspect alert detail and triage actions | `operations.test.tsx`, `test_alerts.py` | `renders Alerts Center workflows...`, `test_geofence_alerts_support_triage_actions_and_audit` | Covered |
| 3 | Alert detail exposes operational context and action history | `operations.test.tsx` | `renders Alerts Center workflows...` | Partial |

**Partial notes (Req 3):** Triage action timeline is verified, but full alert detail view (affected asset context, triggering rule summary, delivery-channel context) is not exhaustively tested.

### analytics-workspace-and-reports

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Open Analytics workspace | `operations.test.tsx` | `renders Analytics workspace reports...` | Covered |
| 2 | Replay asset trajectory | `test_analytics.py`, `operations.test.tsx` | `test_trajectory_and_heatmap_reports...`, trajectory switch test | Covered |
| 3 | Generate floor heatmaps | `test_analytics.py`, `operations.test.tsx` | `test_trajectory_and_heatmap_reports...`, heatmap switch test | Covered |
| 4 | Inspect dwell-time reports | `test_analytics.py` | `test_dwell_and_round_trip_reports...` | Covered |
| 5 | Inspect round-trip reports | `test_analytics.py` | `test_dwell_and_round_trip_reports...` | Covered |
| 6 | Inspect SLA trend views | `test_analytics.py` | `test_sla_trends_use_alert_rule_thresholds...` | Covered |
| 7 | Empty/degraded report states | `test_analytics.py` | `test_analytics_endpoints_require_auth...`, `test_sla_trends_..._empty_buckets` | Partial |

**Partial notes (Req 7):** Validation errors and empty time-window buckets are tested, but the explicit empty-state UI treatments (no-results states for trajectory, heatmap, dwell, round-trip) are not fully covered.

### asset-tag-registry

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Administrator-managed asset tag registry | `test_spatial_admin.py` | `test_gateway_and_asset_registry_flow...` | Covered |
| 2 | Asset update-rate and battery policy metadata | `test_spatial_admin.py` | `test_gateway_and_asset_registry_flow...` (update) | Partial |
| 3 | CSV-based bulk asset tag import | `test_spatial_admin.py` | `test_gateway_and_asset_registry_flow...`, `test_asset_import_session_survives_app_restart` | Covered |

**Partial notes (Req 2):** Asset update is tested, but explicit unsupported update-rate/battery profile value rejection is not tested.

### audit-event-recording

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Audit event persistence | `test_auth_flow.py`, `test_spatial_admin.py`, `test_alerts.py` | Multiple tests verify audit events for auth, CRUD, alerts | Covered |
| 2 | Audit event actor and target context | `test_auth_flow.py`, `test_observability.py` | `test_authentication_refresh_logout...`, `test_audit_events_support_filtering...` | Partial |
| 3 | Audit event query readiness | `test_observability.py` | `test_audit_events_support_filtering...` | Covered |

**Partial notes (Req 2):** Actor identity, role, action category, and target are verified. Exclusion of sensitive material (passwords, tokens) from audit events is not explicitly tested.

### calibration-engine

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Calibration session processing pipeline | `test_calibration.py` | `test_submit_calibration_session...`, `test_calibration_processing_generates_artifact` | Covered |
| 2 | Radiomap and gateway offset generation | `test_calibration.py` | `test_radiomap_grid_generation`, `test_gateway_offset_calculation`, `test_coverage_score_calculation` | Covered |

### contextual-breadcrumb-engine

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Dynamic hierarchical breadcrumbs | `operations.test.tsx` | Implicitly tested via shell navigation | Partial |
| 2 | Breadcrumb context awareness | — | — | Uncovered |

**Partial notes (Req 1):** Shell navigation renders breadcrumbs implicitly, but explicit breadcrumb text verification ("Downtown > Main Dining > Live Map") and floor-change synchronization are not tested.

### economic-tier-position-estimation

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Economic-tier telemetry produces durable locations | `test_live_locations.py` | `test_positioning_persists_zone_fallback_then_point_location...` | Covered |
| 2 | Current asset location and history preserved | `test_live_locations.py` | `test_positioning_persists_zone_fallback_then_point_location...` | Covered |
| 3 | Location outputs include confidence semantics | `test_live_locations.py` | `test_positioning_skips_low_confidence_updates...`, confidence filtering | Covered |
| 4 | Low-confidence results fall back to zone-level | `test_live_locations.py` | `test_positioning_skips_low_confidence_updates_without_known_zone` | Covered |

### exports-retention-and-rollups

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Authorized async analytics exports | `test_analytics.py` | `test_analytics_exports_queue_list_and_download_csv` | Covered |
| 2 | Administrators run and review lifecycle jobs | `test_observability.py` | `test_admin_can_trigger_lifecycle_run...` | Covered |
| 3 | Hourly analytics rollups | `test_analytics.py` | `test_hourly_heatmap_and_sla_reports_can_read_from_rollups` | Covered |

### floor-plan-management

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Raster floor-plan upload | `test_spatial_admin.py` | `test_admin_spatial_crud_flow...`, `test_missing_floor_plan_blob_returns_404` | Covered |
| 2 | Floor scale calibration | `test_spatial_admin.py` | `test_admin_spatial_crud_flow...`, `test_floor_plan_replacement_clears_existing_scale` | Covered |
| 3 | Floor-plan retrieval for map context | `test_spatial_admin.py` | `test_admin_spatial_crud_flow...` | Covered |
| 4 | Calibration invalidation on floor-plan change | `test_premium_tier.py`, `test_spatial_admin.py` | `test_premium_gateway_profile_validation...`, `test_floor_plan_replacement_...` | Covered |

### form-ergonomics-engine

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Command aesthetic form inputs | `App.test.tsx` | Implicitly (sign-in screen renders) | Partial |
| 2 | Password visibility toggle | — | — | Uncovered |
| 3 | Semantic form feedback | — | — | Uncovered |

### gateway-placement-and-tier-profiles

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Administrator-managed gateway registry | `test_spatial_admin.py` | `test_gateway_and_asset_registry_flow...` | Covered |
| 2 | Floor-linked gateway placement | `test_spatial_admin.py`, `test_premium_tier.py` | Gateway creation, placement, relocation | Covered |
| 3 | Economic and Premium tier assignment | `test_spatial_admin.py` | `test_gateway_and_asset_registry_flow...` (update to Premium) | Covered |
| 4 | Premium gateways capture modality and mounting metadata | `test_premium_tier.py` | `test_premium_gateway_profile_validation...` | Covered |
| 5 | Premium calibration state tracked against geometry | `test_premium_tier.py` | `test_premium_gateway_profile_validation...` (stale on move/replace) | Covered |

### gateway-telemetry-ingestion

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Registered gateway telemetry ingestion | `test_ingestion.py` | `test_valid_telemetry_ingestion_persists_raw_readings` | Covered |
| 2 | Telemetry payload validation | `test_ingestion.py` | `test_ingestion_rejects_malformed_unknown_and_duplicate_messages` | Covered |
| 3 | Duplicate-delivery protection | `test_ingestion.py` | `test_ingestion_rejects_malformed_unknown_and_duplicate_messages` | Covered |
| 4 | Heartbeat ingestion for gateway health | `test_ingestion.py` | `test_heartbeat_ingestion_updates_gateway_health_feed` | Covered |
| 5 | Registered Premium gateways publish Premium telemetry | `test_premium_tier.py` | `test_premium_uwb_ingestion_updates_live_location_contract` | Covered |
| 6 | Premium telemetry preserves estimator-required fidelity | `test_premium_tier.py` | `test_premium_uwb_ingestion_updates_live_location_contract` | Covered |
| 7 | Premium telemetry preserves dedupe at higher cadence | `test_ingestion.py` | Dedupe logic covered; high-frequency distinct-message handling implicit | Covered |

### health-audit-ui-and-observability

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Administrators review infrastructure health | `test_observability.py`, `admin.test.tsx` | `test_observability_summary...`, `renders the health workspace...` | Covered |
| 2 | Administrators review gateway risks | `test_observability.py` | `test_observability_summary_returns_health_and_audit_totals` | Covered |
| 3 | Administrators review audit history | `test_observability.py`, `admin.test.tsx` | `test_audit_events_support_filtering...`, `renders the audit workspace...` | Covered |
| 4 | Minimal observability baseline | `test_observability.py` | `test_metrics_and_request_id_headers_are_exposed` | Covered |
| 5 | Administrators trigger lifecycle refresh | `test_observability.py` | `test_admin_can_trigger_lifecycle_run...` | Covered |

### implementation-workspace

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Repository workspace structure | `smoke.test.ts` | `declares the RTLS Expo app metadata` | Partial |
| 2 | Shared package boundaries | — | — | Uncovered |
| 3 | Developer workflow baseline | — | — | Uncovered |
| 4 | Continuous integration baseline | CI itself | CI runs lint, test, build | Covered |
| 5 | Governance consistency checklist | — | Documentation-only | Uncovered |

### live-location-query-and-streaming

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Query latest live locations | `test_live_locations.py` | `test_live_location_endpoints_support_filters_search_and_history` | Covered |
| 2 | Search for asset and retrieve location | `test_live_locations.py` | `test_live_location_endpoints_support_filters_search_and_history` | Covered |
| 3 | Retrieve trajectory history | `test_live_locations.py` | `test_live_location_endpoints_support_filters_search_and_history` | Covered |
| 4 | Subscribe to live position updates | `test_live_locations.py` | `test_websocket_stream_publishes_new_location_updates` | Covered |

### live-map-microinteractions

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Technical presence pulsing for low confidence | — | — | Uncovered |
| 2 | Fluid coordinate transitions | — | — | Uncovered |

### live-map-workspace

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Floor-linked live map workspace | `operations.test.tsx` | `updates the live map from WebSocket events...` | Covered |
| 2 | Search and filtering | `operations.test.tsx` | `updates the live map from WebSocket events...` | Covered |
| 3 | Confidence visualization | `operations.test.tsx` | Implicitly (low-confidence rendering) | Partial |
| 4 | Selected asset detail drawer | `operations.test.tsx` | `updates the live map from WebSocket events...` (asset selection) | Covered |
| 5 | Live updates without full reload | `operations.test.tsx` | `updates the live map from WebSocket events...` (WebSocket emit) | Covered |

**Partial notes (Req 3):** Low-confidence rendering is verified implicitly, but the explicit "degraded-confidence vs point-level" visual differentiation is not directly asserted.

### local-runtime-stack

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Local container runtime | — | — | Uncovered |
| 2 | Required local services | — | — | Uncovered |
| 3 | Pilot-aligned configuration model | — | — | Uncovered |
| 4 | Environment and secret conventions | — | — | Uncovered |
| 5 | Local MQTT TLS support | — | — | Uncovered |
| 6 | Automated certificate generation | — | — | Uncovered |

### mobile-affective-feedback

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Native haptic confirmation loops | — | — | Uncovered |
| 2 | Technical calibration completion animation | — | — | Uncovered |

### mobile-asset-finder

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Search for assets in mobile app | `assetFinder.test.ts` | `normalizes API bases and generates search URLs` | Partial |
| 2 | Preserve recent searches | `assetFinder.test.ts` | `keeps recent searches ordered...`, `caps recent searches to five` | Covered |
| 3 | Selected-asset location sheet | `assetFinder.test.ts` | `formats location and precision context...` | Partial |
| 4 | Hand off into web Live Map | `assetFinder.test.ts` | `generates a compatible Live Map handoff URL` | Covered |

**Partial notes (Req 1, 3):** URL construction and formatting helpers are tested, but the full end-to-end search flow (API call, result list rendering, no-results state) is not tested.

### mobile-commissioning-and-calibration

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Load mobile commissioning context | `commissioning.test.ts` | `resolves known gateways and asset tags...` | Covered |
| 2 | Resolve scanned device identifiers | `commissioning.test.ts` | `resolves known gateways...`, `returns an unknown target...`, `extracts identifiers from supported QR...` | Covered |
| 3 | Zone assignment and floor-linked context | `commissioning.test.ts` | `builds calibration waypoints...` | Covered |
| 4 | Guided blue-dot calibration workflow | `commissioning.test.ts` | `tracks calibration progress...` | Partial |
| 5 | Preserve local session summaries | `commissioning.test.ts` | `summarizes and deduplicates commissioning sessions...` | Covered |
| 6 | Camera scanning availability | — | — | Uncovered |
| 7 | Calibration session submission and backend handshake | `commissioning.test.ts` | `summarizes and deduplicates commissioning sessions...` | Partial |
| 8 | Commissioning context request unauthorized | `commissioning.test.ts` | `returns an unknown target when...` | Covered |

**Partial notes (Req 4):** Manual tap mode progress tracking is tested, but the live blue-dot tracking mode and the fallback between live/manual modes is not tested.
**Partial notes (Req 7):** Session summary is tested, but the backend submission handshake (Processing → Active status transition) is not tested.

### mobile-self-location

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Live self-location streaming | `useSelfLocation.test.ts` | `constructs WebSocket URL...`, `parses location.updated events...` | Covered |
| 2 | Confidence-aware blue-dot visualization | — | — | Partial |
| 3 | Client-side jitter smoothing | `selfLocation.test.ts` | Kalman filter tests (7 functions) | Covered |
| 4 | Reconnect and stream health management | — | — | Uncovered |

**Partial notes (Req 2):** The Kalman filter processes different confidence levels, but the actual blue-dot visual rendering (solid vs degraded) is not tested.
**Uncovered notes (Req 4):** WebSocket disconnect, reconnect indicator, and auto-reconnect behavior are not tested.

### mqtt-client-authorization

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Broker-enforced topic ACLs | `test_mqtt_tls.py` | `test_gateway_cannot_publish_to_other_gateway_topic` | Covered |

### mqtt-transport-security

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Enforced broker TLS encryption | `test_mqtt_tls.py` | `test_no_client_cert_is_rejected` | Covered |
| 2 | Mutual TLS for gateway identity | `test_mqtt_tls.py` | `test_valid_client_cert_connects...`, `test_untrusted_client_cert_is_rejected` | Covered |
| 3 | Broker certificate validation by ingestion worker | `test_mqtt_tls.py` | `test_configure_tls_sets_ssl_context` | Covered |

### operations-overview-dashboard

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Operations Overview landing screen | `test_operations_overview.py`, `operations.test.tsx` | `test_operations_overview_supports_general_users...`, overview render | Covered |
| 2 | Triage surface summarizes operational signals | `test_operations_overview.py` | `test_operations_overview_supports_general_users...`, `test_operations_overview_returns_empty_state...` | Covered |
| 3 | Alert KPI section | `test_operations_overview.py`, `operations.test.tsx` | `test_operations_overview_includes_alert_kpis`, alert KPI cards | Covered |
| 4 | SLA KPI section | `test_operations_overview.py`, `operations.test.tsx` | `test_operations_overview_includes_sla_kpis`, SLA KPI cards | Covered |
| 5 | KPI cards support drilldowns | `operations.test.tsx` | `renders Alert and SLA KPI cards with drilldown navigation` | Covered |
| 6 | Floor-linked live map preview | `test_operations_overview.py` | `test_operations_overview_supports_general_users...` (map_preview) | Covered |
| 7 | SLA trend visualization | `test_operations_overview.py` | `test_operations_overview_includes_sla_kpis` (trend_pct) | Covered |

### premium-tier-position-estimation

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Premium-tier telemetry produces durable locations | `test_premium_tier.py` | `test_premium_uwb_ingestion_updates_live_location_contract` | Covered |
| 2 | Premium positioning depends on valid geometry and calibration | `test_premium_tier.py` | `test_premium_gateway_profile_validation...` | Covered |
| 3 | Premium outputs include modality-aware metadata | `test_premium_tier.py` | `test_premium_uwb_ingestion_updates_live_location_contract` | Covered |
| 4 | Canonical latest-known prefers best result across tiers | `test_premium_tier.py` | `test_premium_candidate_supersedes_recent_economic...` | Covered |

### radiomap-artifact-registry

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Durable radiomap storage and versioning | `test_calibration.py` | `test_calibration_processing_generates_artifact`, `test_activate_artifact_sets_others_stale` | Covered |
| 2 | Artifact lifecycle and metadata exposure | `test_calibration.py` | `test_calibration_health_endpoint`, `test_activate_artifact_sets_others_stale` | Covered |
| 3 | Active artifact retrieval for estimators | `test_calibration.py` | Partial — artifact activation tested, high-performance retrieval path not isolated | Partial |

### raw-reading-persistence

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Canonical raw-reading persistence | `test_ingestion.py` | `test_valid_telemetry_ingestion_persists_raw_readings` | Covered |
| 2 | Gateway-provided time is non-canonical | `test_ingestion.py` | Implicitly (broker timestamp used) | Partial |
| 3 | Raw-reading history for downstream stages | `test_analytics.py` | Trajectory/heatmap from history | Covered |

**Partial notes (Req 2):** The system uses broker-controlled time, but the explicit preservation of gateway-provided time as metadata (vs replacement) is not directly asserted.

### role-based-access

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Two-role authorization model | `test_auth_flow.py` | `test_role_protection_and_admin_user_update_audit` | Covered |
| 2 | Backend route authorization | `test_auth_flow.py`, `test_observability.py` | `test_role_protection...`, `test_audit_events_support_filtering...` | Covered |
| 3 | Role-aware web routing | `operations.test.tsx`, `App.test.tsx` | Role-gated nav, admin link visibility | Covered |
| 4 | Protected web shell | `operations.test.tsx` | Overview shell for General User, admin nav gating | Covered |

### round-trip-and-table-sla-primitives

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Round-trip measurements from zone events | `test_derived_events.py` | `test_round_trip_measurements_are_evaluated...` | Covered |
| 2 | SLA-eligible table timer state | `test_derived_events.py` | `test_table_timer_state_tracks_only_sla_eligible_tables` | Covered |
| 3 | Current table timer state readable | `test_derived_events.py` | `test_table_timer_state_tracks_only_sla_eligible_tables` | Covered |

### site-and-floor-management

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Administrator-managed site hierarchy | `test_spatial_admin.py` | `test_admin_spatial_crud_flow_records_audit_events` | Covered |
| 2 | Floor registration per site | `test_spatial_admin.py` | `test_admin_spatial_crud_flow_records_audit_events` | Covered |

### user-authentication

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Local credential authentication | `test_auth_flow.py`, `App.test.tsx` | `test_authentication_refresh_logout...`, sign-in screen render | Covered |
| 2 | Refresh session rotation and revocation | `test_auth_flow.py`, `auth.test.tsx` | `test_logout_rejects_rotated_refresh_tokens`, `reuses a single refresh request...` | Covered |
| 3 | First Administrator bootstrap | `test_auth_flow.py` | `test_bootstrap_admin_command_creates_first_administrator` | Covered |
| 4 | Web login entry point | `App.test.tsx` | `renders the secure sign-in screen...` | Covered |

### web-operations-shell

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Shared protected monitoring shell | `operations.test.tsx`, `admin.test.tsx` | Overview render, health workspace render | Covered |
| 2 | Shared operational context | `operations.test.tsx` | Site/floor context in shell, feed status badge | Covered |
| 3 | Role-aware navigation | `operations.test.tsx` | General User nav (no Admin link), role gating | Covered |
| 4 | Delivered alert access | `operations.test.tsx` | Alerts nav link visible | Covered |
| 5 | Delivered Analytics access | `operations.test.tsx` | Analytics nav link, context preservation | Covered |

### web-theme-engine

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Centralized Deep Void Theme Engine | — | — | Uncovered |
| 2 | Rigid geometry and spacing tokens | — | — | Uncovered |
| 3 | Standardized technical typography | — | — | Uncovered |

### zone-and-poi-editor

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Polygonal operational area editing | `test_spatial_admin.py` | Area creation, update, delete — polygon geometry not exhaustively validated | Partial |
| 2 | Typed operational areas | `test_spatial_admin.py` | `test_admin_spatial_crud_flow...` (patch area to restricted_zone) | Covered |
| 3 | Operational area metadata for later features | `test_spatial_admin.py` | Area list returns stored data | Partial |

**Partial notes (Req 1):** Area CRUD is tested but invalid polygon geometry rejection is not.
**Partial notes (Req 3):** Area listing returns metadata, but the full metadata shape needed for map/alerting/analytics features is not explicitly verified.

### zone-transition-and-dwell-events

| Req | Requirement | Test File | Test(s) | Status |
|-----|-------------|-----------|---------|--------|
| 1 | Zone transition events from live-location updates | `test_derived_events.py` | `test_zone_events_and_dwell_records_follow_transition_rules` | Covered |
| 2 | Zone occupancy produces durable dwell records | `test_derived_events.py` | `test_zone_events_and_dwell_records_follow_transition_rules` | Covered |
| 3 | Derived events reusable for downstream | `test_derived_events.py` | REST endpoints queried and verified | Covered |
