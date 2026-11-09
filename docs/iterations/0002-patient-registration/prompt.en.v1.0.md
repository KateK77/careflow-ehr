# Approved Phase 1A prompt — English translation v1.0

Translation revision 1.0.0, dated 2026-11-07. Source record version 1.0. [Verbatim Chinese original](prompt.md) · [Translation registry](../../requirements/v1.0-en/README.md).

CareFlow EHR Phase 0 has passed acceptance and merged into main.

I formally approve Phase 1A, Patient Management.

Project directory is `D:\AI-Workspace\Personal\careflow-ehr`. GitHub repository is `KateK77/careflow-ehr`.

## 1. Development preparation

1. Check Git status and confirm main is synchronized with GitHub and has no uncommitted user changes.
2. Read root AGENTS.md, docs/architecture.md, docs/roadmap.md and docs/requirements/v1.0/product-spec.md.
3. Use the existing Django architecture. Do not recreate the project or change to React/FastAPI.
4. Create a Phase 1A GitHub Issue with scope and acceptance criteria.
5. Create phase/0002-patient-registration from the latest main.
6. Use docs/iterations/TEMPLATE.md to establish iteration records and preserve this prompt verbatim.

## 2. Features

### Authentication and roles

Use Django Authentication for demo login. Initially support Administrator, Physician, Nurse and FrontDesk.

Validate permissions in the Django backend in addition to hiding unauthorized UI controls. Provide secure synthetic demo-account initialization without hardcoding passwords in the repository.

### Patient management

Implement real database models and pages for patient listing, creation, search, details, demographic editing, unique MRN validation, potential duplicate warnings, input validation/error feedback, and creation/edit audit records.

Persist all records in the database. A static frontend patient list is insufficient.

### User interface

Design an original modern EHR interface with top navigation, left navigation, current staff identity/role, Dashboard, Patients, search/filter controls, patient table, registration form, details and clear success/failure feedback.

Provide the information density of professional healthcare software while maintaining clarity, usability and responsive layout. Every page must show DEMO — NOT FOR CLINICAL USE. Do not copy Epic trademarks, icons, CSS or proprietary layouts.

### Synthetic data

Provide a repeatable synthetic patient seed command. Use fictional patients exclusively and avoid real healthcare data connections.

### Tests

Write and run automated tests covering at least login/logout, permissions, successful patient creation, search, details, duplicate MRNs, invalid input, unauthorized access and audit records.

Run `python manage.py check` and `python manage.py test`, preserving the existing tests.

## 3. Scope boundaries

Defer appointments/scheduling, physician clinical notes, laboratory/medication/orders, AI and the patient portal.

Preserve existing business code, local database contents and the C-drive backup.

## 4. Development traceability

Preserve requirements/acceptance criteria, the complete prompt, development report, changed-file list, test results, commit SHA, GitHub Issue/PR links and known issues.

Commit on the feature branch, push and open a PR. Wait for GitHub Actions to finish. Do not automatically merge into main or create a formal Release.

## 5. Final delivery

Provide actual run/access instructions, implemented features/pages, synthetic demo-account instructions, database models/migrations, test results, Issue/Commit/PR links, and outstanding features/known issues.

Stop and wait for me to run the application, provide feedback and accept it.
