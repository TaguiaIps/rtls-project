# **Requirements Document: RTLS Analytics Platform**

## **1. Introduction**

### **1.1. Purpose**

This document specifies the functional and non-functional requirements for the Real-Time Location System (RTLS) Analytics Platform. It serves as the authoritative source for project scope and functionality, ensuring a shared understanding between stakeholders and the development team.

### **1.2. Project Scope**

The project entails the development of an end-to-end indoor positioning system. The system will track BLE-enabled asset tags within defined physical spaces (e.g., shopping malls, restaurants, parking lots). The primary focus is not just on real-time tracking, but on providing a suite of analytics tools to derive business intelligence from historical location data. The system will be developed in-house and will initially operate as a standalone platform.

### **1.3. Definitions, Acronyms, and Abbreviations**

| Term | Definition |
| :--- | :--- |
| **Administrator** | A privileged user role responsible for system setup and configuration. |
| **Asset Tag** | A BLE beacon attached to a person or object to be tracked. |
| **BLE** | Bluetooth Low Energy. |
| **Dwell Time** | The total time an asset remains within a predefined zone. |
| **General User** | A standard user role focused on viewing data and running analytics. |
| **Geofence** | A virtual perimeter for a real-world geographic area. |
| **Gateway** | A fixed hardware device that scans for BLE signals and forwards data to the backend. |
| **Heatmap** | A graphical representation of data where values are depicted by color. |
| **RTLS** | Real-Time Location System. |
| **UI** | User Interface. |

---

## **2. User Roles and Characteristics**

The system shall support two distinct user roles with specific permissions:

| Role | Description | Key Responsibilities |
| :--- | :--- | :--- |
| **Administrator** | The technical manager of the system. This user is responsible for the physical and logical setup of the tracking environment. | - Manage floor plans.<br>- Configure and calibrate the gateway network.<br>- Register and manage asset tags.<br>- Define system-wide settings. |
| **General User** | The primary consumer of the location data and analytics. This role corresponds to the "Carlos Mendes" persona, focused on operational insights. | - View real-time asset locations.<br>- Generate and view analytics dashboards (heatmaps, reports).<br>- Configure and receive alerts.<br>- Analyze historical asset movement. |

---

## **3. Functional Requirements**

### **3.1. System Administration (Administrator Role)**

| ID | Requirement |
| :--- | :--- |
| **FR-ADM-001** | The system shall allow an Administrator to upload architectural floor plan images (format to be determined, e.g., PNG, SVG). |
| **FR-ADM-002** | The system shall provide a UI for the Administrator to place, move, and configure gateway icons on the uploaded floor plan. |
| **FR-ADM-003** | The system shall provide a web form for an Administrator to register a single new asset tag, including its unique ID and descriptive name/type. |
| **FR-ADM-004** | The system shall allow an Administrator to perform a bulk import of asset tags via a CSV file upload. The CSV format will include columns for tag ID and name. |
| **FR-ADM-005** | The system shall allow an Administrator to define a configurable data retention period for historical location data, with a range between 30 and 90 days. |

### **3.2. Real-Time Tracking & Visualization (General User & Administrator)**

| ID | Requirement |
| :--- | :--- |
| **FR-VIS-001** | The system shall display a map view with the uploaded floor plan as the background. |
| **FR-VIS-002** | The system shall display the real-time location of all active asset tags as distinct icons on the map. |
| **FR-VIS-003** | The system shall allow users to click on an asset icon to view its name and details. |
| **FR-VIS-004** | The system shall provide a search function to find a specific asset by its name, which then centers the map on that asset's location. |

### **3.3. Analytics & Reporting (General User)**

| ID | Requirement |
| :--- | :--- |
| **FR-ANL-001** | The system shall allow a user to define polygonal zones (geofences) on the map interface. |
| **FR-ANL-002** | The system shall generate a heatmap visualization overlayed on the floor plan, showing areas of high and low asset traffic over a user-selected time period. |
| **FR-ANL-003** | The system shall generate a "dwell time" report, calculating the total time specific assets spent within a predefined geofence over a selected period. |
| **FR-ANL-004** | The system shall be able to display the historical movement path (trajectory) of a selected asset over a user-defined time frame. |
| **FR-ANL-005** | The system shall generate a report detailing when a specific asset enters or exits a predefined geofence (e.g., to monitor if equipment leaves an area). |

### **3.4. Notifications & Alerting (General User)**

| ID | Requirement |
| :--- | :--- |
| **FR-NOT-001** | The system shall allow users to configure alerts to be triggered when an asset enters or exits a specific geofence. |
| **FR-NOT-002** | The system shall deliver triggered alerts via the web application's UI (in-app notifications). |
| **FR-NOT-003** | The system shall deliver triggered alerts via email to the user's registered address. |
| **FR-NOT-004** | The system shall deliver triggered alerts via push notifications to a companion mobile application. |

### **3.5. User Management & Security**

| ID | Requirement |
| :--- | :--- |
| **FR-SEC-001** | The system shall require all users to authenticate via a secure login mechanism (e.g., username/password). |
| **FR-SEC-002** | The system shall enforce access control based on the user's assigned role (Administrator or General User). |

---

## **4. Non-Functional Requirements**

### **4.1. Performance**

| ID | Requirement |
| :--- | :--- |
| **NFR-PER-001** | The system shall update the position of an asset on the UI within **5 seconds** of its physical location change. |
| **NFR-PER-002** | The system shall be capable of processing data from at least **500** concurrently active asset tags. |
| **NFR-PER-003** | Analytics reports (e.g., heatmap, dwell time) for a 24-hour period with 100 tags shall be generated in under 15 seconds. |

### **4.2. Security**

| ID | Requirement |
| :--- | :--- |
| **NFR-SEC-001** | All communication between the client UI and the backend server shall be encrypted using TLS v1.3 or higher. |
| **NFR-SEC-002** | Sensitive data stored in the database shall be encrypted at rest using the AES-256 standard. |

### **4.3. Usability**

| ID | Requirement |
| :--- | :--- |
| **NFR-USA-001** | The UI for defining geofences shall be an interactive, point-and-click drawing tool on the map. |
| **NFR-USA-002** | The primary dashboard shall be intuitive, allowing a new General User to find and view an asset's location with minimal training. |

### **4.4. Reliability & Availability**

| ID | Requirement |
| :--- | :--- |
| **NFR-REL-001** | The system's core services (data ingestion, API, real-time view) shall have an uptime of 99.5%. |
| **NFR-REL-002** | The system shall perform automated, encrypted backups of its database daily. |
