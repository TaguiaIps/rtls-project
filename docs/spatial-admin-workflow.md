# Admin Setup Workflow

This document describes the implemented Administrator setup flow for the RTLS Analytics Platform.

It covers the protected Admin workspace for:

- site and floor hierarchy setup
- raster floor-plan upload
- scale calibration
- polygonal zone, table, restricted-zone, and point-of-interest editing
- gateway placement with Economic or Premium tier assignment
- asset tag registry management
- CSV validation and confirmation for bulk asset-tag onboarding

## 1. Scope

This implementation supports:

- authenticated Administrator access for create, update, upload, import, and delete actions
- authorized-user retrieval of sites, floors, floor-plan metadata, scale, zones, and gateway placements through the shared floor detail view
- one raster floor-plan image per floor
- `PNG` and `JPG` floor-plan uploads
- gateway records with stable identifiers, labels, floor-linked placement coordinates, and Economic or Premium tier assignment
- asset-tag records with stable identifiers, display labels, category, update-rate profile, and battery profile metadata
- CSV import with required columns, duplicate detection, row-level validation, and explicit confirmation before records are created

This implementation intentionally does not support yet:

- CAD or PDF parsing
- vector import pipelines
- floor-plan version history
- snapping grids or CAD-like geometry tools
- polygon holes
- telemetry ingestion, heartbeat processing, or live gateway health
- QR commissioning flows
- calibration sessions beyond the two-point scale step
- live asset rendering, search, or historical replay

## 2. Workflow Sequence

Administrators should use the setup workspace in this order:

1. Create a site.
2. Create one or more floors under that site.
3. Upload the floor-plan image for a selected floor.
4. Place two reference points on the image.
5. Enter the measured real-world distance in meters.
6. Confirm scale so the floor becomes physically calibrated.
7. Define operational zones, tables, restricted zones, and points of interest.
8. Place one or more gateways on the calibrated floor plan.
9. Assign each gateway to the Economic or Premium tier profile.
10. Create asset tags manually or validate a CSV import.
11. Confirm the CSV import only after every row is valid.

This matches the intended Wave 1 dependency order from:

- [requirements-document.md](/home/hugo/Documents/taguia/rtls_project/docs/requirements-document.md)
- [ux-design.md](/home/hugo/Documents/taguia/rtls_project/docs/ux-design.md)
- [implementation-plan.md](/home/hugo/Documents/taguia/rtls_project/docs/implementation-plan.md)

The gateway and asset registry workflow extends the earlier spatial setup baseline instead of replacing it. Floor hierarchy, floor-plan upload, scale calibration, and zone editing still remain the prerequisite foundation for gateway placement.

## 3. Floor-Plan And Scale Behavior

Floor-plan uploads follow these rules:

- Supported MIME types: `image/png`, `image/jpeg`
- Supported source formats: `PNG`, `JPG`, `JPEG`
- The backend validates uploaded images with Pillow before storing metadata
- Floor-plan binaries are stored in object storage
- Floor-plan metadata is stored in the relational database
- Uploading a new file for the same floor replaces the existing stored object and metadata in place
- Replacing a floor plan clears the saved scale so the floor must be recalibrated against the new image before scale-dependent workflows rely on it again

Scale is configured from:

- `point_a`
- `point_b`
- `real_world_distance_m`

The system persists:

- the two normalized image-space points
- the measured distance in meters
- the derived `pixels_per_meter`
- the calibration timestamp

Important behavior:

- scale configuration requires a floor plan to exist first
- points are normalized to the rendered floor-plan image bounds in the range `0..1`
- the derived scale is based on the uploaded image dimensions and the distance between the two points

## 4. Zone And POI Editing

Operational areas are stored as ordered polygon points in normalized floor-relative coordinates.

Each area also stores:

- `name`
- `area_type`
- `sla_eligible`
- `alert_participation`

The current web editor supports:

- click-to-add polygon points on the floor-plan canvas
- numeric adjustment of stored point coordinates
- create, update, list, and delete flows
- visual overlays for saved areas, draft polygons, scale markers, and gateways

## 5. Gateway Placement And Tier Profiles

Gateway records are point placements linked to a floor, not runtime telemetry objects.

Each gateway stores:

- `gateway_identifier`
- `display_name`
- `hardware_tier`
- `placement`
- `notes`

Implemented gateway behavior:

- gateway placement requires an existing floor plan
- placements reuse the same normalized floor-relative coordinate model as the spatial editor
- Administrators can create, update, list, and delete gateways
- Economic and Premium are the only supported tier profiles in this change
- tier assignment is persisted as explicit configuration metadata for later ingestion and positioning changes

## 6. Asset Registry And CSV Import

Asset-tag records store static identity and operational policy metadata.

Each asset tag stores:

- `tag_identifier`
- `display_name`
- `asset_category`
- `update_rate_profile`
- `battery_profile`

The current asset registry supports:

- manual asset-tag create, update, list, and delete flows
- update-rate profiles: `slow`, `balanced`, `realtime`
- battery profiles: `long_life`, `standard`, `performance`

The CSV import workflow is staged:

1. Upload a UTF-8 CSV file with the required header row.
2. Validate every row before any records are created.
3. Review valid rows and row-level errors in the admin UI.
4. Confirm the import only when no invalid rows remain.

Required CSV columns:

- `tag_identifier`
- `display_name`
- `asset_category`
- `update_rate_profile`
- `battery_profile`

Validation behavior:

- missing required values are reported per row
- unsupported update-rate or battery-profile values are rejected
- duplicate `tag_identifier` values inside the CSV file are rejected
- duplicate `tag_identifier` values already present in the registry are rejected
- partial imports are not created; confirmation is available only for a fully valid file

## 7. Security And Audit

The admin setup APIs integrate with the existing identity and audit foundation.

Audit events are written for:

- `site.created`
- `floor.created`
- `floorplan.uploaded`
- `floorplan.replaced`
- `floor.scale.updated`
- `area.created`
- `area.updated`
- `area.deleted`
- `gateway.created`
- `gateway.updated`
- `gateway.deleted`
- `asset.created`
- `asset.updated`
- `asset.deleted`
- `asset.imported`

This keeps configuration history durable before later audit-log, ingestion, and health features are added.

## 8. Deferred Follow-On Changes

The following items remain later changes and are intentionally out of scope for this workflow:

- QR-based mobile commissioning
- automated calibration wizard and radio-map collection
- telemetry ingestion and heartbeat processing
- live gateway health monitoring and maintenance alerts
- live asset rendering, asset search, and historical movement replay
- CAD/PDF parsing and import conversion
- richer map editing behavior such as snapping, drag handles, and geometry constraints
- vector-aware layer import or export

These boundaries preserve the Wave 1 split from the implementation plan:

- change 3 owns the spatial foundation
- change 4 owns gateway and asset registry data
- later changes own calibration, ingestion, positioning, health, and operational visualization
