# Prototype Normalization Plan

This document translates the audit findings into a concrete rewrite plan for the retained prototypes in [README.md](./README.md).

Use it to:

* patch the generated HTML directly
* guide a manual Figma/content cleanup pass
* write focused Stitch refinement prompts for each retained screen

## 1. Goal

Normalize the generated prototypes so they consistently represent the intended product:

* **Product domain:** RTLS analytics for restaurants and large catering operations
* **Core personas:** Operations Manager and System Administrator
* **Visual theme:** Industrial Command Deck
* **Navigation model:** Overview, Live Map, Analytics, Alerts, Admin, Health, Audit Log

## 2. Global Rewrite Rules

Apply these changes across all retained prototype screens before any visual polish work.

### 2.1. Product Naming

Replace fragmented product naming with one consistent product label.

| Replace | With |
| :--- | :--- |
| `SENTINEL ANALYTICS` | `RTLS Analytics Platform` |
| `SENTINEL RTLS` | `RTLS Analytics Platform` |
| `SENTINEL COMMAND` | `RTLS Analytics Platform` |
| `SENTINEL_COMMAND` | `RTLS Analytics Platform` |
| `SENTINEL_INTERFACE` | `RTLS Analytics Platform` |
| `COMMAND_DECK` | `RTLS Analytics Platform` |
| `RTLS COMMAND` | `RTLS Analytics Platform` |
| `RTLS_NODE_ACTIVE` | `Restaurant Ops Cluster` |

### 2.2. Navigation and Shell Language

| Replace | With |
| :--- | :--- |
| `Telemetry` | `Live Map` |
| `Geofencing` | `Alerts` or `Zones` depending on context |
| `Logs` | `Audit Log` or `System Logs` depending on context |
| `Fleet Command` | `Operations Console` |
| `Terminal` | `Audit Log` or `System` depending on screen intent |
| `NEW_SCAN` | `Open Live Map` or remove from overview |

### 2.3. Domain Vocabulary

Replace industrial, warehouse, tactical, or military wording with restaurant/catering wording.

| Replace | With |
| :--- | :--- |
| `Manufacturing` | `Dining Hall`, `Kitchen`, or `Service Floor` based on screen |
| `Warehouse` | `Restaurant Floor` |
| `MHE` | `Cart`, `Tray Cart`, or `Kitchen Cart` |
| `forklift` | `cart`, `tray cart`, or `equipment` |
| `Rover` | `Runner Cart` or `Service Cart` |
| `Sector_Alpha` | `Dining Hall A` |
| `Node_01` | `Site Alpha` or `Gateway Cluster A` |
| `CPT. MILLER` | `Alex` or `Carlos Mendes` depending on persona |
| `mission-critical sensor telemetry` | `real-time operational alerts and tracking events` |
| `Targeting System Active` | `Scanner Ready` |

### 2.4. Asset Naming

Replace generic or industrial asset examples with RTLS-appropriate examples.

| Replace | With |
| :--- | :--- |
| `MHE-091` | `Tray Cart 09` |
| `MHE_09` | `Tray Cart 09` |
| `MHE_042` | `POS Terminal 04` or `Runner Cart 04` |
| `Unit-442 (Sarah J.)` | `Waiter Tag 442 (Sarah J.)` |
| `Unit-812 (Marcus L.)` | `Waiter Tag 812 (Marcus L.)` |
| `Cold Unit 04` | `POS Terminal 04` or `Cold Cart 04` based on context |
| `Staff Tag 102` | `Waiter Tag 102` |
| `TAG_0812` | `POS Tag 0812` or `Waiter Tag 0812` |

### 2.5. Zone and Floor Vocabulary

| Replace | With |
| :--- | :--- |
| `Floor 01: Manufacturing` | `Dining Hall A` |
| `Zone B` | `Kitchen Pass` or a named restaurant zone |
| `Storage B` | `Cold Storage` |
| `Transit Corridor` | `Service Corridor` |
| `Prep Area` | `Prep Station` |
| `Loading Bay` | `Loading Dock` |

## 3. Screen-by-Screen Rewrite List

## 3.1. `operations_overview` -> `WEB-02`

**Decision:** Keep and refine

### Keep

* KPI row layout
* live map preview placement
* Priority Queue structure
* Infrastructure Snapshot structure
* trend row composition

### Rewrite

| Current | Target |
| :--- | :--- |
| `COMMAND_DECK` | `RTLS Analytics Platform` |
| `RTLS_NODE_ACTIVE` | `Restaurant Ops Cluster` |
| `Telemetry` | `Live Map` |
| `Geofencing` | `Alerts` |
| `Logs` | `Audit Log` |
| `NEW_SCAN` | remove or replace with `Open Live Map` |
| `SITE: ALPHA-7` | `Dining Hall A` |
| `KITCHEN CLUSTER A` | `Operations Overview` with a contextual subtitle |
| `SYSTEM_STABLE` | `Live Connection Stable` |
| `Cold Storage Door Open` | `Cold Storage Door Open` can stay |
| `Battery Low: Unit-881` | `Battery Low: Waiter Tag 881` or `Battery Low: POS Tag 881` |

### Add or Adjust

* Subtitle under page title: `Dining Hall A · Lunch Service · Live now`
* Priority queue cards should prefer table, waiter, kitchen, or POS language over generic unit language
* Overview shell should use the final nav model from the UX spec

## 3.2. `live_asset_map` -> `WEB-03`

**Decision:** Primary candidate for the default live map

### Keep

* search bar
* confidence states
* legend
* recent activity timeline
* right-side map stats overlay

### Rewrite

| Current | Target |
| :--- | :--- |
| `SENTINEL_INTERFACE` | `RTLS Analytics Platform` |
| `Floor 01: Manufacturing` | `Dining Hall A` |
| `MHE` | `Equipment` or `Carts` |
| `MHE-091` | `Tray Cart 09` |
| industrial blueprint image alt/copy | restaurant floor plan image alt/copy |

### Add or Adjust

* left filter labels should match spec: `Staff`, `Equipment`, `Tags`, `Zones`, `Active Alerts`
* use restaurant zone names such as `Kitchen Pass`, `Dining West`, `Cold Storage`, `Service Corridor`
* activity timeline items should include SLA and zone events, not generic equipment update logs

## 3.3. `live_asset_map_selected_asset` -> `WEB-04`

**Decision:** Keep and refine

### Keep

* right-side asset drawer layout
* confidence section
* location telemetry section
* asset detail emphasis

### Rewrite

| Current | Target |
| :--- | :--- |
| `SENTINEL_COMMAND` | `RTLS Analytics Platform` |
| `MHE-091` | `Tray Cart 09` or `POS Terminal 09` |
| `forklift` icon/content | cart, terminal, or waiter-tag semantics |
| `01 (Manufacturing)` | `Dining Hall A` |

### Add or Adjust

* Ensure the drawer includes `View Trajectory`, `Center on Map`, and `Open Alert History`
* Add `current zone`, `last seen`, and `confidence` language consistent with the UX spec

## 3.4. `alerts_center` -> `WEB-08`

**Decision:** Keep and refine

### Keep

* tabs: `SLA`, `Unauthorized Geofence`, `Maintenance`, `History`
* filter row
* alert-row density and action structure

### Rewrite

| Current | Target |
| :--- | :--- |
| `SENTINEL COMMAND` | `RTLS Analytics Platform` |
| `Node_01: Sector_Alpha` | `Dining Hall A` |
| `CPT. MILLER` | `Carlos Mendes` or `Alex` |
| `SUPERVISOR` | `Operations Manager` or `System Administrator` |
| `Real-time status of all mission-critical sensor telemetry` | `Real-time operational alerts and tracking events` |
| `MHE Vehicles` | `Carts / Equipment` |
| `MHE-091 [SEC_07]` | `Tray Cart 09` |

### Add or Adjust

* Keep one critical SLA alert based on table service
* Keep one unauthorized geofence alert based on a cart or staff tag entering a restricted zone
* Keep one gateway offline maintenance alert

## 3.5. `analytics_heatmap_analysis` -> `WEB-10`

**Decision:** Keep and refine

### Keep

* report switcher
* filter rail
* map heatmap canvas
* legend
* insight annotation block

### Rewrite

| Current | Target |
| :--- | :--- |
| `SENTINEL RTLS` | `RTLS Analytics Platform` |
| `Floor 01: Manufacturing` | `Dining Hall A` |
| `All Equipment, MHE` | `Waitstaff + Service Carts` or a restaurant cohort |
| `MHE units` | `waitstaff and cart traffic` |

### Add or Adjust

* favor restaurant-centric metrics:
  * `Avg Kitchen Dwell Time`
  * `Waitstaff Round-Trip Time`
  * `Dining Path Density`
* insight copy should mention `Kitchen Pass`, `Dining West`, `Cold Storage`, or `Service Corridor`

## 3.6. `floor_plan_scale_setup` -> `WEB-16`

**Decision:** Keep and refine

### Keep

* upload module
* reference point messaging
* scale confirmation
* admin workflow framing

### Rewrite

| Current | Target |
| :--- | :--- |
| `SENTINEL_ANALYTICS` | `RTLS Analytics Platform` |
| `FLOOR_ADMIN` | `Admin Console` |
| `DEPLOY_CHANGES` | `Save and Continue` |
| `LOG_OUT` | `Sign Out` |

### Add or Adjust

* align admin navigation with final spec:
  * `Floor Plans`
  * `Gateways`
  * `Assets`
  * `Calibration`
  * `Health`
  * `Audit Log`

## 3.7. `calibration_wizard_walk_path_step` -> `WEB-21`

**Decision:** Keep and refine

### Keep

* wizard stepper
* active collection state
* quality panel
* guidance-oriented structure

### Rewrite

| Current | Target |
| :--- | :--- |
| `RTLS COMMAND` | `RTLS Analytics Platform` |
| generic node/site shell labels | restaurant site labels |
| `MAP_LAYER: L01_NORTH_WING` | `Dining Hall A Floor Map` |
| `SCALE: 1:200m` | actual floor calibration context appropriate to venue |

### Add or Adjust

* route text should mention walking through kitchen, dining, and service corridor
* right panel should mention gateways and signal quality in restaurant-specific language

## 3.8. `asset_finder_mobile` -> `MOB-02`

**Decision:** Keep and refine

### Keep

* dominant search bar
* recent searches list
* suggested assets cards
* status strip

### Rewrite

| Current | Target |
| :--- | :--- |
| warehouse image and alt text | restaurant floor mini-map and restaurant-floor alt text |
| `MHE_09` | `Tray Cart 09` |
| `MHE_042` | `POS Terminal 04` |
| `ZONE_B` | `Dining West` or `Kitchen Pass` |
| `GATE_7` | `Service Corridor` or `Cold Storage` |
| `SYSTEM` bottom nav | `Profile` or `Settings` depending on intended flow |

### Add or Adjust

* suggested assets should be things like:
  * `CRITICAL: POS Terminal 07`
  * `WARNING: Tray Cart 09`
  * `Waiter Tag 442`
* keep one unresolved-alert asset in the suggested list

## 3.9. `qr_scanner_detected_state` -> `MOB-06`

**Decision:** Keep and refine

### Keep

* camera-first composition
* detected-state sheet
* `Assign Zone` CTA

### Rewrite

| Current | Target |
| :--- | :--- |
| missing title | add `QR Scanner - RTLS Analytics Platform` |
| `Targeting System Active` | `Scanner Ready` |
| `GATEWAY_NODE_X1` | `Gateway Node X1` or actual gateway naming style |
| tactical scan tone | operational setup tone |

### Add or Adjust

* create companion screens for:
  * idle state
  * invalid/unsupported QR
  * delayed sync state

## 3.10. `infrastructure_health` -> `WEB-22`

**Decision:** Keep and refine

### Keep

* strong health dashboard composition
* gateway summary structure
* uptime and health metrics

### Rewrite

| Current | Target |
| :--- | :--- |
| `Fleet Command` | `Operations Console` |
| generic cluster naming | actual site/floor naming |

### Add or Adjust

* surface battery drops, delayed heartbeat, and packet loss as defined in the spec

## 3.11. `zone_flow_configuration` -> `WEB-15`

**Decision:** Keep and refine

### Keep

* editor-oriented composition
* map legend
* zone tool affordances

### Rewrite

| Current | Target |
| :--- | :--- |
| `Fleet Command` | `Operations Console` |
| generic zone names | `Kitchen Pass`, `Dining West`, `Cold Storage`, `Table 12 Zone` |

### Add or Adjust

* property panel should support:
  * zone type
  * SLA eligibility
  * alert participation
  * restricted-zone toggle

## 4. Screen Consolidation Decisions

### Keep as Primary

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

### Deprioritize

* `live_operations_map`
* `operations_dashboard`
* `sentinel_application_shell`

## 5. Execution Order

Normalize screens in this order:

1. `operations_overview`
2. `live_asset_map`
3. `live_asset_map_selected_asset`
4. `alerts_center`
5. `asset_finder_mobile`
6. `qr_scanner_detected_state`
7. `analytics_heatmap_analysis`
8. `floor_plan_scale_setup`
9. `calibration_wizard_walk_path_step`
10. `infrastructure_health`
11. `zone_flow_configuration`

## 6. Definition of Done

A screen is normalized when:

* the product naming is consistent
* restaurant/catering RTLS vocabulary replaces industrial or military language
* the screen matches the intended UX spec frame purpose
* no duplicate stronger variant exists elsewhere in the prototypes folder
