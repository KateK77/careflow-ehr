# ADR 0004 — Clinical encounters and SOAP documentation

Status: Phase 2A implementation policy, pending manual acceptance.

## Access and context

Retain Django, server templates and SQLite. Clinical access is separate from demographic access. Active Administrator and Nurse users may read single-clinic charts, encounters and notes. Active Physicians may read charts for patients with an appointment or encounter assigned to them, and only their own encounters/notes. Administrator has no implicit authoring/signing privilege. FrontDesk alone has no clinical access. Multiple roles grant the union of read access; writing always requires Physician membership and ownership, even for Administrators. Demographic and scheduling permissions remain unchanged.

## States and concurrency

An arrived appointment permits an explicit start by its assigned active Physician, using the displayed appointment version. Encounter is one-to-one with Appointment and retains Patient and Physician relationships. Check-in never starts an encounter. Appointment remains arrived during and after clinical work; encounter independently transitions from in_progress to completed. No appointment status or check-in provenance is rewritten. Cancellation is rejected once an encounter exists. Existing check-in and cancellation before encounter start remain unchanged.

Encounter completion requires at least one signed note and no remaining drafts. Completed encounters reject further note creation, edits or signing. Start/completion timestamps are server-generated UTC; presentation uses clinic-local time. No reopening, deletion or addenda are provided in this increment.

All clinical writes first update the existing provider serialization row, inside an atomic transaction, before reading current state. Scheduling cancellation takes the same lock. Integer versions reject stale encounter/note updates. A database one-to-one constraint prevents duplicate appointment encounters. Every state/content write and its audit event commit together. SQLite contention produces a retryable conflict. These are application-service guarantees, not a production concurrency assessment.

## Notes and audit

One SOAP note per encounter in this increment. Drafts permit incomplete sections, require explicit synthetic-data confirmation and preserve text on validation errors. Signing requires four nonblank sections, each at most 20,000 characters, plus a separate confirmation POST carrying the current note version. This is a demo completeness rule, not clinical adequacy validation. The original author alone may edit/sign. Signing stores author identity and server timestamp; there is no content edit/delete path for signed notes. No clinical suggestions or diagnoses are generated.

Supported service and model-save paths reject signed-note changes. Direct SQL, bulk ORM writes and database administrators can bypass application controls; database-level immutability is not claimed. Audit events record actor, action, time, patient and changed field names, without copying SOAP text. Chart reads and denied role access are audited. No audit modification UI is exposed.

## Local data

Take a SQLite online backup before additive migrations, verify integrity and foreign keys, and compare every pre-existing application row after migration. Never reseed or reset the local database. Browser and automated fixtures run only against isolated test databases. Existing Chinese documents and English translations remain immutable.
