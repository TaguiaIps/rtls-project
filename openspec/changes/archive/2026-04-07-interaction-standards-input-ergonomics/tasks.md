## 1. Common Form Components

- [x] 1.1 Create `apps/web/src/components/FormErgonomics.tsx` with `CommandInput` and `FormFeedback` components.
- [x] 1.2 Implement the `PasswordInput` component with the visibility toggle logic and Lucide icons.
- [x] 1.3 Add CSS classes for the "Command" aesthetic in `apps/web/src/index.css` (bottom-border focus transitions).

## 2. Validation & Formatting Logic

- [x] 2.1 Implement the `useTechnicalValidation` hook for real-time ID and formatting checks.
- [x] 2.2 Create utility functions for MAC address and IP configuration input masks.
- [x] 2.3 Add a standardized `FormMessage` component for consistent Info/Warning/Error layouts.

## 3. Incremental Refactoring

- [x] 3.1 Refactor the Login form in `apps/web/src/App.tsx` to use the new `CommandInput` and `PasswordInput`.
- [x] 3.2 Update the Asset Tag Registry forms in `AdminSpatialWorkspace.tsx` with real-time ID validation.
- [x] 3.3 Apply input masks to Gateway management fields in the Spatial Admin workflows.
