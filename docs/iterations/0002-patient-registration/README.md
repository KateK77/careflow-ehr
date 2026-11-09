# 0002 — Phase 1A Patient Management

- [Issue #3](https://github.com/KateK77/careflow-ehr/issues/3)
- Branch: `phase/0002-patient-registration`, based on `863e91d3b5c2f89f0beeebe462dbfdc1c014009d`
- [Implementation commit b6f59b8](https://github.com/KateK77/careflow-ehr/commit/b6f59b8d0932a14637d19ff0c0e1e6173ee71090)
- [PR #4](https://github.com/KateK77/careflow-ehr/pull/4)
- [Prompt](prompt.md), [feedback](feedback.md), [verification](verification.md)
- Baseline v1.0, S01–S04 and the demographic subset of S06. [Access decision](../../decisions/0002-patient-management-access.md)

## Requirements and acceptance

Staff authentication and POST logout use Django Authentication. Four staff roles are enforced server-side. Authorized users can search, filter and page real database patients and view their demographics. Administrator and FrontDesk can create and edit. MRNs are unique without case sensitivity. Invalid input, potential duplicate identities and stale edits receive visible feedback. Patient changes and audit events commit together. Seed data is synthetic, repeatable and preserves existing data.

## Development report

Added the patients domain, initial migration, validation, role checks, views, templates, seed command and tests. Added audited auth views, session/auth/messages/static integration and an original responsive shared layout. Extended the original landing page with the demo notice and staff sign-in link. Preserved the health endpoint and existing smoke tests.

Changed files are enumerated by the linked implementation commits and PR. The existing roadmap and architecture now point to the patient increment. Run instructions and demo credentials handling are in the root README. No dependency changes were needed for the application.

## Known limitations

This is a local DEBUG demo for a single synthetic clinic. Staff read access spans the clinic's demographic records. Patient-assignment isolation and the patient portal are outside this phase. There is no account-management UI, password reset by email, login throttling, or deployment configuration. Audit history has no update/delete endpoint or admin registration, but a database operator can change the local database. Insurance coverage, appointments and clinical data remain outside this increment. MRNs are supplied explicitly.

## Review boundary

The user reported all ten manual acceptance checks passed on 2026-11-08, with no blocking functional defects. See [feedback](feedback.md) for the acceptance matrix and five future UI/UX enhancement groups, and [verification](verification.md) for evidence boundaries. PR #4 remains open pending a separate merge decision. The next increment requires approval.

## Changed files

- `.env.example`
- `CHANGELOG.md`
- `README.md`
- `careflow/core/auth_views.py`
- `careflow/core/static/core/app.css`
- `careflow/core/templates/404.html`
- `careflow/core/templates/core/403.html`
- `careflow/core/templates/core/base.html`
- `careflow/core/templates/core/home.html`
- `careflow/core/templates/registration/login.html`
- `careflow/patients/__init__.py`
- `careflow/patients/access.py`
- `careflow/patients/browser_tests.py`
- `careflow/patients/forms.py`
- `careflow/patients/management/__init__.py`
- `careflow/patients/management/commands/__init__.py`
- `careflow/patients/management/commands/seed_synthetic.py`
- `careflow/patients/migrations/0001_initial.py`
- `careflow/patients/migrations/__init__.py`
- `careflow/patients/models.py`
- `careflow/patients/templates/patients/dashboard.html`
- `careflow/patients/templates/patients/detail.html`
- `careflow/patients/templates/patients/form.html`
- `careflow/patients/templates/patients/list.html`
- `careflow/patients/tests.py`
- `careflow/patients/urls.py`
- `careflow/patients/views.py`
- `careflow/settings.py`
- `careflow/urls.py`
- `docs/README.md`
- `docs/architecture.md`
- `docs/decisions/0002-patient-management-access.md`
- `docs/iterations/0002-patient-registration/README.md`
- `docs/iterations/0002-patient-registration/feedback.md`
- `docs/iterations/0002-patient-registration/prompt.md`
- `docs/iterations/0002-patient-registration/verification.md`
- `docs/roadmap.md`
