## Why

The RTLS Analytics Platform already supports Premium as a gateway metadata tier, but the runtime still only executes the economic BLE positioning path. That gap means Alex can register Premium hardware without the platform accepting AoA or UWB measurements, and Carlos still cannot benefit from the faster, more precise tracking and latency targets promised in the requirements.

This change is needed now because the implementation plan separates the metadata side of `FR-ADM-004` from the execution side. Without a dedicated premium-tier change, the platform cannot turn Premium hardware investment into usable live-location behavior or meet the higher-performance expectations captured in `NFR-PER-001` and `NFR-PER-002`.

## What Changes

- Extend gateway profiles so Premium gateways can carry modality, mounting, and calibration-ready metadata beyond the already delivered tier label.
- Extend the telemetry ingestion contract so registered Premium gateways can publish AoA or UWB measurements through a validated, deduplicated, durable ingestion path.
- Add a premium-tier positioning capability that derives canonical asset locations from premium measurements and writes them into the shared latest-location and history surfaces.
- Update live-location query, search, trajectory, and streaming contracts so downstream consumers can distinguish Economic and Premium results through source-tier and precision metadata.
- Define cross-tier arbitration rules so fresher, higher-confidence Premium results can supersede lower-precision outputs without breaking the existing Economic baseline.
- Keep vendor-specific provisioning flows, guided mobile calibration UX, premium-only alert behavior, and new Analytics or Live Map UI work out of scope for this change.

## Capabilities

### New Capabilities

- `premium-tier-position-estimation`: Covers premium AoA/UWB measurement processing, premium location estimation, source-tier metadata, and canonical current-state or history writes.

### Modified Capabilities

- `gateway-placement-and-tier-profiles`: Adds premium-specific gateway modality, mounting, and calibration-state requirements.
- `gateway-telemetry-ingestion`: Adds premium-tier telemetry contracts and higher-rate ingestion semantics while preserving gateway identity and dedupe guarantees.
- `live-location-query-and-streaming`: Expands live-location surfaces so authorized consumers can retrieve and subscribe to canonical results from either delivered hardware tier.

## Impact

- Affects backend data models, validation rules, and ingestion or positioning services for gateways, raw measurements, and canonical location records.
- Affects shared API contracts because live-location queries, search responses, history results, and streaming events need tier-aware metadata.
- Affects system and UX documentation because the delivered location baseline will no longer be Economic-only.
- Introduces additional latency, throughput, calibration, and observability constraints that need to stay explicit before implementation begins.
