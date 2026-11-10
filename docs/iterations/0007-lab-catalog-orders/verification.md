# Verification — Phase 3B-1

## Preparation and migration safety

Verified clean main/local origin at `56ea8b332525926b02759b2afefa93166bd52d31`; approved reference bea741de88fd0c719eb4ed39cf70ec7fd2959f3b remained on open/unmerged design PR #16. Created implementation Issue #17 and feature branch from main, without merging the design branch.

Inventoried 28 original SQLite tables and 21 applied migrations. Read-only integrity/FK checks passed. A consistent online backup `.venv/backups/phase3b1/before.sqlite3` was verified for integrity, foreign keys and every table count. Snapshot includes 31 patients, five appointments, two encounters, one SOAP note, 12 history events, four nursing events and 157 patient audit rows, plus all other existing tables.

Generated `labs.0001_initial` and applied it only in disposable test databases and the separately created `.venv/phase3b1-preview.sqlite3` clone. Its plan creates four lab tables and new-lab-only fields/indexes/constraints; no prior business table alteration. Preview verification found every old row unchanged, integrity ok and no FK violations; only new lab tables and expected additive Django migration/content-type/permission metadata were added. No catalog/clinical seed or password change occurred.

**Original db.sqlite3 was not migrated, reset, reseeded, replaced or deleted.** Its whole-file hash, every original table count, integrity/FK and all original documentation hashes are checked throughout and before publication. The C-drive backup is untouched.

## Local automated evidence

Final local results: `python manage.py check` passed with no issues; `python manage.py makemigrations --check --dry-run` reported no changes; `python manage.py test --noinput` passed **194 tests** (the prior 164 plus 30 lab regression/concurrency cases). New coverage includes catalog schema/version/activation/roles, immutable definitions, draft persistence/context, previews/tokens, pending provenance, repeat warnings, durable replay, stale/terminal states, current/inactive role checks, signed-note/provenance preservation, rollback and competing submits/edits/cancellation/completion.

The combined optional browser command passed **all eight Chromium workflows**, including all seven existing browser modules. The new workflow exercises actual Administrator catalog creation/activation, Physician draft/edit/review/submit/replay/repeat/cancel/history, narrow widths, completed-encounter read, Nurse direct-edit denial and FrontDesk denial. Its final completion setup uses existing backend SOAP/encounter services on the isolated test database, not a claimed user/browser signing action. No old tests were changed to conceal regressions. The 390px laboratory-history screenshot was inspected; full values remain accessible through contained horizontal scrolling. Screenshots stay ignored under `.venv/phase3b1-screenshots/`.

Development harness corrections: JSON initial rendering uses a list rather than an encoded JSON string; browser ORM assertions/setup were moved outside Playwright's async context or to a worker; direct Nurse edit denial is 403 for a visible submitted object, and the browser returns to a staff page before logout from the plain denial page. The new uniqueness test supplies a matching audit patient so it reaches the DB constraint. These are recorded as test/setup corrections, not fabricated user acceptance.

## Publication and limitations

Documentation links, changed-file scope, whitespace and migration shape are checked before commit. Exact commit and Push/PR CI results are recorded on the implementation PR linked from [Issue #17](https://github.com/KateK77/careflow-ehr/issues/17). CI runs the default regression suite, system checks and migration consistency; Chromium is separate local evidence. No manual UAT has been supplied. Keep both design and implementation PRs unmerged, and do not start 3B-2/3B-3.
