# Verification — Phase 1B

## Local automated results

- Django system checks passed with no issues.
- `python manage.py makemigrations --check --dry-run` reported no missing migrations.
- `python manage.py test` passed 66 tests, including the existing 34 Phase 1A/regression tests and 32 scheduling tests.
- Scheduling coverage includes review/confirmation, tampered reviews, persistence, physician calendars and scopes, rescheduling, cancellation, check-in, duplicate/invalid transitions, overlap/adjacency, invalid dates/providers/durations, permissions, audit rollback, stale updates, CSRF, cross-midnight display and DST input/elapsed-duration behavior.
- A two-thread SQLite transaction test produced one accepted booking and one conflict, with one appointment and one event. This is focused concurrency coverage, not a load or PostgreSQL test.
- `python manage.py test careflow.scheduling.browser_tests careflow.patients.browser_tests` passed both Chromium workflows. The new browser workflow exercised actual login, patient search, creation review, confirmation, rescheduling, cancellation, check-in and desktop/mobile presentation. The earlier patient registration browser regression also passed.
- Browser test harness issues with ORM queries inside Playwright's running event loop and fixture-dependent calendar counts were corrected. Final reruns passed.
- Desktop and mobile screenshots were visually inspected. The page fits a 390-pixel viewport, with calendar/table overflow contained in scrollable regions.

## Local migration and data preservation

Applied scheduling.0001_initial to the existing local SQLite database. A read-only digest verified that all 31 existing patient rows retained the same values. Foreign-key consistency checks passed. An ignored local SQLite backup was taken before migration. No reset or patient reseed was performed.

## GitHub Actions

CI results will be recorded after publication. The existing workflow runs application requirements, the Django check and default Django test discovery. Optional browser tooling remains local.

## Acceptance and limits

Hands-on user acceptance is pending. No claim is made for production deployment, PostgreSQL exclusion constraints, stress testing, configurable clinician availability or comprehensive security assessment. The access and time policies are documented in ADR 0003. The branch must remain unmerged until approved.
