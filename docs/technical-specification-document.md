# **Technical Specification Document: RTLS Analytics Platform**

## **1. Introduction**

### **1.1. Purpose**

This document provides a detailed technical specification for the Real-Time Location System (RTLS) project. It outlines the system architecture, component design, data management strategies, and deployment model.

### **1.2. Project Goal**

The primary objective is to develop a hardware-agnostic, event-driven indoor positioning system targeted at **restaurants and large catering operations**. The system captures and analyzes location data to provide actionable intelligence on service SLAs, waitstaff round-trips, and kitchen efficiency.

### **1.3. Scope**

The scope employs a **Two-Tier Strategy** (Economic & Premium), covering:

* **Tier 1 (Economic):** BLE Fingerprinting for SMBs (1-2m accuracy).
* **Tier 2 (Premium):** BLE AoA or UWB for enterprise and high-precision use cases (sub-meter accuracy).
* **Location Engine:** Backend processing combining Message Brokers (MQTT), Smoothing/Filters, and TimescaleDB storage.
* **Interfaces:** Web Dashboard + Mobile App (for blue-dot navigation and commissioning).

---

## **2. System Architecture**

The system follows an agnostic, event-driven pattern connecting hardware infrastructure to an insights engine.

### **2.1. Devices (Tags & Smartphones)**

* **Economic Tier Tags:** Standard BLE beacons (e.g., Minew, Holy-iot). Configured for 0.5-2 Hz advertising intervals to balance responsividade and battery life.
* **Premium Tier Tags:** UWB tags (e.g., Sewio) or CTE-enabled BLE tags for AoA (e.g., Quuppa). Configured for high-frequency updates (5-20 Hz) for critical operations.
* **Smartphones:** Supported via Wi-Fi RTT (Android) or BLE Scanning modes as a secondary/fallback tracking mechanism, primarily for clients or management apps.

### **2.2. Infrastructure (Anchors & Gateways)**

* **Economic Gateways:** Edge devices (Raspberry Pi, ESP32, or vendor BLE gateways) scanning for RSSI. They transmit raw observations (Tag ID, RSSI, Timestamp) to the broker.
* **Premium Locators:** Antenna arrays for AoA that compute IQ samples/angles, or UWB anchors measuring Time-of-Flight (ToF). They generally forward precise coordinate telemetry.
* **Connectivity & Health:** Devices connect via Wi-Fi/Ethernet. Device health (heartbeat, battery) is reported continuously via MQTT.

### **2.3. Platform Services (Cloud / On-prem)**

The backend is structured around microservices:

1. **MQTT Broker (Mosquitto, EMQX):** Handles edge telemetry ingestion on topics `rtls/data/{gateway_id}`, `rtls/premium/{gateway_id}`, and `rtls/heartbeat/{gateway_id}`.
2. **Ingestion & Normalization (Worker):** Subscribes to MQTT topics, validates registered gateway identity, deduplicates retries in Redis (10s TTL on `(gateway_id, message_id)`), stamps canonical `broker_received_at` time, persists raw telemetry (Economic) and normalized AoA/UWB measurements (Premium), and updates latest heartbeat state.
3. **Location Engine (Worker):**
   - *Economic:* Reuses recent accepted raw readings and registered gateway placements on a mapped floor to derive a confidence-aware location result (`high`, `medium`, `low`). Low-confidence updates fall back to a mapped zone result.
   - *Premium:* Processes AoA phase data or UWB ToF measurements with valid gateway geometry and calibration state, producing sub-meter precision with modality-aware metadata. Requires an active calibration artifact (radiomap + gateway offsets) for the floor.
   - Canonical state prefers higher-quality results when both tiers are available.
4. **Calibration Engine (Worker):** Consumes submitted mobile calibration walk sessions and generates radiomap artifacts (signal-strength grids per gateway) and per-gateway offset metadata (signal bias, estimated distance). Artifacts are versioned, stored in object storage, and linked to floors with an `active`/`stale`/`invalid` lifecycle. Automatic invalidation triggers when floor plans or scale configurations change.
4. **Derived Events Engine (Worker):** Evaluates positioning updates against operational areas to generate zone-entry/exit events, dwell records, round-trip measurements, and table SLA timer snapshots. Events persist durable history for downstream alert and analytics workflows.
5. **Alert Pipeline:** Evaluates derived events against configurable alert rules (Table SLA, unauthorized geofence, maintenance) to generate durable alert instances with status tracking and notification delivery (in-app + optional email).
6. **API Service (FastAPI):** Provides REST endpoints for CRUD, analytics queries, alert management, audit review, and export jobs. Uses **WebSockets** (`/ws/locations`) for real-time map pushes.
7. **Analytics & Exports:** Bounded read-only queries for trajectory, heatmaps, dwell, round-trips, and SLA trends. Async CSV export jobs with object-storage artifacts. Hourly analytics rollups for query acceleration.
8. **Data Lifecycle:** Administrator-triggered retention runs (raw readings: 90d, premium measurements: 90d, location history: 30d, exports: 7d) and hourly rollup refresh.

### **2.4. Data Storage Model**

* **PostgreSQL:** Operational Data (Users, Profiles, Sites, Floorplans, Zones, Assets).
* **TimescaleDB:** Time-series extension mapping append-only `raw_readings` plus later `location_history` workloads. The Stage B baseline also keeps a latest heartbeat snapshot per registered gateway.
* *(Optional)* **ClickHouse:** OLAP database for complex, enterprise-level historical heatmap generations and aggregates.

Current scope notes:

* The full pipeline is delivered: ingestion, two-tier positioning, derived events, alert rules and alerts center, analytics workspace, mobile asset finder, and mobile commissioning.
* Premium-tier AoA/UWB telemetry, guided mobile calibration, and production mTLS remain deferred to later implementation-plan changes.

---

## **3. Positioning Algorithm Strategy**

### **3.1. Economic Tier: Confidence-Aware Placement Baseline**

1. **Recent-reading aggregation:** The engine looks at the latest accepted raw reading per gateway inside a short backend-controlled time window.
2. **Floor selection:** Candidate readings are grouped by floor through the registered gateway map, and the strongest floor wins the update.
3. **Point estimation:** The current baseline computes a weighted floor-plan coordinate from the selected gateways' placements.
4. **Confidence Scoring & Fallback:** The backend emits `high`, `medium`, or `low` confidence. Low-confidence updates fall back to a mapped zone when possible and are dropped when no credible mapped placement exists.
5. **Future calibration extension:** Later mobile calibration work can enrich this stage with radiomap/fingerprinting inputs without changing the persisted latest-location, history, or streaming contracts.

### **3.2. Premium Tier: Deterministic Location**

1. **Telemetry Input:** Receives Phase/IQ calculations for BLE AoA or ToF data for UWB.
2. **Positioning:** Applies trilateration/triangulation with sub-meter accuracy.
3. **Refinement:** Overlays against Map Matching for absolute correctness.

---

## **4. Data Management & Integrations**

### **4.1. Core Database Schema Highlights**

* `users`: Platform user accounts with email, password hash, and role.
* `sites` / `floors`: Spatial hierarchy for operational scope.
* `floor_plans`: Raster image metadata and storage references per floor.
* `operational_areas`: Polygonal zones, tables, restricted zones, and POIs linked to floors.
* `gateways`: Registered gateway records with floor-linked placement, tier, and Premium-specific metadata.
* `assets`: Asset tag records with identity, category, update-rate, and battery profiles.
* `raw_readings` (TimescaleDB Hypertable): Append-only Economic-tier raw telemetry.
* `premium_raw_measurements`: Normalized AoA/UWB measurements with modality and quality context.
* `asset_current_locations`: Latest known floor-linked state per tracked asset, including confidence, source-tier, source-modality, and optional zone fallback.
* `location_history` (TimescaleDB Hypertable): Append-only location results for trajectory and replay.
* `zone_events`: Canonical zone-entry and zone-exit events.
* `dwell_records`: Durable dwell windows from zone occupancy.
* `table_timers`: Current SLA timer snapshots for SLA-eligible tables.
* `alert_rules`: Configurable alert rule definitions (Table SLA, unauthorized geofence).
* `alert_instances`: Durable alert instances with status tracking.
* `alert_actions`: Acknowledgement and resolution history per alert.
* `alert_notification_deliveries`: In-app and email notification delivery records.
* `audit_events`: Authentication lifecycle and configuration mutation audit trail.
* `analytics_rollups`: Hourly heatmap density and SLA aggregates.
* `export_jobs`: Async CSV export tracking with object-storage references.

### **4.2. API & Observability**

* **OpenTelemetry (OTel):** Application tracing and performance monitoring across the ingestion pipeline.
* **Prometheus + Grafana:** Infrastructure monitoring (Gateway uptime, packet rate, latencies).

---

## **5. Deployment, OTA & Operations**

* **Containerization:** All backend services packaged via Docker, orchestrated locally via Docker Compose (production target: k3s or Kubernetes).
* **Commissioning Playbook:** Standardized flow mapping: Site -> Floor -> Floor Plan -> Calibrate Scale -> Define Zones -> Place Gateways -> Register Asset Tags.
* **Mobile Commissioning:** Expo-based mobile app with native camera QR scanning, site/floor/zone assignment, floor-linked preview with gateway markers, and tap-driven calibration checkpoint capture.
* **Device Management (OTA):** Employs solutions like Eclipse hawkBit or AWS IoT to securely push firmware updates to edge gateways.
* **Compliance:** Verification that selected hardware possesses required Anatel homologation (for Brazilian operations) and respects LGPD data-minimization practices regarding staff tracking.
* **Observability:** Local `/metrics` endpoint, `X-Request-ID` tracing, administrator Health workspace with gateway-risk cards and audit totals, and data lifecycle management with configurable retention windows.
