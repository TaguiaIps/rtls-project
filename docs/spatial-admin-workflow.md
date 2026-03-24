# Spatial Admin Workflow

This document describes the first spatial configuration workflow implemented for the RTLS Analytics Platform.

It covers the protected Administrator flow for:

- site and floor hierarchy setup
- raster floor-plan upload
- scale calibration
- polygonal operational-area editing

## 1. Scope

This implementation supports:

- authenticated Administrator access only for create, update, upload, and delete actions
- authorized-user retrieval of sites, floors, floor-plan metadata, floor details, and operational areas
- one floor-plan image per floor
- `PNG` and `JPG` floor-plan uploads
- area types: `zone`, `table`, `restricted_zone`, and `poi`

This implementation explicitly does not support yet:

- CAD or PDF parsing
- vector import pipelines
- floor-plan version history
- snapping grids or CAD-like geometry tools
- polygon holes
- collaborative multi-user editing

## 2. Workflow Sequence

Administrators should configure spatial data in this order:

1. Create a site.
2. Create one or more floors under that site.
3. Upload the floor-plan image for a selected floor.
4. Place two reference points on the image.
5. Enter the measured real-world distance in meters.
6. Confirm scale so the floor becomes physically calibrated.
7. Draw polygonal operational areas on the floor plan.
8. Name and classify each area before saving it.

This sequence matches the UX intent from:

- [requirements-document.md](/home/hugo/Documents/taguia/rtls_project/docs/requirements-document.md)
- [ux-design.md](/home/hugo/Documents/taguia/rtls_project/docs/ux-design.md)
- [implementation-plan.md](/home/hugo/Documents/taguia/rtls_project/docs/implementation-plan.md)

## 3. Floor-Plan Upload Rules

- Supported MIME types: `image/png`, `image/jpeg`
- Supported source formats: `PNG`, `JPG`, `JPEG`
- The backend validates the uploaded file with Pillow before storing metadata
- Floor-plan binaries are stored in object storage
- Floor-plan metadata is stored in the relational database
- Uploading a new file for the same floor replaces the existing stored object and metadata in place

## 4. Scale Calibration Behavior

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
- points are normalized to the image bounds in the range `0..1`
- the derived scale is based on the uploaded image dimensions and the distance between the two points

## 5. Operational Area Editing

Operational areas are stored as ordered polygon points in normalized image-space coordinates.

Each area also stores:

- `name`
- `area_type`
- `sla_eligible`
- `alert_participation`

The current web editor supports:

- click-to-add polygon points on the floor-plan canvas
- numeric adjustment of stored point coordinates
- create, update, list, and delete flows
- visual overlays for existing areas, draft polygons, and scale markers

The first implementation intentionally favors clarity and data durability over advanced editing ergonomics.

## 6. Security and Audit

The spatial admin APIs integrate with the current identity and audit foundation.

Audit events are written for:

- `site.created`
- `floor.created`
- `floorplan.uploaded`
- `floorplan.replaced`
- `floor.scale.updated`
- `area.created`
- `area.updated`
- `area.deleted`

This ensures later audit-log and observability features can reuse the stored history instead of retrofitting it.

## 7. Deferred Follow-On Changes

The following items should be treated as later changes rather than expanding this implementation:

- CAD/PDF parsing and import conversion
- richer map editing behavior such as snapping, drag handles, and geometry constraints
- gateway placement on top of the calibrated floor plan
- calibration-session workflows beyond the two-point scale step
- vector-aware layer import or export

These boundaries are deliberate so the platform can stabilize the base spatial model before adding import and editing complexity.
