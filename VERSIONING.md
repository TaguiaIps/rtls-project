# Versioning Policy

This repository uses Semantic Versioning (`MAJOR.MINOR.PATCH`) for project releases and repository tags.

There is no release number yet because the project does not have an implementation baseline. Until that exists, the repository stays in a pre-1.0 phase.

## Current Phase

- Status: pre-release
- Tag policy: do not create a numbered release tag until the first code-backed baseline is ready
- Starting point: the first official release tag should normally be `v0.1.0`

## SemVer Rules For This Project

### `MAJOR`

Increment `MAJOR` for breaking changes to agreed project contracts, such as:

- incompatible API changes
- incompatible data model changes
- incompatible device or gateway integration changes
- incompatible UX flows that invalidate previous implementation assumptions

Before `1.0.0`, major instability is still expected. Even so, keep using SemVer discipline so the release history stays meaningful.

### `MINOR`

Increment `MINOR` for backward-compatible additions, such as:

- new product capabilities
- new documented modules or subsystems
- new user stories that expand scope without breaking existing contracts
- new screens, reports, or admin workflows that are additive

### `PATCH`

Increment `PATCH` for backward-compatible corrections, such as:

- bug fixes
- documentation clarifications
- prototype consistency fixes
- wording, layout, or spec corrections that do not change agreed behavior

## Pre-release Labels

Use pre-release identifiers when a build is not ready for a stable tag:

- `v0.1.0-alpha.1`: early internal validation
- `v0.1.0-beta.1`: feature-complete but still under validation
- `v0.1.0-rc.1`: release candidate

Optional build metadata may be appended when useful:

- `v0.1.0-rc.1+20260323.shaabcdef`

## When To Move To `1.0.0`

Cut `1.0.0` only when all of the following are true:

- core implementation exists
- the primary architecture is stable
- the initial product contract is considered releasable
- breaking changes are expected to become exceptional rather than normal

## Tag Format

Use annotated git tags in this format:

- `v0.1.0`
- `v0.2.0`
- `v0.2.1`
- `v0.3.0-beta.1`

Do not use bare numeric tags like `0.1.0`.

## Commit Convention

Use Conventional Commits so version bumps are easy to reason about:

- `feat:` normally implies a `MINOR` bump
- `fix:` normally implies a `PATCH` bump
- `docs:` usually implies no release by itself, unless docs change an agreed external contract
- `refactor:`, `chore:`, `test:` usually imply no release by themselves

If a change is breaking, mark it explicitly:

- `feat!: ...`
- `fix!: ...`

Include a `BREAKING CHANGE:` footer in the commit body when applicable.

## Changelog Policy

The changelog source is [`CHANGE.LOG`](./CHANGE.LOG).

Maintain it using these sections:

- `Unreleased`
- released versions in descending order

Each release should use Keep a Changelog style headings:

- `Added`
- `Changed`
- `Fixed`
- `Removed`

## First Release Recommendation

When the first implementation baseline exists, use:

1. `v0.1.0` for the first coherent code-backed baseline
2. `v0.2.0` for the next additive milestone
3. `v0.2.1` for stabilization and corrections

Until then, keep changes under `Unreleased` in the changelog and avoid tagging numbered releases.
