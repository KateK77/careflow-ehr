# CareFlow EHR

**An end-to-end electronic health record and hospital-workflow prototype for local education, research, and software engineering.** Built independently with Django and server-rendered templates, using workflow concepts familiar from enterprise EHRs. This project is not affiliated with Epic or any EHR vendor.

> **SYNTHETIC DATA ONLY — NOT FOR CLINICAL USE.** No real patient data, medical treatment, payer transactions, or production deployment. The development settings use `DEBUG=True` and a development secret. Hosted or clinical use requires a separate security, privacy, architecture, and regulatory review.

## v1.0 release-candidate status

Phases **0–4B are merged into `main`**. Phases **5–8 are implemented, tested on the integrated release branch, and pending final review** in [Draft PR #47](https://github.com/KateK77/careflow-ehr/pull/47) (`release/v1.0` → `main`). **This is not yet a merged or tagged release.** See [current project status](docs/project-status.md).

## Features

| Module | Implemented synthetic workflows |
| --- | --- |
| Patient administration | Staff role-based access; registration, MRN uniqueness, search, demographic editing, appointments, scheduling and check-in |
| Physician and clinical | Authorized patient charts, encounters, SOAP drafting/signing, history, problems, allergies and encounter diagnoses |
| Nursing and laboratory | Rooming and vitals; longitudinal flowsheets; laboratory catalog, orders, specimen processing, results, corrections/withdrawals and physician review |
| Medication and MAR | Medication orders, pharmacist verification, simulated dispensing, nurse administration events, holds/refusals/omissions and corrections |
| Patient Portal | Dedicated linked patient sign-in, authorized released records, messages, appointment requests and released billing statements |
| Billing and insurance | Synthetic coverage, charges, statements, mock claims, denials/appeals and simulated patient/payer payments and reversals |
| Imaging and radiology | Imaging orders, exam scheduling and execution, preliminary/final/corrected/withdrawn report versions, physician acknowledgement |
| Inpatient and ED | Facilities and bed availability; admission, transfers, discharge; ED arrival, fictional triage, room assignment, provider review and ED-to-inpatient handoff |

All clinical measurements, triage labels, pharmacy transactions and claim outcomes are fictional simulation data, not validated clinical logic.

## Architecture and engineering practices

- **Stack:** Python, Django 5.2, SQLite for local development, server-rendered templates.
- **Design:** Modular monolith with separate patient, scheduling, clinical, nursing, lab, medication, MAR, portal, billing, imaging and hospital modules.
- **Correctness:** Role/record access controls, constrained workflow transitions, optimistic version checks, transactions, immutable version history through supported services, and audit events.
- **Engineering process:** GitHub Issues, feature branches, stacked PRs, a two-parent Phase 5–7 integration commit, Django tests, local Chromium browser workflows, CI and manual acceptance records.
- **Limits:** Direct database access can bypass application-level guarantees. No claims of clinical validation, certification, accessibility conformance, full security assurance, production scalability or real interoperability.

[Architecture](docs/architecture.md) · [Decisions](docs/decisions/) · [Roadmap](docs/roadmap.md) · [Iteration history](docs/iterations/)

## Local setup: fresh, isolated synthetic database

From the repository root with **Python 3.12+**, on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:CAREFLOW_DB_PATH = Join-Path (Resolve-Path '.venv').Path 'careflow-v1-fresh-demo.sqlite3'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open the [CareFlow landing page](http://127.0.0.1:8000/) and choose **Staff Sign In** or **Patient Sign In**. Direct links are available for [staff sign-in](http://127.0.0.1:8000/login/), [patient sign-in](http://127.0.0.1:8000/portal/login/) and the [health endpoint](http://127.0.0.1:8000/health/). A fresh database is empty; use the documented [opt-in synthetic seeding](docs/iterations/0002-patient-registration/README.md) and [integrated demo account/preview guide](docs/iterations/0022-emergency-tracking/preview-and-uat.md) only for your intended database. No demo password is published.

**Important:** Existing `db.sqlite3` and Phase 3–8 UAT preview databases must never be reset, reseeded, overwritten or migrated as a routine setup step. Always verify `CAREFLOW_DB_PATH` before running management commands: if unset, Django defaults to `db.sqlite3`. Existing accepted-preview setup is documented [here](docs/iterations/0022-emergency-tracking/preview-and-uat.md).

## Tests and evidence

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

For code candidate `d6881ff`, Codex reported **345 passing Django tests, 23 local Chromium workflows and two additional audit probes**. [GitHub Actions CI on release PR #47](https://github.com/KateK77/careflow-ehr/actions/runs/43150653448) passed Django system checks, tests and migration consistency against `main`. **Chromium workflows and audit probes were run locally, not by that CI job.** The user separately reported successful core manual UAT for Phases 5–8, selected cross-patient/role isolation and preservation of a signed SOAP note and MAR history. These results do not cover all edge cases, roles, browsers or load. The new documentation commit requires its own CI verification.

## Development and PR history

Phases 0–4B are merged, through [PR #30](https://github.com/KateK77/careflow-ehr/pull/30). Original Phase 5–8 work remains tracked in open PRs [#32](https://github.com/KateK77/careflow-ehr/pull/32), [#34](https://github.com/KateK77/careflow-ehr/pull/34), [#36](https://github.com/KateK77/careflow-ehr/pull/36), [#38](https://github.com/KateK77/careflow-ehr/pull/38), [#40](https://github.com/KateK77/careflow-ehr/pull/40), [#42](https://github.com/KateK77/careflow-ehr/pull/42), [#44](https://github.com/KateK77/careflow-ehr/pull/44), and [#46](https://github.com/KateK77/careflow-ehr/pull/46). The complete integration is in [Draft PR #47](https://github.com/KateK77/careflow-ehr/pull/47); existing iteration documents are preserved as historical evidence.

**No merger, release tag, external hosting or clinical deployment is implied by this README.**
