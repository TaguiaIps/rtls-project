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

1. **MQTT Broker (e.g., Mosquitto, EMQX):** Handles edge telemetry ingestion.
2. **Ingestion & Normalization:** A shared worker subscribes to `rtls/data/{gateway_id}` and `rtls/heartbeat/{gateway_id}`, validates registered gateway identity, deduplicates retries in Redis, stamps canonical broker time, and persists raw telemetry plus latest heartbeat state.
3. **Location Engine:**
   - *Economic:* Applies **Kalman Filters** or Median smoothing to RSSI, then uses KNN/WKNN Fingerprinting to estimate position, yielding a `Confidence Score`.
   - *Premium:* Processes AoA phase data or UWB ToF for precise (X,Y) coordinates.
   - Constrains outputs using Geofence/Floorplan mapping to prevent "wall crossing".
4. **Events / Rules Engine:** Evaluates positioning against business logic (Table SLAs, Zone Entry/Exit, Dwell Time) and generates Alerts.
5. **API Service (FastAPI / Django REST):** Provides REST endpoints for CRUD and serves Analytics. Uses **WebSockets** for real-time map pushes.

### **2.4. Data Storage Model**

* **PostgreSQL:** Operational Data (Users, Profiles, Sites, Floorplans, Zones, Assets).
* **TimescaleDB:** Time-series extension mapping append-only `raw_readings` plus later `location_history` workloads. The Stage B baseline also keeps a latest heartbeat snapshot per registered gateway.
* *(Optional)* **ClickHouse:** OLAP database for complex, enterprise-level historical heatmap generations and aggregates.

Current Stage B scope notes:

* Raw-reading persistence and latest gateway heartbeat state are implemented first.
* Position estimation, live-map delivery, alerts, analytics rollups, and premium-tier telemetry remain deferred to later implementation-plan changes.

---

## **3. Positioning Algorithm Strategy**

### **3.1. Economic Tier: Filtered Fingerprinting**

1. **Preprocessing & Smoothing:** RSSI data is notoriously noisy. The engine applies an **Extended Kalman Filter (EKF)** or moving average to smooth RSSI values from multiple gateways before evaluation.
2. **Classification:** Uses K-Nearest Neighbors (KNN) to compare real-time smoothed RSSI against the calibrated radiomap.
3. **Confidence Scoring & Fallback:** Generates a confidence metric (entropy of neighbors). If confidence drops below a threshold, the system reports the position at a "Zone-level" fallback rather than a pinpoint dot.
4. **Map Matching:** Uses physical vectors (walls, corridors) to "snap" estimated dots to realistic pathways.

### **3.2. Premium Tier: Deterministic Location**

1. **Telemetry Input:** Receives Phase/IQ calculations for BLE AoA or ToF data for UWB.
2. **Positioning:** Applies trilateration/triangulation with sub-meter accuracy.
3. **Refinement:** Overlays against Map Matching for absolute correctness.

---

## **4. Data Management & Integrations**

### **4.1. Core Database Schema Highlights**

* `site_hierarchy`: Defines Sites -> Buildings -> Floors -> Zones.
* `asset_entities`: Links an asset to a Profile (update rate, battery spec).
* `position_estimate` (Timescale): Timestamp, AssetID, X, Y, Z, Confidence, Method (Fingerprint/AoA).
* `business_events`: Logs of entry/exit, SLA violations, alert triggers.

### **4.2. API & Observability**

* **OpenTelemetry (OTel):** Application tracing and performance monitoring across the ingestion pipeline.
* **Prometheus + Grafana:** Infrastructure monitoring (Gateway uptime, packet rate, latencies).

---

## **5. Deployment, OTA & Operations**

* **Containerization:** All backend services packaged via Docker, orchestrated via Kubernetes.
* **Commissioning Playbook:** Standardized flow mapping: Site -> Floorplan -> Calibrate Scale -> Draw Zones -> Deploy Gateways.
* **Automated Calibration:** Tools inside the app let an Admin walk the restaurant scanning signals for 15-30 minutes to auto-generate the Fingerprint map.
* **Device Management (OTA):** Employs solutions like Eclipse hawkBit or AWS IoT to securely push firmware updates to edge gateways.
* **Compliance:** Verification that selected hardware possesses required Anatel homologation (for Brazilian operations) and respects LGPD data-minimization practices regarding staff tracking.
