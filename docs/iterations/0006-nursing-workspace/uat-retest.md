# Cross-phase targeted manual UAT retest v1.0

Source: the [approved retest prompt](../0004-physician-workspace/uat-retest-prompt.md), preserved verbatim. This documentation-only addendum follows [the implementation/UAT report](uat-followup.md) and [publication receipt](uat-publication.md). Earlier evidence remains unchanged and historical; pending-retest statements are superseded only for the checks below.

## Actual user-reported results

| Retest | Outcome | Observed behavior and qualification |
| --- | --- | --- |
| 01 — Duplicate Primary Diagnosis | **Passed** | Duplicate rejected with a clear, user-friendly message; internal constraint name no longer displayed. |
| 02 — Allergy Assessment Validation | **Passed** | Contradictory No known allergies rejected; no `__all__` label; submitted status and confirmation remained visible. The user did not intentionally change saved allergy records. |
| 03 — Linked Problem Status | **Passed** | Secondary diagnosis displayed Essential hypertension (Resolved); Problem List continued to show Resolved. |
| 04 — Date Input | **User-reported passed** | Updated date-entry behavior was acceptable; earlier saved history date was valid. Additional malformed-date cases were not evidenced as manually executed. |
| 05 — Responsive Physician Workspace | **Passed at tested width** | Names/MRNs readable; appointment and encounter statuses visible; clinical navigation/encounter links accessible; Recent Encounters displayed correctly. Viewport dimensions were not supplied. |

The allergy observation is user-reported behavior and intent; no independent database comparison across that manual session is claimed. Database preservation verification for this documentation task uses a fresh baseline captured after the reported retests. The date finding remains a UX observation, not confirmed database corruption. The responsive result is not extrapolated to narrower widths, other browsers or all clinical tables.

## Current manual status by phase

| Phase | Recorded status | Outstanding evidence limits |
| --- | --- | --- |
| 2A — Physician Workspace | Prior 12 reported workflow observations remain passed. Retests 04 and 05 passed with their stated qualifications. | No additional malformed-date cases, viewport dimensions or broad role/security acceptance supplied. The earlier nursing-read observation used the integrated descendant stack. |
| 2B — Clinical History | Prior 20 reported workflow observations remain passed. Retests 01–03 passed; date entry was also user-reported acceptable. | No comprehensive relationship, concurrency, role/security or date-variant manual testing is inferred. Intentional fresh re-review was not included in these five retests. |
| 3A — Nursing Workspace | Prior nine reported nursing observations remain passed. Applicable parent retest evidence is now inherited and recorded. | No new manual nursing/flowsheet retest, nursing responsive-width test or fresh end-to-end nursing-to-physician run was supplied in this request. |

These are the outcomes of the reported checks, not comprehensive acceptance of every phase feature or approval to merge. User merge approval remains a separate step.

## Deferred non-blocking enhancements

1. Consolidate the allergy conflict message currently shown in both summary and inline error regions. Validation passed; duplicate presentation is not classified as a blocking functional defect.
2. Improve audit labels where numeric IDs appear instead of readable patient, clinician or problem labels. Preserve authorized access, identifiers and provenance when this is considered later.
3. Continue monitoring tables at narrower viewport widths. The current Physician Workspace pass is limited to the tested width.

No deferred enhancement is implemented now, and none is represented as an approved new functional change. Broader historical UX backlog remains deferred.

## Existing and current automated evidence

The unchanged application implementation previously passed 102 / 133 / 164 default tests and four / five / seven local Chromium workflows on Phases 2A / 2B / 3A respectively. [The prior publication receipt](uat-publication.md) pins exact implementation commits and successful Push/PR CI runs. Those Chromium results remain historical automated evidence and are not recast as manual retests or newly rerun browser checks.

For this documentation-only update, each owner branch reran system checks, migration consistency and its full default suite: **102 Phase 2A, 133 Phase 2B and 164 integrated Phase 3A tests passed**. Whitespace, relative links and staged documentation-only scope passed. Tests used disposable synthetic test databases; no migrations were created or applied. The fresh local SQLite whole-file hash stayed unchanged; all 27 baseline historical source/translation/policy/Phase 0/prompt files were preserved byte-for-byte on the final integrated branch.

Normal parent merges propagate the Phase 2A documentation to Phase 2B, then Phase 2B to Phase 3A, preserving both parents and all commits. No conflicts, force push or history rewrite occurred. Actual new HEAD CI and commit links are verified and recorded in [PR #8](https://github.com/KateK77/careflow-ehr/pull/8), [PR #10](https://github.com/KateK77/careflow-ehr/pull/10) and [PR #12](https://github.com/KateK77/careflow-ehr/pull/12). The base relationships remain #8→main, #10→Phase 2A and #12→Phase 2B; none is merged.

Verified parent documentation publications: Phase 2A [48de22b153cc0ae5dea34e5dfc996298904bf9e8](https://github.com/KateK77/careflow-ehr/commit/48de22b153cc0ae5dea34e5dfc996298904bf9e8), [Push passed](https://github.com/KateK77/careflow-ehr/actions/runs/42750434042), [PR passed](https://github.com/KateK77/careflow-ehr/actions/runs/42750439080); Phase 2B [fd46bc2453fe7b031802f176f3fbfd420da181be](https://github.com/KateK77/careflow-ehr/commit/fd46bc2453fe7b031802f176f3fbfd420da181be), [Push passed](https://github.com/KateK77/careflow-ehr/actions/runs/42750657570), [PR passed](https://github.com/KateK77/careflow-ehr/actions/runs/42750665807). These are actual Actions results for the exact documentation heads. The resulting Phase 3A publication and its actual checks are linked on PR #12 after publication.

## Modified files and traceability

- Phase 2A / existing [Issue #7](https://github.com/KateK77/careflow-ehr/issues/7): `docs/iterations/0004-physician-workspace/README.md`, `feedback.md`, `verification.md`, new `uat-retest.md` and new `uat-retest-prompt.md`.
- Phase 2B / existing [Issue #9](https://github.com/KateK77/careflow-ehr/issues/9): `docs/iterations/0005-clinical-history/README.md`, `feedback.md`, `verification.md` and new `uat-retest.md`; parent documentation inherited.
- Phase 3A / existing [Issue #11](https://github.com/KateK77/careflow-ehr/issues/11): `docs/iterations/0006-nursing-workspace/README.md`, `feedback.md`, `verification.md` and new `uat-retest.md`; parent documentation inherited.

All 13 changed files are iteration Markdown documents. No application code, settings, dependency, migration, database, signed note, historical source or original prompt was changed. No new Issue/PR, release, deployment or functional phase was created.

## Remaining risks and review boundary

Unverified manual behaviors include narrower history/nursing layouts, other browsers/devices, assistive-technology accessibility, additional malformed/extended/early date cases, deliberate re-review, broader roles/security and a fresh full nursing-to-physician workflow after the UX changes. Prior automated coverage of some of these behaviors does not establish manual acceptance. Direct database tamper resistance, production concurrency and comprehensive security are not certified.

The remaining feedback is non-blocking. Preserve all three open PRs and wait for separate final review and merge approval.
