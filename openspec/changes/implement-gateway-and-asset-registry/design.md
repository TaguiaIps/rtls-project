## Context

The RTLS Analytics Platform now has an implementation workspace, identity foundation, and spatial setup baseline with sites, floors, floor plans, and operational areas. The next dependency in the implementation plan is the gateway and asset registry layer. The requirements and UX documents make this a distinct administrative concern:

- `FR-ADM-002`: place gateways corresponding to the Economic or Premium tier
- `FR-ADM-004`: support provision of Economic and Premium hardware tier profiles
- `FR-ADM-005`: bulk import asset tags via CSV with update rate and battery profile settings

This change must give Administrators a durable registry for infrastructure devices and tracked assets without pulling in telemetry ingestion, calibration logic, or live position rendering. It should build directly on the newly implemented floor hierarchy and floor-plan editor so gateway placement reuses the same floor-relative spatial coordinates and admin workspace patterns.

## Goals / Non-Goals

**Goals:**

- Introduce a protected gateway registry with per-floor placement and editable gateway metadata.
- Introduce explicit Economic and Premium tier assignment on gateway records.
- Introduce a protected asset/tag registry with stable identifiers and operational metadata such as update rate and battery profile.
- Introduce validated CSV import for asset tags with row-level feedback and explicit confirmation.
- Define stable gateway and asset identifiers so later ingestion, calibration, live tracking, alerts, and analytics changes can reuse the same records.

**Non-Goals:**

- Implement telemetry ingestion, heartbeat handling, or MQTT registration in this change.
- Implement automated calibration sessions or blue-dot mobile commissioning workflows.
- Implement gateway health monitoring, packet-loss views, or offline alerts.
- Implement live asset search, position history, or map playback behavior.
- Finalize every future asset profile type; this change establishes the baseline registry and import model only.

## Decisions

### 1. Separate gateway registry metadata from future telemetry state

Gateway records should capture the administrative identity and placement of each gateway, while runtime health and telemetry state remain future concerns. Each gateway should store a stable identifier, display label, assigned floor, floor-relative placement coordinates, and tier profile metadata, but not attempt to model live status yet.

Rationale:

- It matches the current dependency order where gateway placement comes before ingestion and health monitoring.
- It gives later telemetry changes a canonical `gateway_id` without forcing this change to own runtime state.
- It keeps the first admin workflow focused on setup and placement rather than device diagnostics.

Alternatives considered:

- Combine registry and runtime status in one change: too broad and would pull in ingestion dependencies early.
- Keep gateway placement only in front-end state until ingestion exists: too fragile and blocks later data contracts.

### 2. Represent hardware tier as an explicit gateway profile choice

The gateway model should persist an explicit hardware tier value of `Economic` or `Premium`, plus tier-linked configuration metadata that later positioning and ingestion components can interpret. The first pass should not over-model vendor-specific radio settings.

Rationale:

- It directly covers `FR-ADM-004` and the Gateway Placement UX flow.
- It creates an explicit contract for later changes to branch positioning logic by tier.
- It avoids premature schema churn around vendor-specific settings before hardware integrations are implemented.

Alternatives considered:

- Store a free-form hardware profile blob only: too weak for authorization, UX filtering, and later logic branching.
- Postpone tier data until premium support exists: would force later changes to retrofit gateway records.

### 3. Use floor-relative placement coordinates for gateway markers

Gateway placements should reuse the same normalized floor-relative coordinate model used by the spatial editor rather than introducing a second geometry system. Gateways are point placements linked to a floor, not free-floating infrastructure records.

Rationale:

- It builds directly on the floor-plan and scale model already implemented.
- It simplifies later live map and calibration overlays because all floor-linked objects share one coordinate basis.
- It avoids unnecessary conversion logic at the registry stage.

Alternatives considered:

- Store raw pixel coordinates only: harder to keep consistent across image replacements or rendering changes.
- Store only room labels without coordinates: insufficient for map placement and calibration planning.

### 4. Keep the asset registry focused on static identity and operational policy

Asset tag records should store static identity and operational metadata such as tag identifier, display name, asset category, update-rate policy, and battery profile. They should not try to own live position, health, or historical telemetry in this change.

Rationale:

- It satisfies `FR-ADM-005` without coupling the registry to future live-tracking implementation details.
- It gives the platform a durable source of truth for assets before readings start arriving.
- It keeps CSV import semantics simple and testable.

Alternatives considered:

- Model live asset state inside the registry now: creates false coupling to yet-unbuilt ingestion and positioning services.
- Limit the registry to tag IDs only: too weak for search, asset policy, and future analytics context.

### 5. Use a staged CSV import flow with validation before commit

CSV import should be a validate-review-confirm workflow rather than a single upload that silently creates partial results. The system should report row-level errors, duplicates, and unsupported values before the Administrator confirms creation.

Rationale:

- It matches the UX direction for inline validation and avoids silent admin mistakes.
- It protects the registry from partial imports with mixed validity.
- It creates a reusable import contract for later batch workflows.

Alternatives considered:

- Immediate best-effort insert with a summary afterward: too error-prone for administrative data quality.
- Require only one-by-one asset entry: too slow for the intended onboarding workflow.

## Risks / Trade-offs

- [Gateway metadata may need more vendor-specific fields later] → Mitigation: keep the first schema extensible and reserve later vendor specialization for a focused follow-on change.
- [CSV import can become complex if too many optional columns are introduced] → Mitigation: keep the first template narrow and aligned to the immediate policy fields already required.
- [Separating registry from runtime health means administrators will not yet see device liveliness] → Mitigation: document health monitoring as a later change and keep the current scope explicit.
- [Gateway placement accuracy depends on the already-configured floor plan and scale] → Mitigation: require existing floor context and reuse normalized coordinates from the spatial setup workflow.

## Migration Plan

1. Add persistence models for gateway records, tier metadata, and asset/tag registry records.
2. Add protected backend APIs for gateway CRUD, floor placement, asset CRUD, and CSV import validation plus confirmation.
3. Add shared request and response contracts so the web admin flows and later backend changes reuse consistent identifiers and metadata shapes.
4. Add the web admin Gateway Placement and Asset Registry workflows inside the current admin setup experience.
5. Validate that later ingestion and live-tracking changes can reference the resulting gateway and asset records without redefining their core identity.

Rollback strategy:

- If the registry schema proves unstable, revert the gateway and asset registry change as one unit rather than leaving partially adopted identifiers in downstream use.
- If CSV import proves operationally noisy, keep manual asset CRUD and temporarily disable bulk import until validation rules are corrected.

## Open Questions

- Whether the first asset registry should include person-versus-equipment classification as a required field or leave it optional until search and analytics features are implemented.
- Whether gateway labels should be unique per floor or globally unique across a site.
- Whether tier profile metadata should include vendor model fields in the first pass or wait for the premium hardware support change.
