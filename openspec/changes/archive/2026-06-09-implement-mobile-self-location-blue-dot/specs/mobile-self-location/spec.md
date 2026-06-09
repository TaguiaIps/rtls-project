## ADDED Requirements

### Requirement: Live self-location streaming on mobile
The RTLS Analytics Platform SHALL support streaming real-time self-location updates to the mobile application for administrative and operational use.

#### Scenario: Mobile app starts self-location stream
- **WHEN** an authorized Administrator enables self-location on a selected floor
- **THEN** the mobile app SHALL establish a high-frequency stream (e.g., via WebSocket) to receive current position updates for the mobile device's associated tag

#### Scenario: Mobile app receives a location update
- **WHEN** a new location update is received via the self-location stream
- **THEN** the app SHALL update the on-screen blue dot position with minimal latency

### Requirement: Confidence-aware blue-dot visualization
The mobile application SHALL visually represent the precision and confidence of the current self-location update to inform the operator of positioning quality.

#### Scenario: High-confidence location update
- **WHEN** a location update is received with high precision (e.g., < 1m) and high confidence score
- **THEN** the mobile app SHALL render a solid blue dot with a small, sharp precision radius

#### Scenario: Low-confidence or degraded location update
- **WHEN** a location update is received with low confidence or high precision error
- **THEN** the mobile app SHALL render the blue dot with a larger, semi-transparent precision circle or a "degraded" visual state

### Requirement: Client-side jitter smoothing and filtering
The mobile application SHALL apply client-side smoothing or filtering to the self-location stream to ensure a fluid and stable blue-dot movement on the map.

#### Scenario: High-frequency jitter in location stream
- **WHEN** the self-location stream contains high-frequency jitter or minor position oscillations
- **THEN** the mobile app SHALL apply a smoothing filter (e.g., Kalman filter or moving average) to render a stable movement path

### Requirement: Reconnect and stream health management
The mobile application SHALL monitor the health of the self-location stream and attempt to reconnect automatically during intermittent connectivity.

#### Scenario: Self-location stream disconnects
- **WHEN** the WebSocket or streaming connection is lost during an active session
- **THEN** the mobile app SHALL show a "Reconnecting" indicator and attempt to re-establish the stream without requiring a full workflow reset
