# Verification and acceptance — Phase 1A

## Local automated checks

- `python manage.py check` passed with no issues.
- `python manage.py makemigrations --check --dry-run` reported no missing migrations.
- `python manage.py test` passed 34 tests, including the original 2 smoke tests. Coverage includes four-role read access, create/edit permissions, anonymous and no-role denials, login/logout and external-next protection, patient creation/editing, MRN normalization and database constraints, duplicate confirmation, validation, search/filter/pagination, stale editor conflicts, CSRF, escaping, patient-scoped details, audit rollback and seed idempotency.
- `python manage.py test careflow.patients.browser_tests` passed 1 Chromium test using an isolated test database. It exercised actual browser login, search, creation, editing, logout, and desktop/mobile layouts. Screenshots at 1440 and 390 pixels were visually inspected.
- Browser validation initially exposed selectors that did not match label punctuation and decorative navigation glyphs. Corrected the selectors and hid decorative glyphs from accessible names. The final rerun passed.
- Applied Django auth/contenttypes/sessions and patients migrations to the existing local database without resetting it. Seeded 30 synthetic patients and four demo users using a random bootstrap password that was not saved or disclosed. Users can set their chosen local password with `changepassword`.

## GitHub Actions

The existing workflow installs only application requirements and runs the system check and default Django test discovery. The optional browser test is run locally and is not included in default discovery. The [push run](https://github.com/KateK77/careflow-ehr/actions/runs/42341431350) and [PR run](https://github.com/KateK77/careflow-ehr/actions/runs/42341434174) passed for [implementation commit b6f59b8](https://github.com/KateK77/careflow-ehr/commit/b6f59b8d0932a14637d19ff0c0e1e6173ee71090). Both completed the Django system check and all 34 default tests. Subsequent documentation-only evidence commits are checked on the same workflow, with current results linked from [PR #4](https://github.com/KateK77/careflow-ehr/pull/4).

## Acceptance

Hands-on user acceptance is pending. This branch must remain unmerged until approved. No production credentials, patient data, local database or browser artifacts are included in the commit.

A request to leave a hidden background development server running was rejected by automatic approval review. Browser tests did start and exercise their temporary local server successfully. Start the application manually with the documented runserver command for hands-on acceptance.
