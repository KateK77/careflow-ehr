# Manual UAT and UX follow-up v1.0

Recorded 2026-11-09. Source: the [verbatim approved cross-phase request](../0004-physician-workspace/uat-followup-prompt.md). These are user-reported observations, separate from automated tests. No comprehensive manual acceptance or merge approval is inferred.

## Reported passing observations

| ID | User observation |
| --- | --- |
| B-UAT-01 | Created and viewed synthetic medical history. |
| B-UAT-02 | Saved dates, source and comments. |
| B-UAT-03 | Recorded a medical-history review. |
| B-UAT-04 | Edited a reviewed record. |
| B-UAT-05 | Editing cleared review while retaining original authorship. |
| B-UAT-06 | Created an active problem. |
| B-UAT-07 | Changed the problem to Resolved. |
| B-UAT-08 | Onset, resolution and original author were retained. |
| B-UAT-09 | Created an active, unconfirmed allergy. |
| B-UAT-10 | Summary changed to Documented allergies. |
| B-UAT-11 | Attempted No known allergies with an active allergy. |
| B-UAT-12 | Contradictory allergy assessment was rejected. |
| B-UAT-13 | Created an active medication statement. |
| B-UAT-14 | Changed it to Stopped with an end date. |
| B-UAT-15 | Original authorship and history were retained. |
| B-UAT-16 | Completed encounters were read-only. |
| B-UAT-17 | Created a Primary diagnosis in an in-progress encounter. |
| B-UAT-18 | Created a Secondary diagnosis linked to a resolved problem. |
| B-UAT-19 | Attempted a second Primary diagnosis. |
| B-UAT-20 | Rejection preserved the two existing diagnoses. |

No blocking workflow defect was reported in these checks. Presentation issues below were separately reported and addressed. Unreported roles, security scenarios and concurrency behavior are not described as manually tested.

## Reproductions and changes

- UX-01: native HTML date controls can accept extended years. Django rejects unsupported dates; the actual saved date was valid **2020-04-15**. No corruption was confirmed. History fields now use ISO input, supported-year guidance and min/max bounds consistent with existing future-date validation. Server tests preserve year 0001, pre-1900 and 2020 dates without truncation.
- UX-02: history lists group source/review/update into a four-column layout. Shared minimum widths, contained scrolling and conditional keyboard-scroll hints preserve full text. Audit before/after tables wrap long values.
- UX-03: posting No known allergies while an active allergy exists reproduced an internal non-field-error label. A shared readable summary and bound retry form now show a plain-language conflict and retain submitted choices and confirmation. Existing state/version safeguards remain authoritative.
- UX-04: a second primary diagnosis previously exposed the database constraint name through model validation. Explicit model validation now supplies a rank-field message; the service also translates a database-race conflict. The existing database uniqueness constraint is unchanged and still tested directly.
- UX-05: diagnosis details include the linked problem's current clinical status. Linking a resolved problem does not reactivate or modify it.
- UX-06: history and chart audit presentation use human-readable event/field labels while retaining actor, timestamps, versions and before/after values. Stored action identifiers and audit rows are not rewritten.

## Repeated review investigation

Read-only local metadata showed reviews at **2026-11-10 01:16:17.603031 UTC** and **01:16:27.243619 UTC**, both actor ID 2, advancing versions **1→2** and **2→3**. These are successive fresh versions about 9.64 seconds apart, consistent with a second review; the evidence does not establish an accidental duplicate defect or prove the user's intent.

Focused regression tests demonstrate that replaying the same version receives HTTP 409 and creates no second review event; submitting the current version legitimately adds another attestation. The review button now says **Review again** after review and explains the new attestation. The inherited browser submission guard blocks repeated submits while navigating, without suppressing legitimate later reviews or changing backend version checks. No arbitrary time-window suppression was added.

## Verification and remaining gaps

System checks and migration consistency passed. The complete Phase 2B default suite passed **133 tests** (126 existing, three inherited presentation tests and four new focused UAT tests). Chromium results and publication links are recorded in verification.md and PR #10. An initially incorrect browser-test CSS selector was corrected; application behavior did not cause that harness failure.

New UX changes require user retesting, including native date typing in the user's browser, split-screen readability, retained allergy input, duplicate-primary messaging, linked resolved status and explicit re-review. Automated tests do not establish comprehensive security, database-level audit immutability or clinical readiness. No migration, local database write, signed-note change, historical-source rewrite, deployment, PR merge or new phase is part of this follow-up.
