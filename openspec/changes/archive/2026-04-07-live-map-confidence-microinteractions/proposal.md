## Why

The current Live Map experience feels static and lacks "honest" data visualization regarding asset confidence. Asset markers currently "teleport" between positions, which is jarring and reduces the sense of real-time fluidity. Additionally, the map needs more robust filtering to allow operators like Carlos Mendes to slice and dice active telemetry by confidence and status simultaneously.

## What Changes

- **Pulsing Glassmorphism**: Implement a technical pulsing effect using glassmorphism for low-confidence assets instead of static indicators.
- **Fluid Motion (Micro-interactions)**: Add subtle (200-300ms) CSS transitions for asset position updates to eliminate jarring "teleportation" of icons.
- **Faceted Search Refactor**: Refactor the map's filter system into a faceted search that allows combining asset type, status, and confidence level filters.
- **Selection Glow**: Enhance the selected asset state with a signature "Inner Glow" box-shadow to match the backlit physical button aesthetic of the Command Deck.

## Capabilities

### New Capabilities
- `live-map-microinteractions`: Standardized utility classes and components for pulsing confidence states and fluid motion.

### Modified Capabilities
- `live-map-workspace`: Update the Live Map requirements to enforce faceted filtering and fluid coordinate interpolation.

## Impact

- **Web Frontend**: Update to `OperationsShell.tsx` (MapCanvas integration) and `index.css`.
- **User Experience**: Higher trust in "honest" data visualization; reduced visual fatigue through fluid transitions.
- **Performance**: Transitions must be optimized to ensure high data density doesn't cause frame-rate drops.
