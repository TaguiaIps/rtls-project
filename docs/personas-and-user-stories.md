# **Personas & User Stories: RTLS Analytics Platform**

## **1. Personas**

There are two different primary personas for the project.

### **Persona 1: The Administrator**

| **Name** | **Alex (The Setup Guru)** |
| :--- | :--- |
| **Role** | IT / Systems Administrator |
| **Personality** | Meticulous, detail-oriented, and pragmatic. Alex values precision and reliability above all else. |
| **Core Goal** | To ensure the RTLS platform is a trustworthy source of truth. The data must be accurate, the hardware must be reliable, and the system must be stable. |
| **Motivations** | - Setting up a system that "just works" without constant firefighting.<br>- Empowering operational teams with data they can trust.<br>- Preventing "garbage in, garbage out" by ensuring precise calibration. |
| **Frustrations** | - Vague setup instructions.<br>- Systems that require constant manual adjustments.<br>- Inaccurate data that undermines user confidence and leads to support tickets. |
| **Quote** | *"If the data isn't accurate, the entire system is useless. My job is to make sure we can trust every single data point."* |

### **Persona 2: The General User**

| **Name** | **Carlos Mendes (The Operations Manager)** |
| :--- | :--- |
| **Role** | Operations Manager (e.g., Mall Manager, Restaurant General Manager) |
| **Personality** | Strategic, results-driven, and busy. Carlos needs to see the big picture quickly but also needs the ability to investigate anomalies. |
| **Core Goal** | To use location data to make smarter operational decisions that improve efficiency, enhance customer experience, and reduce costs. |
| **Motivations** | - Quickly understanding staff and asset movement patterns.<br>- Identifying bottlenecks and inefficiencies in workflows.<br>- Proactively addressing issues before they become major problems. |
| **Frustrations** | - Drowning in raw data without clear insights.<br>- Spending too much time searching for assets or people.<br>- Not having concrete evidence to back up operational changes. |
| **Quote** | *"Don't just show me dots on a map. Show me what it means. How can I use this information to run my business better today?"* |

---

## **2. User Story Map**

This story map organizes our features into a narrative flow, showing how users will progress through the system to achieve their goals.

### **Backbone: Major User Activities**

**System Setup & Configuration** `(Alex)` <br>
→ **Daily Operations Monitoring** `(Carlos)` <br>
→ **Deep-Dive Analysis** `(Carlos)` <br>
→ **On-the-Go Location & Navigation** `(Alex & Carlos)`

---

### **Detailed User Stories**

#### **Activity 1: System Setup & Configuration (Alex)**

*As Alex, I need to set up the physical and digital environment flawlessly to ensure data accuracy.*

| ID | User Story | Confirmation (Acceptance Criteria) | Priority |
| :--- | :--- | :--- |
| **US-ADM-01** | As **Alex**, I want to upload a floor plan image, so that I have a visual canvas for my gateway and asset layout. | - User can select a valid image file (PNG, SVG).<br>- The uploaded image is displayed as the map background.<br>- An error message is shown for invalid file types or files exceeding a size limit (e.g., 10MB). | **Must-have** |
| **US-ADM-02** | As **Alex**, I want to place and label gateway icons on the map, so that the system knows the physical location of each data collector. | - User can drag a gateway icon from a toolbox onto the map.<br>- User can click a placed icon to enter its name/ID.<br>- The position and name of the gateway are saved successfully. | **Must-have** |
| **US-ADM-03** | As **Alex**, I want to use the mobile app to walk the floor and perform a signal strength calibration, so that the positioning algorithm is tuned to the specific environment. | - Mobile app has a "Calibration Mode" accessible only to Administrators.<br>- In this mode, the user's location is shown as a "blue dot."<br>- A "Record Signal" button sends current location and all visible beacon RSSI values to the server.<br>- A success message confirms the data was received. | **Must-have** |
| **US-ADM-04** | As **Alex**, I want to add new asset tags one by one via a simple web form, so I can quickly register new equipment. | - The form contains fields for Tag ID and Name.<br>- A success message is shown upon successful creation.<br>- An error message is shown if the Tag ID already exists.<br>- Form fields cannot be submitted if empty. | **Should-have** |
| **US-ADM-05** | As **Alex**, I want to bulk-import a list of asset tags from a CSV file, so that I can efficiently set up a new site with hundreds of assets. | - A sample CSV template is available for download.<br>- The system successfully imports a correctly formatted CSV.<br>- The system rejects a CSV with incorrect headers.<br>- If a file contains a mix of valid and invalid rows (e.g., duplicate IDs), the valid rows are imported, and a report of the failed rows is provided. | **Must-have** |

#### **Activity 2: Daily Operations Monitoring (Carlos)**

*As Carlos, I need a high-level overview to quickly assess the current state of my operations.*

| ID | User Story | Confirmation (Acceptance Criteria) | Priority |
| :--- | :--- | :--- | :--- |
| **US-GEN-01** | As **Carlos**, I want to see a high-level dashboard with key metrics (e.g., active assets, active alerts) when I first log in, so I can get a quick snapshot of the day. | - The dashboard is the default landing page after login.<br>- It correctly displays the number of "Active Assets" and "Active Alerts."<br>- The data on the dashboard refreshes automatically at a set interval (e.g., every 5 minutes). | **Must-have** |
| **US-GEN-02** | As **Carlos**, I want to see all my assets moving in real-time on a map, so I can understand the current operational flow. | - Asset icons are displayed on the correct floor plan.<br>- The position of the icons updates automatically without a page refresh.<br>- The update latency is within the 5-second NFR. | **Must-have** |
| **US-GEN-03** | As **Carlos**, I want to filter the map view by asset type (e.g., "waiter," "security cart"), so I can focus on a specific group without visual clutter. | - A filter control (e.g., dropdown) is available on the map page.<br>- Selecting an asset type (e.g., "waiter") hides all other asset types.<br>- Selecting "All" or clearing the filter shows all assets again. | **Should-have** |
| **US-GEN-04** | As **Carlos**, I want to receive an in-app and email alert when a high-value asset leaves a designated "safe zone," so I can prevent potential theft or loss. | - **Given** a "safe zone" geofence is configured for a "high-value" asset.<br>- **When** the asset's location is detected outside the zone.<br>- **Then** an alert appears in the UI's notification center within 1 minute.<br>- **And** an email with alert details is sent to the user's registered address. | **Must-have** |

#### **Activity 3: Deep-Dive Analysis (Carlos)**

*As Carlos, I need to investigate patterns and specific incidents to find opportunities for improvement.*

| ID | User Story | Confirmation (Acceptance Criteria) | Priority |
| :--- | :--- | :--- | :--- |
| **US-ANL-01** | As **Carlos**, I want to view the historical trajectory of a single asset on the map (e.g., "Table 5," "Restroom Entrance," "Loading Bay 2"), so I can understand its exact path during a specific time period. | - User can select a single asset.<br>- User can select a start and end date/time.<br>- A continuous line is drawn on the map representing the asset's path.<br>- The trajectory loads in an acceptable time (e.g., under 10 seconds for a 24-hour period). | **Must-have (Highest Priority Feature)** |
| **US-ANL-02** | As **Carlos**, I want to define specific points of interest (POIs) on the map. | - A "draw POI" tool is available in the UI.<br>- User can draw a polygon on the map and give it a name.<br>- The created POI is saved and can be selected in the reporting tools. | **Must-have** |
| **US-ANL-03** | As **Carlos**, I want to generate a report for an asset that shows the **number of visits** to a list of pre-defined POIs, so I can verify that required tasks were completed (e.g., janitor visiting restrooms). | - User can select an asset, a time range, and one or more POIs.<br>- The report generates a table with columns: "POI Name" and "Number of Visits."<br>- The visit count is accurate based on the asset's historical location data. | **Must-have** |
| **US-ANL-04** | As **Carlos**, I want to see a heatmap of the entire floor, so I can identify high-traffic areas and potential bottlenecks. | - User can select a time range for the heatmap data.<br>- A colored overlay is correctly rendered on the map (e.g., red for high traffic, blue for low).<br>- The heatmap can be toggled on and off. | **Should-have** |

#### **Activity 4: On-the-Go Location & Navigation (Mobile App)**

*As a user on the floor, I need to find assets quickly and calibrate the system effectively.*

| ID | User Story | Confirmation (Acceptance Criteria) | Priority |
| :--- | :--- | :--- | :--- |
| **US-MOB-01** | As **Carlos**, I want to search for an asset on my mobile app and see its location as a pin on the map, so I can find it quickly. | - The app has a search bar that autocompletes asset names.<br>- Selecting an asset from the search results centers the map on its last known location.<br>- The asset is clearly highlighted with a pin or icon. | **Must-have** |
| **US-MOB-02** | As **Carlos**, I want to see my own location as a "blue dot" on the map and get the shortest path to a target asset, so I can navigate to it efficiently. | - The app correctly displays the user's current location on the map.<br>- After selecting a target asset, a "Navigate" button is available.<br>- Tapping the button draws a line on the map representing the shortest walkable path. | **Must-have** |
| **US-MOB-03** | As **Alex**, I want to see my own location as a "blue dot" while in calibration mode, so I can accurately map signal strengths at known locations. | - When "Calibration Mode" is active, the user's location is accurately displayed on the map.<br>- The "blue dot" updates as the user moves through the facility. | **Must-have** |
