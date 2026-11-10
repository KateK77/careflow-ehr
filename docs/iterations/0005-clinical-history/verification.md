# Phase 2B verification v1.0 — 2026-11-09

## Preparation and data preservation

Local Phase 2A branch and GitHub base matched approved eff5a2b94891e5deae8304ac2e9036c6dc8eaf43, with clean index/worktree. Issue #9 and phase/0005-clinical-history were created. No merge was performed. Original prompts, prior iteration records, Chinese source documents and English translations remain unchanged.

A consistent SQLite online backup was written under ignored `.venv/backups/phase2b/` before schema changes. Read-only integrity and foreign-key checks passed. Baseline contained 31 patients, four appointments, 59 patient audit rows, seven appointment event rows, one provider serialization row, and zero saved encounters, SOAP notes or clinical events. All pre-existing table rows were snapshotted for comparison, including auth/session data. Automated/browser tests left the original database file hash unchanged.

`python manage.py migrate --noinput` applied history.0001_initial only, creating eight new history domain tables and a partial uniqueness constraint for primary encounter diagnoses. No existing application tables or data were rewritten. All pre-existing rows were found unchanged afterward; patient, scheduling and clinical tables matched exactly. New auth permissions/content types are additive. Integrity returned ok and foreign_key_check returned no violations. Thirty-six existing requirements/iteration files and the six source-manifest hashes were verified unchanged.

There were no local signed notes to migrate; signed-note preservation is additionally covered with synthetic signed-note fixtures in regression tests. No reset, reseed, record deletion, password change or C-drive backup modification occurred. The database file changes for schema additions; unchanged whole-file hashes are not claimed across migration. Its post-migration hash is checked again before publication.

## Local automated results

- `python manage.py check`: passed, no issues.
- `python manage.py makemigrations --check --dry-run`: passed, no changes detected.
- `python manage.py test`: passed **126 tests**, including the previous 99 and 27 Phase 2B tests.
- Coverage includes four medical-history categories, source/authorship, edit/review history, cleared reviews, problem resolution/inactivation, medication states/dates, all four allergy assessments and contradictory-state rejection, clinical/verification validation, model/form errors, stale POSTs, primary/secondary diagnoses, database primary uniqueness, foreign problem rejection, completed encounter protection, role/direct-URL checks, forged context, CSRF, escaping, audit rollback and unchanged signed SOAP content.
- Three two-thread transaction tests cover competing edits, allergy creation versus no-known assessment, and diagnosis editing versus encounter completion. SQLite busy responses are retryable conflicts, including contention during initial service reads. These are focused concurrency checks, not load testing or PostgreSQL verification.
- `python manage.py test careflow.history.browser_tests careflow.clinical.browser_tests careflow.scheduling.browser_tests careflow.patients.browser_tests`: passed **four Chromium workflows** on isolated test databases. The new workflow exercises history creation/edit/review, problem creation, allergy no-known-to-documented change, documented medication statement, primary diagnosis linked to a patient problem, chart timeline and narrow viewport.
- Desktop (1440 px) and mobile (390 px) screenshots were visually inspected. No whole-page horizontal overflow was observed in the new workflow. Screenshots stay ignored under `.venv/phase2b-screenshots/`.
- Git whitespace, documentation links, staged-file scope, historical hashes and local database preservation are checked before publication.

## Resolved development findings

Initial form tests exposed date validation attempting to dereference an excluded author relation during ModelForm construction. Restricting the loop to date fields resolved the issue. The browser test exposed an existing encounter template failing on missing check-in actor provenance; explicit fallback text and a regression test resolved it without modifying stored provenance. Browser locators/navigation waits were made explicit. These were developer findings, not user UAT reports.

## CI and acceptance boundaries

The stacked PR must target phase/0004-physician-workspace. The [push run](https://github.com/KateK77/careflow-ehr/actions/runs/42722660536) and [PR run](https://github.com/KateK77/careflow-ehr/actions/runs/42722722654) passed for [implementation commit bd44d22e](https://github.com/KateK77/careflow-ehr/commit/bd44d22e3942fd36f5431efe95a978b55436d226), including all 126 tests, system checks and migration consistency. The evidence-only follow-up uses the same workflow; latest checks are linked from [stacked PR #10](https://github.com/KateK77/careflow-ehr/pull/10). CI runs system checks, migration consistency and the default regression suite; optional Chromium dependencies are local only.

Neither Phase 2A nor Phase 2B has passed manual UAT. The [acceptance guide](acceptance.md) remains pending. No claim is made for comprehensive security testing, database-operator immutability, real clinical terminology, automated medication/allergy safety checking, production concurrency, deployment or clinical readiness.

## UAT follow-up verification v1.0 — 2026-11-09

The user-reported 20 manual passes are listed in [the follow-up](uat-followup.md); they do not replace automated or security verification. Shared changes were inherited by a normal parent-branch merge from [Phase 2A commit 6490841](https://github.com/KateK77/careflow-ehr/commit/6490841ab18e67b14c9409552a619f1279f1fcf0), preserving history.

- Django system check passed; migration consistency: no changes detected.
- Complete default suite: **133 tests passed**. Four focused tests cover malformed/extended/historical dates, retained allergy-conflict input, friendly duplicate-primary errors and unchanged database constraint, resolved linked-problem status, rejected same-version review replay and permitted fresh re-review.
- Five local Chromium workflows passed: shared date/responsive/submit guard, clinical history with allergy conflict and duplicate-primary feedback, physician SOAP, scheduling and patient registration. A wrong CSS selector in the new browser assertion was corrected before the successful rerun.
- No schema migration or local database write. Before/after whole-file SQLite hash and available immutable source/prompt bytes matched; final integrated preservation is also checked on Phase 3A. Tests use disposable synthetic test databases.
- Phase 2A Push and PR CI passed: [Push](https://github.com/KateK77/careflow-ehr/actions/runs/42741609207), [PR](https://github.com/KateK77/careflow-ehr/actions/runs/42741615233). Phase 2B actual HEAD checks and resulting commit are linked in [PR #10](https://github.com/KateK77/careflow-ehr/pull/10). Local results are not described as GitHub results.
- UI changes still require user retesting. No comprehensive security or database-level audit immutability claim.

## Documentation-only retest verification v1.0

[User-reported retest results](uat-retest.md) are distinct from automated results. The prior passing manual observations remain preserved; targeted passes have the stated date/viewport limitations. No additional malformed-date cases, nursing retests or comprehensive security testing are claimed.

Current owner-branch local verification: Django system check passed; migration consistency reported no changes; **133 default regression tests passed** using isolated synthetic test databases. Documentation whitespace, relative links and staged documentation-only scope passed. The local SQLite whole-file hash and available original historical source/prompt bytes matched a fresh pre-task baseline. No migration, reseed, signed-note modification or application code change occurred. Prior Chromium results are cited as historical evidence and were not rerun for this documentation-only change.

Actual latest documentation HEAD Push/PR Actions results and commit links are verified after publication and recorded on [PR #10](https://github.com/KateK77/careflow-ehr/pull/10). Local test results are not substituted for GitHub results. All three stacked PRs remain open and require separate merge approval.
