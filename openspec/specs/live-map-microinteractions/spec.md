# live-map-microinteractions Specification

## Purpose
Standardizes visual feedback for asset confidence and movement fluidity to ensure "honest" and high-fidelity real-time monitoring.

## Requirements

### Requirement: Technical Presence Pulsing for Low Confidence
The RTLS Analytics Platform SHALL visualize low-confidence asset estimates using a pulsing glassmorphism effect to communicate uncertainty honestly.

#### Scenario: Low-confidence asset is rendered on map
- **WHEN** an asset marker is rendered with `low` confidence
- **THEN** the map SHALL render a circular glassmorphism element behind the icon that pulses between 0.4 and 0.8 opacity with a 2s duration

### Requirement: Fluid Coordinate Transitions
The RTLS Analytics Platform SHALL ensure asset markers move fluidly between estimated positions to reduce visual jarring.

#### Scenario: Asset position update is received
- **WHEN** a new coordinate update is applied to a rendered asset marker
- **THEN** the marker SHALL transition to the new position using a 300ms ease-out duration instead of immediate teleportation
