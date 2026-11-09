# ADR 0005 — Longitudinal history and encounter diagnoses

Status: Phase 2B implementation policy; neither Phase 2A nor Phase 2B has passed manual UAT.

## Stacked scope and access

Build on Phase 2A eff5a2b94891e5deae8304ac2e9036c6dc8eaf43 in a separate history Django app. Target the Phase 2A branch, not main. The user explicitly approved this increment before Phase 2A UAT; this does not approve merging either PR.

Retain existing clinical read access. Longitudinal records are patient-wide, so an authorized Physician sees the patient's history across authors. A treating Physician may create/edit/review longitudinal records when assigned a scheduled/arrived appointment or in-progress encounter for the patient. Historical assignments alone retain chart read access, but do not grant history writes. Administrator/Nurse are read-only unless they also qualify as a treating Physician. FrontDesk cannot access detailed clinical records. Diagnosis read access follows the existing encounter scope; diagnosis writes require the encounter's assigned Physician and an in-progress encounter. No diagnosis action changes longitudinal problems automatically.

## Records, versions and audit

Medical/surgical/family/social history, problems, allergies and medication statements retain original author/source, last editor, timestamps, dates, comments and review metadata. Explicit review records actor/time without altering clinical content. Content edits clear prior review certification; event history preserves earlier reviews. All writes require the displayed integer version (zero for new records), synthetic-content confirmation, validation and transactional audit. There is no delete endpoint. Resolved/inactive/stopped records remain visible and may be explicitly updated with history.

A patient serialization row coordinates longitudinal writes and allergy summaries. Diagnosis writes acquire the existing provider lock first, then the patient lock, so completion and diagnosis edits cannot commit out of order through supported services. Current state and versions are rechecked inside the transaction. At most one primary diagnosis per encounter is enforced by a database constraint. Other diagnoses are secondary; users explicitly demote a prior primary before selecting another. Linked problems must belong to the same patient; encounter/patient relationships are immutable through the UI.

Audit events retain actor/time/action/changed field names. History events additionally preserve structured before/after clinical values in the synthetic database, accessible only through clinical authorization, to make past states inspectable. No clinical text is copied to ordinary logs. Direct SQL/bulk ORM writes can bypass service controls; database-level immutability and production concurrency are not claimed.

## Allergy state

No summary means Not reviewed, never No known allergies. Explicit summary states are Not reviewed, Unknown, No known allergies and Documented allergies. An active, non-refuted allergy requires Documented allergies. Adding/reactivating such an entry updates the summary atomically and clears prior summary review. Inactivating the last active entry changes the summary to Not reviewed, requiring a new explicit assessment; it does not infer No known allergies. Unknown/No known/Not reviewed cannot be selected while active entries exist; Documented requires an active entry. Historical inactive/resolved/refuted entries remain visible separately. Contradictory active/refuted or active/entered-in-error records are rejected.

## Dates and terminology

Dates are optional except a resolved problem's resolution date and a stopped medication's end date. End dates cannot precede onset/start; history dates cannot be future dates. Non-resolved problems have no resolution date; active medication statements have no end date. Problem and diagnosis terminology codes are optional free-text mock identifiers, not validated clinical terminology. Medication dose/route/frequency are descriptions, never executable orders or recommendations. Patient-reported/documented/family-reported provenance is explicit and not independently verified by the application.

## Compatibility

Use an additive migration and consistent local SQLite backup with integrity, foreign-key and row-preservation checks. Do not alter Patient, Appointment, Encounter or signed Note rows during migration. No SOAP text is rewritten from history changes; signed documentation remains its original snapshot. The Phase 2A encounter-completion requirement remains a signed note, without introducing mandatory diagnoses. Only isolated test databases are seeded.
