## Context

The current forms in the RTLS Analytics Platform are built with standard HTML input styles and manual validation logic. This has led to inconsistent error reporting and a "Standard SaaS" look that conflicts with the high-trust Industrial Command Deck aesthetic. We need a unified `form-ergonomics-engine` to centralize these interaction standards.

## Goals / Non-Goals

**Goals:**
- Create a reusable `CommandInput` component that implements the bottom-border-only aesthetic.
- Implement a `PasswordInput` component with a built-in visibility toggle.
- Standardize real-time validation hooks for technical identifiers (MAC, IP, Tag ID).
- Refactor the Login and Admin Spatial forms to use these new components.
- Implement a standardized `FormFeedback` component with semantic icons (Lucide).

**Non-Goals:**
- Migrating to a third-party form library (e.g., Formik or React Hook Form) unless strictly necessary for complexity (we will stick to controlled components for now).
- Changing backend validation logic (this is a frontend ergonomics enhancement).

## Decisions

- **CSS-Only Aesthetics**: The "Command" look will be achieved via CSS classes in `index.css`, targeting `border-bottom` and using a transition for the focus state.
  - *Rationale*: Minimal overhead and maximum consistency across the app.
- **Lucide Icon Integration**: Use `Eye` and `EyeOff` icons for password visibility, and `AlertCircle`, `CheckCircle`, `Info` for feedback.
  - *Rationale*: Professional, monoline icons that match the Sentinel aesthetic.
- **Hook-Based Validation**: Implement a `useTechnicalValidation` hook that returns status and human-readable messages based on regex and existing ID lookups.
  - *Rationale*: Decouples validation logic from the presentation components.

## Risks / Trade-offs

- **[Risk]** Breaking existing form accessibility.
  - **Mitigation**: Ensure all new components use standard `<label>` and `<input>` elements with proper `aria-` attributes for error reporting.
- **[Risk]** Refactoring complexity in large forms (e.g., Spatial Editor).
  - **Mitigation**: Refactor forms incrementally, starting with Login, then moving to specific Admin modules.
