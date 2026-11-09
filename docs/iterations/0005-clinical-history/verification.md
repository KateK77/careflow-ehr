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

The stacked PR must target phase/0004-physician-workspace. Push/PR CI results are checked after publication and linked from the PR and final handoff. CI runs system checks, migration consistency and the default regression suite; optional Chromium dependencies are local only.

Neither Phase 2A nor Phase 2B has passed manual UAT. The [acceptance guide](acceptance.md) remains pending. No claim is made for comprehensive security testing, database-operator immutability, real clinical terminology, automated medication/allergy safety checking, production concurrency, deployment or clinical readiness.
