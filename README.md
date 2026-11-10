# CareFlow EHR

CareFlow EHR is an independently developed educational and research prototype for electronic health records and hospital workflows. Its scope is inspired by workflows found in enterprise EHRs such as Epic. It uses original code and design.

**Use only synthetic data.** Keep real patient records, credentials, and production exports out of the application, repository, and logs. The scaffold is for local development and research.

## Run locally

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

Open [staff sign in](http://127.0.0.1:8000/login/). This computer has 30 synthetic patients and the four accounts below, initialized with a generated bootstrap password that was not saved or disclosed. Use `changepassword` locally to choose the password for each account you want to test. Passwords must contain at least 12 characters and meet Django's common/numeric-password checks.

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

The local database, virtual environment and passwords stay outside Git. This is a DEBUG-only, single-clinic educational application. Time is stored in UTC and displayed in `CAREFLOW_TIME_ZONE` (default `America/Chicago`). Clinical charts, scheduling, portal access and deployment hardening are future work.

### Verification

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

An optional Playwright browser test is in `careflow/patients/browser_tests.py`. It uses an isolated Django test database. Install `playwright` and Chromium in a development environment, then run `python manage.py test careflow.patients.browser_tests`. Browser tooling is not an application dependency and is not installed by CI.

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

See the [complete startup and manual acceptance guide](docs/iterations/0004-physician-workspace/acceptance.md), [access/state policy](docs/decisions/0004-encounters-and-soap.md) and [verification record](docs/iterations/0004-physician-workspace/verification.md). One SOAP note per encounter, explicit draft saves and no addenda/reopening are provided. Signed content is protected through supported application paths, not against database administrators. No real clinical use is supported. Phase 2A is awaiting manual acceptance.
