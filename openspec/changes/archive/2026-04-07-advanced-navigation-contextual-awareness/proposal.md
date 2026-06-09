## Why

As the RTLS Analytics Platform grows in complexity, users (Alex and Carlos) need a clearer mental map of their current location within the hierarchy of sites, floors, and workspaces. The current navigation lacks deep contextual awareness, which can lead to disorientation during multi-step analysis or commissioning workflows. This change implements standard interaction patterns like breadcrumbs and persistent live-feed status to ensure users remain in control and informed.

## What Changes

- **Breadcrumb Navigation**: Introduce a dynamic breadcrumb trail in the Top Bar showing `Site > Floor > Workspace` context.
- **Command Rail Refinement**: Enhance the high-density navigation sidebar with monoline iconography and optimized all-caps labeling for rapid scanning.
- **Contextual Heartbeat**: Implement a visible "Live Feed" status treatment in the sticky header that reflects the real-time health of the telemetry socket.
- **Sticky Layout Optimization**: Refine the Top Bar to remain compact (under 15% screen height) while preserving essential contextual controls.

## Capabilities

### New Capabilities
- `contextual-breadcrumb-engine`: System for tracking and rendering the Site > Floor > Workspace hierarchy across all monitoring routes.

### Modified Capabilities
- `web-operations-shell`: Update requirements to enforce contextual breadcrumbs and the integrated live-feed heartbeat status.

## Impact

- **Web Frontend**: Modification of `OperationsShell.tsx` and related CSS to accommodate the new Top Bar architecture.
- **User Experience**: Reduced time-to-orientation when deep-linking into specific floors or assets.
- **System Trust**: Increased visibility into telemetry health through the persistent heartbeat indicator.
