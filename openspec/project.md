# OpenSpec Project Context

## Product

The product planned and implemented in this repository is the **RTLS Analytics Platform**.

It is an indoor real-time location and analytics platform focused primarily on restaurants and large catering operations, with secondary applicability to industrial environments when the same architecture fits.

## Repository Purpose

This repository is both:

- the implementation monorepo for the current platform baseline
- the documentation-first planning workspace for future platform changes through OpenSpec

OpenSpec changes in this repository should describe real product increments that build on the implemented codebase already present under `apps/`, `packages/`, and `docs/`.

## Current Implementation Baseline

The repository already includes an implemented baseline for:

- backend authentication, RBAC, and audit foundations
- site, floor, floor-plan, and zone management
- gateway and asset registry workflows
- MQTT ingestion and raw-reading persistence
- economic-tier live positioning, location history, and live streaming
- web operations shell, operations overview, and live map baseline

Later OpenSpec changes should treat those areas as existing foundations unless the change explicitly modifies them.

## Primary Personas

- **Alex**: Administrator responsible for setup, calibration, infrastructure health, security, and configuration governance
- **Carlos Mendes**: Operations Manager responsible for live monitoring, incident triage, alerts, and analytics

## Domain Priorities

The platform should keep prioritizing:

- real-time asset visibility
- table SLA monitoring
- dwell and round-trip analysis
- actionable alerts
- infrastructure health and auditability

Use restaurant and catering terminology by default. See [GLOSSARY.md](./GLOSSARY.md) for preferred language.

## Authoritative References

Use these repository documents to ground OpenSpec work:

- `docs/requirements-document.md`
- `docs/system-design.md`
- `docs/technical-specification-document.md`
- `docs/ux-design.md`
- `docs/implementation-plan.md`
- `openspec/GLOSSARY.md`
- current merged specs under `openspec/specs/`

When those sources disagree, proposals should call out the mismatch explicitly instead of silently choosing one.

## Architecture Direction

The current platform direction is:

- backend: FastAPI, SQLAlchemy, JWT auth, WebSockets, MQTT ingestion
- data: PostgreSQL with TimescaleDB-oriented modeling and Redis for coordination/runtime state
- web: React plus Vite
- mobile: Expo React Native baseline for later mobile workflows
- infrastructure: local Docker Compose with a Kubernetes-oriented target architecture

OpenSpec changes should preserve the split between presentation, business logic, persistence, and shared contracts.

## Backlog Planning Rule

`docs/implementation-plan.md` is the default source for selecting the next backlog item when the user asks for the next proposal.

The repository should usually keep:

- one active OpenSpec implementation change at a time before broader platform maturity
- tightly scoped changes that map to one bounded concern

## OpenSpec Output Expectations

OpenSpec artifacts in this repository should:

- distinguish clearly between what is already implemented and what is only being proposed
- keep proposals concise and explicit about scope and non-goals
- use testable requirements in spec deltas
- keep tasks ordered, verifiable, and implementation-oriented
- update docs when behavior, terminology, architecture, or contracts materially change

## Archive Rule

Archive a change only after:

- implementation tasks are complete
- related specs are ready to sync
- validation passes for the change or the full spec set, as appropriate
