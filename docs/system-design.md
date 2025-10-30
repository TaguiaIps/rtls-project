# **Software Design Document: RTLS Analytics Platform**

## **1. Introduction**

### **1.1. Purpose**

This document provides a comprehensive software design for the RTLS Analytics Platform. It details the system's architecture, data models, component interactions, and key implementation strategies. This document is intended for the in-house development team to guide the implementation, testing, and deployment of the system.

### **1.2. Scope**

This design covers the four primary tiers of the RTLS system: the backend microservices (Ingestion, API, Analytics), the database layer, the frontend web application, and the cross-platform mobile application. It translates the functional and non-functional requirements into a concrete technical implementation plan.

---

## **2. System Architecture Overview**

The system will be implemented using a microservices architecture, containerized with Docker, and orchestrated by Kubernetes. This approach ensures scalability, resilience, and maintainability.

### **2.1. Architectural Diagram (Container View)

![System architecture (container view)](diagrams/system-design-component-diagram.png)

---

## **3. Backend Design**

### **3.1. Gateway Communication Layer**

* **Protocol:** MQTT
* **MQTT Topic Structure:** `rtls/data/{gateway_id}`
* **Payload Format (JSON):** Each message published by a gateway will contain a list of observed beacons.

    ```json
    {
      "gatewayId": "gw-01-lobby",
      "timestamp": "2025-10-29T18:30:00Z",
      "beacons": [
        { "tagId": "A1:B2:C3:D4:E5:F6", "rssi": -65 },
        { "tagId": "B2:C3:D4:E5:F6:A1", "rssi": -72 }
      ]
    }
    ```

### **3.2. Data Ingestion & Positioning Service**

* **Language/Framework:** Python (using a high-performance library like `asyncio` for concurrency).
* **Core Logic:**
    1. The service subscribes to the MQTT topic `rtls/data/#`.
    2. Incoming beacon readings are stored in an in-memory buffer.
    3. **Aggregation Window:** A process runs every **3 seconds** (configurable), averaging RSSI values for each tag from each gateway.
    4. **Position Calculation:** The service calculates the asset's (X, Y) coordinates using the **Weighted Centroid Localization (WCL)** algorithm.
    5. **Data Persistence:** The service writes the raw readings to the `raw_readings` table and the calculated position to the `location_history` table.

### **3.3. API Service**

* **Language/Framework:** Python with Django REST Framework.
* **Security:** Stateless **JSON Web Tokens (JWT)**. The flow includes short-lived access tokens and long-lived refresh tokens.
* **API Endpoint Specification:**

| Resource | Method | Path | Description |
| :--- | :--- | :--- | :--- |
| **Authentication** | `POST` | `/api/token` | Authenticates user with credentials, returns access/refresh tokens. |
| | `POST` | `/api/token/refresh` | Obtains a new access token using a valid refresh token. |
| **Assets** | `GET` | `/api/assets` | Retrieves a paginated list of all assets. Supports filtering by type. |
| | `POST` | `/api/assets` | Creates a new asset (US-ADM-04). |
| | `GET` | `/api/assets/{id}` | Retrieves details for a single asset. |
| | `PUT` | `/api/assets/{id}` | Updates details for a single asset. |
| | `DELETE` | `/api/assets/{id}` | Deletes an asset. |
| | `POST` | `/api/assets/bulk_import` | Imports assets from a CSV file (US-ADM-05). |
| **Analytics** | `GET` | `/api/analytics/trajectory` | Retrieves historical location points for an asset within a time range (US-ANL-01). |
| | `GET` | `/api/analytics/heatmap` | Retrieves aggregated data for heatmap visualization (US-ANL-04). |
| | `GET` | `/api/analytics/visit_count` | Retrieves a report of visits to specified POIs by an asset (US-ANL-03). |
| **Admin - Gateways** | `GET` | `/api/gateways` | Retrieves a list of all configured gateways. |
| | `POST` | `/api/gateways` | Registers a new gateway and its location (US-ADM-02). |
| | `PUT` | `/api/gateways/{id}` | Updates a gateway's configuration. |
| **Admin - Zones & POIs** | `GET` | `/api/zones` | Retrieves a list of all geofences and Points of Interest. |
| | `POST` | `/api/zones` | Creates a new geofence or POI (US-ANL-02). |
| | `PUT` | `/api/zones/{id}` | Updates a zone's geometry or name. |
| **Data Export** | `POST` | `/api/export/request` | Requests an async export of raw data. Returns a job ID. |
| | `GET` | `/api/export/status/{job_id}` | Checks the status of an export job and provides a download URL when complete. |
| **Real-time** | `WS` | `/ws/locations` | WebSocket endpoint for streaming real-time location updates. |

### **3.4. Analytics & Inference Service**

* **Implementation:** A set of scheduled tasks managed by a job queue like **Celery** with a scheduler like Celery Beat.
* **Core Jobs:**
  * **Data Aggregation (Nightly):** Purges raw data older than 90 days after creating permanent hourly summaries.
  * **Insight Generation (Scheduled):** Populates the `analytics_insights` table with actionable information.

---

## **4. Database Design**

* **System:** PostgreSQL with the TimescaleDB extension.
* **Key Schemas:**
  * **`assets`**:
    * `id` (PK),
    * `tag_id` (VARCHAR, UNIQUE),
    * `name` (VARCHAR),
    * `type` (VARCHAR).
  * **`gateways`**:
    * `id` (PK),
    * `gateway_id` (VARCHAR, UNIQUE),
    * `name` (VARCHAR),
    * `location_x` (FLOAT),
    * `location_y` (FLOAT).
  * **`raw_readings`** (TimescaleDB Hypertable):
    * `timestamp` (TIMESTAMPTZ),
    * `tag_id` (FK to assets),
    * `gateway_id` (FK to gateways),
    * `rssi` (INTEGER).
  * **`location_history`** (TimescaleDB Hypertable):
    * `timestamp` (TIMESTAMPTZ),
    * `asset_id` (FK to assets),
    * `location_x` (FLOAT),
    * `location_y` (FLOAT).
* **Data Lifecycle Management:** A TimescaleDB **retention policy** will automatically delete raw data older than **90 days**.

Of course. Visualizing the data model is a critical step. An Entity-Relationship Diagram (ERD) will provide your team with a clear blueprint of the database structure, showing how different pieces of information relate to one another.

The data model includes the core tables we've discussed and adds necessary tables for users, zones, and alerts to create a complete picture.

### **Data Model (Entity-Relationship Diagram)**

This diagram illustrates the primary database tables and their relationships.

![Data model (ERD)](diagrams/system-design-er-diagram.png)

### **Explanation of Relationships:**

* **`assets` to `location_history` (One-to-Many):** Each asset can have a long history of calculated locations.
* **`assets` to `raw_readings` (One-to-Many):** Each asset's tag generates many raw signal readings.
* **`gateways` to `raw_readings` (One-to-Many):** Each gateway captures many raw signal readings from various assets.
* **`assets` and `zones` to `alerts` (Many-to-Many via `alerts` table):** An asset can trigger alerts in multiple zones, and a zone can have alerts from multiple assets. The `alerts` table links them.
* **`assets` to `analytics_insights` (One-to-Many, Optional):** An analytical insight might be related to a specific asset, but it could also be a system-wide observation.

---

## **5. Frontend Design**

* **Framework:** React.js (using Vite for the build tool).
* **State Management:** **Zustand**.
* **Key Components:** `MapView`, `DashboardView`, `AnalyticsPanel`, `AdminPanel`.

### **5.1. General User Flow Diagram**

![User flow](diagrams/system-design-user-flow-diagram.png)

---

## **6. Mobile Application Design**

* **Framework:** A cross-platform framework like **Flutter** or **React Native**.
* **Core Logic:** On-device pathfinding using the **A* (A-star) algorithm** with a pre-downloaded map graph.

---

## **7. Sequence Diagrams**

### **7.1. Real-Time Map View Update**

This diagram shows how a beacon's signal results in an icon moving on the user's screen.

![Real-time map view update](diagrams/system-design-map-view-sequence-diagram.png)

### **7.2. Generating a Trajectory Report**

This diagram illustrates the flow for fulfilling user story US-ANL-01.

![Generating a trajectory report](diagrams/system-design-trajectory-sequence-diagram.png)

### **7.3. Administrator Adds a New Asset**

This diagram illustrates the flow for fulfilling user story US-ADM-04.

![Administrator adds a new asset](diagrams/system-design-add-asset-sequence-diagram.png)

## **8. Testing Strategy**

A multi-layered testing strategy will be implemented to ensure code quality, service reliability, and correctness of the user experience.

### **8.1. Unit Testing**

* **Objective:** To verify the correctness of individual functions, classes, and components in isolation.
* **Backend (Python):**
  * **Framework:** `pytest`.
  * **Scope:**
    * Pure functions within the **Positioning Service**, such as the WCL algorithm implementation and data aggregation logic.
    * API endpoint serializers and data validation rules in the **API Service**.
    * Business logic within the **Analytics Service**, such as insight generation rules.
* **Frontend (React):**
  * **Frameworks:** `Jest` and `React Testing Library`.
  * **Scope:**
    * Individual React components (e.g., `AssetDetailsPanel`, `FilterDropdown`).
    * Custom hooks and state management logic (Zustand stores).
    * Utility functions (e.g., date formatting, data transformation).

### **8.2. Integration Testing**

* **Objective:** To verify the interactions and data flow between microservices and the database.
* **Framework:** `Docker Compose` will be used to create an isolated test environment.
* **Scope:**
  * **Positioning Pipeline:** A test will publish a mock MQTT message and assert that the correct `location_history` record is created in the test database.
  * **API-Database Interaction:** Tests will cover the full lifecycle of API calls, ensuring that a `POST` to `/api/assets` correctly creates a record and a subsequent `GET` retrieves it.
  * **Inter-service Communication:** Tests will verify that events published by the Positioning Service (e.g., via Redis Pub/Sub) are correctly received and handled by the API Service.

### **8.3. End-to-End (E2E) Testing**

* **Objective:** To validate complete user flows from the perspective of the user, ensuring the entire system works together as expected.
* **Framework:** `Cypress` or `Playwright`.
* **Scope:**
  * **Admin Setup Flow:** A test will simulate an Administrator logging in, uploading a floor plan, creating a gateway, and bulk-importing assets.
  * **Analytics Flow:** A test will simulate a General User logging in, navigating to the map, selecting an asset, and successfully generating a trajectory report for the last 24 hours.
  * **Real-time Update Flow:** A test will verify that when the backend receives new location data, the corresponding asset icon on the map updates its position within the specified 5-second latency window.

---

## **9. Deployment & CI/CD**

A continuous integration and continuous deployment pipeline will be established to automate the process of building, testing, and deploying the application to the Kubernetes cluster.

### **9.1. Source Control & CI Trigger**

* **Repository:** A monorepo or multiple repositories hosted on Git (e.g., GitHub).
* **Trigger:** The CI pipeline will be triggered automatically on every push to the `main` branch or on the creation of a pull request against `main`.

### **9.2. Continuous Integration (CI) Pipeline**

The pipeline will execute the following steps for each relevant service:

1. **Lint & Analyze:** Run static code analysis to check for code quality and potential bugs.
2. **Test:** Execute all unit and integration tests. A failing test will fail the pipeline.
3. **Build Docker Image:** If tests pass, a new Docker image will be built for the service.
4. **Tag Image:** The image will be tagged with the Git commit hash for traceability.
5. **Push to Registry:** The tagged image will be pushed to a private container registry (e.g., Docker Hub, Google Container Registry).

### **9.3. Continuous Deployment (CD) Pipeline**

* **Strategy:** A GitOps approach using a tool like **Argo CD** is recommended for managing deployments.
* **Workflow:**
    1. A separate Git repository will hold the Kubernetes YAML manifests for all services.
    2. After the CI pipeline successfully pushes a new Docker image, a step will automatically update the corresponding Deployment manifest in the GitOps repository with the new image tag.
    3. Argo CD, running in the Kubernetes cluster, will detect the change in the GitOps repository.
    4. Argo CD will automatically apply the updated manifest to the cluster, triggering a **rolling update** of the service. This ensures zero-downtime deployments.
