# CareFlow EHR — v1.0 release-candidate status

**Snapshot: 2026-11-11 (America/Chicago).** This page describes the reviewed **local, synthetic-data release candidate**, not a merged, tagged or clinical-ready v1.0 release.

- **Merged main:** [`00c624553cc265e6275a9d2750ab0041a7e6d97f`](https://github.com/KateK77/careflow-ehr/commit/00c624553cc265e6275a9d2750ab0041a7e6d97f), through Phase 4B.
- **Verified code candidate:** [`d6881ff1b3b912ee891fd22beb2252814e56ef56`](https://github.com/KateK77/careflow-ehr/commit/d6881ff1b3b912ee891fd22beb2252814e56ef56), Phases 5–8 and candidate UX fixes. Documentation updates follow this SHA and require fresh CI.
- **Release review:** [Draft PR #47](https://github.com/KateK77/careflow-ehr/pull/47), `release/v1.0` → `main`. No merge approval or release tag.

## Merged delivery ledger

| Increment | Delivered capability | Merged PRs |
| --- | --- | --- |
| Phase 0 | Foundation and development records | [#2](https://github.com/KateK77/careflow-ehr/pull/2) |
| Phase 1A/1B | Staff access, patients, scheduling/check-in | [#4](https://github.com/KateK77/careflow-ehr/pull/4), [#6](https://github.com/KateK77/careflow-ehr/pull/6) |
| Phase 2A/2B | Physician SOAP and longitudinal history | [#8](https://github.com/KateK77/careflow-ehr/pull/8), [#10](https://github.com/KateK77/careflow-ehr/pull/10) |
| Phase 3A | Nursing, vitals and flowsheets | [#12](https://github.com/KateK77/careflow-ehr/pull/12) |
| Phase 3B-1/2/3 | Lab ordering, processing, revisioned results and review | [#18](https://github.com/KateK77/careflow-ehr/pull/18), [#20](https://github.com/KateK77/careflow-ehr/pull/20), [#22](https://github.com/KateK77/careflow-ehr/pull/22) |
| Phase 4A-1/2 | Medication orders, pharmacist review, simulated dispensing | [#24](https://github.com/KateK77/careflow-ehr/pull/24), [#26](https://github.com/KateK77/careflow-ehr/pull/26) |
| Phase 4B-1/2 | Nurse MAR, exceptions, corrections | [#28](https://github.com/KateK77/careflow-ehr/pull/28), [#30](https://github.com/KateK77/careflow-ehr/pull/30) |

## Implemented and UAT-reviewed; not yet merged

| Increment | Candidate capability | Original open PRs |
| --- | --- | --- |
| Phase 5A/5B | Patient portal, released records, messages, appointment requests | [#32](https://github.com/KateK77/careflow-ehr/pull/32), [#34](https://github.com/KateK77/careflow-ehr/pull/34) |
| Phase 6A/6B | Billing, insurance, claims, appeals, simulated payments | [#36](https://github.com/KateK77/careflow-ehr/pull/36), [#38](https://github.com/KateK77/careflow-ehr/pull/38) |
| Phase 7A/7B | Imaging, radiology, report revisions, physician review | [#40](https://github.com/KateK77/careflow-ehr/pull/40), [#42](https://github.com/KateK77/careflow-ehr/pull/42) |
| Phase 8A | Inpatient facilities, admission, transfer, discharge | [#44](https://github.com/KateK77/careflow-ehr/pull/44) |
| Phase 8B | ED arrival, fictional triage, tracking, disposition, ED-to-inpatient admission | [#46](https://github.com/KateK77/careflow-ehr/pull/46) |

Both Phase 5–6 and Phase 7 lines were preserved through a two-parent integration commit before Phase 8. All eight original PR heads are ancestors of code candidate `d6881ff`. Original PRs remain open until **after** a separately approved integrated release merge and historical reconciliation.

## Verification evidence

**Manual UAT (user-reported):** core portal and billing flows, messaging and requests, imaging publications/corrections/withdrawal, hospital admission/transfer/discharge, ED triage/provider review/discharge/admission, selected cross-patient/role direct URL denials, and preservation of completed Encounter #4's signed read-only SOAP and MAR history. Not an exhaustive role, state, browser or security matrix.

**Automated audit (Codex-reported):** **345 Django tests**, **23 local Chromium workflows** and **two audit probes** passed; Django checks, migration consistency and Git whitespace checks passed. [PR #47 initial CI](https://github.com/KateK77/careflow-ehr/actions/runs/43150653448) separately passed Django system checks, default tests and migrations **against main**. It does **not** execute Chromium or the audit probes. The new documentation commit must receive fresh CI.

**Database preservation (Codex-reported):** SHA-256 hashes unchanged across 47 existing SQLite files, including original `db.sqlite3` and accepted preview. Separate temporary clones passed reported integrity and upgrade checks. This is not a new production backup or independent clinical audit.

**Integration diff:** `main` → code candidate: 10 commits ahead, none behind; eight added migrations (two each for portal, billing, imaging, hospital), no existing migration replacements. Fresh-install and upgrade rehearsals used isolated databases; do not infer that all legacy-populated database shapes were tested.

## Unverified and out of scope

- Mixed-role and role-revocation sessions, exhaustive direct POST/CSRF checks, concurrent ED disposition/payment-reference collisions, fully populated independent Phase 7 upgrade, comprehensive accessibility, multiple-browser and load testing.
- Simulated radiology workflow permits an assigned authorized exam to start earlier than scheduled. Payment/reversal references must be unique.
- Application audit restrictions do not protect against privileged SQL or bulk ORM modifications; no tamper-evident storage, formal security assurance or production performance guarantees.
- `DEBUG=True`, a local development secret, SQLite and synthetic data only. **Not for real patient records, clinical treatment, hosted deployment, payer/lab connectivity or regulatory certification.**
- Future FHIR interoperability, AI assistance and hosted usage are proposals only; there is no implementation authorization.

## Remaining release gates

1. Confirm the documentation-only update, new exact PR head, current main baseline and passing new target-`main` CI.
2. Review permissions, integrated diff, migration graph, fresh isolated install and upgrade evidence; preserve all original and UAT databases.
3. Obtain explicit approval for merging; use a **merge commit**, never squash/rebase or force-push history.
4. Check merged-main tree, ancestry, CI and original PR reconciliation; release tagging and hosting are separate decisions.

Earlier dated reports, prompts and acceptance results remain intact under [docs/iterations](iterations/) and [docs/decisions](decisions/).
