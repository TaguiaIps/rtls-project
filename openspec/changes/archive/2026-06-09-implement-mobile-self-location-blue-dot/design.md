## Context

The mobile calibration workflow currently requires manual intervention (taps) to mark the operator's position during a walk. This is inefficient and error-prone. We want to leverage the platform's real-time positioning capabilities to provide a "live blue dot" for the operator, automating position capture and improving the overall quality of environmental calibration.

## Goals / Non-Goals

**Goals:**
- Enable real-time self-location tracking in the mobile calibration view.
- Provide visual feedback on positioning confidence and precision.
- Implement robust smoothing to handle positioning jitter on the mobile map.
- Support manual fallback for unreliable positioning environments.

**Non-Goals:**
- Implementing a new positioning algorithm (we leverage existing Premium/Economic tier estimators).
- Supporting self-location for general users (focus is on Administrator calibration tasks).

## Decisions

### 1. Leverage Existing Live Location WebSockets
Instead of building a dedicated calibration-only stream, we will reuse the `/ws/locations` WebSocket endpoint.
- **Rationale**: Reduces backend complexity and leverages existing authentication and filtering logic.
- **Implementation**: The mobile app will subscribe to its own `asset_tag_id` when entering calibration mode.

### 2. Client-Side Smoothing with Kalman Filter
Mobile rendering of raw location updates can appear "jumpy" due to latency and high-frequency positioning updates.
- **Decision**: Implement a client-side Kalman filter in the React Native app.
- **Rationale**: Provides a smoother, more intuitive movement experience for the operator without increasing backend load.

### 3. Dynamic Precision Radius
The blue dot will be accompanied by a semi-transparent "precision circle".
- **Decision**: Map the `precision_meters` field from the location update to the circle's radius.
- **Rationale**: Communicates the trustworthiness of the current position to the operator in real-time.

### 4. Hybrid Capture Mode (Live + Manual)
- **Decision**: The mobile app will offer a toggle between "Live Tracking" and "Manual Capture".
- **Rationale**: Ensures the calibration process can continue even in areas with zero initial coverage or during network degradation.

## Risks / Trade-offs

- **[Risk] WebSocket Latency** → **Mitigation**: Optimize the `live_location_stream_poll_interval_ms` on the backend and ensure the mobile app uses an efficient high-frequency update rate.
- **[Risk] Positioning Jitter** → **Mitigation**: Use a configurable Kalman filter and implement a minimum movement threshold before updating the UI position.
- **[Risk] Battery Drain** → **Mitigation**: Automatically close the WebSocket stream when calibration mode is exited or the app moves to the background.

## Migration Plan

1. **Backend**: No major changes needed if `/ws/locations` is used, but ensure `asset_tag_id` filtering is robust.
2. **Mobile**: Implement the Kalman filter and precision radius rendering in the MapView.
3. **Integration**: Update the `Mobile Commissioning` workflow to include the "Live Tracking" mode.

## Open Questions

- Should the mobile device's associated `AssetTag` be pre-configured, or should the operator select which tag they are carrying at the start of calibration? (Likely pre-configured or selected during "Calibration Setup" step).
