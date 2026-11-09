# 0004 — Phase 2A physician workspace and SOAP documentation

- [Issue #7](https://github.com/KateK77/careflow-ehr/issues/7)
- [PR #8](https://github.com/KateK77/careflow-ehr/pull/8) — open, awaiting manual acceptance
- [Implementation commit 63afb065](https://github.com/KateK77/careflow-ehr/commit/63afb0651de93a107eab58aafc9fbb1b2688a429)
- Branch: `phase/0004-physician-workspace`, based on `9e04a80498303d588972394c90eb35028d766228`
- [Approved prompt, preserved verbatim](prompt.md)
- [Access, states and signing decision](../../decisions/0004-encounters-and-soap.md)
- [Verification](verification.md), [manual acceptance guide](acceptance.md), [feedback](feedback.md), [changed files](changed-files.md)
- Requirements baseline v1.0 / English translation 1.0.0: limited S02, S06–S08, S10 and the encounter/documentation portion of W01. The approved prompt narrows the full baseline; rooming, diagnoses, orders, addenda and AVS are not included.

## Scope and acceptance

Use the existing Patient and Appointment records to provide authorized longitudinal charts, a dated physician worklist, explicit encounter start, encounter completion and four-section SOAP drafts with confirmed signing. Persist all writes and transactional audit events. Enforce backend role/ownership checks, nested patient/encounter/note isolation, versions, duplicate prevention and signed-content protection. Every clinical page carries the existing demo statement.

## Implementation report

Added the clinical Django app with Encounter, Note and ClinicalEvent models, additive migrations, service policies, forms, views, templates and tests. Reused authentication, provider serialization locks, audit records and the existing visual identity. Added links from demographics and appointment details. Added migration consistency to CI. Existing registration and scheduling behavior remains, except appointment transitions are now rejected after encounter start to preserve clinical context.

Appointments remain arrived; encounter states independently track clinical work. One SOAP note per encounter is supported. Administrator and Nurse read clinic clinical records; Physician reads assigned-patient charts and own encounters/notes. Only the assigned active Physician may author/sign/complete. FrontDesk has no clinical content access. Multi-role read access is a union; Administrator alone cannot sign.

The local database was backed up through SQLite's online backup API before migrations. Both migrations have been applied locally. All original database rows, 31 patients and four appointments were preserved, and integrity/foreign-key checks passed. No seed/reset was run. See verification for exact boundaries.

## Known limitations and review boundary

This is a local, single-clinic synthetic demonstration. Assignment derives from appointments/encounters, including historical assignments; no care-team or assignment-expiry model exists. Explicit Save draft is provided, without autosave. One note per encounter; no addendum, reopening, deletion, cosigning or general encounter state editor. Completion requires a signed four-section SOAP note, not clinical adequacy, diagnosis or order validation. Notes can be incomplete drafts. The chart lists bounded recent history (50 encounters/notes, 10 appointments, 100 merged timeline items); the worklist paginates encounters.

Direct SQL and bulk ORM updates can bypass service controls, including signed-content protection. No database-level audit immutability, comprehensive security test, production readiness, PostgreSQL validation or clinical safety certification is claimed. Browser checks cover a primary workflow and responsive dimensions, not a full accessibility audit.

Prior Phase 1A/1B UX feedback remains deferred. Medications, allergies, problems, laboratory, imaging, nursing, prescribing, billing, AI and deployment are excluded. Do not merge or begin Phase 2B until separately approved. User manual acceptance is pending.
