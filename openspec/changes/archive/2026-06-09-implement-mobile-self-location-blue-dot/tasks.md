## 1. Mobile Self-Location Infrastructure

- [x] 1.1 Implement WebSocket client in the mobile app to subscribe to `/ws/locations`
- [x] 1.2 Add support for filtering by `asset_tag_id` in the WebSocket subscription
- [x] 1.3 Implement a Kalman filter utility for client-side position smoothing
- [x] 1.4 Add reconnect logic and connection health monitoring for the location stream

## 2. Blue-Dot Visualization

- [x] 2.1 Create a `SelfLocationMarker` component with a dynamic precision radius
- [x] 2.2 Implement visual states for different confidence levels (High, Medium, Low)
- [x] 2.3 Add smoothing to the `SelfLocationMarker` updates to prevent jitter
- [x] 2.4 Integrate the `SelfLocationMarker` into the calibration map view

## 3. Calibration Workflow Integration

- [x] 3.1 Update the calibration setup view to allow selection of the "carry-on" asset tag
- [x] 3.2 Implement a toggle for "Live Tracking" vs "Manual Capture" mode in the walkthrough
- [x] 3.3 Automate signal sample capture based on the current live blue-dot position
- [x] 3.4 Ensure manual tap-driven fallback works correctly when live tracking is disabled or lost

## 4. Verification and Testing

- [x] 4.1 Add mobile unit tests for the Kalman filter and jitter smoothing
- [x] 4.2 Create integration tests for the WebSocket connection and message handling
- [x] 4.3 Verify the blue-dot rendering with mock location updates of varying precision
- [x] 4.4 Update `docs/spatial-admin-workflow.md` with instructions for live blue-dot calibration
