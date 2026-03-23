# Comprehensive Guide to Building a BLE Indoor Asset Tracking System

## 1. System Architecture and Core Technologies

### 1.1. Overview of BLE for Indoor Positioning

#### 1.1.1. Fundamental Principles of BLE Asset Tracking
Bluetooth Low Energy (BLE) serves as the backbone for modern indoor asset tracking due to its low power consumption, cost-effectiveness, and native smartphone integration. The system relies on small battery-powered **tags** continuously broadcasting a unique identifier, and a fixed infrastructure of **gateways** measuring these signals (specifically RSSI, or phase data for AoA) to estimate distance and direction. This data feeds into a central **Location Engine** to calculate the real-time exact or zone-based position of the asset.

For the demanding environment of restaurants and large catering operations (high metal, water, and human body interference), tracking workflows rely on robust engine math and clear business logic.

#### 1.1.2. The Two-Tier Hardware Strategy
To balance budget constraints against accuracy needs, the platform is structured around a **Two-Tier Strategy**:

*   **Economic Tier (SMB / Standard Operations):** Uses inexpensive BLE beacons (e.g., Minew, Holy-iot) and RSSI scanners. The strategy dictates that RSSI alone is too volatile for precise tracking, so the system utilizes **Fingerprinting** (radiomaps) combined with smoothing algorithms (like Kalman Filters). Update rates are lower (0.5–2 Hz) to preserve battery. Expected accuracy is 1-2 meters or "Zone-Level" confidence fallback.
*   **Premium Tier (Enterprise / High Precision):** Requires **BLE AoA (Angle of Arrival)** or **UWB (Ultra-Wideband)**. AoA evaluates phase differences across a locator's multi-antenna array, while UWB measures exact Time-of-Flight (ToF). Both can achieve sub-meter, deterministic accuracy. Update rates are higher (5-20 Hz). This Tier is ideal for tight kitchen layouts or critical inventory tracing.

#### 1.1.3. Real-Time Processing: MQTT to Websockets
Data acquisition adopts an event-driven flow. Gateways at the edge continuously publish raw telemetry to an **MQTT Broker** (like Mosquitto). MQTT is an ISO standard, lightweight, and perfect for handling gateway dropouts.
The backend normalizes and smooths the data, writes it to a time-series database (TimescaleDB), and publishes finalized estimated coordinates back to the UI dashboards using **WebSockets**.

### 1.2. Core System Architecture

#### 1.2.1. The Data Pipeline
*   **Acquisition (Edge):** Tags → Scanners/Gateways → MQTT Broker.
*   **Location Engine (Core):** Reads from MQTT. Performs Deduplication, Timestamp sync, Kalman filtering, and KNN Fingerprint matching. Outputs an (X, Y) coordinate and a `Confidence Score`.
*   **Events & Rules (Logic):** Evaluates if the new coordinate triggers a geofence, breaches a Table SLA, or starts/ends a round-trip cycle.
*   **Storage (DB):** Operational context stored in PostgreSQL; `position_estimates` and `raw_readings` stored in TimescaleDB. Complex enterprise queries can optionally route to ClickHouse.

#### 1.2.2. Edge Processing Considerations
While the primary location engine runs centrally (cloud or on-prem server), edge-processing at the gateway level is leveraged to filter out severe RSSI outliers and aggregate local metrics, minimizing unnecessary MQTT payload bloat over restaurant Wi-Fi networks.

### 1.3. Infrastructure Deployment Playbooks

#### 1.3.1. Hardware Selection and Compliance
*   **Asset Tags:** Battery life is critical. Select tags configurable to 1-2 second advertising intervals. Tags placed in kitchens or dishwashing areas must be IP67 rated.
*   **Gateways:** Ranging from DIY Raspberry Pi 4B scanners for Economic testing to enterprise AoA locators like Quuppa. Ensure all devices are homologated by local telecommunications agencies (e.g., Anatel in Brazil).

#### 1.3.2. Commissioning and Auto-Calibration
A system is only as good as its deployment. In restaurants, layouts change and signal profiles vary drastically between empty and full dining rooms.
1.  **Map Sync:** Upload floorplans and define zones (Kitchen, Dining Room 1, Pass-through).
2.  **QR Scanning:** Admins use a mobile app to scan gateway MACs and affix them to the digital map.
3.  **Auto-Calibration Routine:** Before launch, an admin activates "Calibration Mode" on their phone and walks the floor naturally for 15-30 minutes. The system builds the baseline RSSI Fingerprint radiomap.

---

## 2. Positioning Algorithms and Analytics

### 2.1. Handling Noise with Smoothing Filters
The Economic Tier relies exclusively on RSSI. Due to multipath signal bouncing off metal kitchen appliances and human bodies, raw RSSI is unmanageable. The engine passes raw signals through an **Extended Kalman Filter (EKF)** or a moving median filter before classification.

### 2.2. Confidence Scores & Fallbacks
When the KNN fingerprinting returns high entropy (the algorithm is unsure exactly where the tag is), it lowers the `Confidence Score`. The UI responds by falling back to "Zone-Level" highlighting rather than displaying a jumping, inaccurate blue dot.

### 2.3. Analytics Unique to Restaurants and Catering
Unlike warehouses mapping inventory, restaurants need operational workflow intelligence:
*   **Table Service SLAs:** Measuring the exact dwell time since a waiter last entered a table's geofence.
*   **Round-Trip Times:** Correlating the time a staff member leaves the Kitchen to when they return, serving as a proxy measure for dining room efficiency.
*   **Bottleneck Heatmaps:** Identifying cross-traffic collisions during peak service times around the expo line or loading docks.

---

## 3. Maintenance, Scale, and OTA

### 3.1. Infrastructure Observability
Monitoring gateway health is paramount. Integrating **OpenTelemetry** for data-pipeline traces and **Prometheus** for infrastructure metrics (e.g., battery levels, packet drop rates, and Gateway CPU utilization).

### 3.2. Firmware Updates (OTA)
Managing 50 gateways across a large catering hall requires automated fleet management. The architecture incorporates Over-The-Air (OTA) updates using protocols provided by platforms like AWS IoT or Eclipse hawkBit, ensuring security patches and algorithm updates can be pushed seamlessly.

### 3.3. Security and Compliance
*   **LGPD & Privacy:** Location data of staff is sensitive. The platform utilizes role-based access control, restricts data retention to the defined 30-90 days, and strictly enforces data minimization (limiting PII in the telemetry payload).
*   **Transport Security:** MQTT connections must use mTLS (Mutual TLS). REST APIs are secured via modern JWT endpoints.
