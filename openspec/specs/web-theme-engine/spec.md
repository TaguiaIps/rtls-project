# web-theme-engine Specification

## Purpose
Provides a centralized CSS variable-driven theme engine that implements the "Deep Void" palette and rigid industrial geometry for the web platform.

## Requirements

### Requirement: Centralized Deep Void Theme Engine
The RTLS Analytics Platform SHALL provide a centralized CSS variable-driven theme engine that implements the "Deep Void" palette for all web applications.

#### Scenario: Application loads the theme engine
- **WHEN** the web application initializes
- **THEN** the theme engine SHALL inject CSS variables for `--surface-base` (#0e131e), `--surface-container` (#1b1f2b), and `--surface-accent` (#00f0ff)

### Requirement: Rigid Geometry and Spacing Tokens
The RTLS Analytics Platform SHALL enforce a rigid geometry using standardized radius and spacing tokens.

#### Scenario: Component uses geometry tokens
- **WHEN** a container or status chip component is rendered
- **THEN** it SHALL use `--radius-xl` (8px) for containers and `--radius-sm` (2px) for status elements, avoiding rounded "bubble" aesthetics

### Requirement: Standardized Technical Typography
The RTLS Analytics Platform SHALL provide standardized typography tokens for the "Industrial Command Deck" aesthetic.

#### Scenario: Header is rendered
- **WHEN** a technical terminal header or large metric is rendered
- **THEN** it SHALL use the `Space Grotesk` font family with appropriate weight and letter spacing tokens
