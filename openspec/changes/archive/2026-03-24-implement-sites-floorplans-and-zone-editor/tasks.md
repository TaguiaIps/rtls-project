## 1. Spatial Domain Foundation

- [x] 1.1 Define persistence models for sites, floors, floor-plan metadata, and typed operational areas
- [x] 1.2 Define the floor scale calibration model using two reference points and a measured real-world distance
- [x] 1.3 Define supported raster floor-plan upload rules and explicitly record CAD/PDF parsing as out of scope for this change

## 2. Backend Spatial APIs

- [x] 2.1 Add protected Administrator APIs for site and floor creation, listing, and retrieval
- [x] 2.2 Add protected Administrator APIs for floor-plan upload metadata and scale calibration
- [x] 2.3 Add protected Administrator APIs for creating, editing, listing, and deleting typed polygonal areas
- [x] 2.4 Add audit-event writes for site, floor, floor-plan, and operational-area configuration changes

## 3. Web Admin Spatial Workspace

- [x] 3.1 Add the protected Admin Console flow for site and floor management
- [x] 3.2 Add the floor-plan upload and scale setup experience in the web admin UI
- [x] 3.3 Add the polygon drawing and editing experience for zones, tables, restricted zones, and POIs

## 4. Documentation and Verification

- [x] 4.1 Document the spatial admin workflow, supported floor-plan formats, and scale-calibration behavior
- [x] 4.2 Verify consistency with the requirements, UX floor-plan and zone-editor flows, and the implementation plan
- [x] 4.3 Record CAD/PDF parsing and any advanced map-editing behaviors as later changes instead of expanding this change
