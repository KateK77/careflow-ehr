# Iteration 0029 — CareFlow v3 username registration and blue interface

Current scope: [v3.1 prompt](../../requirements/v3.0/prompt.en.v3.1.md), superseding email signup per [latest user feedback](feedback.md). The directory retains its original draft name for traceability.

- [Issue #60](https://github.com/KateK77/careflow-ehr/issues/60).
- [PR #61](https://github.com/KateK77/careflow-ehr/pull/61), open and unmerged.
- Implementation: [bf8cf41cde748ccb15be1c7f236bd1686cf0add9](https://github.com/KateK77/careflow-ehr/commit/bf8cf41cde748ccb15be1c7f236bd1686cf0add9).
- Branch: `feature/v3-account-registration`.
- Parent: [PR #59](https://github.com/KateK77/careflow-ehr/pull/59), [949a6d74415561070a1bf3e6ccd712b24c1160dc](https://github.com/KateK77/careflow-ehr/commit/949a6d74415561070a1bf3e6ccd712b24c1160dc).
- Original prompt: [Chinese](prompt.original.zh.md), [English](prompt.en.v1.0.md).
- [Architecture](architecture.md), [verification](verification.md), [acceptance](acceptance.md), [deployment](../../deployment/v3/README.md).
- Earlier email design is preserved in [history](history/) as superseded, unapproved draft evidence.

## Local preview

From a checkout, use the existing Django virtual environment:

```powershell
.\.venv\Scripts\python.exe tools\v3_preview.py --port 8015
```

The isolated worktree is `D:\AI-Workspace\Personal\careflow-ehr\.venv\worktrees\v3`. It shares installed Python dependencies with the original root, not databases. In that worktree, use:

```powershell
& 'D:\AI-Workspace\Personal\careflow-ehr\.venv\Scripts\python.exe' tools\v3_preview.py --port 8015
```

Choose a synthetic demo password at the hidden prompt. Each startup creates a NEW database containing basic fictional patients and appointments; it never opens or migrates an earlier preview. The launcher prints the selected database path. No mail is sent, saved or required.

Staff usernames: administrator.demo, frontdesk.demo, physician.demo, nurse.demo, lab.demo, pharmacist.demo, billing.demo, radiology.demo, hospital.demo. Patient usernames: patient1.demo and patient2.demo. These use the password you supplied. Never publish it.

Alternatively, create your own patient account using the home-page registration link. It starts with an independent fictional chart. Staff applicants choose a requested role and wait for administrator.demo to review it at Staff applications. Password recovery through email is intentionally unavailable.

## Review order and hosting

This worktree belongs to the same Git repository. The original root remains on v2, preserving prior servers and files. The v3 PR stacks on #59; neither PR is automatically merged. A GitHub PR is source for review, not a public running site.

The local preview uses HTTP on loopback only. Hosted configuration is separate, HTTPS-only and requires new persistent storage and a securely provisioned owner account. The owner subsequently authorized free PythonAnywhere hosting. [Public deployment verification](public-deployment.md) records the live HTTPS site and independent synthetic database.

## Staff login clarification

New staff registrations require Administrator approval. Pending applicants who enter the correct password now receive explicit guidance rather than the generic incorrect-credentials error. [Follow-up evidence](login-followup.md). Patient registrations can log in immediately through the Patient Portal.

## Final local handover

[Visitor/operator guide](../../user-guide/v3/README.md) and [final publication request](final-handover.md) record usernames, separate private password delivery, staff approval and the initial hosting dependency. The later [public deployment](public-deployment.md) completes that dependency without merging the source branch.
