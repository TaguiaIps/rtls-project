# **Requirements Document: RTLS Analytics Platform**

## **1. Introduction**

### **1.1. Purpose**

This document specifies the functional and non-functional requirements for the Real-Time Location System (RTLS) Analytics Platform. It serves as the authoritative source for project scope and functionality, ensuring a shared understanding between stakeholders and the development team.

### **1.2. Project Scope**

The project entails the development of an end-to-end indoor positioning system optimized for **restaurants and large catering operations**, with horizontal applicability to industry. The system will employ a **Two-Tier Architecture** (Economic Tier via BLE Fingerprinting and Premium Tier via BLE AoA/UWB) to track assets within defined physical spaces. The primary focus is generating business intelligence from location data, including actionable insights like service time, Table SLAs, and round-trips. The system handles real-time tracking, deployment playbooks, and complex analytical reports.

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

---

## **2. User Roles and Characteristics**

The system shall support two distinct user roles with specific permissions:

| Role | Description | Key Responsibilities |
| :--- | :--- | :--- |
| **Administrator** | The technical manager. Responsible for physical rollout, infrastructure health, and logical setup. | - Manage floor plans and scales.<br>- Commission gateways/tags via QR.<br>- Run auto-calibration routines.<br>- Manage tiers and update profiles. |
| **General User** | The primary consumer of location data and analytics. Focused on operations and restaurant SLAs. | - View real-time asset tracking with confidence scores.<br>- Generate heatmaps, dwell times, and round-trip reports.<br>- Configure threshold alerts.<br>- Monitor Table SLAs. |

---

## **3. Functional Requirements**

### **3.1. System Administration (Administrator Role)**

| ID | Requirement |
| :--- | :--- |
| **FR-ADM-001** | The system shall allow an Administrator to upload floor plan images and set real-world scaling via reference points. |
| **FR-ADM-002** | The system shall provide a UI to place gateways corresponding to the Economic or Premium tier. |
| **FR-ADM-003** | The system shall provide a guided mobile calibration workflow that allows an Administrator to select site and floor context, assign zone or room context, capture floor-linked checkpoints with a visible blue-dot marker, and save a calibration session summary for later follow-up. |
| **FR-ADM-004** | The system shall support provision of two hardware tiers: Economic (BLE RSSI/Fingerprinting) and Premium (BLE AoA/UWB) profiles. |
| **FR-ADM-005** | The system shall allow bulk import of asset tags via CSV, allowing specification of update rates and battery profiles. |
| **FR-ADM-006** | The system shall provide an automated calibration engine for BLE fingerprinting that ingests collected calibration samples, generates floor-level radiomap and baseline offset artifacts, persists calibration status and quality metadata, and makes the resulting artifacts available to the positioning pipeline. |

### **3.2. Real-Time Tracking & Visualization (General User & Administrator)**

| ID | Requirement |
| :--- | :--- |
| **FR-VIS-001** | The system shall display a map view with the uploaded floor plan and define specific zones (e.g., Kitchen, Dining). |
| **FR-VIS-002** | The system shall display real-time tracking of assets, rendering new positions via WebSockets. |
| **FR-VIS-003** | The system shall display a visual **Confidence Score** for estimated locations, falling back to zone highlighting when point-precision degrades. |
| **FR-VIS-004** | The system shall allow users to search for specific assets and filter by asset category (e.g., Waiters, Carts). |

### **3.3. Analytics & Reporting (General User)**

| ID | Requirement |
| :--- | :--- |
| **FR-ANL-001** | The system shall allow users to define polygonal geofences/zones on the map. |
| **FR-ANL-002** | The system shall generate heatmaps showing traffic density and potential bottlenecks over selected times. |
| **FR-ANL-003** | The system shall calculate round-trip times between defined zones (e.g., Kitchen to Dining Area) to measure staff efficiency. |
| **FR-ANL-004** | The system shall generate a "dwell time" report for calculating time spent in specific zones. |
| **FR-ANL-005** | The system shall display the historical movement path (trajectory) of a selected asset. |
| **FR-ANL-006** | The system shall measure Table Service SLAs, highlighting violations when a specific operation exceeds maximum time limits. |

### **3.4. Notifications & Alerting (General User)**

| ID | Requirement |
| :--- | :--- |
| **FR-NOT-001** | The system shall trigger alerts when predefined Table SLAs are violated (e.g., waitstaff absent from dining area for >15 mins). |
| **FR-NOT-002** | The system shall trigger alerts when assets enter/exit unauthorized geofences. |
| **FR-NOT-003** | The system shall deliver in-app notifications and support optional email delivery. |

### **3.5. User Management & Security**

| ID | Requirement |
| :--- | :--- |
| **FR-SEC-001** | The system shall authenticate users via secure login mechanisms (JWT). |
| **FR-SEC-002** | The system shall enforce role-based access control. |
| **FR-SEC-003** | The system shall provide an audit log for configuration changes, ensuring compliance and data governance (LGPD context). |

---

## **4. Non-Functional Requirements**

### **4.1. Performance**

| ID | Requirement |
| :--- | :--- |
| **NFR-PER-001** | The system shall support differing update rates: **0.5–2 Hz** for the Economic Tier, and **5–20 Hz** for the Premium Tier. |
| **NFR-PER-002** | End-to-end latency (tag to dashboard) shall be **<1-2 seconds** for typical tracking, and **<500 ms** for critical Premium alerts. |
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
| **NFR-USA-001** | The UI for defining geofences must be a drag-and-drop/point-and-click drawing tool. |
| **NFR-USA-002** | Mobile commissioning workflows shall minimize manual entry by supporting scanner-based or QR-derived device intake and floor-linked assignment in the mobile app. |
| **NFR-USA-003** | Production mobile commissioning workflows shall support native camera-based QR scanning to reduce setup errors and avoid dependency on external scanners. |

### **4.4. Reliability & Availability**

| ID | Requirement |
| :--- | :--- |
| **NFR-REL-001** | The system shall monitor infrastructure health (gateways offline, battery drops) and trigger maintenance alerts. |
| **NFR-REL-002** | The system's core messaging broker and events engine shall support multi-node clustering for High Availability (HA). |
