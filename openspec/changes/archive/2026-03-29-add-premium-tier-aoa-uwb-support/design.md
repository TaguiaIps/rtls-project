## Context

The current repository baseline includes:

- gateway registration, floor placement, and explicit Economic or Premium tier labels
- MQTT ingestion, payload validation, dedupe, and durable raw-reading persistence
- an Economic-only positioning flow that produces canonical latest-known state, location history, and live-location APIs

The backlog item `add-premium-tier-aoa-uwb-support` is the execution half of the already planned two-tier architecture. The design must let Alex configure and maintain Premium hardware responsibly while giving Carlos access to faster and more precise live positions through the same downstream contracts already used by Operations workflows.

Constraints:

- the existing Economic pipeline must keep working unchanged for already delivered behavior
- Premium support must remain vendor-agnostic at the contract layer even if the first implementation targets a narrow device set
- guided mobile commissioning or calibration UX is a later backlog item, so this change can depend only on backend-managed placement and calibration state

## Goals / Non-Goals

**Goals:**

- add a Premium positioning path for AoA and UWB measurements without replacing the delivered Economic baseline
- extend gateway and telemetry contracts with the minimum validated metadata needed for Premium estimation
- preserve one canonical latest-location, history, and streaming surface for downstream consumers
- make tier, modality, freshness, and precision semantics explicit enough for later Live Map, Alerts, Health, and Mobile work
- support Premium update cadence and latency expectations through an event-driven processing path

**Non-Goals:**

- vendor-specific provisioning or firmware management flows
- operator-facing Live Map redesigns or Premium-only UI treatments
- guided mobile calibration capture, QR scanning, or field commissioning workflows
- Premium analytics reports, exports, or Premium-specific alert semantics
- replacing Economic estimation math or forcing all assets onto Premium hardware

## Decisions

### 1. Premium estimation will be a parallel positioning flow that writes into the shared canonical location surface

The platform should not extend the Economic estimator into one large mixed-modality algorithm. Premium AoA and UWB inputs have different geometry, cadence, and quality semantics, so the cleaner boundary is:

- Premium telemetry ingestion normalizes accepted AoA or UWB measurements
- a Premium estimator consumes those measurements plus gateway placement or calibration context
- the estimator writes canonical latest-known state and append-only history using the same downstream contract family already used by Economic outputs

This keeps the delivered Economic path stable while letting later work evolve Premium estimation independently.

Alternative considered:
- Extending the Economic estimator directly was rejected because it would couple two very different signal models and make confidence behavior harder to reason about or test.

### 2. Premium gateways need explicit validated geometry and calibration-state fields, not an opaque metadata blob

Premium estimation depends on more than a tier label. The gateway model should add validated Premium-only fields such as supported modality, antenna orientation or mounting metadata, and a calibration-state marker tied to the current floor geometry.

Using explicit fields keeps admin validation, migration, and future calibration invalidation rules testable.

Alternative considered:
- Storing Premium setup in a generic JSON metadata field was rejected because it weakens validation and makes later calibration or health workflows harder to build on consistently.

### 3. Premium telemetry should normalize into a vendor-agnostic measurement envelope before estimation

The ingestion layer should preserve identity checks, timestamp normalization, and dedupe behavior while also capturing Premium-specific measurement details such as modality, sequence identity, quality indicators, bearing or range values, and any timing metadata needed by the estimator.

That normalized envelope becomes the handoff between broker-facing ingestion and estimator-facing positioning logic.

Alternative considered:
- Passing vendor payloads directly into estimation was rejected because it spreads vendor assumptions across the codebase and complicates replay, testing, and future multi-vendor support.

### 4. Canonical live-location outputs should remain unified and add source-tier metadata instead of forking the API surface

Downstream consumers should keep one latest-location, search, history, and streaming API family. The contract should expand to expose:

- `sourceTier` such as `Economic` or `Premium`
- `sourceModality` such as `BLE_AOA` or `UWB`
- modality-aware precision or confidence metadata

If the same asset has overlapping candidate outputs, the canonical latest-known state should prefer the freshest result that also has the best supported precision or confidence for that moment.

Alternative considered:
- Separate Premium-only query and stream endpoints were rejected because they would fragment downstream consumers and make mixed-fleet operations harder.

### 5. Premium calibration validity should be tied to gateway placement and floor geometry boundaries

The repository already treats floor-plan replacement as a recalibration boundary. Premium support should extend that principle: if a Premium gateway's placement geometry or the underlying floor context changes materially, the system should mark related Premium calibration state stale instead of silently trusting prior alignment.

Alternative considered:
- Allowing old calibration state to survive placement or floor changes was rejected because it would hide a high-risk source of misleading precision.

## Risks / Trade-offs

- [Risk] Premium vendor payloads differ more than expected. → Mitigation: define a narrow vendor-agnostic normalized envelope and document unsupported payload variants explicitly.
- [Risk] Higher-rate Premium telemetry increases ingestion and stream load. → Mitigation: keep the processing path event-driven, preserve dedupe boundaries, and instrument queue or write latency before expanding scope.
- [Risk] Cross-tier arbitration could hide useful lower-tier fallback context. → Mitigation: persist source-tier metadata in history and expose tier-aware fields in canonical responses instead of silently erasing provenance.
- [Risk] Premium calibration cannot be fully operationalized before the later mobile workflow. → Mitigation: scope this change to backend-managed calibration state and treat richer field capture as a future UX enhancement, not a blocker for the contract baseline.

## Migration Plan

1. Extend gateway and telemetry schemas with nullable Premium-specific fields so existing Economic records remain valid.
2. Introduce Premium measurement normalization and persistence without changing the delivered Economic endpoints.
3. Add Premium estimation and cross-tier arbitration behind the shared canonical location writer.
4. Expand live-location contracts to include source-tier metadata in a backward-compatible way where possible.
5. Roll out Premium traffic only after validation confirms the new flow does not regress Economic ingestion or live-location behavior.

Rollback approach:

- disable Premium telemetry acceptance and estimator execution while leaving the existing Economic pipeline and canonical live-location surfaces intact
- preserve stored Premium raw measurements for later replay instead of discarding them during rollback

## Open Questions

- Which Premium vendor payload shape should be treated as the first supported contract for AoA and for UWB normalization?
- Should cross-tier arbitration prefer freshest-result-first unconditionally, or should Premium retain a bounded precedence window over slightly newer but lower-confidence Economic updates?
- Which backend actor or workflow owns initial Premium calibration-state transitions before the later mobile commissioning experience is delivered?
