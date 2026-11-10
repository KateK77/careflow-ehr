# Current project status — closeout v1.0

Verified 2026-11-10 against main [65a7d3e2f01d9af0c99126c340e9f426c954401c](https://github.com/KateK77/careflow-ehr/commit/65a7d3e2f01d9af0c99126c340e9f426c954401c). This is the current disposition of the local synthetic-data prototype. The product's longer-term roadmap is not complete.

## Completed phases and merge ledger

| Existing phase name | Merge / closed Issue | Merge commit |
| --- | --- | --- |
| Phase 2A — Physician Workspace | [PR #8](https://github.com/KateK77/careflow-ehr/pull/8) / [Issue #7](https://github.com/KateK77/careflow-ehr/issues/7) | [afc0ed16d7f90fd8abe87c9cb686712efddbce49](https://github.com/KateK77/careflow-ehr/commit/afc0ed16d7f90fd8abe87c9cb686712efddbce49) |
| Phase 2B — Clinical History | [PR #10](https://github.com/KateK77/careflow-ehr/pull/10) / [Issue #9](https://github.com/KateK77/careflow-ehr/issues/9) | [2146713966e0e7407e33c554c4b7145fe5765bab](https://github.com/KateK77/careflow-ehr/commit/2146713966e0e7407e33c554c4b7145fe5765bab) |
| Phase 3A — Nursing Workspace | [PR #12](https://github.com/KateK77/careflow-ehr/pull/12) / [Issue #11](https://github.com/KateK77/careflow-ehr/issues/11) | [65a7d3e2f01d9af0c99126c340e9f426c954401c](https://github.com/KateK77/careflow-ehr/commit/65a7d3e2f01d9af0c99126c340e9f426c954401c) |

All three completed their approved review for the local prototype and were merged using merge commits, retaining their development history and branches. They are not pending the acceptance or merge decision required for those merges. Earlier requirements, ADRs, iteration reports, prompts and changelog delivery entries remain historical evidence; their former pending/stacked language is superseded for current status by this ledger. It is not rewritten to fabricate contemporaneous approvals.

## Available features

- Existing patient/scheduling foundation: Django staff authentication, backend roles, synthetic patient registration/search/demographic editing, MRN uniqueness and duplicate warnings, audited writes, reviewed appointments, calendars and check-in.
- Phase 2A — Physician Workspace: scoped physician worklists/charts; explicit encounter start from an arrived appointment; persistent SOAP drafts, confirmed signing, supported-path signed-note edit denial, completion and provenance.
- Phase 2B — Clinical History: medical/surgical/family/social history; active/resolved/inactive problems; allergy records and explicit assessment; medication history statements; primary/secondary encounter diagnoses, review/version history and audit events. Medication history is not prescribing or administration.
- Phase 3A — Nursing Workspace: saved worklist progress, rooming/readiness, corrected assessments and vital panels, explicit units/timestamps, chronological flowsheets, physician read access and scoped chart/timeline integration. Nursing saves do not create encounters or rewrite signed notes.

Role and state rules remain those in [architecture](architecture.md) and [ADRs](decisions/). The application remains the existing Django modular monolith with server-rendered templates and a local SQLite database.

## Manual and automated evidence

The user reported 12 Phase 2A, 20 Phase 2B and nine Phase 3A passing workflow observations. The five targeted retests passed with their original qualifications: duplicate-primary feedback; contradictory allergy rejection with retained input; resolved linked-problem display; user-reported acceptable date entry without extra evidenced malformed-date cases; and responsive Physician Workspace behavior at the tested, unspecified width. See [the consolidated retest record](iterations/0006-nursing-workspace/uat-retest.md).

These observations and the subsequent explicit merge approvals complete the approved review scope. They do not establish comprehensive testing of every role, browser, security behavior or viewport. No new nursing manual retest or fresh user-run end-to-end workflow is inferred from the five targeted retests.

Actual merged-main verification at the baseline above:

- Django system check passed; migration consistency reported no changes.
- **164 default regression tests passed.**
- **Seven local Chromium workflows passed:** shared UI; outpatient registration-to-completion integration; nursing assessment/vitals/corrections/flowsheet/physician review; history/diagnoses; physician SOAP; scheduling; patient management.
- [Merged-main Actions CI passed](https://github.com/KateK77/careflow-ehr/actions/runs/42756802365), running system checks, the default suite and migration consistency. Chromium was local evidence, not part of that CI workflow.
- The merge-verification SQLite hash and every table count were unchanged; read-only integrity and foreign-key checks passed. Patient, appointment, encounter, signed SOAP, history, nursing and audit records were retained. No reset, reseed or migration was performed during merge verification.

This documentation closeout has its own [verification record](maintenance/0001-project-closeout/verification.md). Prior test results are not presented as a new manual or browser run.

## Deferred enhancements — non-blocking, not implementation approval

- Latest cross-phase feedback: consolidate duplicate allergy summary/inline errors; show authorized readable labels where audit numeric IDs appear; continue monitoring narrower tables. These were not merge blockers.
- [Phase 1A's five feedback groups](iterations/0002-patient-registration/feedback.md): patient-directory density, demographic layout/hierarchy, consistent action labels, form guidance/synthetic-confirmation usability and audit-history presentation. Later targeted clinical UI improvements do not imply this entire earlier backlog is closed.
- [Phase 1B's four feedback groups](iterations/0003-scheduling-checkin/feedback.md): configurable appointment types while retaining visit reason, compact schedule filters, responsive appointment history/long cancellation reasons, and configurable working hours/leave/early check-in policy.

Each future implementation needs scoped approval. This closeout does not implement these items or recategorize them as blocking defects.

## Prototype limitations

Synthetic data only; all screens retain DEMO — NOT FOR CLINICAL USE. This is a DEBUG-only, single-clinic educational/research prototype, not a deployed, certified or clinically ready EHR and not affiliated with Epic. Use original assets and preserve privacy boundaries.

Supported services enforce authorization, context, validation, optimistic versions and auditing, but direct SQL/bulk ORM/database operators can bypass application controls. Database-level audit immutability, production concurrency, infrastructure security and comprehensive penetration testing are not established. SQLite remains a local-development choice; any shared deployment requires separate architecture/security review.

Additional malformed-date manual cases, other browsers/devices, narrower history/nursing layouts, assistive-technology accessibility, deliberate re-review and broader manual role/security coverage remain unverified. SOAP has no addenda, reopening or cosigning workflow. Medication statements do not prescribe, dispense or administer. Orders/lab results, MAR, portals, billing, interoperability and AI remain outside the delivered scope.

## Proposed next increment

**Orders & Laboratory Results** is proposed, pending separate approval. No phase name/number, detailed functional specification, implementation branch or new clinical feature is authorized here. Refine workflows, ownership/permissions, provenance, statuses, synthetic-data handling and acceptance criteria before seeking approval. No external laboratory service or deployment is approved.
