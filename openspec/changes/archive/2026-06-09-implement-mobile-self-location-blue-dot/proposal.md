## Why

The current mobile calibration workflow relies on manual tap-driven checkpoints, which can be prone to human error and are time-consuming for large sites. By upgrading to live self-location "blue-dot" tracking, we can automate the positioning of signal samples during calibration sessions, significantly increasing the efficiency and accuracy of radiomap generation.

## What Changes

- **Live Blue-Dot Tracking**: Integrate real-time location streaming into the mobile calibration interface.
- **Continuous Sample Mapping**: Automatically associate signal samples with the current blue-dot position.
- **Confidence-Aware Visualization**: Render the blue dot with visual feedback indicating current positioning confidence and precision.
- **Fallback Manual Mode**: Retain tap-driven checkpoints as a fallback for areas with poor initial coverage or connectivity.
- **Smoothing and Jitter Control**: Implement client-side filtering to ensure a stable blue-dot movement during the calibration walk.
- **Reconnect Logic**: Add robust handling for intermittent mobile connectivity during live streams.

## Capabilities

### New Capabilities
- `mobile-self-location`: Streaming and rendering real-time self-location on the mobile map during administrative tasks.

### Modified Capabilities
- `mobile-commissioning-and-calibration`: Update the guided calibration walkthrough to support live blue-dot tracking as the primary input modality.

## Impact

- **Mobile App**: New React Native components for live location streaming and confidence visualization; updated state management for calibration sessions.
- **Backend (API/Worker)**: Potential updates to WebSocket/streaming endpoints to support targeted mobile self-location feeds.
- **UX**: Significant change to the calibration walkthrough; requires updates to the `docs/ux-design.md` or related prototypes.
- **Performance**: Increased battery and data usage on mobile devices due to continuous streaming and high-frequency UI updates.
