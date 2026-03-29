# OpenSpec Agent Guide

This file defines repository-specific guidance for agents working inside `openspec/`.

## Purpose

Use OpenSpec artifacts in this repository to plan, implement, and archive product changes for the RTLS Analytics Platform. OpenSpec work must stay aligned with the implemented codebase, the current merged specs, and the product terminology already established in `docs/` and [GLOSSARY.md](./GLOSSARY.md).

## Before Editing

1. Read [project.md](./project.md) for current repository and product context.
2. Review `docs/implementation-plan.md` when the user asks for the next backlog proposal.
3. Run `openspec list` and `openspec list --specs` before creating or archiving changes.
4. Inspect related code, docs, and merged specs so proposals and implementations reflect current behavior.

## Proposal Rules

- Use a unique verb-led change id in kebab-case.
- Create proposal artifacts under `openspec/changes/<change-id>/`.
- Proposal files must explain `Why`, `What Changes`, `Capabilities`, and `Impact`.
- Distinguish new capabilities from modified capabilities. Only list a modified capability when spec-level behavior changes.
- Keep scope tight. Do not fold future alerts, analytics, exports, mobile, and premium-tier work into one change unless the implementation plan explicitly calls for it.
- If repository context is ambiguous, state the assumption clearly in the proposal or design instead of hiding it.

## Spec Delta Rules

- Place spec deltas at `openspec/changes/<change-id>/specs/<capability>/spec.md`.
- Use `## ADDED Requirements`, `## MODIFIED Requirements`, and `## REMOVED Requirements` exactly as needed.
- Every requirement must be testable and include at least one `#### Scenario:`.
- Prefer additive requirements unless a breaking change is intentional and documented.
- Keep Administrator and General User behavior distinct when role-specific behavior matters.

## Design Rules

- Add `design.md` when a change is cross-cutting, introduces a new pattern, changes persistence shape, or needs trade-off discussion before coding.
- Focus on architecture, data flow, risks, and rollout strategy rather than implementation trivia.
- Call out security, performance, reliability, and observability implications when they matter.

## Task Rules

- `tasks.md` must use checkbox items in the `- [ ] X.Y Description` format.
- Order tasks by dependency.
- Keep tasks small enough to verify in one implementation pass.
- Include validation and documentation tasks whenever behavior or architecture changes.

## Implementation Alignment

- Treat merged specs in `openspec/specs/` as the current contract baseline.
- Treat archived changes in `openspec/changes/archive/` as history, not the active source of truth.
- Do not assume a feature is only planned if the codebase already implements it.
- When a proposal depends on behavior that already exists in code but is missing from docs, note that mismatch and fix the docs in the later implementation change.

## Terminology

- Use the product name `RTLS Analytics Platform`.
- Prefer restaurant and catering examples such as Kitchen, Dining Hall, Kitchen Pass, Service Corridor, Cold Storage, Waiter Tag, Tray Cart, and Table SLA.
- Avoid military or industrial placeholder naming unless the change is explicitly about cross-domain generalization.

## Validation

- Validate new proposals with `openspec validate <change-id> --strict`.
- Validate archives with `openspec validate --all --strict` after `openspec archive <change-id> --yes`.
- If validation fails, inspect the active change, the referenced capability names, and the delta syntax before changing scope.

## Archive Guidance

- Archive only completed changes.
- Confirm the change id with `openspec list` before archiving.
- After archive, verify that synced specs landed under `openspec/specs/` and that validation still passes.
