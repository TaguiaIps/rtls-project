## Context

The current RTLS Analytics Platform web interface relies on a standard SaaS-style layout with 1px solid borders for sectioning and rounded containers. This implementation is inconsistent with the "Industrial Command Deck" vision which prioritizes structural authority through depth and tonal layering. Currently, styles are centralized in `index.css` but lack a formal token system for the desired "Deep Void" palette.

## Goals / Non-Goals

**Goals:**
- Implement a centralized token system (CSS Variables) for the "Deep Void" palette.
- Refactor the global `dashboard-shell` to support the "Command Rail" (narrow sidebar) and "Telemetry Canvas" (expansive main area).
- Replace all structural borders with background color shifts (`surface` to `surface-container`).
- Standardize typography tokens for `Space Grotesk` and `Inter`.
- Create a set of "Industrial Utilities" for glassmorphism and rigid geometry.

**Non-Goals:**
- Modifying the underlying business logic or API contracts.
- Updating the mobile app styling (this change is scoped to the Web Frontend).
- Complete redesign of the Admin settings pages (focus is on the Operations/Monitoring shell).

## Decisions

- **Token-Driven Tonal Hierarchy**: We will use a semantic naming convention for CSS variables (e.g., `--surface-base`, `--surface-container-low`, `--surface-accent`) rather than raw hex codes.
  - *Rationale*: Ensures consistency across new modules and simplifies maintenance.
- **CSS Grid for Intentional Asymmetry**: The main shell will use `grid-template-columns: var(--rail-width) 1fr` to enforce the high-density rail layout.
  - *Rationale*: Grid provides the necessary rigidity for the "Industrial" look compared to Flexbox.
- **"Milled" Panel Effect**: Boundaries between functional areas will be achieved by nesting a container with a darker background (`surface-container-lowest`) within a lighter surface, creating a recessed look without borders.
  - *Rationale*: Aligns with the "No-Line" rule while maintaining clear information architecture.
- **Glassmorphism for Map HUDs**: Floating modules on the Live Map will use `rgba` backgrounds with `backdrop-filter: blur(24px)`.
  - *Rationale*: Creates the "Physicality of Light" effect where UI feels integrated into a digital glass pane.

## Risks / Trade-offs

- **[Risk]** Visual regressions in existing monitoring routes (Alerts, Analytics).
  - **Mitigation**: Implement the change as a "Global Theme Overlay" first and refactor specific layouts incrementally within the same PR.
- **[Risk]** High cognitive load from increased data density.
  - **Mitigation**: Use `Space Grotesk` sparingly for key headers and ensure adequate gutter spacing (`0.3rem` per the design spec) to let data "breathe."
- **[Risk]** Performance of `backdrop-filter` on lower-end machines.
  - **Mitigation**: Provide a fallback `solid` background for browsers that do not support or struggle with backdrop filters.
