## 1. Theme Engine & Tokens

- [x] 1.1 Implement CSS Variables for the "Deep Void" palette in `apps/web/src/index.css` (e.g., `--surface-base`, `--surface-container`).
- [x] 1.2 Add typography tokens for `Space Grotesk` and `Inter` with appropriate weights and letter-spacing.
- [x] 1.3 Define rigid geometry tokens: `--radius-xl` (8px), `--radius-sm` (2px), and `--gutter-industrial` (0.3rem).

## 2. Web Operations Shell Refactor

- [x] 2.1 Update `.dashboard-shell` to use CSS Grid for the "Intentional Asymmetry" layout.
- [x] 2.2 Refactor `.nav-rail` into the high-density "Command Rail" with monoline icons and all-caps labels.
- [x] 2.3 Implement the "No-Line" structural rule by removing borders and using background color shifts for primary containers.

## 3. Live Map & Selected Asset Workspace

- [x] 3.1 Create a glassmorphism utility class (`.hud-glass`) with backdrop-blur and 60% opacity backgrounds.
- [x] 3.2 Apply glassmorphism to Live Map HUD overlays (floor details, status indicators).
- [x] 3.3 Refactor the Selected Asset drawer to use the "Deep Void" tonal hierarchy and rigid geometry tokens.

## 4. Global Refinements & Documentation

- [x] 4.1 Perform a global audit of `apps/web/src` to remove deprecated `border: 1px solid` rules in operational views.
- [x] 4.2 Update `docs/ux-design.md` to reflect the final "Industrial Command Deck" token names and structural patterns.
- [x] 4.3 Verify that every primary action button utilizes the signature gradient and "Inner Glow" box-shadow state.
