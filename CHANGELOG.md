# Changelog

## Documentation closeout — 2026-11-10

Phase 2A — Physician Workspace (PR #8), Phase 2B — Clinical History (PR #10), and Phase 3A — Nursing Workspace (PR #12) completed their approved local-prototype reviews and are merged into main. See [current status and evidence](docs/project-status.md). Earlier pending-review/acceptance headings below are preserved historical delivery entries and do not describe the current state. This documentation maintenance creates no release or new functional phase.

## Unreleased

- Added a versioned product requirements baseline and archived the supplied development-package documents.
- Established the Issue, branch, commit, PR, review, and merge workflow with reusable iteration records.
- Documented the decision to retain Django and SQLite for local development.

### Phase 1A — pending review

- Added Django staff authentication, role-based demographic access, patient registration, search, details and editing.
- Added MRN constraints, duplicate warnings, optimistic edit conflicts, transactional audits, synthetic seeding, responsive templates and automated regression coverage.

### Phase 1B — pending review

- Added physician day/week schedules, reviewed appointment creation/editing, cancellation and Front Desk check-in.
- Added appointment/provider serialization models, transactional audit events, reservation conflict validation, UTC/local-time handling and scheduling access scopes.

## Phase 2A — pending acceptance

- Added physician workspace, authorized longitudinal charts and explicit encounters from arrived appointments.
- Added persistent SOAP drafts, confirmed signing, signed-content protection and transactional clinical history.
- Added role/ownership/isolation tests and migration consistency to CI. Preserved local patient and appointment records through additive migrations.

## Phase 2B — pending acceptance (stacked on Phase 2A)

- Added longitudinal medical/surgical/family/social history, problem list, allergy assessment/entries, medication statements and encounter diagnoses.
- Added persisted reviews, before/after audit history, optimistic versions, role/context checks and consistent allergy summary transitions.
- Added one additive migration, 27 regression/concurrency tests and an isolated browser workflow. Existing clinical records and signed notes are preserved.

## Phase 3A — pending manual acceptance (stacked on Phase 2B)

- Added persisted nursing worklists, rooming/readiness assessments, structured vital panels and chronological flowsheets.
- Added Nurse-only authoring, scoped clinical reads, validated units/context/times, versioned corrections and transactional before/after history.
- Integrated latest nursing information and events into charts/encounters without changing appointment states or signed SOAP content.
