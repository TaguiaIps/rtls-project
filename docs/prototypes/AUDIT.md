# Prototype Audit Against UX Spec

This audit compares the generated Google Stitch prototypes in [README.md](./README.md) against the target UX specification in [../ux-design.md](../ux-design.md).

## Overall Verdict

**Status:** `Partial fit`

The prototype set is strong enough to serve as a high-fidelity starting point, but it does **not yet fully align** with the RTLS restaurant/catering product spec.

The main problem is not layout quality. The main problem is **semantic drift**:

* product naming changes between `RTLS`, `Sentinel`, `COMMAND_DECK`, and `SENTINEL_COMMAND`
* several screens drift into **fleet / manufacturing / mission command** language
* some generated variants are overlapping, and the weaker variant should be discarded rather than refined

## Highest-Priority Findings

### 1. Domain and Branding Drift

**Severity:** High

Across the prototype set, the intended RTLS restaurant/catering product is mixed with unrelated terminology:

* `COMMAND_DECK`, `RTLS_NODE_ACTIVE`, `NEW_SCAN` in [operations_overview/code.html](./operations_overview/code.html)
* `Fleet Command`, `Rover`, `MHE`, and manufacturing references in [live_operations_map/code.html](./live_operations_map/code.html)
* `CPT. MILLER`, `Node_01: Sector_Alpha`, and “mission-critical sensor telemetry” in [alerts_center/code.html](./alerts_center/code.html)
* warehouse imagery and `MHE` asset naming in [asset_finder_mobile/code.html](./asset_finder_mobile/code.html)
* mixed product titles such as `SENTINEL ANALYTICS`, `SENTINEL RTLS`, `SENTINEL_COMMAND`, and `RTLS COMMAND` across multiple screens

**Impact:**

The screens no longer read as one coherent product for restaurant and catering operations. This is the main blocker before presentation or stakeholder review.

### 2. Wrong Operational Vocabulary for the Target Industry

**Severity:** High

Several screens should talk about:

* tables
* dining zones
* kitchen pass
* waitstaff
* POS terminals
* carts / trays
* gateways

Instead, the prototypes often refer to:

* `MHE`
* `forklift`
* `Rover`
* `Manufacturing`
* `Sector Alpha`
* `Fleet`

Examples:

* [analytics_heatmap_analysis/code.html](./analytics_heatmap_analysis/code.html) uses `Floor 01: Manufacturing` and `All Equipment, MHE`
* [live_asset_map_selected_asset/code.html](./live_asset_map_selected_asset/code.html) centers on `MHE-091`
* [asset_finder_mobile/code.html](./asset_finder_mobile/code.html) uses warehouse-style map imagery and MHE search history

**Impact:**

Even visually strong screens will feel “wrong” to stakeholders because the content model does not match the product’s actual users or stories.

### 3. Competing Variants for the Default Live Map

**Severity:** High

There are at least two map variants:

* [live_operations_map/code.html](./live_operations_map/code.html)
* [live_asset_map/code.html](./live_asset_map/code.html)

The second one is the stronger base for the UX spec because it includes:

* explicit confidence states
* a map legend
* a recent activity timeline
* better RTLS-specific map behavior

The first variant is visually solid but drifts harder into fleet-command language and omits some core map semantics from the spec.

**Recommendation:** Use `live_asset_map` as the base for `WEB-03`, not `live_operations_map`.

## Screen Audit Matrix

| Prototype | UX Target | Status | Notes |
| :--- | :--- | :--- | :--- |
| `operations_overview` | `WEB-02` | `Partial` | Strong structure and KPI layout, but branding and side-nav language drift away from product spec. |
| `live_operations_map` | `WEB-03` | `Fail as primary candidate` | Good visual quality, but wrong semantics and missing some desired RTLS behaviors compared with alternate map variant. |
| `live_asset_map` | `WEB-03` alternate | `Partial` | Stronger candidate for default map because it includes confidence states, legend, and timeline. Still needs naming and restaurant-specific content cleanup. |
| `live_asset_map_selected_asset` | `WEB-04` | `Partial` | Drawer structure fits the spec, but selected asset content is warehouse/manufacturing-oriented. |
| `alerts_center` | `WEB-08` | `Partial` | Strong list design and tab/filter model. Needs product/domain normalization and removal of military/mission phrasing. |
| `analytics_heatmap_analysis` | `WEB-10` | `Partial` | Analytics structure is strong, but cohort/floor labels drift into manufacturing instead of restaurant operations. |
| `floor_plan_scale_setup` | `WEB-16` | `Partial` | Best-aligned admin screen. Core flow is present, but naming still drifts to `SENTINEL_ANALYTICS`. |
| `calibration_wizard_walk_path_step` | `WEB-21` | `Partial` | Good stepper and quality/status framing. Needs product naming cleanup and more restaurant-floor realism. |
| `asset_finder_mobile` | `MOB-02` | `Partial` | Strong mobile hierarchy and search-first behavior. Content is too warehouse/MHE-oriented. |
| `qr_scanner_detected_state` | `MOB-06` | `Partial` | Good detected-state composition, but only one state is represented and the tone is too tactical/targeting-oriented. |
| `infrastructure_health` | `WEB-22` likely | `Partial` | Solid extra screen. Useful for future inclusion after language cleanup. |
| `zone_flow_configuration` | `WEB-15` likely | `Partial` | Useful extra screen. Good editor direction, but needs restaurant/POI semantics and naming cleanup. |

## Detailed Notes by Screen

### `operations_overview`

**What matches well**

* KPI row structure matches the intended overview model
* live map preview + priority queue + infrastructure snapshot is aligned with the UX spec
* trend row covers SLA, kitchen dwell time, and round-trip time

**Gaps**

* product shell uses `COMMAND_DECK` and `RTLS_NODE_ACTIVE`
* left rail contains `Telemetry`, `Geofencing`, `Logs` instead of the final navigation set
* CTA `NEW_SCAN` is not part of the web overview flow

**Recommendation**

Keep the layout, replace the shell language and navigation.

### `live_asset_map`

**What matches well**

* search bar
* asset-type filters
* explicit confidence states
* map legend
* recent activity timeline

**Gaps**

* still uses manufacturing floor content
* still references `MHE`
* shell title uses `SENTINEL_INTERFACE`

**Recommendation**

Promote this to the primary `WEB-03` candidate and rewrite all domain content around kitchen/dining/table/waitstaff/tag workflows.

### `live_operations_map`

**What matches well**

* strong map-first composition
* filter list on the left
* alert panel on the right

**Gaps**

* too much fleet-command language
* lacks the stronger confidence communication found in `live_asset_map`
* no explicit recent activity timeline equivalent to the spec

**Recommendation**

Archive or merge into `live_asset_map`; do not keep both as parallel directions.

### `live_asset_map_selected_asset`

**What matches well**

* selected asset drawer concept
* confidence and location details
* right-side detail pattern

**Gaps**

* selected object is `MHE-091`
* floor name includes manufacturing wording

**Recommendation**

Keep the drawer structure, replace the asset model with RTLS restaurant assets such as `Waiter Tag`, `POS Terminal`, `Tray Cart`, or `Kitchen Runner`.

### `alerts_center`

**What matches well**

* tab structure maps well to `SLA`, `Unauthorized Geofence`, `Maintenance`, and `History`
* filter row is useful and production-like
* alert row actions are aligned with the spec

**Gaps**

* military/operator identity and sector naming
* subtitle says “mission-critical sensor telemetry”
* one unauthorized geofence row uses `MHE-091`

**Recommendation**

Keep layout and row model, replace copy, user identity, and object vocabulary.

### `analytics_heatmap_analysis`

**What matches well**

* report switcher
* parameter rail
* map heatmap canvas
* legend and insight annotation

**Gaps**

* floor and cohort naming are manufacturing-oriented
* operational insight mentions `MHE` rather than staff or service flow

**Recommendation**

Retain structure, rewrite metrics and annotations toward kitchen pass, dining area, waitstaff, and SLA bottlenecks.

### `floor_plan_scale_setup`

**What matches well**

* upload area
* reference-point logic
* scale confirmation

**Gaps**

* naming inconsistency only

**Recommendation**

This is close. Use as-is structurally and normalize branding.

### `calibration_wizard_walk_path_step`

**What matches well**

* stepper
* walk guidance
* quality panel
* progress framing

**Gaps**

* product naming drift
* route context is generic rather than restaurant-floor specific

**Recommendation**

Keep the composition and rewrite contextual copy.

### `asset_finder_mobile`

**What matches well**

* search is dominant
* recent searches and suggested assets fit the flow
* mobile hierarchy is strong

**Gaps**

* warehouse map image
* `MHE` and forklift content
* bottom nav naming is more generic system tooling than asset-finding flow

**Recommendation**

Retain the structure and rewrite all example assets and map imagery.

### `qr_scanner_detected_state`

**What matches well**

* clear camera-first composition
* detected-state bottom-sheet content
* `Assign Zone` CTA is correct

**Gaps**

* missing `<title>`
* tone uses `Targeting System Active`, which is wrong for this product
* only detected state is represented, while the spec also needs idle and invalid states

**Recommendation**

Keep as the detected-state variant, then generate or build idle and invalid companions.

## Recommended Consolidation Plan

### Keep and Refine

* `operations_overview`
* `live_asset_map`
* `live_asset_map_selected_asset`
* `alerts_center`
* `analytics_heatmap_analysis`
* `floor_plan_scale_setup`
* `calibration_wizard_walk_path_step`
* `asset_finder_mobile`
* `qr_scanner_detected_state`
* `infrastructure_health`
* `zone_flow_configuration`

### Archive or Deprioritize

* `live_operations_map`
* `operations_dashboard`
* `sentinel_application_shell`

These are not unusable, but they overlap with stronger variants and increase review noise.

## Next Recommended Action

Before any visual polish pass, do a **content normalization pass** across all retained screens:

1. Replace all `Sentinel`, `Fleet`, `MHE`, `Rover`, `Manufacturing`, and tactical/military language
2. Align navigation and labels with the UX spec frame names and flows
3. Standardize product naming to one system name across all prototypes
4. Keep only one primary variant per target frame
