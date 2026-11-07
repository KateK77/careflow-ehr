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
