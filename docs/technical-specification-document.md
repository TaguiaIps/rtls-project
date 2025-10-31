# **Technical Specification Document: RTLS Analytics Platform**

## **1. Introduction**

### **1.1. Purpose**

This document provides a detailed technical specification for the Real-Time Location System (RTLS) project. It outlines the system architecture, component design, data management strategies, and deployment model. This specification is intended for the in-house engineering team to guide the development, testing, and deployment of the platform.

### **1.2. Project Goal**

The primary objective is to develop an indoor positioning system that not only tracks assets in real-time but, more importantly, captures and analyzes location data to provide actionable business intelligence. The system will leverage inference models to suggest optimizations for resource allocation, workflow efficiency, and space utilization within environments like shopping malls and large restaurants.

### **1.3. Scope**

The scope of this project includes the design and implementation of all four tiers of the RTLS architecture:

* **Asset Tags:** Inexpensive BLE beacons.
* **Anchors:** A network of gateways to receive beacon signals.
* **Location Engine:** Backend services for data ingestion, positioning, and analytics.
* **Application Layer:** A web-based dashboard for visualization and administration.
* **Application Layer:** A mobile application for blue-dot navigation and asset tracking.

The initial deployment will not include integration with external systems, but the architecture will be designed with extensible APIs to support future integrations (e.g., with security systems).

---

## **2. System Architecture**

The system will be designed following a modular, four-tier RTLS model. This microservices-based approach ensures scalability and maintainability, aligning with the requirements for an in-house, evolving solution.

### **2.1. Tier 1: Asset Tags**

* **Technology:** Bluetooth Low Energy (BLE) beacons.
* **Recommended Hardware:** Inexpensive, commodity beacons such as **Holy-iot** or similar models.
* **Protocol:** Tags must be configured to broadcast standard **iBeacon** or **Eddystone** packets. This ensures compatibility with a wide range of gateway hardware.
* **Configuration:**
  * **Broadcast Interval:** A default of **1 second (1000ms)** is recommended to balance real-time updates with battery life (RNF003).
  * **Transmission Power:** To be calibrated during deployment to optimize for coverage and reduce signal noise.

### **2.2. Tier 2: Anchors (Gateways)**

A hybrid gateway strategy will be adopted to balance cost, control, and accuracy.

* **Primary Gateway (Cost-Effective):**
  * **Hardware:** **Raspberry Pi 4B or Zero 2 W** with a built-in or external BLE adapter. This aligns with the "Tier 2" developer-focused approach from the gateway analysis.
  * **Software:** A custom Python script using the `bluepy` or `bleak` library will run on each Raspberry Pi.
  * **Functionality:** The script will continuously scan for BLE advertisements, filter for known asset tags, and publish the data (Tag ID, RSSI, Gateway ID, Timestamp) to the backend via MQTT.
  * **Deployment:** Gateways will be powered via standard USB power and connect to the network via Wi-Fi or Ethernet.

* **Optional Gateway (High-Accuracy Zones):**
  * **Hardware:** For areas requiring sub-meter accuracy (e.g., high-value zones, checkout areas), **Holy-IOT HL-A18 (AoA Gateway)** or a similar "Tier 3" device can be deployed.
  * **Integration:** These gateways will have their own data output format (often pre-calculated coordinates), which will be ingested by a dedicated adapter service in the backend.

### **2.3. Tier 3: Location Engine (Backend)**

The backend will be a set of containerized microservices orchestrated by Kubernetes.

* **Communication Protocol:**
  * **Data Ingestion:** An **MQTT Broker** (e.g., Mosquitto) will serve as the entry point for all data from the gateways. This is a lightweight and scalable protocol ideal for IoT data streams.
  * **Real-time Updates:** **WebSockets** will be used to push real-time location updates from the API service to the web dashboard.

* **Core Services:**
    1. **Positioning Service (Python):**
        * Subscribes to the MQTT broker to receive raw RSSI data.
        * Implements the positioning algorithm (see Section 3).
        * Writes the calculated (X, Y) coordinates and the raw source data to the database.
    2. **Analytics & Inference Service (Python):**
        * Periodically queries the historical location database.
        * Runs analysis models (e.g., dwell time, heatmap generation, path analysis, anomaly detection).
        * Generates actionable suggestions and stores them in the database for retrieval by the API.
    3. **API Service (Python/Django REST Framework):**
        * Provides secure, RESTful endpoints for the web application (RF005, RF006).
        * Manages assets, users, beacons, and system configuration.
        * Serves historical and analytical data to the dashboard.
        * Handles WebSocket connections for real-time data streaming.

* **Database:**
  * **Technology:** **PostgreSQL** with the **TimescaleDB** extension.
  * **Rationale:** This provides a powerful solution for both time-series data (location history) and standard relational data (asset information, user roles) within a single, robust database system. It is optimized for the high-volume writes and complex time-based queries required for the analytics goal.

### **2.4. Tier 4: Application Layer**

* **Technology:** A **Single Page Application (SPA)** built with **React.js**, as specified in the architecture document.
* **Key Features:**
  * **Real-Time Map View:** Displays asset locations on an interactive floor plan (RF001, RF002).
  * **Historical Playback:** Visualizes the movement history of selected assets (RF009).
  * **Analytics Dashboard:** Presents heatmaps, zone traffic reports, and actionable insights generated by the backend (RF020).
  * **Admin Panel:** Allows administrators to manage assets, configure beacons, define geofenced zones, and manage user access (RF004, RF006).

---

## **3. Positioning Algorithm Strategy**

The system will implement a multi-phase algorithm strategy to manage complexity and meet accuracy requirements (RNF001).

* **Phase 1: Weighted Centroid Localization (WCL):**
  * **Description:** A simple and computationally efficient algorithm. The asset's location is calculated as the weighted average of the positions of the gateways that detect it, with the weights being derived from the RSSI values.
  * **Advantage:** Easier to implement than trilateration and more resilient to noisy RSSI data. Provides sufficient accuracy (2-5 meters) for initial deployment.

* **Phase 2: Fingerprinting (Future Enhancement):**
  * **Description:** For environments with high multipath interference (like shopping malls), a fingerprinting model will be implemented. This involves creating a radio map of the environment during a calibration phase.
  * **Advantage:** Can significantly improve accuracy over pure RSSI-based models in complex indoor spaces.

* **Phase 3: Angle of Arrival (AoA) Integration:**
  * **Description:** Data from optional AoA gateways will be processed to provide sub-meter accuracy within designated high-precision zones. The backend will be designed to accept pre-calculated coordinates from these gateways.

---

## **4. Data Management & Communication**

### **4.1. Database Schema (High-Level)**

* `assets`: Information about each tracked item (ID, name, type, metadata).
* `gateways`: Location and status of each gateway (ID, name, location_x, location_y).
* `location_history` (TimescaleDB Hypertable): Stores calculated positions (timestamp, asset_id, location_x, location_y).
* `raw_readings` (TimescaleDB Hypertable): Stores raw data from gateways for diagnostics and model retraining (timestamp, asset_id, gateway_id, rssi).
* `zones`: Geofenced areas defined on the map (ID, name, polygon_coordinates).
* `analytics_insights`: Stores actionable suggestions generated by the inference service.

### **4.2. API Design**

The API will be RESTful and provide endpoints for:

* ` /assets `: CRUD operations for assets.
* ` /locations/realtime `: WebSocket endpoint for live location streams.
* ` /locations/history?asset_id=<id>&start=<ts>&end=<ts> `: Historical data queries.
* ` /analytics/heatmaps `: Data for generating heatmaps.
* ` /analytics/insights `: Actionable suggestions.

---

## **5. Deployment & Operations**

* **Containerization:** All backend services will be packaged as **Docker** containers.
* **Orchestration:** **Kubernetes** will be used to manage, scale, and ensure the resilience of the containerized services. This provides a robust, scalable production environment.
* **Logging & Monitoring:** The **ELK Stack** (Elasticsearch, Logstash, Kibana) will be used for centralized, structured logging and system monitoring. This is critical for debugging and maintaining system health.
