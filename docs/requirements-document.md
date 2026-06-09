# **Requirements Document: RTLS Analytics Platform**

## **1. Introduction**

### **1.1. Purpose**

This document specifies the functional and non-functional requirements for the Real-Time Location System (RTLS) Analytics Platform. It serves as the authoritative source for project scope and functionality, ensuring a shared understanding between stakeholders and the development team. Requirements are cross-referenced against the OpenSpec specifications that define their acceptance criteria.

### **1.2. Project Scope**

The project entails the development of an end-to-end indoor positioning system optimized for **restaurants and large catering operations**, with horizontal applicability to industry. The system employs a **Two-Tier Architecture** (Economic Tier via BLE Fingerprinting and Premium Tier via BLE AoA/UWB) to track assets within defined physical spaces. The primary focus is generating business intelligence from location data, including actionable insights like service time, Table SLAs, and round-trips. The system handles real-time tracking, deployment playbooks, and complex analytical reports.

### **1.3. Definitions, Acronyms, and Abbreviations**

| Term | Definition |
| :--- | :--- |
| **Administrator** | A privileged user role responsible for system setup, calibration, and configuration. |
| **Asset Tag** | A BLE or UWB beacon attached to a person or object to be tracked. |
| **BLE** | Bluetooth Low Energy. |
| **AoA** | Angle of Arrival (Direction Finding precision method). |
| **UWB** | Ultra-Wideband (Time of Flight precision method). |
| **Dwell Time** | The total time an asset remains within a predefined zone. |
| **Round Trip** | Time taken by staff/asset to travel from point A to point B and back. |
| **General User** | A standard user role focused on operations and analytics (e.g., Restaurant Manager). |
| **Geofence** | A virtual perimeter for a real-world geographic area or zone. |
| **Gateway** | A fixed hardware device (Anchor/Locator) that scans for tag signals and forwards data via MQTT. |
| **Confidence Score** | A metric (`high`, `medium`, `low`) indicating the reliability of a position estimate. |
| **POI** | Point of Interest — a typed operational area on a floor plan. |
| **SLA** | Service Level Agreement — a threshold timer tied to table or zone operations. |
| **MQTT** | Message Queuing Telemetry Transport — lightweight pub/sub protocol for gateway telemetry. |
| **JWT** | JSON Web Token — token-based authentication standard. |

---

## **2. User Roles and Characteristics**

The system supports two distinct user roles with specific permissions:

| Role | Description | Key Responsibilities |
| :--- | :--- | :--- |
| **Administrator** | The technical manager. Responsible for physical rollout, infrastructure health, and logical setup. | - Create and manage sites, floors, floor plans, and scale calibration.<br>- Define operational zones, tables, restricted zones, and POIs.<br>- Register gateways with Economic or Premium tier profiles.<br>- Manage asset tag registry and CSV bulk import.<br>- Commission devices via QR on mobile.<br>- Configure alert rules and review audit logs.<br>- Monitor infrastructure health and gateway calibration state. |
| **General User** | The primary consumer of location data and analytics. Focused on operations and restaurant SLAs. | - View real-time asset tracking with confidence scores.<br>- Search and filter assets by name, tag ID, or category.<br>- Generate heatmaps, dwell times, and round-trip reports.<br>- Configure threshold alerts and review alert center.<br>- Monitor Table SLAs and SLA trends.<br>- Export analytics data to CSV.<br>- View trajectory replay and floor heatmaps. |

---

## **3. Functional Requirements**

### **3.1. Authentication & Access Control**

*OpenSpec references: `user-authentication`, `role-based-access`, `audit-event-recording`*

| ID | Requirement |
| :--- | :--- |
| **FR-SEC-001** | The system shall authenticate users via local email-and-password credentials and issue JWT access tokens and refresh tokens. Access tokens shall be short-lived; refresh tokens shall be rotated on use. |
| **FR-SEC-002** | The system shall enforce a two-role authorization model (`Administrator` and `General User`) on both backend routes and web application routing. Administrators shall be routed to setup/management areas; General Users shall be routed to operations/analytics areas. |
| **FR-SEC-003** | The system shall persist audit events for all authentication lifecycle actions (sign-in, sign-out, refresh, bootstrap) and configuration mutations, excluding sensitive material such as passwords and tokens. Audit events shall support future filtering by actor, action type, target, and time range. |
| **FR-SEC-004** | The system shall provide a non-UI bootstrap path to create the first Administrator account for local and pilot-style deployments. |
| **FR-SEC-005** | The web login experience shall implement "Command" interaction standards including password visibility toggles and real-time validation feedback. |

### **3.2. Spatial Administration (Administrator Role)**

*OpenSpec references: `site-and-floor-management`, `floor-plan-management`, `zone-and-poi-editor`, `gateway-placement-and-tier-profiles`, `asset-tag-registry`*

| ID | Requirement |
| :--- | :--- |
| **FR-ADM-001** | The system shall allow an Administrator to create and manage sites and their floors using "Command" style interaction standards with technical input masks for identifiers. |
| **FR-ADM-002** | The system shall allow an Administrator to upload one raster floor-plan image (PNG or JPG) per floor and calibrate floor scale using two reference points and a real-world measured distance. Floor-plan metadata and retrieval information shall be exposed for downstream map rendering. |
| **FR-ADM-003** | The system shall allow an Administrator to create, edit, and delete polygonal operational areas (zone, table, restricted zone, POI) on a floor plan with sufficient metadata for alerting, analytics, and live map rendering. |
| **FR-ADM-004** | The system shall allow an Administrator to register and manage gateway records with stable identifiers, floor-linked placement coordinates, Economic or Premium tier assignment, and Premium-specific modality and mounting metadata. Premium gateway calibration state shall be tracked against the current floor and placement geometry. |
| **FR-ADM-005** | The system shall allow an Administrator to create and manage asset tag records with stable tag identity, display name, category, update-rate profile, and battery profile metadata. The system shall support validated CSV bulk import with row-level validation and explicit confirmation. |
| **FR-ADM-006** | The system shall provide an automated calibration engine for BLE fingerprinting that ingests collected calibration samples, generates floor-level radiomap and baseline offset artifacts, persists calibration status and quality metadata, and makes the resulting artifacts available to the positioning pipeline. |

### **3.3. Telemetry Ingestion & Persistence**

*OpenSpec references: `gateway-telemetry-ingestion`, `raw-reading-persistence`*

| ID | Requirement |
| :--- | :--- |
| **FR-ING-001** | The system shall accept MQTT telemetry only from registered gateways using the documented ingestion topic contract, rejecting telemetry from unknown gateways. |
| **FR-ING-002** | The system shall validate telemetry payload structure and required fields before persisting raw-ingestion state, rejecting malformed payloads without creating raw-reading records. |
| **FR-ING-003** | The system shall protect the ingestion path from duplicate telemetry delivery caused by MQTT retries, using message identity deduplication with a bounded time window. |
| **FR-ING-004** | The system shall accept and persist gateway heartbeat messages to maintain latest-known liveness state for operational monitoring. |
| **FR-ING-005** | The system shall accept Premium-tier telemetry (AoA/UWB) through a parallel ingestion contract preserving modality, quality, and sequence context. |
| **FR-ING-006** | The system shall use backend-controlled `broker_received_at` as the canonical timestamp for all persisted readings, storing gateway-provided time as non-canonical metadata. |

### **3.4. Position Estimation**

*OpenSpec references: `economic-tier-position-estimation`, `premium-tier-position-estimation`*

| ID | Requirement |
| :--- | :--- |
| **FR-POS-001** | The system shall derive durable asset locations from BLE raw readings using registered gateway placements on mapped floors, with confidence semantics (`high`, `medium`, `low`) and zone-level fallback when confidence is insufficient for a point estimate. |
| **FR-POS-002** | The system shall preserve both current location and location history for each tracked asset. |
| **FR-POS-003** | The system shall derive locations from Premium-tier AoA/UWB measurements using valid gateway geometry and calibration state, with modality-aware precision metadata. |
| **FR-POS-004** | When both Economic and Premium positioning results are available, the canonical state shall prefer the higher-quality result based on source-tier and precision metadata. |

### **3.5. Live Location Access**

*OpenSpec references: `live-location-query-and-streaming`*

| ID | Requirement |
| :--- | :--- |
| **FR-LOC-001** | The system shall expose an API to query latest known asset locations with filters for site, floor, asset, and confidence level. |
| **FR-LOC-002** | The system shall support asset search by name or tag identifier, returning the latest known location context for matches. |
| **FR-LOC-003** | The system shall expose durable trajectory history for a selected asset and time range. |
| **FR-LOC-004** | The system shall support live position update subscriptions via WebSocket for real-time map rendering. |

### **3.6. Derived Events**

*OpenSpec references: `zone-transition-and-dwell-events`, `round-trip-and-table-sla-primitives`*

| ID | Requirement |
| :--- | :--- |
| **FR-EVT-001** | The system shall generate zone-entry and zone-exit events from accepted live-location updates when assets cross defined operational area boundaries. |
| **FR-EVT-002** | The system shall create dwell records for occupancy windows, persisting start time, end time, and duration for downstream analytics and alert workflows. |
| **FR-EVT-003** | The system shall measure round-trip times by evaluating origin-destination-origin cycles from canonical zone-entry history. |
| **FR-EVT-004** | The system shall maintain current timer state for SLA-eligible tables, exposing timer snapshots for downstream alert and analytics workflows. |
| **FR-EVT-005** | All derived events shall persist durable history for downstream reporting and review. |

### **3.7. Real-Time Visualization**

*OpenSpec references: `operations-overview-dashboard`, `live-map-workspace`, `web-operations-shell`*

| ID | Requirement |
| :--- | :--- |
| **FR-VIS-001** | The system shall provide a shared protected web operations shell with "Command Rail" layout, role-aware navigation, and integrated alert and analytics access. |
| **FR-VIS-002** | The system shall provide an Operations Overview landing screen with live operational state summary, floor-linked live map preview, and a priority queue derived from live signals. |
| **FR-VIS-003** | The system shall provide a floor-linked Live Map workspace with glassmorphism HUD, search and filtering capabilities, confidence-aware asset visualization, and selected-asset inspection drawer. |
| **FR-VIS-004** | The system shall render asset positions in real-time via WebSocket updates, with visual confidence indicators and zone-level fallback when point-precision degrades. |
| **FR-VIS-005** | The system shall allow users to search for specific assets and filter by asset name, tag identifier, or category. |

### **3.8. Alert Rules & Alert Center**

*OpenSpec references: `alert-rules-and-notification-delivery`, `alerts-center-triage`*

| ID | Requirement |
| :--- | :--- |
| **FR-NOT-001** | The system shall support configurable alert rules for Table SLA violations and unauthorized geofence breaches, with severity, scope, and enabled/disabled state. |
| **FR-NOT-002** | The system shall generate durable alert instances when alert rule conditions are triggered, with status tracking (`active`, `acknowledged`, `resolved`). |
| **FR-NOT-003** | The system shall deliver in-app notifications for active alerts and support optional email delivery attempts. |
| **FR-NOT-004** | The system shall provide an Alerts Center for reviewing active and historical alerts, with detail inspection, acknowledgement, and resolution actions. |
| **FR-NOT-005** | The system shall generate system-managed maintenance alerts for stale or low-battery gateways. |

### **3.9. Analytics & Reporting**

*OpenSpec references: `analytics-workspace-and-reports`*

| ID | Requirement |
| :--- | :--- |
| **FR-ANL-001** | The system shall provide an Analytics workspace with a report switcher for trajectory replay, floor heatmaps, dwell-time reports, round-trip reports, and table SLA trends. |
| **FR-ANL-002** | The system shall generate heatmaps showing traffic density and potential bottlenecks over selected time ranges. |
| **FR-ANL-003** | The system shall calculate and display round-trip times between defined zone pairs. |
| **FR-ANL-004** | The system shall generate dwell-time reports showing time spent in specific zones. |
| **FR-ANL-005** | The system shall display the historical movement path (trajectory) of a selected asset on the floor plan. |
| **FR-ANL-006** | The system shall display time-bucketed Table SLA trend data using the configured alert-rule threshold baseline. |
| **FR-ANL-007** | The system shall support async CSV export for analytics scopes, with export job tracking and artifact download. |

### **3.10. Mobile Applications**

*OpenSpec references: `mobile-asset-finder`, `mobile-commissioning-and-calibration`*

| ID | Requirement |
| :--- | :--- |
| **FR-MOB-001** | The mobile app shall provide an Asset Finder screen for searching assets by name or tag identifier, displaying location context with confidence/precision metadata, and handing off to the web Live Map. |
| **FR-MOB-002** | The mobile app shall persist recent searches locally and order them by most recent access. |
| **FR-MOB-003** | The mobile app shall provide an Administrator commissioning workflow with native camera-based QR scanning for device identification, site/floor/zone assignment, floor-linked preview with gateway markers and route checkpoints, and tap-driven checkpoint capture for calibration sessions. |
| **FR-MOB-004** | The mobile app shall persist completed commissioning sessions locally with target identity, floor and zone context, elapsed time, sample count, and checkpoint progress. |
| **FR-MOB-005** | The mobile app shall accept an access token plus configurable API and web base URLs for authorized API access. |

### **3.11. Observability & Data Lifecycle**

*OpenSpec references: `local-runtime-stack`*

| ID | Requirement |
| :--- | :--- |
| **FR-OBS-001** | The system shall expose a local `/metrics` endpoint with text-based metrics for gateway counters, alert counters, telemetry counters, and audit counters. |
| **FR-OBS-002** | The system shall attach `X-Request-ID` to every API response for request tracing. |
| **FR-OBS-003** | The system shall provide an administrator Health workspace with gateway-risk cards, telemetry totals, alert pressure, and audit totals. |
| **FR-OBS-004** | The system shall support administrator-triggered data lifecycle runs that apply retention windows to raw telemetry, location history, and export artifacts, and refresh hourly analytics rollups. |
| **FR-OBS-005** | The system shall support hourly analytics rollups for heatmap density and table SLA aggregates to accelerate compatible analytics queries. |

---

## **4. Non-Functional Requirements**

### **4.1. Performance**

| ID | Requirement |
| :--- | :--- |
| **NFR-PER-001** | The system shall support differing update rates: **0.5–2 Hz** for the Economic Tier, and **5–20 Hz** for the Premium Tier. |
| **NFR-PER-002** | End-to-end latency (tag to dashboard) shall be **<1–2 seconds** for typical tracking, and **<500 ms** for critical Premium alerts. |
| **NFR-PER-003** | Analytics (heatmap, trajectory) for 100 tags over 24 hours shall generate in under 15 seconds. |

### **4.2. Security**

| ID | Requirement |
| :--- | :--- |
| **NFR-SEC-001** | The development and pilot baseline shall support MQTT deployment on a trusted private network without mTLS, provided the broker is not publicly exposed and the environment is documented as non-production. |
| **NFR-SEC-002** | Sensitive DB data (including user locations if classified as PII under LGPD) shall be subject to access controls and minimization. |
| **NFR-SEC-003** | Production MQTT transport shall use TLS with broker certificate validation and mutual TLS (mTLS) for gateway-to-broker communication, including per-gateway identity and broker-enforced access controls. |

### **4.3. Usability**

| ID | Requirement |
| :--- | :--- |
| **NFR-USA-001** | The UI for defining geofences must be a point-and-click polygon drawing tool on the floor plan canvas. |
| **NFR-USA-002** | Mobile commissioning workflows shall minimize manual entry by supporting scanner-based or QR-derived device intake and floor-linked assignment in the mobile app. |
| **NFR-USA-003** | Production mobile commissioning workflows shall support native camera-based QR scanning to reduce setup errors and avoid dependency on external scanners. |
| **NFR-USA-004** | The web application shall implement "Command" interaction standards with focus-responsive Cyan borders, semantic form feedback, and real-time validation for all administrative workflows. |

### **4.4. Reliability & Availability**

| ID | Requirement |
| :--- | :--- |
| **NFR-REL-001** | The system shall monitor infrastructure health (gateways offline, battery drops) and trigger maintenance alerts through the Alerts Center. |
| **NFR-REL-002** | The system's core messaging broker and events engine shall support multi-node clustering for High Availability (HA). |
| **NFR-REL-003** | The system shall enforce data retention windows: raw readings (90 days), premium measurements (90 days), location history (30 days), export artifacts (7 days). |

---

## **5. OpenSpec Cross-Reference**

Each functional requirement area maps to one or more OpenSpec specifications under `openspec/specs/`. The specifications define the detailed acceptance criteria and scenarios for each requirement.

| OpenSpec Spec | Requirement IDs |
| :--- | :--- |
| `user-authentication` | FR-SEC-001, FR-SEC-004, FR-SEC-005 |
| `role-based-access` | FR-SEC-002 |
| `audit-event-recording` | FR-SEC-003 |
| `site-and-floor-management` | FR-ADM-001 |
| `floor-plan-management` | FR-ADM-002 |
| `zone-and-poi-editor` | FR-ADM-003 |
| `gateway-placement-and-tier-profiles` | FR-ADM-004 |
| `asset-tag-registry` | FR-ADM-005 |
| `gateway-telemetry-ingestion` | FR-ING-001, FR-ING-002, FR-ING-003, FR-ING-004, FR-ING-005 |
| `raw-reading-persistence` | FR-ING-006 |
| `economic-tier-position-estimation` | FR-POS-001, FR-POS-002 |
| `premium-tier-position-estimation` | FR-POS-003, FR-POS-004 |
| `live-location-query-and-streaming` | FR-LOC-001, FR-LOC-002, FR-LOC-003, FR-LOC-004 |
| `zone-transition-and-dwell-events` | FR-EVT-001, FR-EVT-002, FR-EVT-005 |
| `round-trip-and-table-sla-primitives` | FR-EVT-003, FR-EVT-004, FR-EVT-005 |
| `operations-overview-dashboard` | FR-VIS-002 |
| `live-map-workspace` | FR-VIS-003, FR-VIS-004, FR-VIS-005 |
| `web-operations-shell` | FR-VIS-001 |
| `alert-rules-and-notification-delivery` | FR-NOT-001, FR-NOT-003, FR-NOT-005 |
| `alerts-center-triage` | FR-NOT-002, FR-NOT-004 |
| `analytics-workspace-and-reports` | FR-ANL-001 through FR-ANL-007 |
| `mobile-asset-finder` | FR-MOB-001, FR-MOB-002, FR-MOB-005 |
| `mobile-commissioning-and-calibration` | FR-MOB-003, FR-MOB-004 |
| `local-runtime-stack` | FR-OBS-001 through FR-OBS-005 |
