## Why

The RTLS Analytics Platform now has an implementation workspace and an identity foundation, but it still lacks the spatial model that every live map, gateway-placement, analytics, and alerting workflow depends on. This change is needed now because later tracking and reporting features cannot be implemented responsibly until sites, floors, floor plans, scale calibration, and business-meaningful zones exist as first-class platform objects.

## What Changes

- Add a site and floor hierarchy that Administrators can manage through protected backend and web admin flows.
- Add floor-plan upload and storage for one raster floor-plan image per floor, with real-world scaling based on two reference points and a measured distance.
- Add the first spatial canvas for floor-aware map context in the admin UI.
- Add polygon drawing and editing for operational areas including zones, tables, restricted zones, and points of interest.
- Add floor, zone, and POI metadata models that later gateway placement, positioning, analytics, and alerting changes can reuse.
- Explicitly keep CAD/PDF parsing out of this change and treat it as a later extension after the base floor-plan and zone model is stable.

## Capabilities

### New Capabilities
- `site-and-floor-management`: Covers site creation, floor registration, floor metadata, and protected admin workflows for spatial hierarchy management.
- `floor-plan-management`: Covers raster floor-plan upload, object-storage-backed asset handling, scale setup, and floor-linked map context.
- `zone-and-poi-editor`: Covers polygonal zone, table, restricted-area, and POI creation and editing for later map, alert, and analytics features.

### Modified Capabilities
- None.

## Impact

- Affects backend data modeling, object storage usage, and protected admin APIs.
- Affects the web application by adding the first real admin spatial workspace beyond authentication.
- Establishes the canonical floor and zone model that later gateway, positioning, analytics, and alert changes will consume.
- Touches UX alignment for the Admin Console, Floor Plans & Scale, and Zone & POI Manager flows already documented in the UX specification.
- Leaves CAD/PDF parsing, vector import, and advanced spatial-editing ergonomics for a later implementation change.
