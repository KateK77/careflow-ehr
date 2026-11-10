# Cross-phase manual UAT and UX follow-up v1.0

Recorded 2026-11-09 from the [verbatim approved request](../0004-physician-workspace/uat-followup-prompt.md). This report supplements historical records; it does not rewrite original prompts, requirements, Chinese sources or English translations.

## User-reported Phase 3A passes

| ID | Actual observation |
| --- | --- |
| C-UAT-01 | Opened the nursing worklist and an arrived patient's record. |
| C-UAT-02 | Created and corrected a rooming assessment. |
| C-UAT-03 | Recorded pain score and nursing observations. |
| C-UAT-04 | Set Ready for provider. |
| C-UAT-05 | Recorded a complete synthetic vital-sign panel. |
| C-UAT-06 | Viewed saved values and units. |
| C-UAT-07 | Viewed the vital-sign flowsheet. |
| C-UAT-08 | Physician could read the assessment and vital signs. |
| C-UAT-09 | Nursing documentation did not automatically create an encounter. |

These nine observations passed. The parent records separately preserve [12 Phase 2A observations](../0004-physician-workspace/uat-followup.md) and [20 Phase 2B observations](../0005-clinical-history/uat-followup.md). No comprehensive acceptance of every role/feature, security behavior or follow-up UI change is claimed. No PR merge was approved in this request.

## Changes and ownership

| Branch / PR | Follow-up ownership |
| --- | --- |
| Phase 2A / #8 | Shared ISO date guidance and supported-year validation; shared accessible non-field error summary; compact physician worklist; full-text contained scrolling and hints; readable chart audit labels; duplicate submission guard; 12 observations and regression records. |
| Phase 2B / #10 | History date fields; retained allergy-conflict input and plain-language errors; friendly duplicate-primary validation with unchanged database constraint; linked problem status; explicit re-review; compact history list and audit table; 20 observations and four focused tests. |
| Phase 3A / #12 | Compact four-column nursing worklist retaining patient/MRN, clinician, appointment interval/status, assessment readiness, vital count and actions; human-readable nursing event/field labels and wrapping before/after audit table; adapted integration/browser assertions; responsive nursing checks; nine observations and consolidated verification. |

Phase 2A was safely merged into Phase 2B, then Phase 2B into Phase 3A using normal merge commits. No branch was rebased, deleted or force-pushed, and no PR was merged. The one Phase 2B chart-template merge conflict was resolved by retaining its history links and adding the parent event formatter. Phase 3A parent propagation merged without conflicts. All clinical/nursing context and existing descendant functionality were retained.

## Findings and evidence boundaries

- Confirmed presentation defects: internal allergy `__all__` label, internal primary-diagnosis constraint message, and missing linked-problem status in diagnosis details. Regression tests now cover the readable output and retained records. Existing allergy/primary backend rules and the primary uniqueness constraint remain in place.
- Date behavior is a UX/validation improvement, **not confirmed data corruption**. The reported saved date was 2020-04-15. Browser guidance and server tests reject unsupported/malformed years while retaining supported early historical dates; values are not silently truncated.
- Responsive changes preserve full data, with horizontal scrolling when necessary. Mobile layouts still require scrolling for wide flowsheets; eliminating every horizontal scroll was not claimed. Shared navigation has clearer individual links without replacing the existing interface.
- Two review events approximately ten seconds apart were successive versions, not proof of duplicate processing. Same-version replay is rejected; a fresh review legitimately creates another attestation. See the Phase 2B investigation for timestamps and scope. No arbitrary time-window deduplication or audit deletion was introduced.
- New tests initially required CSS-selector and human-readable-label assertion corrections. Those harness mismatches were corrected, and the final full/browser runs passed. No unresolved application failure was identified by these runs.

## Actual local verification

- `python manage.py check`: passed, no issues.
- `python manage.py makemigrations --check --dry-run`: passed, no changes detected. **No migrations were created or applied.**
- Complete default suite: **164 tests passed** (157 pre-existing plus three shared presentation regressions and four history UAT regressions).
- Seven Chromium workflows passed: shared date/responsive/submit-guard checks; registration-to-completion integration; nursing assessment/vitals/correction/flowsheet/physician read; history and diagnosis validation; physician SOAP; scheduling; patient management.
- New browser coverage checks extended-year rejection, early valid dates, duplicate submit suppression, physician/nursing table containment at 1440/700/390 widths, scroll hints, readable audit details, retained allergy selections and friendly duplicate-primary rejection. Existing integration tests continue to verify backend roles, patient/encounter isolation, explicit state transitions, signed-note preservation and check-in provenance; these are automated results, not additional user observations.
- Local screenshots were generated under ignored `.venv/uat-followup/screenshots/` and inspected for narrow history/nursing/flowsheet presentation. They contain disposable synthetic test data and are not committed.
- Read-only database backup, whole-file SHA-256 comparison, integrity and foreign-key checks verify preservation of **31 patients, five appointments, two encounters, one SOAP note, 12 history events and four nursing events**. Unchanged whole-file content covers existing signed documentation and all saved records. Test databases are isolated and disposable.
- Original requirement/source/translation documents, Phase 0 records and previously approved prompts were compared byte-for-byte with the pre-follow-up baseline. The new approved request is retained verbatim in the Phase 2A iteration. No C-drive backup was modified.

## GitHub traceability and results

- Phase 2A: [6490841](https://github.com/KateK77/careflow-ehr/commit/6490841ab18e67b14c9409552a619f1279f1fcf0); [Push CI passed](https://github.com/KateK77/careflow-ehr/actions/runs/42741609207); [PR CI passed](https://github.com/KateK77/careflow-ehr/actions/runs/42741615233); [Issue #7](https://github.com/KateK77/careflow-ehr/issues/7); [PR #8](https://github.com/KateK77/careflow-ehr/pull/8).
- Phase 2B: [dfe412a](https://github.com/KateK77/careflow-ehr/commit/dfe412a0f2e2f54126e7c33f93d489b46b941010); [Push CI passed](https://github.com/KateK77/careflow-ehr/actions/runs/42742435730); [PR CI passed](https://github.com/KateK77/careflow-ehr/actions/runs/42742441527); [Issue #9](https://github.com/KateK77/careflow-ehr/issues/9); [PR #10](https://github.com/KateK77/careflow-ehr/pull/10).
- Phase 3A: [Issue #11](https://github.com/KateK77/careflow-ehr/issues/11) and [PR #12](https://github.com/KateK77/careflow-ehr/pull/12) record the resulting publication commit and actual HEAD Push/PR CI outcomes. Local results above are not substituted for GitHub results. PR bases remain #8→main, #10→Phase 2A, #12→Phase 2B.

## Remaining manual retest and limitations

1. Retest native date typing in the user's browser, including a five-digit year, malformed input, 2020-04-15 and an appropriate pre-1900 synthetic history date. Confirm errors are clear and saved values are unchanged.
2. Inspect physician/history/nursing tables and expanded audit before/after values at the user's split-screen widths. Confirm full names, long labels and long comments remain accessible through wrapping/scrolling.
3. Retest contradictory allergy assessment: plain-language feedback, retained input, unchanged saved allergy summary; reload before retrying a stale version.
4. Retest duplicate-primary messaging and retained diagnoses; verify a resolved linked problem displays Resolved and remains resolved.
5. Review readable event labels, actors, timestamps, versions and previous values; intentionally use Review again to confirm a new attestation, without mistaking it for a replay.
6. Repeat the integrated nursing-to-physician workflow after these UI changes. Broader role combinations, accessibility with assistive technology, other browsers, production concurrency, infrastructure/security hardening and direct database audit tampering have not received comprehensive manual testing.

No clinical readiness or comprehensive security certification is asserted. Existing unrelated future UX backlog remains deferred. All three PRs stay open and await final review; future merge order remains Phase 2A, Phase 2B, then Phase 3A, with fresh base/CI verification at each step. No release, deployment or next phase was started.
