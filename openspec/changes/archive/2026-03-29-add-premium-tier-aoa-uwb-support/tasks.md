## 1. Contracts and data model

- [x] 1.1 Define the Premium gateway profile contract, including modality, mounting metadata, and calibration-state invalidation rules.
- [x] 1.2 Define the Premium telemetry contract and normalized raw-measurement schema for supported AoA and UWB payloads.
- [x] 1.3 Define canonical live-location contract updates for source-tier, source-modality, and modality-aware precision metadata.

## 2. Ingestion and positioning

- [x] 2.1 Implement Premium telemetry validation, identity checks, and dedupe behavior on top of the existing ingestion pipeline.
- [x] 2.2 Implement Premium raw-measurement persistence and the Premium positioning flow that consumes calibrated gateway context.
- [x] 2.3 Implement cross-tier latest-state arbitration so fresher, higher-quality Premium results can supersede weaker canonical outputs without losing history provenance.

## 3. Delivery surfaces

- [x] 3.1 Update authorized live-location query, search, trajectory, and streaming APIs to expose Premium-aware source and precision metadata.
- [x] 3.2 Add regression coverage for Premium gateway validation, Premium telemetry ingestion, calibration invalidation, and cross-tier arbitration behavior.
- [x] 3.3 Update system and UX documentation to distinguish the delivered Economic baseline from the new Premium-tier AoA or UWB support.

## 4. Validation

- [x] 4.1 Validate the change with `openspec validate add-premium-tier-aoa-uwb-support --strict`.
