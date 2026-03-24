## Context

The RTLS Analytics Platform already has an implementation workspace and a protected admin-capable web shell, but it does not yet have any domain model for sites, floors, floor plans, or zones. The requirements and UX documents make this a hard dependency for several next steps:

- `FR-ADM-001`: upload floor plans and set real-world scale
- `FR-ANL-001`: define polygonal geofences and zones
- `FR-VIS-001`: display the uploaded floor plan with specific zones
- `NFR-USA-001`: use a drag-and-drop or point-and-click drawing tool

This change is the first spatial foundation change. It must provide enough functionality for Administrators to create map context and operational areas without overreaching into gateway placement, calibration, or full map analytics. The user already chose the default scope for the first pass:

- backend plus web admin UI only
- `site -> floor` hierarchy now
- one uploaded floor-plan image per floor
- `PNG` and `JPG` uploads first
- polygon editing for `zone`, `table`, `restricted zone`, and `POI`
- two-point real-world scale setup
- no CAD/PDF parsing, collaborative editing, or advanced CAD behaviors in this change

The design should therefore keep the spatial model durable, while keeping the editing workflow simple enough for a first implementation pass.

## Goals / Non-Goals

**Goals:**

- Introduce protected site and floor management for Administrators.
- Introduce one floor-plan image per floor with object-storage-backed file handling.
- Introduce real-world scale calibration using two reference points and a known distance.
- Introduce polygon editing for zones, tables, restricted zones, and POIs in the web admin experience.
- Define stable IDs and metadata so later gateway placement, live positioning, analytics, and alert rules can reuse the same spatial entities.

**Non-Goals:**

- Implement gateway placement, calibration sessions, or live asset rendering in this change.
- Implement mobile commissioning or mobile map editing.
- Support CAD or PDF parsing in the first implementation pass.
- Support multi-version floor-plan history, collaborative editing, snapping grids, or vector-layer editing.
- Finalize every future map interaction pattern; this change only establishes the admin spatial foundation.

## Decisions

### 1. Separate site hierarchy from floor-plan assets

Sites and floors should be persisted as operational entities in the database, while the uploaded floor-plan file should live in object storage with metadata and a stable storage key in the database.

Rationale:

- It matches the deployment model already chosen for object storage.
- It avoids bloating relational records with binary content.
- It makes later floor-plan replacement, caching, and export handling easier.

Alternatives considered:

- Store file blobs directly in the database: simpler initially, but poor fit for larger assets and later media handling.
- Use only local filesystem paths: weaker portability across containers and pilot deployments.

### 2. Start with raster upload only

The first implementation should accept `PNG` and `JPG` uploads for floor plans and explicitly exclude CAD/PDF parsing from this change.

Rationale:

- It keeps the first spatial workflow implementable without parser complexity.
- It gives later gateway and zone editing work a stable foundation sooner.
- It keeps the operational UI focused on map meaning rather than document-conversion problems.

Alternatives considered:

- Support CAD/PDF import immediately: potentially valuable, but it adds conversion, parsing, scale inference, and support-surface complexity that is not required to unblock the next platform changes.
- Postpone all uploads until vector support exists: unnecessary delay for the core roadmap.

### 3. Represent floor scale explicitly

Each floor should store two image-space reference points, a real-world measured distance, and a derived scale factor. The scale record should remain part of floor metadata so later gateway placement and trajectory math use a shared physical basis.

Rationale:

- It directly matches the UX flow and requirement wording.
- It keeps later spatial computations from inventing separate scale assumptions.
- It provides a clear validation rule: a floor is not fully spatially ready until scale has been confirmed.

Alternatives considered:

- Implicit scale only from width/height assumptions: too fragile.
- Manual numeric scale input without reference points: weaker usability and easier to misconfigure.

### 4. Use a typed polygon model for operational areas

Zones, tables, restricted zones, and POIs should use one common geometry model with a typed discriminator and per-type metadata fields. Geometry should be persisted as ordered polygon coordinates in floor-relative space.

Rationale:

- It keeps the first editing implementation small.
- It allows alerts, analytics, and live map rendering to reuse one shape model later.
- It avoids splitting operational areas into many tables before their differences are proven necessary.

Alternatives considered:

- Separate tables for each area type now: more rigid and more migration overhead.
- Untyped free-form annotations: too weak for later business logic.

### 5. Keep the first admin UI as a protected single spatial workspace

The web admin experience should provide a site/floor list, a floor-plan upload and scale setup surface, and a zone/POI editor in one protected admin workspace. This should favor clear sequential setup over highly dynamic multi-pane behavior.

Rationale:

- It aligns with the current UX specification for Admin Console, Floor Plans & Scale, and Zone & POI Manager.
- It keeps navigation simple while the data model is still new.
- It fits the current React shell and Administrator role model already implemented.

Alternatives considered:

- Split each sub-flow into separate mini-apps: too fragmented for the current stage.
- Add a generic map shell first and defer admin editing: delays the real requirement coverage.

## Risks / Trade-offs

- [Raster-only floor plans may frustrate teams with CAD/PDF source files] → Mitigation: document CAD/PDF parsing as a planned follow-on and keep stored metadata compatible with later import pipelines.
- [Polygon editing UX can become awkward if implemented too generically] → Mitigation: keep the initial editing toolset small and aligned to the documented admin workflows.
- [Scale calibration errors will affect later gateway and analytics work] → Mitigation: make scale confirmation explicit and persist the calibration inputs, not just the derived result.
- [A shared area model may need type-specific fields later] → Mitigation: keep per-type metadata extensible and treat later specialization as additive.
- [Object storage introduces another moving part for the admin flow] → Mitigation: reuse the already-approved object-storage runtime and keep one-file-per-floor semantics simple.

## Migration Plan

1. Add site, floor, floor-plan asset metadata, and spatial-area persistence models.
2. Add protected backend APIs for site/floor creation, floor-plan upload metadata, scale calibration, and zone editing.
3. Add object-storage integration for floor-plan file upload and retrieval.
4. Add the protected web admin spatial workspace for floor setup and polygon editing.
5. Validate that later gateway, live map, and analytics changes can consume the resulting floor and zone entities without redefining them.

Rollback strategy:

- If the spatial data model proves unstable, revert this change as one unit rather than leaving partially defined site or floor records in active use.
- If object-storage integration causes early instability, keep the site/floor records but revert floor-plan upload handling until corrected.

## Open Questions

- Whether polygon coordinates should be stored only in normalized image-space coordinates or also in derived real-world coordinates.
- Whether the first API should support replacing a floor-plan file in place or require explicit floor-plan re-upload flows later.
- Whether the first editor should support holes or only simple polygons.
- When to schedule the separate CAD/PDF parsing extension in the implementation backlog.
