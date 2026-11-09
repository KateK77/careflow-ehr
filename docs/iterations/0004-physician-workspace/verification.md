# Verification — Phase 2A

## Preparation and local database

On 2026-11-09, local main, origin/main and GitHub main matched `9e04a80498303d588972394c90eb35028d766228`; index and worktree were clean. Created Issue #7 and the dedicated branch. Preserved the approved prompt byte-for-byte and retained historical Chinese originals and English translations.

Before migration, a read-only SQLite integrity check returned ok. A consistent online backup was saved locally under `.venv/backups/phase2a/` (ignored by Git), together with a row baseline. Baseline contained 31 patients and four appointments. `python manage.py migrate --noinput` applied only clinical.0001_initial and clinical.0002_alter_note_assessment_alter_note_objective_and_more. All pre-existing table rows were compared against the baseline and retained; patient/scheduling tables matched exactly. Post-migration integrity returned ok and foreign_key_check returned no violations. The post-migration database hash remained unchanged through all subsequent tests. No reset, reseed, deletion or C-drive backup modification occurred. The database file necessarily changes when adding schema; unchanged-file hashes are not claimed.

Historical requirements and previous iteration records (27 tracked files) were compared with main and remained unchanged. The original prompt was copied without rewriting it.

## Automated verification

- `python manage.py check`: passed, no issues.
- `python manage.py makemigrations --check --dry-run`: passed, no changes detected.
- `python manage.py test`: passed 95 tests: all 66 previous tests plus 29 new clinical tests.
- Coverage includes role/ownership GET/POST boundaries, scoped worklists and charts, explicit encounter start, appointment provenance preservation, unique encounter constraints, a two-thread duplicate-start test, invalid/stale transitions, draft create/reopen/edit, synthetic confirmation and text limits, signing confirmation/completeness/versioning, signed-note save protection, encounter completion, nested URL isolation, forged context, audit rollback, CSRF and HTML escaping.
- Optional Chromium checks: the new physician workflow passed after fixture/locator setup corrections. The existing patient and scheduling workflows also passed. The final combined command `python manage.py test careflow.clinical.browser_tests careflow.scheduling.browser_tests careflow.patients.browser_tests` passed all three workflows.
- Desktop (1440 px) and mobile (390 px) screenshots were inspected. No whole-document horizontal overflow was observed in the clinical workflow. Local screenshots stay ignored under `.venv/phase2a-screenshots/`.

A failing length-limit service test exposed missing TextField validators; explicit MaxLengthValidator rules corrected it. Browser setup initially used the sandbox's empty browser cache; pointing PLAYWRIGHT_BROWSERS_PATH to the existing ignored `.venv/browsers` fixed launch. The new browser locator was corrected to accept Django's label colon. These resolved test/setup failures are not outstanding application defects.

## Evidence boundaries

These are developer-run automated results, not user-reported manual acceptance. No comprehensive security assessment, database-operator resistance, load test, production concurrency certification or full accessibility audit was performed. SQLite service serialization and targeted two-thread tests do not replace PostgreSQL constraints or load testing. Synthetic-content confirmation is a user assertion, not automated PHI detection. Signing completeness checks do not establish clinical adequacy. Optional browser dependencies are local and not installed by default CI.

## GitHub Actions

Push and PR results will be linked after publication. CI executes Django checks, all default tests and migration consistency. User manual acceptance remains pending; PR must remain open.
