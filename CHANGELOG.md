# Changelog

## v1.0 release candidate — Unreleased (2026-11-11)

**Status:** Integrated synthetic-data local-demo candidate in [Draft PR #47](https://github.com/KateK77/careflow-ehr/pull/47). Not yet merged to `main`, tagged, hosted or approved for clinical use.

### Already merged to main (Phases 0–4B)

- Foundation, staff access, synthetic patient registration, scheduling and check-in; physician charts, encounters, SOAP signing, medical history, problems, allergies and diagnoses.
- Nursing worklists, rooming, vital observations and flowsheets.
- **Phase 3B:** Lab catalog and orders, specimen processing, revisioned results and physician review ([#18](https://github.com/KateK77/careflow-ehr/pull/18), [#20](https://github.com/KateK77/careflow-ehr/pull/20), [#22](https://github.com/KateK77/careflow-ehr/pull/22)).
- **Phase 4A:** Medication catalog, orders, pharmacist verification and simulated dispensing ([#24](https://github.com/KateK77/careflow-ehr/pull/24), [#26](https://github.com/KateK77/careflow-ehr/pull/26)).
- **Phase 4B:** Nurse MAR, fictional administrations, exceptions, corrections and chart integration ([#28](https://github.com/KateK77/careflow-ehr/pull/28), [#30](https://github.com/KateK77/careflow-ehr/pull/30)).

### Implemented in release candidate, awaiting merge (Phases 5–8)

- **Phase 5:** Linked patient portal, controlled lab-result releases, messaging and appointment requests ([#32](https://github.com/KateK77/careflow-ehr/pull/32), [#34](https://github.com/KateK77/careflow-ehr/pull/34)).
- **Phase 6:** Simulated coverage/charges/statements, mock claims, appeals, payment and reversal ledger ([#36](https://github.com/KateK77/careflow-ehr/pull/36), [#38](https://github.com/KateK77/careflow-ehr/pull/38)).
- **Phase 7:** Imaging orders and catalog, radiology exam, report revisions/withdrawal and physician acknowledgement ([#40](https://github.com/KateK77/careflow-ehr/pull/40), [#42](https://github.com/KateK77/careflow-ehr/pull/42)).
- **Phase 8A:** Inpatient admission, beds, transfers and discharge ([#44](https://github.com/KateK77/careflow-ehr/pull/44)).
- **Phase 8B:** ED registration, fictional triage and tracking, disposition and ED-to-inpatient admission ([#46](https://github.com/KateK77/careflow-ehr/pull/46)).
- Integrated the separate Phase 5–6 and Phase 7 histories through a two-parent integration commit, preserving original commits.
- Candidate UX improvements: clearer imaging stale-revision recovery, role-neutral staff sign-in guidance, payment-reference instructions, and early-imaging-start simulation documentation.

### Verification and known limitations

- Reported local candidate audit: **345 Django tests, 23 Chromium workflows and two additional probes** passed; system checks, migrations and whitespace checks passed.
- The original [release PR Django CI](https://github.com/KateK77/careflow-ehr/actions/runs/43150653448) passed against `main`; Chromium and audit probes were **local tests**, not CI jobs. A new documentation commit must be checked separately.
- User-reported manual UAT covered core Phases 5–8, sampled patient/role isolation and signed SOAP/MAR retention. This is not exhaustive clinical/security verification.
- Audit reported SHA-256 preservation of 47 pre-existing SQLite databases, including the original and Phase 3–8 previews.
- Outstanding coverage: exhaustive POST/CSRF, mixed roles and revocation, concurrent ED dispositions, payment-reference collisions, populated Phase 7 upgrade, accessibility and load testing.
- Local prototype uses `DEBUG=True`, a development secret and SQLite. Synthetic data only; no production deployment, medical validation or external clinical/payer integration.

## Historical entries

### Documentation closeout — 2026-11-10

Phases 2A (PR #8), 2B (PR #10) and 3A (PR #12) completed review and merged into main. Earlier pending-review headings were contemporaneous historical descriptions, not current states.

### Phase 0–3A original development notes

- Requirements baseline, documented Issues/branches/PRs, Django/SQLite local architecture.
- Phase 1A: staff login, role-based demographics, patient registration/search/editing, MRN uniqueness and auditing.
- Phase 1B: schedules and appointments, rescheduling/cancellation, physician calendars, check-in, optimistic versions and audit history.
- Phase 2A: physician worklist/charts, encounters and persistent signed SOAP with protected revisions.
- Phase 2B: longitudinal medical and medication history, problems, allergies, encounter diagnoses and audit events.
- Phase 3A: nursing worklists, assessments, vitals, correction history, flowsheets and chart integration.

Detailed earlier reports are preserved in [docs/iterations](docs/iterations/).
