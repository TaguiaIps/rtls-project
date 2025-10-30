# **Comparison of Requirement Specifications**

This table maps the requirements from the original `rf.md` and `rnf.md` files to the newly defined requirements in the `Requirements Document`.

Data analized based on documents at date 30 of october, 2025.

| Original ID | Original Description | New ID(s) | Status in New Document | Notes/Refinement |
| :--- | :--- | :--- | :--- | :--- |
| **Functional - General** |
| RF001, RF002 | Track and display assets in real-time | FR-VIS-002 | **Covered** | The core real-time tracking feature is central to the new specification. |
| RF003 | Send automatic location notifications | FR-NOT-001, 002, 003, 004 | **Covered & Refined** | The vague "location notifications" were specified as geofence-based alerts with multiple delivery channels. |
| RF004 | Manage beacon registration/config | FR-ADM-003, FR-ADM-004 | **Covered & Refined** | This was refined into specific requirements for single and bulk CSV registration. |
| RF005 | Secure user authentication | FR-SEC-001 | **Covered** | Secure login is a baseline requirement. |
| RF006 | Role-Based Access Control (RBAC) | FR-SEC-002 | **Covered & Refined** | The general RBAC requirement was refined into two specific roles: Administrator and General User. |
| RF009 | Display asset location history | FR-ANL-004 | **Covered** | This is covered by the "trajectory" feature. |
| RF020 | Develop analytics dashboard | FR-ANL-002, 003, 004, 005 | **Covered & Refined** | The generic "dashboard" was specified as concrete analytics features: heatmaps, dwell time, trajectories, and geofence reports. |
| **Functional - Advanced Navigation (Original Scope)** |
| RF011, RF027 | Real-time indoor navigation for users | US-MOB-02 | **Partially Covered** | The scope was narrowed from general public navigation to only navigating *towards a target asset* for staff. |
| RF012, RF028 | Display maps with custom POIs | FR-ANL-001 | **Partially Covered** | POIs are covered, but only in the context of analytics (for visit counts), not for public navigation. |
| RF013, RF029 | Search for locations with shortest route | US-MOB-02 | **Partially Covered** | Covered only for finding the shortest path to an *asset*, not a general location like "Restroom." |
| RF014, RF030 | Implement 2D/3D interactive maps | FR-VIS-001 | **Partially Covered** | 2D maps are covered. 3D maps were scoped out as they were not part of the refined project goals. |
| RF016, RF032 | Accessibility for reduced mobility | | **Not Covered** | This feature is part of a public navigation system and was scoped out based on the focus on asset analytics. |
| RF017, RF034 | Share real-time location between users | | **Not Covered** | This social/collaboration feature was not included in the refined project goals. |
| RF018, RF036 | Access maps via QR Code | | **Not Covered** | This is a feature for public access, which was scoped out. |
| RF019, RF037 | Advanced search (autocomplete, voice) | FR-VIS-004 | **Partially Covered** | Basic search by name is covered. Autocomplete and voice search were scoped out for the initial build. |
| **Functional - Implementation Details (Moved to Design)** |
| RF007, RF008, RF039, RF040 | Structured logging | | **Not Covered** | This is a non-functional, architectural requirement. It was moved to the Software Design Document (ELK Stack) and is not a user-facing feature. |
| RF038 | Implement positioning algorithms | | **Not Covered** | This is an implementation detail, not a functional requirement. It is specified in the Software Design Document. |
| **Non-Functional** |
| RNF001 | Accuracy minimum: ±2 meters | | **Not Covered** | The new NFRs do not specify a minimum accuracy. This is a gap. |
| RNF002 | Max position update time: 5 seconds | NFR-PER-001 | **Covered** | This is directly covered. |
| RNF003 | Min beacon battery life: ≥2 years | | **Not Covered** | This is a hardware selection criterion, not a software requirement. It was addressed in the Technical Specification but removed from the software requirements. |
| RNF004 | Scalability: support up to 500 beacons | NFR-PER-002 | **Covered** | This is directly covered. |
| RNF004 (2) | Strong encryption (TLS v1.3) | NFR-SEC-001 | **Covered** | This is directly covered. |
| RNF005 | Encrypted data storage (AES-256) | NFR-SEC-002 | **Covered** | This is directly covered. |
| RNF006 | Multi-Factor Authentication (MFA) | | **Not Covered** | The new requirements specify secure login but did not include MFA. This is a gap. |
| RNF007 | Privacy by Design / Anonymization | | **Not Covered** | This high-level principle was not translated into a specific NFR in the new document. This is a gap. |
| RNF008 | Automated security testing | | **Not Covered** | This is a process requirement, not a system NFR. It was moved to the Testing Strategy in the Software Design Document. |
| RNF009 | Max incident notification time: 5 mins | US-GEN-04 | **Covered & Improved** | The new user story acceptance criteria specifies a notification time of "within 1 minute." |
| RNF010 | Secure backups, 30-day retention | NFR-REL-002, FR-ADM-005 | **Covered & Refined** | Covered by requirements for encrypted backups and a configurable retention policy. |

---

### **List of Requirements Not Covered in the New Specification**

The following requirements from the original `rf.md` and `rnf.md` files are not included in the new `Requirements Document`. This is primarily due to the **strategic decision to focus the project on asset tracking and operational analytics** rather than building a public-facing indoor navigation system.

#### **1. Advanced Public Navigation Features**

These features were part of a broader, public-facing navigation scope that was intentionally deferred to focus on the core goal of asset analytics.

* **RF011, RF027:** General indoor navigation with optimized routes for users.
* **RF014, RF030:** 3D Maps.
* **RF016, RF032:** Accessibility routes for users with reduced mobility.
* **RF017, RF034:** Real-time location sharing between users.
* **RF018, RF036:** Accessing maps via QR codes.
* **RF019, RF037:** Voice search and advanced autocomplete for locations.

#### **2. Specific Non-Functional Requirements**

These were either deemed out of scope for the initial build or are hardware/process-related.

* **RNF001 (Accuracy minimum: ±2 meters):** A specific accuracy target was not included in the new NFRs. This should be discussed and potentially added.
* **RNF003 (Min beacon battery life):** This is a hardware procurement requirement, not a software feature.
* **RNF006 (Multi-Factor Authentication - MFA):** The initial requirement for login is secure authentication, but MFA was not included in the refined scope.
* **RNF007 (Privacy by Design):** This high-level principle was not specified as a concrete requirement.

#### **3. Implementation & Process Details**

These items were re-categorized from requirements to design or process definitions, as they are not user-facing features.

* **RF007, RF008, RF039, RF040 (Logging):** Moved to the Software Design Document as an architectural choice (ELK Stack).
* **RF038 (Positioning Algorithms):** Moved to the Software Design Document as an implementation detail.
* **RNF008 (Automated Security Testing):** Moved to the Software Design Document as part of the Testing Strategy.
