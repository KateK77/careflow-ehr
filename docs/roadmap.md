# CareFlow EHR — delivery roadmap

**Current stage:** integrated Phases 0–8 local synthetic-data prototype; workspace UX upgrade under review. See [project status](project-status.md) for evidence, merged/unmerged distinctions and constraints.

## Delivered phases and current state

| Increment | State | Scope |
| --- | --- | --- |
| Phase 0 | **Merged** | Foundation, requirements and engineering workflow |
| Phase 1A/1B | **Merged** | Staff roles, patient administration, scheduling and check-in |
| Phase 2A/2B | **Merged** | Physician workspace, SOAP, longitudinal history and diagnoses |
| Phase 3A | **Merged** | Nursing, vitals and flowsheets |
| Phase 3B-1/2/3 | **Merged** | Laboratory catalog/orders, processing, results and physician review |
| Phase 4A-1/2 | **Merged** | Medication orders, pharmacy verification and simulated dispensing |
| Phase 4B-1/2 | **Merged** | MAR, omissions/refusals, corrections and chart history |
| Phase 5A/5B | **Integrated via PR #47** | Portal, released records, messages and appointment requests |
| Phase 6A/6B | **Integrated via PR #47** | Billing, coverage, claims, appeals and simulated payment ledger |
| Phase 7A/7B | **Integrated via PR #47** | Imaging and radiology, report revision, physician review |
| Phase 8A | **Integrated via PR #47** | Inpatient beds, admission, transfer and discharge |
| Phase 8B | **Integrated via PR #47** | ED tracking, fictional triage, disposition and ED admission |

The Phase 5–8 code was integrated through [PR #47](https://github.com/KateK77/careflow-ehr/pull/47), merged at `a9e0913b626b88908ad2ca3041d2ec9497ba7d15`. Original phase names and iteration evidence remain unchanged.

## Current upgrade

- Open PRs #49–#55 provide portal entry, expanded verification, native CUA infrastructure and appointment guidance.
- [Issue #56](https://github.com/KateK77/careflow-ehr/issues/56) delivers a cohesive workspace presentation, clearer patient/appointment actions, readable audits and nonduplicated allergy errors.
- The upgrade stacks on PR #55. No existing PR is merged or retargeted by this work.
- Manual upgrade UAT, paid native CUA, merging, tagging and deployment require separate approval.
- [Feedback disposition and acceptance](iterations/0027-workspace-upgrade/feedback.md) distinguish existing fixes, this upgrade and deferred business-rule changes.

## Deferred engineering and research directions

Potential improvements include more role-revocation/POST/CSRF and concurrency coverage, accessibility and load testing, additional design/usability improvements, optional interoperability standards and rigorously evaluated AI-assisted workflows. **None of these is an approved Phase 9**, production scope or clinical feature.

## Original broad planning categories (historical)

| Original category | Planning theme |
| --- | --- |
| 0 | Foundation |
| 1 | Patient access and scheduling |
| 2 | Clinical encounters |
| 3 | Orders, medications and laboratory |
| 4 | Hospital operations and patient engagement |
| 5 | Revenue cycle |
| 6 | Interoperability and decision support |

Historical category numbers do **not** rename the delivered phase identifiers above. Individual prompts, engineering rationale and past acceptance notes are preserved in [iteration records](iterations/) and [architecture decisions](decisions/).
