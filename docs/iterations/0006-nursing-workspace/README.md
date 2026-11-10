# Iteration 0006 — Phase 3A nursing workspace v1.0

- [Issue #11](https://github.com/KateK77/careflow-ehr/issues/11)
- [Stacked PR #12](https://github.com/KateK77/careflow-ehr/pull/12) — open, targeting Phase 2B
- [Implementation commit 48ff86a](https://github.com/KateK77/careflow-ehr/commit/48ff86a250de2b5cab2b893cd2b12b1eb5329a37)
- Branch: `phase/0006-nursing-workspace`
- Base: `phase/0005-clinical-history` at `f5209f86dedc6ad7c3aa5e5b80b0c3039027b300`
- Stack target is Phase 2B, not main. PRs #8 and #10 remain open and unmerged.
- [Original approved prompt](prompt.md), [ADR 0006](../../decisions/0006-nursing-rooming-and-vitals.md), [verification](verification.md), [feedback](feedback.md), [changed files](changed-files.md), [manual checklist](acceptance.md).
- English product baseline v1.0 / translation 1.0.0: limited S09, S19, nursing context in S06–S08 and the rooming/vitals portion of W01. Approved scope excludes broader nursing/MAR and order workflows.

## Requirements and acceptance

Provide an appointment-backed nursing worklist with date/patient/status filters and persisted assessment/readiness/vital indicators. Persist one rooming assessment per appointment and multiple structured vital observations with recording Nurse, observation time, source, units, versioned corrections and transactional before/after history. Enforce Nurse authoring, scoped clinical reads, patient/appointment/encounter consistency, valid data and stale-write protection. Integrate chronological flowsheets, latest accessible nursing information and timeline events into charts and encounter context. Existing signed notes and physician-only explicit encounter start must be preserved.

## Development report

Added the nursing Django app with RoomingAssessment, VitalObservation and NursingEvent, one additive migration, typed forms, role/state policies, service writes, worklist/detail/correction/flowsheet pages and tests. Reused shared clinic styling, authentication, provider serialization and patient audit identity. Added chart/encounter summary sections, functional nursing navigation and appointment links. All clinical pages inherit the demo banner.

The new permission extension requires active Nurse membership for authoring, including corrections by a different Nurse in the single clinic. Original recording Nurse is preserved; last editor and previous values remain visible in history. Physician reads only their appointment-linked nursing data; Nurse/Administrator read the clinic. Administrator alone has no write privilege. Other role policies are unchanged.

Writes require arrived appointments without completed encounters. Readiness is a Nurse assertion on rooming, independent of appointment and encounter states. Check-in and nursing saves do not create encounters. Optional encounter association is validated and fixed at record creation; pre-encounter records remain appointment-linked and appear in its encounter context. Partial vital panels are explicit, with at least one measurement and no inference of missing values. Numeric bounds and allowed units are documented in ADR 0006 as demo input validation, not clinical normal ranges or decision rules.

## Cross-phase integration readiness review

The [consolidated review](integration-readiness.md) and [approved review prompt](integration-review-prompt.md) cover Phase 2A/2B/3A. A confirmed gap in continuous handoff coverage led to four HTTP integration tests and one full registration-to-completion Chromium journey on this branch. No application logic or migration change was needed. The default suite now contains 157 tests; the optional combined browser suite contains six workflows. All manual UAT remains pending; future merge order is #8 → #10 → #12, with retargeting/checks and separate approval at each step.

## Known limitations and review boundary

Local single-clinic SQLite prototype. No nurse-assignment roster, inpatient beds, care plans, fall-risk algorithm, nursing task engine, MAR, medication administration, prescribing, pharmacy, labs/orders, AI, billing, external integration or deployment. Progress indicators describe saved records only. No automated readiness or clinical abnormal-value interpretation is provided.

One assessment per appointment, retained through audited correction; multiple vital panels provide flowsheet time points. No delete, discharge amendment, encounter reassignment or unit conversion. Completed encounters are read-only for new nursing documentation/corrections; a future amendment policy needs separate approval. Chart summary shows one latest accessible panel without merging values from different times. Assessment and panel may have different source appointments, each identified. Flowsheets paginate by 12 time columns; worklists by 25 appointments; detail history shows the latest 100 events.

Direct SQL/bulk ORM can bypass application services. No database-operator immutability, comprehensive security, production concurrency, full accessibility audit or clinical readiness is claimed. Neither Phase 2A, Phase 2B nor Phase 3A has passed manual UAT. The user explicitly approved this stacked increment before earlier UAT. Keep all three PRs open; no merge, release, deployment or Phase 3B.

## Manual UAT and UX follow-up v1.0

[Publication receipt](uat-publication.md) records the exact implementation commit and successful CI links for each owner branch.

[Consolidated cross-phase report](uat-followup.md), [feedback](feedback.md), [verification](verification.md) and [follow-up changed files](uat-changed-files.md) supplement the preserved implementation history. [Issue #11](https://github.com/KateK77/careflow-ehr/issues/11) and [PR #12](https://github.com/KateK77/careflow-ehr/pull/12) carry publication commit and CI links. Nine user-reported nursing passes are documented; follow-up UI retesting and final review remain pending.
