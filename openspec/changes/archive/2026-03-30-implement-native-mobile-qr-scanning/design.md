## Context

The mobile commissioning baseline already loads protected admin context, resolves identifiers against the delivered registry, and stores local session summaries, but device intake still depends on pasted or externally scanned payloads. This change adds native camera scanning inside the existing Expo mobile workflow without changing backend contracts or the downstream calibration-session model.

The main constraints are:
- keep the current manual identifier path working for simulators and constrained devices
- avoid introducing backend changes for QR parsing
- fit within the existing Expo mobile stack and permission model

## Goals / Non-Goals

**Goals:**
- Add native camera-based QR scanning to the commissioning screen.
- Normalize supported QR payload formats before registry lookup.
- Handle camera permissions and scanning state explicitly inside the mobile UI.
- Preserve manual entry as a supported fallback path.

**Non-Goals:**
- Building the future calibration engine, radiomap generation, or backend calibration persistence.
- Adding vendor-specific provisioning or write-back flows for scanned devices.
- Changing registry APIs or introducing a new backend QR-resolution endpoint.

## Decisions

### Use `expo-camera` with `CameraView`
- Decision: Use Expo SDK 55's supported `expo-camera` package and render a camera panel inside the commissioning screen.
- Why: It fits the current Expo baseline, supports QR scanning directly, and avoids custom native work.
- Alternative considered: Add a dedicated navigation route or third-party scanner library. Rejected because the current mobile app has no navigation stack and a separate scanner dependency would add unnecessary complexity.

### Keep QR parsing in the commissioning helper layer
- Decision: Normalize QR payloads in `commissioning.ts` before registry lookup.
- Why: The app already centralizes identifier resolution there, so camera scans, pasted payloads, and external scanners can share one resolution path.
- Alternative considered: Parse payloads inline in the screen component. Rejected because it would duplicate logic and weaken testability.

### Preserve manual fallback behavior
- Decision: Keep the manual input field and external-scanner path even after camera support lands.
- Why: It preserves simulator testing and avoids blocking operators on permission or device hardware limitations.
- Alternative considered: Make camera scanning mandatory. Rejected because it would make local development and emulator validation harder without improving the registry contract.

### Use one-shot scan locking
- Decision: Pause scanning after the first QR read until the operator explicitly re-arms scanning.
- Why: It prevents repeated scans from thrashing state while the user reviews the resolved target.
- Alternative considered: Stream every scan result continuously. Rejected because the commissioning workflow is single-target and benefits from deliberate confirmation.

## Risks / Trade-offs

- [Camera permission denied] → Keep manual entry visible and provide an explicit fallback path.
- [Different QR payload shapes across vendors] → Normalize plain identifiers, JSON payloads, and URL query payloads first; treat unsupported shapes as unknown identifiers rather than adding speculative parsing.
- [Camera support varies by device or simulator] → Keep the scanner panel optional and preserve external-scanner or pasted input.
- [Extra native dependency increases mobile maintenance] → Use Expo's first-party camera package and document the plugin configuration in the Expo app config.
