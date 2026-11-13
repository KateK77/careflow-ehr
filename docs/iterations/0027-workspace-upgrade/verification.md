# Verification — workspace upgrade v1.0

Date: 2026-11-13 (America/Chicago). These are automated observations, not manual UAT or live native CUA acceptance.

## Isolation and baseline

- Parent: PR #55, `214a309f52af642b4c59be85f3bc7ec646766815`.
- Fresh in-memory Django test databases; management checks use new paths beneath `.venv/uat-followup/workspace-upgrade-01/`.
- CUA rehearsals provision and dispose of their own new temporary synthetic database for each scenario.
- No application model, migration, workflow service, auth policy, network/action policy, or native request budget was changed.
- Existing untracked `debug.log` is preserved and excluded from commits.
- Browser runtimes differ: Django Chromium uses the matching 1248 browser in `.venv/browsers`; CUA uses its installed 1228 browser under the user's Playwright cache.

## Commands and local outcomes

Run from the repository root with `PYTHONDONTWRITEBYTECODE=1` and an explicitly isolated `CAREFLOW_DB_PATH`.

| Check | Actual outcome |
| --- | --- |
| `.venv/Scripts/python.exe manage.py check` | PASS; zero issues |
| `.venv/Scripts/python.exe manage.py makemigrations --check --dry-run` | PASS; no changes detected |
| `.venv/Scripts/python.exe manage.py test --noinput` | PASS; 481 tests, 70.345 seconds |
| New `careflow.core.test_workspace_upgrade` cases | 10 passed; included in 481 |
| New `careflow.core.workspace_browser_tests` | 4 passed in the final complete 28-workflow run |
| Complete Chromium module selection | PASS; 28 workflows, 82.652 seconds, zero failures/skips; includes the four new workflows |
| `tools/cua/.venv/Scripts/python.exe -m unittest discover -s tools/cua -p 'test_*.py' -v` | PASS; 21 tests, 48.255 seconds; includes independent registration, appointment, check-in and combined Front Desk rehearsals |
| Final mixed-role label regression | PASS; all 10 targeted Django tests after adding Lab Staff separator coverage |
| Documentation links | PASS; 29 current/new relative links (historical preimages retain original bases) |
| Static discovery for app, landing, workspace, navigation and portal assets | PASS |
| `git diff --check` | PASS |
| Protected database hashes | 50/50 unchanged |
| Existing documentation preservation | Historical files unchanged; two current-status documents updated with preimages archived |
| Paid API requests | None |

The Chromium module list is generated with `rg --files careflow -g '*browser_tests.py'` and passed as dotted modules to Django test. Browser tests are explicitly selected because the default Django test pattern does not discover these filenames.

Local logs and additional screenshots: `.venv/uat-followup/workspace-upgrade-01/`. Do not publish raw logs that may include synthetic session tokens from assertion failures.

## Investigated verification failures

- Initial dashboard rewrite omitted the existing laboratory-catalog shortcut; restored it and reran the full Django suite successfully.
- A new portal assertion incorrectly expected an MRN on a page that displays the linked patient's name. Corrected the assertion to the actual authorized UI; retained direct staff-route denial and nondisclosure checks.
- Initial sandbox browser startup stalled; stopped it. The first elevated launch used a browser cache incompatible with the application's installed Playwright. Selected the already-installed matching workspace browser; no package downloads or dependencies changed.
- Historical patient and nursing browser tests still targeted the Sex dropdown replaced upstream by radio controls. Updated selectors to the accessible Unknown radio. Scheduling search now explicitly opens the existing optional disclosure.
- CUA visible check-in assertions targeted the raw `appointment_arrive` identifier. Updated only visible UI expectations to Patient checked in. Independent database checks still assert exact stored audit actions, actor, order and linkage.
- Screenshot inspection found narrow MRNs wrapping character by character. Gave the patient table a minimum width and preserved unbroken MRN tags inside the scroll region.
- One full browser run measured a newly navigated mobile document before final layout (337 vs 320 pixels); subsequent isolated run passed. Added bounded document-load and two-animation-frame settling before layout assertions, without network-idle waits or relaxed bounds.

## Observed browser behavior

At 1280x800, Patient, Physician, Appointment start and Review appointment are all within the initial viewport. Optional search is collapsed by default and visibly separate. A searched query reopens it to expose active filtering.

Review and confirmation create one Scheduled appointment linked to the expected patient and physician with one appointment_create audit and the FrontDesk actor. Existing CUA rehearsals separately verify Arrived, check-in actor and ordered audit history.

Directory and patient portal layouts are checked at 1280, 700 where applicable, 390 and 320 pixels. Patient identifiers retain readable horizontal layout. Lab Staff brand returns to its permitted worklist. Portal direct access to a staff patient URL returns 403 without disclosing that patient's MRN.

No claim of comprehensive WCAG conformance, every browser/zoom combination, production security or concurrency validation is made.

## CI and acceptance boundary

GitHub CI runs Django checks, default tests and migration consistency; it does not run Chromium or the offline CUA suite. The [implementation PR CI run](https://github.com/KateK77/careflow-ehr/actions/runs/43528162249) passed for commit `81cbc2b2e9b97513c5adf539912fdcd29ad735a2`: environment setup, Django checks, tests and migration consistency all succeeded. The subsequent traceability-only commit receives a separate run; its final status is recorded on [PR #57](https://github.com/KateK77/careflow-ehr/pull/57).

Manual acceptance of this upgrade is pending. Previously completed manual UAT remains historical evidence; no duplicate retesting is requested for already accepted unchanged scenarios. All paid native retries remain subject to separate approval.

## Reproduce and review safely

Use the existing development virtual environment. Set `CAREFLOW_DB_PATH` to a newly created temporary location before checks or testing. Never unset it and then migrate, seed or run a preview against the default database.

For a user-operated preview, create a uniquely named QA directory under `.venv/uat-followup`, set `CAREFLOW_DB_PATH` to a new file in that directory, and run the existing migration/demo provisioning commands only against that new file. Supply the synthetic demo password through the documented environment variable, never a committed file. Start Django on an unused loopback port and open the root landing page.

The short manual checklist is in [feedback](feedback.md). No production or external service setup is needed.
