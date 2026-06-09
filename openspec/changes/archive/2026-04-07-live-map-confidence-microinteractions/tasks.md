## 1. Micro-interactions & Visual Effects

- [x] 1.1 Implement `.presence-pulse` CSS keyframes and glassmorphism utility in `apps/web/src/index.css`.
- [x] 1.2 Update asset marker containers in `MapCanvas` to use `transition: left 0.3s, top 0.3s`.
- [x] 1.3 Apply the technical pulse effect to markers with `low` confidence in the Live Map.
- [x] 1.4 Add \"Selection Glow\" styles to `index.css` and apply to the active asset in the map view.

## 2. Live Map Faceted Search

- [x] 2.1 Refactor the Live Map filter state in `OperationsShell.tsx` to support faceted multi-select.
- [x] 2.2 Update the `live-map-sidebar` UI to render faceted filter groups (Category, Confidence).
- [x] 2.3 Implement the combined intersection logic for active facets in the live locations result set.

## 3. Verification & Documentation

- [x] 3.1 Verify that markers move fluidly without "jumping" during real-time updates.
- [x] 3.2 Audit the pulsing visibility across dark and light areas of mapped floor plans.
- [x] 3.3 Update `docs/ux-design.md` to document the "Presence Pulse" and position transition standards.
