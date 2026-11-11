# Architecture revision v0.2

**Design proposal; implementation is not approved.** Retain the existing Django modular monolith, server-rendered interface and local synthetic SQLite context. This document amends [v0.1 architecture](../v0.1/architecture.md); no source files, groups, permissions, tables or migrations are changed now.

## Separate identities and responsibilities

The original ordering physician remains immutable provenance and the provider-serialization key. Current responsible physician is an immutable LabReviewAssignment selected by the order pointer; current laboratory processor remains assigned_lab_staff. These three relationships are not interchangeable.

Review reassignment is a guarded administrative operation, not an edit to Encounter.physician, Appointment.physician, Patient, Note.author, old LabResultReview.reviewer or ordering_physician. Its explicit capability is narrower than clinical authoring. A covering Physician without pre-existing chart rights uses a restricted lab requisition/report header and lab-specific queryset, never a workaround that inserts appointments, calls chart-context builders or broadens the global four-role whitelist.

Current review queries include final, corrected **and withdrawn** publications and test for a review of the current publication/current assignment pair. An inactive assignee is a separate eligibility overlay, not an acknowledged state. Reassignment after a prior review creates another obligation for that publication; reactivation alone changes neither pointer nor old acknowledgement.

## Transaction and lock protocol

Continue provider-first serialization using the **original** ordering_physician_id, even if inactive. The protected original user row remains; do not switch lock keys when coverage changes. Lock order and relevant assignment/publication/specimen/draft rows consistently afterward. Submission still shares the existing encounter-completion provider lock. Catalog-only operations retain v0.1 catalog locking without an inversion.

For a new mutation: authenticate/capability/scope-check; inspect a successful same-command receipt only if current authorization permits disclosure; acquire/recheck aggregate and child versions, current pointer/assignment and actor/target eligibility; validate payload; commit domain updates, audit/provenance and receipt atomically. Success-replay administrative eligibility is distinct from new-command transition eligibility: an authorized replay returns the original assignment outcome rather than creating another epoch. Old physician acknowledgement replay after losing responsibility is denied, not re-executed.

Reassignment transaction creates one assignment+LabEvent/AuditEvent and changes current assignment/order version only. Withdrawal transaction creates one notice publication+LabEvent/AuditEvent and changes current publication/order status/version only. Acknowledgement creates immutable review+LabEvent/AuditEvent; it changes neither clinical report status nor original signed documentation. Required explicit abandonment of a correction draft is its own audited transaction, not a silent side effect of withdrawal.

SQLite serialization tests remain necessary; direct database operators, bulk ORM and independent identity administration can bypass application assumptions. No production concurrency, identity-governance or audit-tamper-proof claim is added. Sensitive payload projection/serialization must be permission-aware, not merely a hidden template block.

## Publication validity and quarantine

A withdrawal is an append-only publication notice and a terminal order outcome, not a mutation/deletion of any old row. Current pointer always resolves to the notice. There is no automatic last-valid-result fallback: a previous revision may itself be wrong. No subsequent report or correction is published on a withdrawn order; replacement work is a new authorized order.

When reason=context_error, restrict the whole chain's value payloads, before/after snapshots, old free-text comments and unrestricted reason text from ordinary chart/review/history/search/error responses. Expose safe reason category, withdrawal time, actual authorized actor identity and prior review metadata only. Assigned Lab Staff or an Administrator with explicit quarantine-inspection permission can audit original content in scoped protected views. Neither quarantine nor inspection changes patient/order/specimen relationships. Signed SOAP is not rewritten to remove a value that a user may previously have documented; it remains signed history, with the lab withdrawal visible separately.

## Storage and migration planning

Typed JSON is the preferred MVP decision. Validator dispatch uses pinned schema_version+kind and a frozen catalog; publication immutability applies to both report and withdrawal payloads. Database constraints protect relational uniqueness/status/pointers as far as local columns permit, while service validation protects JSON semantics and joined relationships. Numeric trending/aggregation is explicitly outside the MVP; a future normalized component model is an approved-later alternative, not a missing current dependency.

See [increments](increments.md) for additive boundaries. Because no laboratory schema exists on current main, these are future migration specifications, not conversions run against a live lab database. Existing Phase 2A/2B/3A patient, appointment, encounter, SOAP, history/nursing and audit rows must be preserved. Any later backfill creates only explicitly reviewed new lab responsibility rows and system-provenance events, never retroactively fabricated clinical actions or acknowledgements.

For this documentation revision, verify unchanged whole SQLite hash and every original tracked-file hash, including v0.1 and prior Chinese/English sources. Future implementation testing compares protected clinical rows and expected new lab/audit deltas; it must not claim an unchanged database file across intentional schema/writes.

## Future interoperability and exclusions

The [v0.1 conceptual R4 discussion](../v0.1/architecture.md) remains non-executable mapping context. A future withdrawal mapping must distinguish entered-in-error/withdrawal semantics from absent or negative analytes; internal assignment epochs/acknowledgements are not silently turned into diagnostic-report statuses or server meta.versionId. Resolve profiles/history/authorization separately before any FHIR implementation. No transport, connector, real terminology, clinical CDS, medication/billing/AI functionality, cloud deployment or release is introduced by v0.2.
