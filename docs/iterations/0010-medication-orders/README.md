# Phase 4A-1 — Medication Catalog & Physician Orders

[Issue #23](https://github.com/KateK77/careflow-ehr/issues/23). Baseline `ea477e305a94e57aa8ba7c5390bc2def07f79cb8`. Requirements S12, S13 and W03 in the English baseline.

## State and ownership decisions

- Catalog revisions are created inactive. Administrators explicitly activate or retire a revision. One revision per synthetic code may be active. Revision content is immutable.
- An assigned Physician opens a draft only in an in-progress Encounter. Draft edits and signing use the same provider lock as Encounter completion. A reviewed, expiring token binds the actor, order and version. Signing freezes the catalog snapshot and all order content.
- A draft or signed order may become cancelled with a reason. A draft cancellation requires an in-progress Encounter. A signed cancellation can occur after completion. Cancellation retains the original signature and records its own actor and time.
- Only the ordering Physician sees their drafts. Administrator and Nurse can read signed orders through their existing chart scope. Pharmacist and Lab Staff have separate access policies.
- Every successful write adds a domain event with before/after snapshots and an audit event in the same transaction. The event stores an actor-scoped UUID and request digest for durable replay. Conflicting versions and reused keys with different input fail.
- MedicationStatement and Allergy remain historical records. This increment provides no clinical interpretation or allergy clearance.

Manual UAT is deferred until both increments are published.
