# Verification — CareFlow EHR 2.0 website v1.0

Date: 2026-11-14, America/Chicago. All results here are automated or developer-observed evidence. V2 manual acceptance and new live native CUA acceptance are not claimed.

## Local checks

| Check | Observed result |
| --- | --- |
| Django system check | PASS, zero issues |
| Migration consistency (`makemigrations --check --dry-run`) | PASS, no changes detected |
| Full Django regression suite | PASS, 492 tests in 74.462 seconds |
| New v2 Django tests | 11 passed, included in 492 |
| Complete Chromium module selection | PASS, 29 workflows in 85.996 seconds; zero failures/skips |
| Offline CUA suite | PASS, 21 tests in 55.400 seconds |
| Static discovery and browser CSS requests | PASS; `core/v2.css` resolved and loaded successfully |
| Preview launcher `--prepare-only` | PASS with a deliberately inherited original database path overridden by a NEW unique preview path |
| New preview fixture assertions | 30 synthetic patients, 11 accounts, two separate patient links, three appointments and three creation audits |
| New preview SQLite checks | Integrity `ok`; no foreign-key violations |
| Documentation links | PASS; 32 local links, including screenshot navigation |
| Git whitespace | PASS |
| Paid API calls | None |

The prior 481-test baseline also passed before adding 11 new v2 checks. Existing regression tests were retained; only expected stylesheet/skip-link assertions were updated for the actual redesign.

## What is tested

Dashboard tests verify physician-scoped appointments, other-role denials, anonymous redirect, actual counts by clinic-local date and status, stable first-eight sorting with complete totals, and no dashboard writes. Patient tests verify the real appointment-request route and the continued presence of all registration fields.

Preview allocator tests ensure each call yields an absent database in a new directory, ignoring an inherited database path and preserving existing bytes. Preparation independently verified fixture counts and integrity.

Chromium exercises portal entry, staff and patient login, directory navigation, registration/editing, appointment review and confirmation, clinical/history/nursing/lab/medication/pharmacy/MAR/portal/billing/imaging/hospital workflows, selected permission denials and responsive layouts. V2-specific keyboard coverage requires explicit Unknown selection and synthetic confirmation, checks native valueMissing before confirmation, and verifies the resulting patient and creation audit after browser shutdown.

Offline CUA includes screenshot lifecycle/retry, sanitized diagnostics, API mocks, budgets, protected actions, independent registration/appointment/check-in and combined Front Desk rehearsals. These scripted offline rehearsals are not model-driven live acceptance.

## Verification issue corrected

The first new keyboard browser test attempted a synchronous Django ORM assertion while Playwright's event loop was active, producing `SynchronousOnlyOperation`. The test now checks the visible required-checkbox validity at that point and performs independent patient/audit assertions after Playwright closes. Existing application code, asynchronous safety and required confirmation were not weakened.

A later full browser run exposed a pre-existing MAR fixture timing race: the browser formatted a just-created dispense timestamp to whole seconds, making it earlier than the service's fractional-second lower bound. The service correctly rejected it. Both MAR browser workflows now allow 1.05 seconds of test time to elapse after fixture dispensing before entering a whole-second event time. No application validation, clinical data or service clock was modified.

## Reproduce

Use the existing virtual environments, set `PYTHONDONTWRITEBYTECODE=1`, and point `CAREFLOW_DB_PATH` at a NEW QA location before management checks.

- `.venv/Scripts/python.exe manage.py check`
- `.venv/Scripts/python.exe manage.py makemigrations --check --dry-run`
- `.venv/Scripts/python.exe manage.py test --noinput`
- Generate all browser modules using `rg --files careflow -g '*browser_tests.py'`, convert paths to dotted modules and pass all to `manage.py test`.
- `tools/cua/.venv/Scripts/python.exe -m unittest discover -s tools/cua -p 'test_*.py' -v`
- `git diff --check`

Application Chromium uses its matching revision 1248 under `.venv/browsers`; the CUA virtual environment uses its matching revision 1228 from the user's Playwright cache. Browser tests create isolated test databases. CUA fixtures create fresh temporary databases.

Local full logs: `.venv/uat-followup/v2-website-01/`. Screenshots committed below contain synthetic fixtures only and no login credentials.

## Preservation

Before/after SHA-256 comparison: **52/52 existing database files unchanged**, **182/182 historical documentation files unchanged**, and the pre-existing untracked `debug.log` unchanged. The manifest covers 235 protected files. No original or existing preview SQLite file was opened for migrations, seeding or tests.

The current root README receives an additive v2 startup section; its exact preimage is preserved under [history](history/README.before-v2.md). All other new records are additive. No model/migration, clinical service, authentication or role definition was edited. Existing signed-note/clinical preservation scenarios pass in the regression suite.

Main and all parent branch references are preserved; only the new feature branch is published. No merge, release, deployment, paid API test or database reset was performed.

## CI and remaining limits

CI executes Django checks, default regression tests and migration consistency. Chromium and CUA are local results and are not misrepresented as GitHub jobs. [Implementation PR CI](https://github.com/KateK77/careflow-ehr/actions/runs/43677681983) passed for commit 6d42c82e594cd1551e09e040c4f992b15775529e: setup, Django checks, regression tests and migration consistency all succeeded. The subsequent traceability-only commit receives its own CI run; the final result is shown on [PR #59](https://github.com/KateK77/careflow-ehr/pull/59).

Selected layout widths are 1440/1280, 700 where applicable, 390 and 320. This is not comprehensive accessibility, browser/device, security, concurrency or production certification. Existing deferred business-policy enhancements remain deferred. The new preview starts with basic fictional registration/scheduling fixtures; advanced clinical scenarios must be exercised through existing workflows.

Git reference verification: GitHub main remains `a9e0913b626b88908ad2ca3041d2ec9497ba7d15`; local main remains `00c624553cc265e6275a9d2750ab0041a7e6d97f`. The parent branch remains `86d307540386fa587e962430b2dfbb0eb76a5f11`. They were deliberately not synchronized or merged during this feature task.
