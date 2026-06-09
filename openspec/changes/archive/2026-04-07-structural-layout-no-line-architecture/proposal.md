## Why

The current web interface utilizes a "Standard SaaS" aesthetic characterized by 1px borders, generous whitespace, and rounded shapes. While functional, this style lacks the structural authority and data density required for a mission-critical RTLS Analytics Platform. To increase user confidence and provide a professional, industrial-grade experience, we need to transition to the "Industrial Command Deck" design system, which replaces visual clutter (borders) with functional depth (tonal layering).

## What Changes

- **Structural Architecture**: Move away from 1px solid borders for sectioning. Layout boundaries will now be defined by background color shifts (Tonal Layering).
- **Geometry & Depth**: Replace 24px/16px border-radius with a more rigid 8px (xl) for containers and 2px (sm) for status elements.
- **Navigation Refactor**: The primary navigation sidebar will be transformed into a high-density "Command Rail" featuring monoline iconography and technical-brutalist labels.
- **Typography Standard**: Formally adopt `Space Grotesk` for headlines/display metrics and `Inter` for all data-dense grids.
- **Surface Hierarchy**: Implement the "Deep Void" palette across the web shell, utilizing `surface`, `surface-container`, and `surface-container-highest` tokens.

## Capabilities

### New Capabilities
- `web-theme-engine`: Core infrastructure for CSS variables (Deep Void palette), typography tokens, and the "No-Line" structural utility classes.

### Modified Capabilities
- `web-operations-shell`: Update the shell requirement to enforce the high-density Command Rail layout and tonal surface hierarchy.
- `live-map-workspace`: Update the workspace to support glassmorphism HUD overlays and intentional asymmetry in layout.

## Impact

- **Web Frontend**: Significant refactor of `apps/web/src/index.css` and shared component styles.
- **UX Documentation**: Updates to `docs/ux-design.md` to reflect the finalized Industrial Command Deck implementation details.
- **Developer Experience**: New standardized component library for building data-dense operational views without manual border styling.
