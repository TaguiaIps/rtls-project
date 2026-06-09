## Context

The current Live Map implementation in `OperationsShell.tsx` renders asset markers as immediate absolute-positioned elements. When a new WebSocket update arrives, the icon jumps to the new coordinate. Confidence is visualized via color, but lacks "presence." Filtering is currently limited to one category at a time via top-bar dropdowns.

## Goals / Non-Goals

**Goals:**
- Enable hardware-accelerated fluid motion for asset markers.
- Visualize low-confidence states using a "Presence Pulse" (glassmorphism circle).
- Implement a Faceted Search sidebar for the Live Map.
- Standardize "Selection Glow" for focused assets.

**Non-Goals:**
- Rewriting the MapCanvas SVG rendering logic (we will enhance existing markers).
- Implementing trajectory tails (this is scoped to Analytics).

## Decisions

- **CSS Coordinate Transitions**: Use `transition: left 0.3s ease-out, top 0.3s ease-out` on marker containers.
  - *Rationale*: Cleanest implementation for fluid motion without overhead of a physics library.
- **Glassmorphism Pulse Utility**: Use a circular SVG element with a `backdrop-filter: blur(4px)` and a `@keyframes pulse-industrial` animation.
  - *Rationale*: Communicates "honest" uncertainty by visually blurring the background beneath the estimated position.
- **Facet-State Context**: Extend the shell search parameters to support multi-select arrays for `categories`, `confidence`, and `status`.
  - *Rationale*: Allows operators to perform complex queries like "Show all Staff with Low Confidence."

## Risks / Trade-offs

- **[Risk]** Overlapping transitions during high-frequency updates.
  - **Mitigation**: Use `ease-out` timing to ensure the latest position is reached quickly if a new update arrives mid-transition.
- **[Risk]** Visual noise from too many pulsing elements.
  - **Mitigation**: Limit the pulsing effect to assets with `low` confidence only; `medium` and `high` remain static.
