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

The user reported on 2026-11-08 that all ten listed manual acceptance checks passed and no blocking functional defects were identified. See the UAT-01–UAT-10 matrix in [feedback](feedback.md). PR #4 remains open pending a separate merge decision. The historical automated evidence above records the earlier implementation checks.

A request to leave a hidden background development server running was rejected by automatic approval review. Browser tests did start and exercise their temporary local server successfully. Start the application manually with the documented runserver command for hands-on acceptance.

## Evidence boundaries — acceptance follow-up

| Evidence | Source and scope |
| --- | --- |
| Manual observations | User report dated 2026-11-08, UAT-01–UAT-10 in feedback.md. The documentation author did not rerun these manual checks. |
| Existing automated evidence | The earlier 34 Django tests and separate Chromium workflow recorded above. Automated coverage is distinct from the user's manual observations. |
| Documentation follow-up | Historical-file hashes, documentation links, acceptance-matrix completeness and staged diff checks. Latest GitHub CI evidence is added after publication. |

Successful UI display of audit events does not establish database-level audit immutability or tamper resistance. Physician direct-URL denials demonstrate those tested manual routes. They do not establish protection against every HTTP method, crafted request or privilege-escalation attempt. FrontDesk and Nurse manual checks, patient-account isolation, session expiry, login throttling and broader security assessment were not reported as part of this manual acceptance. Some protections have targeted automated tests, as listed above, but no comprehensive security assessment is claimed.

The five user-supplied UI/UX groups UX-01–UX-05 are future, non-blocking enhancements recorded in feedback.md. Clinical sections and new encounter/status data remain future scope. No UI/UX implementation is included in this follow-up.

## Documentation follow-up checks — 2026-11-08

The documentation check verified all 10 user-reported acceptance rows, all five future UX groups, English text and nine relative links. SHA-256 checks confirmed that the 66 existing tracked files outside the three updated acceptance documents were preserved, including application code, historical sources and the English language policy. The staged diff is limited to README.md, feedback.md, verification.md and the new verbatim acceptance-request.md within this iteration directory. Whitespace checks passed.

Local application tests were not rerun for this documentation-only change. Earlier automated results remain identified as historical evidence, and the GitHub workflow will execute the existing application checks on the published commit.
