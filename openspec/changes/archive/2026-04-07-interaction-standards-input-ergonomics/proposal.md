## Why

The current input ergonomics in the RTLS Analytics Platform follow generic SaaS patterns that lack the precision and authority required for a mission-critical operations console. By implementing advanced interaction standards, we can reduce data entry errors (especially for technical identifiers like MAC addresses and Tag IDs), improve accessibility, and provide a more professional, high-trust experience for Administrators and Operations Managers.

## What Changes

- **Command-Style Inputs**: Standardize all text inputs to use a "Command" aesthetic (bottom-border only) with a high-contrast focus state in Telemetry Cyan.
- **Password Visibility Standard**: Implement eye-icon toggles for all password and sensitive configuration fields.
- **Advanced Validation Logic**: Move away from generic error messages toward real-time, human-readable validation for technical IDs (e.g., preventing duplicate Gateway IDs before form submission).
- **Technical Input Masks**: Apply input masks for MAC addresses and IP configurations in Admin workflows to enforce correct formatting.
- **Affective Feedback Labels**: Standardize the structure of form feedback to include well-known icons for Info, Warning, and Error states.

## Capabilities

### New Capabilities
- `form-ergonomics-engine`: A standardized set of React components and hooks for handling "Command" inputs, visibility toggles, and technical masks.

### Modified Capabilities
- `user-authentication`: Update the login and credential management flows to support password visibility toggles and refined ergonomics.
- `site-and-floor-management`: Update spatial administration forms to use input masks for gateway hardware identifiers.
- `asset-tag-registry`: Implement real-time identifier validation for new asset tags.

## Impact

- **Web Frontend**: Creation of a new shared component library for form elements. Refactor of existing forms in the Admin and Login workspaces.
- **User Experience**: Faster, more accurate data entry for technical configuration. Reduced anxiety during sensitive credential management.
- **Accessibility**: Improved focus visibility and clearer semantic error reporting.
