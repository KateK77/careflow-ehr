# Targeted manual UAT retest v1.0

Source: the [approved cross-phase retest prompt](../0004-physician-workspace/uat-retest-prompt.md). Earlier [UAT follow-up](uat-followup.md), original prompts and evidence remain preserved. This addendum supersedes pending-retest statements only for the observations below.

## User-reported outcomes

| Retest | Outcome and actual observations |
| --- | --- |
| 01 — Duplicate Primary Diagnosis | **Passed.** The duplicate was rejected with a clear, user-friendly error. The internal database constraint name was no longer displayed. |
| 02 — Allergy Assessment Validation | **Passed.** Contradictory No known allergies was rejected; `__all__` was no longer displayed; submitted status and confirmation remained visible. The user did not intentionally change saved allergy records. |
| 03 — Linked Problem Status | **Passed.** A Secondary diagnosis displayed **Essential hypertension (Resolved)**; the underlying Problem List continued to show Resolved. |
| 04 — Date Input | **User-reported passed.** Updated date-entry behavior was acceptable and the earlier saved history date was valid. No additional malformed-date cases were evidenced as manually executed. |

The allergy observation is a statement of user intent and UI behavior; it is not an independently measured before/after database comparison spanning the manual session. Preservation checks for this documentation task begin from the current local database baseline. The linked-problem result is the user's observed status, not a claim that all possible relationships were manually tested.

The earlier 20 reported Phase 2B workflow observations remain passed. These applicable targeted retests also passed with their stated limitations. The Physician Workspace responsive result is recorded in the [Phase 2A addendum](../0004-physician-workspace/uat-retest.md) and is limited to the tested width. No new nursing retest, comprehensive manual/security acceptance or permission to merge is inferred.

## Deferred, non-blocking UX feedback

- The allergy conflict is displayed twice, in summary and inline regions. Future consolidation is recorded without changing validation or implementing it now.
- Audit history sometimes displays numeric internal IDs instead of readable patient, clinician or problem labels. Future presentation improvements must preserve provenance and authorized access; no such change is implemented now.
- Continue monitoring clinical tables at narrower widths; the supplied responsive pass does not establish all history/nursing layouts or viewport sizes.

These are future enhancements, not blocking functional defects or approved new functionality. The broader existing backlog remains deferred.

## Automated evidence and outstanding risks

The unchanged implementation [dfe412a](https://github.com/KateK77/careflow-ehr/commit/dfe412a0f2e2f54126e7c33f93d489b46b941010) previously passed **133 default tests and five local Chromium workflows**. Actual [Push CI](https://github.com/KateK77/careflow-ehr/actions/runs/42742435730) and [PR CI](https://github.com/KateK77/careflow-ehr/actions/runs/42742441527) passed. Automated date validation, primary uniqueness, allergy conflict/input retention, linked-problem preservation and stale/fresh review tests remain automated evidence, not newly reported manual cases. Current documentation-only checks are recorded in verification.md; new HEAD CI and commit links are verified on [PR #10](https://github.com/KateK77/careflow-ehr/pull/10).

Manual malformed/extended-year variants, additional browsers, narrower history layouts, deliberate re-review semantics, broader role/security scenarios and database-operator audit tampering remain unverified by this retest report. No corruption, comprehensive security or database-level immutability claim is made. No application code, schema, local database or signed note is changed. All stacked PRs remain open, pending separate merge approval.
