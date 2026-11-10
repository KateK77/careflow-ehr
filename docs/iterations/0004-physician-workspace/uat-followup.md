# Manual UAT and UX follow-up v1.0

Recorded 2026-11-09 from the [original approved request](uat-followup-prompt.md). These are user-reported observations, separate from developer automated/browser checks. No comprehensive feature/role acceptance or merge approval is inferred.

## Phase 2A reported passes

| ID | Actual user observation |
| --- | --- |
| A-UAT-01 | Opened an authorized patient chart. |
| A-UAT-02 | Viewed nursing documentation from the Physician chart in the integrated stack. |
| A-UAT-03 | Explicitly started an encounter from an arrived appointment. |
| A-UAT-04 | Created a structured SOAP draft. |
| A-UAT-05 | Saved and reopened the draft. |
| A-UAT-06 | Edited and resaved the draft. |
| A-UAT-07 | Reviewed all four SOAP sections. |
| A-UAT-08 | Signed with explicit confirmation. |
| A-UAT-09 | Observed signed/read-only presentation and signing history. |
| A-UAT-10 | Direct note-edit URL access was rejected after signing. |
| A-UAT-11 | Completed the encounter. |
| A-UAT-12 | Confirmed completion time/version and original check-in provenance. |

The reported workflow passed without a blocking functional defect. This does not add unreported manual testing of all roles, forged POSTs, concurrency, CSRF, cross-patient isolation, migration upgrades or comprehensive security. Phase 2A's nursing display observation depends on the integrated descendant stack, not the Phase 2A branch alone.

## Shared UX changes owned by Phase 2A

- UX-01 foundation: shared ISO date-field configuration, four-digit-year guidance, native min/max and client validity messages. History-specific fields are owned by Phase 2B. Values are never silently truncated. Native HTML permits extended years; Python/Django supported dates stop at 9999. No database corruption was confirmed; the user reported the saved date was 2020-04-15. Dates 0001 and pre-1900 remain supported where domain rules permit.
- UX-02: compact four-column Physician appointment worklist preserves patient/MRN/clinician, date and both state contexts. Minimum readable cell widths and contained overflow preserve full text. Overflow hints appear only when needed, with focusable keyboard-scrolling regions; desktop tables retain density. Existing tables inherit the shared affordance, with history/nursing-specific improvements on their owner branches.
- UX-03 foundation: shared form-error summary renders non-field messages directly, not the internal __all__ key. Clinical and appointment action errors use it; allergy/history pages adopt it in Phase 2B.
- UX-06: human-readable event and changed-field labels, distinct chart-navigation links and clearer appointment action text preserve actor/time/version and stored audit identifiers. No audit rows are rewritten. Dependent history/nursing templates adopt the shared formatter on their owner branches.
- Submission guard: prevents repeated submits while one form submission is navigating, without disabling named submitters or changing payloads. Back/forward page restoration resets the guard. It does not suppress legitimate later reviews; backend version checks remain authoritative.

References: [HTML valid date syntax](https://html.spec.whatwg.org/multipage/common-microsyntaxes.html#valid-date-string) permits four or more year digits; [MDN date controls](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date) documents min/max constraint validation. These explain browser entry behavior, not a storage-corruption finding.

## Verification and limits

Phase 2A default suite: 102 tests passed, including three new presentation/date regressions. Core UI Chromium scenario passed for extended-year rejection, valid 2020/pre-1900/year-0001 input, long patient names at 1440/700/390 widths, overflow guidance and duplicate-submit suppression. Existing clinical, scheduling and patient browser workflows are rerun before publication. A browser harness URL match initially omitted the harmless GET query string; the corrected harness passed. No application failure remains from that setup issue.

System/migration consistency and Git whitespace checks are recorded in verification.md; owner-branch CI and commit links are recorded on PR #8 and the final handoff. All follow-up UI changes still need focused user retesting. No signed SOAP content, local data, historical source/translation or original prompt was changed. No merge, release, deployment or next phase is approved.
