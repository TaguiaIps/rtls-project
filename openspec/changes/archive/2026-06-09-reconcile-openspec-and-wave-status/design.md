## Context

The RTLS Analytics Platform has matured through several waves of implementation. However, the supporting documentation—specifically the active specifications and the implementation plan—contains placeholders and status indicators that do not fully reflect the current delivered state. This design outlines the approach for reconciling these artifacts to ensure documentation integrity and project governance.

## Goals / Non-Goals

**Goals:**
- Align `docs/implementation-plan.md` with the current implementation status (Waves 1-5).
- Finalize all "Purpose" statements in `openspec/specs/` to replace "TBD" placeholders.
- Establish a "Change Archive Checklist" in the implementation plan to prevent documentation drift in future changes.
- Ensure clear requirement-to-spec traceability.

**Non-Goals:**
- Modifying system behavior or implementation code.
- Updating functional or non-functional requirements (except for metadata/governance).
- Changing the system architecture or UX design.

## Decisions

### 1. Finalizing Spec Purpose Statements
The "TBD Purpose" placeholders in `openspec/specs/` will be replaced with concise statements that define the scope and intent of the specification. These statements will be derived from the existing requirements within each spec and the original change descriptions.

- **Approach**: Read each spec's requirements and summarize the core capability into a 1-2 sentence purpose statement.

### 2. Updating Wave Status
The `docs/implementation-plan.md` currently lists Wave 5 as "Partially implemented". Since maintenance alerts and native QR scanning are now part of the delivered baseline, this status will be updated.

- **Decision**: Mark Wave 5 as "Implemented" and ensure all delivered components are listed.
- **Rationale**: Reflecting the true state of the platform is critical for planning Wave 6 and beyond.

### 3. Implementation Plan Governance Checklist
To maintain documentation quality, a new "Change Archive Checklist" will be added to `docs/implementation-plan.md`. This checklist will be a requirement for all future change archives.

- **Checklist Items**:
  - Implementation status updated in `docs/implementation-plan.md`.
  - Specification `## Purpose` statements finalized (no "TBD" placeholders).
  - Terminology aligns with `openspec/GLOSSARY.md`.
  - Delta specs successfully merged into main specs.
  - Requirement-to-change traceability verified.

### 4. Terminology Standardization
Standardize the use of "Delivered", "Deferred", and "Pending" across all planning artifacts.

- **Delivered**: Implementation is complete, verified, and merged.
- **Deferred**: Scope was originally planned for a wave but moved to a later wave or backlog.
- **Pending**: Scope is planned for the current or future wave but not yet implemented.

## Risks / Trade-offs

- **[Risk]** Inaccurate or overly broad purpose statements.
  - **Mitigation**: Use the existing requirements in each spec as the primary source of truth for the purpose statement.
- **[Risk]** Documentation drift during parallel changes.
  - **Mitigation**: The governance checklist ensures that every change archive turnstile includes a documentation reconciliation step.
