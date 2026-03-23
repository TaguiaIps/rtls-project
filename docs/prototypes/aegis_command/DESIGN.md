# Design System Specification: Industrial Command Deck

## 1. Overview & Creative North Star
**The Creative North Star: "The Sentinel Interface"**

This design system is engineered for high-stakes, mission-critical environments where split-second decisions rely on data clarity and structural authority. We are moving away from the "playful SaaS" aesthetic and toward a sophisticated, industrial-grade console. The interface does not merely display information; it monitors, alerts, and commands.

To break the "template" look, we utilize **Intentional Asymmetry**. Dashboards should not be perfectly mirrored grids; instead, they should prioritize primary telemetry through expansive "Hero" map modules offset by dense, vertically-stacked data sidebars. We utilize layered depth and tonal shifts to create a "Physicality of Light," where the UI feels like a high-end hardware console integrated into a digital glass pane.

---

### 2. Colors & Surface Architecture
The palette is rooted in the "Deep Void" spectrum—surfaces that recede to let active telemetry pop with surgical precision.

#### The "No-Line" Rule
Traditional 1px solid borders for sectioning are strictly prohibited for structural layout. Boundaries must be defined through **Background Color Shifts**. For example, a `surface-container-low` panel should sit on a `surface` background to create a "milled" effect, rather than being outlined.

#### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Nesting is the key to information density:
*   **Base Layer (`surface` / `#0e131e`):** The primary application canvas.
*   **Primary Containers (`surface-container` / `#1b1f2b`):** Major functional areas (Sidebars, Map overlays).
*   **Elevated Modules (`surface-container-highest` / `#303541`):** Active interactive elements or high-priority readouts.

#### The "Glass & Gradient" Rule
To elevate the "Sentinal" vibe, floating HUD elements must utilize **Glassmorphism**. Use `surface-container-low` at 60% opacity with a `24px` backdrop blur. 
*   **Signature Textures:** For primary action states, apply a subtle linear gradient from `primary` (#dbfcff) to `primary_container` (#00f0ff) at a 135-degree angle. This adds a "lithographic" soul to the buttons that flat hex codes cannot achieve.

---

### 3. Typography: The Authority of Information
The type system balances technical precision with rapid scanning.

*   **Display & Headlines (`Space Grotesk`):** Chosen for its wide aperture and "technical-brutalist" character. Use `headline-lg` for terminal headers and `display-sm` for massive, single-source metrics (e.g., "Active Units: 42").
*   **Body & Labels (`Inter` / `DM Sans` equivalents):** Used for all data-dense grids and system logs. The `label-md` and `label-sm` tokens are the workhorses of this system, often set in **All Caps with 0.05em letter spacing** for a "readout" aesthetic.

**Hierarchy Strategy:** Use `primary_container` (Cyan) for active labels and `on_surface_variant` (muted teal-grey) for secondary metadata to ensure the eye hits the critical "Command" values first.

---

### 4. Elevation & Depth: Tonal Layering
We do not use shadows to represent "elevation" in the traditional sense; we use them to represent **Active Focus**.

*   **The Layering Principle:** Depth is achieved by stacking `surface-container-lowest` (#090e19) cards on top of `surface-container-low` (#171b27) backgrounds. This creates a recessed, "etched" look characteristic of premium aerospace hardware.
*   **Ambient Shadows:** For floating modals only. Use a 40px blur, 0% offset, and 8% opacity. The shadow color must be tinted with the `surface_tint` (#00dbe9) to mimic the glow of a CRT or high-end LED panel.
*   **The "Ghost Border" Fallback:** Where extreme density requires separation, use a "Ghost Border": the `outline-variant` (#3b494b) at 15% opacity. This provides a "wireframe" hint without cluttering the visual field.

---

### 5. Components: The Industrial Toolkit

#### Buttons (Tactile Command)
*   **Primary:** Solid `primary_container` (#00f0ff) with `on_primary` (#00363a) text. 8px rounded corners (`xl`). Use the Signature Gradient on hover.
*   **Secondary:** Ghost style. `outline` token at 20% opacity. On hover, the border becomes `secondary_fixed_dim`.
*   **States:** Interactive states must use a 1px "inner glow" (box-shadow: inset) of the accent color to simulate a physical backlit button.

#### Technical Chips
*   Used for status tags (e.g., "STABLE," "EN ROUTE").
*   **Geometry:** 2px radius (`sm`) for a more rigid, industrial look.
*   **Coloring:** Backgrounds at 10% opacity of the status color (Amber for Warning, Red for Critical), with 100% opacity text.

#### Input Fields
*   **Surface:** `surface_container_lowest` (#090e19).
*   **Bottom Border Only:** To maintain the "Command Deck" feel, inputs use a 2px bottom border of `outline_variant` that transitions to `primary` on focus.

#### Data Cards & Lists
*   **The Divider Rule:** Strictly forbid horizontal lines between list items. Use 1.5 spacing (`0.3rem`) as a gutter and alternate background subtle shifts (`surface-container-low` vs `surface-container-high`) for zebra-striping if necessary.

#### The "Telemetry Gauge" (Custom Component)
*   A custom component for this system: A 2px thin arc using `primary_fixed` with a `backdrop-blur` background to show sensor levels. It embodies the "Data-Dense but Readable" requirement.

---

### 6. Do's and Don'ts

#### Do
*   **DO** use `secondary` (#adc6ff) for "Actionable Info" and `primary` for "System Status."
*   **DO** utilize the `Spacing Scale 10+` for layout margins to let complex data "breathe."
*   **DO** use 1px "Technical Iconography"—icons should be monoline and match the weight of the `label-sm` font.

#### Don't
*   **DON'T** use purple, pink, or rounded "bubble" buttons. This is an operations deck, not a social app.
*   **DON'T** use 100% white (#FFFFFF). Use `on_surface` (#dee2f2) to reduce eye strain in dark control rooms.
*   **DON'T** use standard shadows. If a component feels "flat," increase the background contrast between the container and the surface, rather than adding a drop shadow.