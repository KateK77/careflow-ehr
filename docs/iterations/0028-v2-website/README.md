# Iteration 0028 — CareFlow EHR 2.0 website

Status: development preview; awaiting user review. Not a release.

- [Issue #58](https://github.com/KateK77/careflow-ehr/issues/58).
- Branch: `feature/v2-website`.
- Parent: [PR #57](https://github.com/KateK77/careflow-ehr/pull/57), `ui/unified-workspace-upgrade`, commit [86d307540386fa587e962430b2dfbb0eb76a5f11](https://github.com/KateK77/careflow-ehr/commit/86d307540386fa587e962430b2dfbb0eb76a5f11).
- New PR and implementation commit will be recorded after publication.
- [Original prompt](prompt.original.zh.md); [English translation v1.0](prompt.en.v1.0.md).
- [Requirements, architecture and feedback disposition](../../requirements/v2.0/README.md).
- [Verification](verification.md); [feedback and acceptance](feedback.md); [files](files.md).

## Delivered

A new public landing, split login experiences, staff shell, patient shell, dashboard agenda, grouped registration, appointment progression and responsive visual system. Existing clinical and administrative routes inherit the new shared layout. Backend permissions, state transitions and historical records remain.

## Run the isolated website locally

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe tools\v2_preview.py
```

Enter a new synthetic demo password at the hidden prompt (at least 12 characters, subject to existing password policy). Open http://127.0.0.1:8012/. Use `--port 8013` if 8012 is occupied.

Staff usernames: `administrator.demo`, `frontdesk.demo`, `physician.demo`, `nurse.demo`, `lab.demo`, `pharmacist.demo`, `billing.demo`, `radiology.demo`, `hospital.demo`.

Patient usernames: `patient1.demo` and `patient2.demo`, separately linked to DEMO-0001 and DEMO-0002. All use the password supplied at launch. No password is committed or printed.

Each invocation creates a NEW database under `.venv/uat-followup/v2-preview-*/preview.sqlite3`, runs existing migrations only there, creates 30 fictional patients, 11 demo accounts and three audited future appointments. Near midnight, those appointments may fall on the next clinic-local date; use Schedule to view them.

Ctrl+C stops the server. The preview database remains locally for inspection, but the next invocation creates another fresh one. It never resumes, resets, reseeds or migrates an existing database. Existing clinical datasets are intentionally not copied into the preview. Advanced worklists start empty until fictional records are created through the existing workflows.

This launcher is for local development with Django's development server. It is not deployment configuration. `--prepare-only` creates fixtures and exits without starting a server.

## Review order

This branch stacks on PR #57 so that previous fixes are included without copying or dropping history. Do not merge or retarget automatically. Review the parent stack before any future sequential integration.

## Actual browser screenshots

- [Desktop landing](screenshots/careflow-landing-1440.png)
- [Mobile landing](screenshots/careflow-landing-390.png)
- [Staff workspace](screenshots/staff-workspace-1280.png)
- [Appointment form at 1280x800](screenshots/appointment-1280-initial.png)
- [Patient portal on mobile](screenshots/patient-portal-390.png)
- [Registration with explicit confirmation required](screenshots/v2-registration-1280.png)
