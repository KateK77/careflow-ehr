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

The [push run](https://github.com/KateK77/careflow-ehr/actions/runs/42574506148) and [PR run](https://github.com/KateK77/careflow-ehr/actions/runs/42574510773) passed for [implementation commit 9b8f884](https://github.com/KateK77/careflow-ehr/commit/9b8f884bef583aa338d490eb9cf4a3b9785a90b6), executing the Django system check and all 66 default tests. Later evidence-only commits use the same workflow, with current results linked from [PR #6](https://github.com/KateK77/careflow-ehr/pull/6). The existing workflow runs application requirements, the Django check and default Django test discovery. Optional browser tooling remains local.

## Acceptance and limits

The user reported all eleven manual acceptance checks passed on 2026-11-09, with no blocking functional defects. The [feedback matrix](feedback.md) records UAT-1B-01–UAT-1B-11. No claim is made for production deployment, PostgreSQL exclusion constraints, stress testing, configurable clinician availability or comprehensive security assessment. The access and time policies are documented in ADR 0003. The branch must remain unmerged until approved.

## Manual evidence and its boundaries

The manual report covers confirmed creation, daily-calendar visibility, rescheduling and time updates, sequential overlap rejection and absence of the rejected booking, cancellation history, rebooking a released slot, check-in actor/time/history, persistence after refresh, Physician own-appointment visibility with management controls absent, and a direct edit-URL denial.

These observations were supplied by the user. They do not add unreported manual checks for weekly calendars, Nurse/Administrator/FrontDesk role combinations, cross-physician detail isolation, direct cancellation POST requests, forged requests, CSRF, session expiry, database tampering, load or concurrency. Earlier targeted automated tests cover some of those concerns and remain separately identified above. UI history display does not establish database-level audit immutability, and no comprehensive security assessment is claimed.

The four Phase 1B backlog groups in feedback.md are future enhancements for evaluation. In particular, configurable appointment types, working hours, leave and an early check-in window are not approved behavior changes in this documentation update.

## Documentation follow-up verification

Documentation checks passed for all eleven reported outcomes, four backlog groups, English text, ten relative links, staged scope and whitespace. SHA-256 checks confirmed preservation of all 88 existing tracked files outside the three updated acceptance documents and an unchanged local SQLite file. Local application/browser tests were not rerun and no database commands were executed. Latest GitHub CI evidence is recorded after publication.
