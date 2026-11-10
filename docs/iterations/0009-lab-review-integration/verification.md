# Verification — Phase 3B-3

## Automated evidence

- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: no changes.
- `python manage.py test --noinput`: **243 tests passed** (213 parent plus 30 new tests: review/security/races, migration backfill, and safe provisioning).
- Complete ten-module Chromium run: integrated lab lifecycle, 3B-2 processing, 3B-1 orders, core UI, nursing integration, nursing, history, clinical, scheduling and patients. The final complete ten-workflow rerun passed. Its mobile quarantine view was visually inspected; no previous payload or comment appeared. Actual GitHub run links are recorded in the PR/completion report. Chromium is local, not currently a hosted CI job.
- Integrated Chromium covers Physician UI draft/submit, Nurse identity-confirmed collection, Lab Staff claim/receipt/draft/preview/finalization, initial acknowledgement, correction and fresh acknowledgement, ineligible covering reassignment, quarantine withdrawal and notice acknowledgement. First publication occurs after encounter completion. SOAP signing/completion and identity deactivation are explicit backend fixture preparation, not claimed as browser/manual SOAP/account administration.
- Browser checks include unauthorized chart access by covering Physician, withheld values/comments/reasons, zero JavaScript errors and responsive 1440/700/390 widths. Other direct role/context denials, stale versions, duplicate keys/commands, rollback and concurrency are regression evidence, not invented browser steps.
- Threaded SQLite tests cover laboratory claim, receipt/cancellation, publication, duplicate withdrawal, correction/withdrawal, acknowledgement/withdrawal and simultaneous reassignment. Only one aggregate version wins. Application tests do not certify production cross-service identity races or PostgreSQL behavior.

## Migration and preservation

`labs.0003` adds immutable review assignments/reviews, pointers/events and corrected/withdrawn contracts. `0004` records system-provenance responsibility backfill for existing submitted/fulfilled orders, with null acting actor/command UUID and no acknowledgement. `0005` adds post-backfill responsibility/publication/provenance constraints. Only lab schema/data is changed. No existing clinical schema or signed-note mutation occurs.

A MigrationExecutor test uses a disposable database containing a published report and signed SOAP, moves through the parent 3B-2 schema and upgrades. Exact stored JSON bytes, report content and signed rows remain; ineligible original Physician remains the unresolved initial assignee, with source=migration_backfill. Draft/cancelled orders receive no fabricated assignment or review.

Fresh `.venv/phase3b3-preview.sqlite3` was cloned from the verified original consistent backup and explicitly migrated. All pre-existing rows/counts remain; only additive Django migration/content-type/permission metadata is allowed. SQLite integrity and FK checks passed. Original `db.sqlite3`, consistent backup and 3B-1 preview match baseline SHA-256. 3B-2 preview remains at its own migration boundary and is not migrated in place. All historical tracked documentation matches preserved hashes. No real patient data, credentials, databases, caches or screenshots are staged.

Original inventory retained: 31 patients, 5 appointments, 2 encounters, 1 SOAP note, 12 history events, 4 nursing events and 157 patient audit events. No default-database migration/seed, clinical account reset, C-drive backup write, merge, force push, branch deletion, deployment or release was performed.

## Unperformed verification / limits

Manual user acceptance is deferred, not completed. No independent-production laboratory verification, comprehensive security audit, database-operator tamper resistance, clinical interpretation, external interface, production load or real-data testing is claimed. Supported application publication/review/assignment history cannot be edited/deleted, but direct SQL/bulk ORM is outside that guarantee. See acceptance.md for remaining human checks.
