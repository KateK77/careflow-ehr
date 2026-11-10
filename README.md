# CareFlow EHR

CareFlow EHR is an independently developed educational and research prototype for electronic health records and hospital workflows. Its scope is inspired by workflows found in enterprise EHRs such as Epic. It uses original code and design.

**Use only synthetic data.** Keep real patient records, credentials, and production exports out of the application, repository, and logs. This prototype is for local development and research.

## Current development branch

Phase 3B implementation is approved for automated development; manual UAT is intentionally deferred for consolidated testing. Specimen collection, lab processing, immutable reports/corrections/withdrawals and version-specific review are implemented for review. No production or independent laboratory verification is claimed. See [the current iteration](docs/iterations/0009-lab-review-integration/README.md) and [laboratory architecture decision](docs/decisions/0008-laboratory-processing-and-review.md).

## Merged main baseline (prior closeout)

Phase 2A — Physician Workspace, Phase 2B — Clinical History, and Phase 3A — Nursing Workspace completed their approved local-prototype review and were merged through PRs [#8](https://github.com/KateK77/careflow-ehr/pull/8), [#10](https://github.com/KateK77/careflow-ehr/pull/10), and [#12](https://github.com/KateK77/careflow-ehr/pull/12). The verified integrated baseline is [65a7d3e](https://github.com/KateK77/careflow-ehr/commit/65a7d3e2f01d9af0c99126c340e9f426c954401c), with 164 regression tests, seven local Chromium workflows and merged-main CI passed.

See [current status, evidence and limitations](docs/project-status.md). Earlier pending-acceptance/stacked-PR statements in original iteration records describe their historical delivery state; they are not the current status. The proposed next increment is **Orders & Laboratory Results**, pending separate approval. No new phase identifier or implementation scope is approved by this documentation closeout.

## Run locally

**Integrated Phase 3B feature-branch testing:** 3B-1, 3B-2 and 3B-3 are implemented on stacked branches for review, not merged or manually accepted. Follow the [integrated preview startup and consolidated UAT checklist](docs/iterations/0009-lab-review-integration/acceptance.md). The original local database is deliberately **unmigrated**. Use the separately prepared `.venv/phase3b3-preview.sqlite3` through `CAREFLOW_DB_PATH`; do not run the generic migration/seed commands below against the original database. Clinical pages now integrate laboratory queries and require the migrated preview. Earlier phase instructions below describe their own baseline; they are not instructions to migrate the original database.

Install Python 3.12 or newer and create a virtual environment from the repository root.

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on macOS or Linux. Then run:

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open [the landing page](http://127.0.0.1:8000/). The [health endpoint](http://127.0.0.1:8000/health/) reports process availability.

```sh
python manage.py check
python manage.py test
```

See [architecture](docs/architecture.md) for module boundaries and the [roadmap](docs/roadmap.md) for planned work.

## Phase 1A patient management (Windows)

Run these commands in PowerShell from `D:\AI-Workspace\Personal\careflow-ehr`. A local `.venv` has been prepared on this computer. For a fresh checkout, create the virtual environment and install `requirements.txt` first.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py changepassword frontdesk.demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open [staff sign in](http://127.0.0.1:8000/login/). Local record counts depend on prior synthetic testing. The seed command creates the four accounts below with a locally supplied bootstrap password; no password is published in the repository. Continue using existing local accounts and records. Use `changepassword` only when you need to choose a new local password. Passwords must contain at least 12 characters and meet Django's common/numeric-password checks.

| Username | Role | Patient demographics access |
| --- | --- | --- |
| `administrator.demo` | Administrator | Read, create, edit |
| `frontdesk.demo` | FrontDesk | Read, create, edit |
| `physician.demo` | Physician | Read |
| `nurse.demo` | Nurse | Read |

The dashboard is at `/app/dashboard/`, patients at `/app/patients/`, registration at `/app/patients/new/`, and a record at `/app/patients/<id>/`. Search accepts name, MRN, ISO date of birth and phone. The directory also filters by recorded sex and paginates results. A potential same-name/same-birthday duplicate requires explicit confirmation. An existing MRN is rejected, including case variants. Stale edits return a conflict and require reloading.

### Initialize a fresh synthetic demo

The seed command requires explicit local opt-in and a password provided through the process environment. It preserves existing records and passwords on repeat execution. `.env.example` is reference documentation and is not loaded automatically.

```powershell
$env:CAREFLOW_ALLOW_DEMO_SEED = "1"
$demoSecret = Read-Host "Choose a local demo password" -AsSecureString
$demoCredential = [System.Net.NetworkCredential]::new("", $demoSecret)
try {
    $env:CAREFLOW_DEMO_PASSWORD = $demoCredential.Password
    .\.venv\Scripts\python.exe manage.py seed_synthetic
} finally {
    Remove-Item Env:CAREFLOW_DEMO_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:CAREFLOW_ALLOW_DEMO_SEED -ErrorAction SilentlyContinue
    $demoCredential = $null
    $demoSecret = $null
}
```

The local database, virtual environment and passwords stay outside Git. This is a DEBUG-only, single-clinic educational application. Time is stored in UTC and displayed in `CAREFLOW_TIME_ZONE` (default `America/Chicago`). Scheduling, clinical charts, SOAP documentation, clinical history and nursing workflows are implemented. Patient portal access and deployment hardening remain future work. Do not reseed or reset an existing database as part of routine startup.

### Verification

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Optional Playwright tests use isolated Django test databases. Install `playwright` and Chromium in a development environment, then run:

```sh
python manage.py test careflow.core.ui_browser_tests careflow.nursing.integration_browser_tests careflow.nursing.browser_tests careflow.history.browser_tests careflow.clinical.browser_tests careflow.scheduling.browser_tests careflow.patients.browser_tests
```

On this prepared Windows workspace, set `PLAYWRIGHT_BROWSERS_PATH` to `D:\AI-Workspace\Personal\careflow-ehr\.venv\browsers` if using its existing Chromium installation. Browser tooling is not an application dependency and is not installed by CI.

## Phase 1B scheduling and check-in

Use the existing local staff accounts and passwords. Administrator and FrontDesk may manage appointments. Physician-only staff read their own appointments, and Nurses read the single-clinic schedule.

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

1. Sign in at [staff login](http://127.0.0.1:8000/login/) as `frontdesk.demo` or `administrator.demo`.
2. Open Schedule, choose a date and physician, then switch between Day and Week views.
3. Choose New appointment. Search by patient name/MRN or start from Schedule appointment on an existing patient's demographic page.
4. Select the patient and active physician, enter a future clinic-local start, duration, type and optional synthetic reason. Choose Review appointment, then Confirm appointment.
5. Verify the booking in its detail page, patient context and physician calendar. Use Reschedule / edit to change it through the same review flow.
6. Attempt an overlapping booking for the same physician to see a conflict. Adjacent bookings and different physicians are permitted. Cancel with a reason to release the slot.
7. For check-in, create an appointment with a future start later on the clinic's current date. Open Patient check-in, search the patient's MRN, open the appointment and choose Mark Arrived. The status, actor and timestamp persist on refresh.
8. Sign in as `physician.demo` to verify own-schedule read access and direct-URL write denials. The existing `changepassword` command can set a local password if needed.

Pages are `/app/schedule/`, `/app/appointments/new/`, `/app/appointments/<id>/` and `/app/check-in/`. Clinic time zone defaults to America/Chicago and may be set with `CAREFLOW_TIME_ZONE`. Store UTC timestamps and display clinic-local labels. Ambiguous/nonexistent local DST input is rejected. Cross-midnight bookings appear on both dates.

Creation and edits require a review token valid for ten minutes. Rescheduling requires the current version and a scheduled state. Check-in is limited to the appointment's local date. Cancellation/no-show require reasons. No-show can be recorded after the start has been reached. Cancelled/no_show are terminal. See [ADR 0003](docs/decisions/0003-scheduling-and-checkin.md) for the complete transition and concurrency policy.

The new migration creates scheduling tables only. The existing patient data and staff passwords are preserved. No appointment seed is required. Current availability is based on active physicians and conflicting reservations, with provider working hours and leave deferred.

Run `python manage.py check`, `python manage.py makemigrations --check --dry-run` and `python manage.py test`. Optional browser checks run with `python manage.py test careflow.scheduling.browser_tests careflow.patients.browser_tests` after installing Playwright/Chromium. The default GitHub workflow runs the Django suite, not the optional browser checks.

## Phase 2A physician workspace and clinical documentation

Run the existing Django application using the commands above; the local additive clinical migrations have been applied. Existing accounts/passwords and data remain. Open [Physician workspace](http://127.0.0.1:8000/app/physician/) as physician.demo. Start an encounter explicitly from an arrived appointment, save/reopen/edit a synthetic SOAP draft, review and confirm signing, then complete the encounter. Administrator/Nurse read clinic clinical records; FrontDesk has no clinical note access.

See the [startup and historical manual checklist](docs/iterations/0004-physician-workspace/acceptance.md), [access/state policy](docs/decisions/0004-encounters-and-soap.md) and [verification record](docs/iterations/0004-physician-workspace/verification.md). One SOAP note per encounter, explicit draft saves and no addenda/reopening are provided. Signed content is protected through supported application paths, not against database administrators. No real clinical use is supported. Phase 2A completed its approved review and was merged in PR #8; [current status](docs/project-status.md) distinguishes reported manual observations from automated coverage.

## Phase 2B longitudinal clinical history

Phase 2B completed its approved review and was merged in PR #10. Continue the same local Django startup; `python manage.py migrate` applies the additive history schema on a fresh checkout (already applied on this computer). Use existing local accounts/passwords, without reseeding. Open the physician chart and use Medical history, Problems, Allergies and Medications; open an encounter for Encounter diagnoses. Treating Physicians maintain records; Nurse/Administrator read access remains and FrontDesk is denied detailed clinical content. Medication records are history statements, never prescriptions.

See the [startup and historical manual checklist](docs/iterations/0005-clinical-history/acceptance.md), [verification](docs/iterations/0005-clinical-history/verification.md), [changed-file report](docs/iterations/0005-clinical-history/changed-files.md) and [state/access policy](docs/decisions/0005-clinical-history.md). Reported workflow checks and targeted retests passed within their documented limits; [the closeout status](docs/project-status.md) supersedes historical pending-merge statements.

## Phase 3A nursing workspace, rooming and vitals

Phase 3A completed its approved review and was merged in PR #12. The additive nursing schema is already applied on this computer; fresh checkouts use the normal migration command. Continue using the existing server, records and passwords. As nurse.demo, open [Nursing workspace](http://127.0.0.1:8000/app/nursing/), filter an arrived synthetic appointment and open Nursing record to document rooming/readiness and vital observations. Flowsheet time columns open record history and permitted corrections. Assigned Physicians review through their charts; Administrator alone is read-only and FrontDesk has no detailed nursing access. Nursing saves do not start encounters.

See the [startup/manual checklist](docs/iterations/0006-nursing-workspace/acceptance.md), [verification](docs/iterations/0006-nursing-workspace/verification.md), [changed files](docs/iterations/0006-nursing-workspace/changed-files.md) and [state/access/input policy](docs/decisions/0006-nursing-rooming-and-vitals.md). Numeric bounds are demo data-entry checks, not clinical interpretation. No real medical use, medication administration or deployment is supported.
