# Changelog

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
