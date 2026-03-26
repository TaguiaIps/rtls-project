## 1. Gateway And Asset Domain Foundation

- [x] 1.1 Define persistence models for gateway records, tier assignment, floor-linked placement coordinates, and asset tag registry metadata
- [x] 1.2 Define the supported Economic and Premium tier profile metadata and the initial asset policy fields for update rate and battery profile
- [x] 1.3 Define the CSV import contract, validation rules, and duplicate-handling behavior for bulk asset tag onboarding

## 2. Backend Registry APIs

- [x] 2.1 Add protected Administrator APIs for gateway creation, listing, retrieval, update, and floor placement management
- [x] 2.2 Add protected Administrator APIs for asset tag creation, listing, retrieval, update, and deletion
- [x] 2.3 Add protected Administrator APIs for CSV import validation, import confirmation, and error reporting
- [x] 2.4 Add audit-event writes for gateway, tier-profile, and asset-registry configuration changes

## 3. Web Admin Registry Workflows

- [x] 3.1 Add the protected Admin Console flow for gateway placement and tier assignment on configured floors
- [x] 3.2 Add the protected Asset Registry flow for manual asset tag management and policy editing
- [x] 3.3 Add the CSV import review and confirmation workflow with inline validation feedback in the admin UI

## 4. Documentation And Verification

- [x] 4.1 Document the gateway placement, tier profile, and asset registry workflows and align terminology with the UX and glossary
- [x] 4.2 Verify consistency with the requirements document, implementation plan Wave 1 ordering, and the existing spatial setup change
- [x] 4.3 Record calibration, QR commissioning, telemetry ingestion, and health monitoring as later changes rather than expanding this change
