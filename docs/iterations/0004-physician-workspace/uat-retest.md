# Targeted manual UAT retest v1.0

Source: the [approved retest prompt](uat-retest-prompt.md), preserved verbatim. This addendum follows [UAT/UX follow-up v1.0](uat-followup.md); earlier evidence remains historical and unchanged. It supersedes pending-retest statements only for the observations explicitly supplied below.

## Phase 2A observations

| Retest | User-reported outcome | Evidence boundary |
| --- | --- | --- |
| 04 — Date input | **User-reported passed.** Updated date-entry behavior was acceptable; the earlier saved history date was valid. | No additional malformed-date, extended-year, earliest-year or other-browser manual cases were evidenced. Prior developer automated date tests remain separate evidence. No database corruption was established. |
| 05 — Responsive Physician Workspace | **Passed at the tested width.** Names and MRNs remained readable; appointment and encounter statuses were visible; clinical navigation and encounter links remained accessible; Recent Encounters displayed correctly. | The tested viewport dimensions were not supplied. This does not establish behavior at all narrower widths, devices or browsers, or for history/nursing tables. |

The previous 12 user-reported Phase 2A workflow observations remain passed. Nursing information seen from the physician chart belongs to the integrated descendant stack, not the Phase 2A branch in isolation. The applicable targeted retests above passed with their stated qualifications; comprehensive feature/role/security acceptance and merge approval are not inferred.

## Shared deferred, non-blocking feedback

1. Allergy conflict messages appear in both summary and inline error regions. Consolidation is a future UX enhancement, not a blocking functional defect; no change is made now.
2. Audit history sometimes shows internal numeric IDs instead of human-readable patient, clinician or problem labels. Future label resolution should preserve provenance and access scope; it is not implemented or treated as a current blocker.
3. Continue monitoring responsive tables at narrower widths. The observed Physician Workspace pass applies only to the tested width.

The clinical-history retests 01–03 are owned by Phase 2B and recorded on its branch; the Phase 3A descendant consolidates the results. No new nursing retest or comprehensive acceptance is implied by this addendum.

## Automated evidence and remaining risks

The unchanged Phase 2A implementation [6490841](https://github.com/KateK77/careflow-ehr/commit/6490841ab18e67b14c9409552a619f1279f1fcf0) previously passed 102 default tests and four local Chromium workflows. Its actual [Push CI](https://github.com/KateK77/careflow-ehr/actions/runs/42741609207) and [PR CI](https://github.com/KateK77/careflow-ehr/actions/runs/42741615233) passed. These are prior automated results, not new manual observations. Current documentation-only regression and Actions results are recorded in verification.md and [PR #8](https://github.com/KateK77/careflow-ehr/pull/8).

Remaining unverified manual behaviors include broader role/security scenarios, assistive-technology accessibility, other browsers, malformed date variants and responsive layouts outside the tested width. No comprehensive security or database-level audit-immutability claim is made. No application code, schema, signed note or local database is changed by this documentation update. All PRs remain open, awaiting separate merge approval.
