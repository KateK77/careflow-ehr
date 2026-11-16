# Iteration 0029 — CareFlow v3 email access and blue interface

Status: implementation and offline verification in progress; public hosting not provisioned.

- [Issue #60](https://github.com/KateK77/careflow-ehr/issues/60).
- Branch: `feature/v3-email-registration`.
- Parent: [PR #59](https://github.com/KateK77/careflow-ehr/pull/59), commit [949a6d74415561070a1bf3e6ccd712b24c1160dc](https://github.com/KateK77/careflow-ehr/commit/949a6d74415561070a1bf3e6ccd712b24c1160dc).
- Original prompt: [Chinese](prompt.original.zh.md), [English translation](prompt.en.v1.0.md).
- [Versioned v3 implementation prompt](../../requirements/v3.0/prompt.en.v3.0.md).
- [Architecture and scope](architecture.md), [verification](verification.md), [acceptance](acceptance.md), [deployment](../../deployment/v3/README.md).

## Local preview

In a checkout of this branch, use the existing Django virtual environment:

```powershell
.\.venv\Scripts\python.exe tools\v3_preview.py --port 8014
```

The current isolated worktree is `D:\AI-Workspace\Personal\careflow-ehr\.venv\worktrees\v3`. For that worktree, run the root project's Python executable against this worktree's `tools/v3_preview.py`; it shares installed dependencies, not databases.

The launcher prompts for a demo password and creates a NEW SQLite database and a NEW private email outbox. It prints the outbox directory, never the message contents or password. Local email is not delivered to external inboxes; open the newly written message in the private directory to copy its code into Verify email or password recovery. Never commit or publicly serve the outbox.

Existing demo usernames remain available: administrator.demo, frontdesk.demo, physician.demo, nurse.demo, lab.demo, pharmacist.demo, billing.demo, radiology.demo, hospital.demo, patient1.demo and patient2.demo. They use the launcher-supplied password. New applicants use their verified email and chosen password after the appropriate activation/approval.

Each startup creates fresh fixtures. It does not modify or resume existing preview databases. Stop the server with Ctrl+C. For persistent review sessions, reuse only the explicitly identified new v3 database through a separate server restart; do not rerun seed or migration commands against earlier previews.

## Review order

This worktree belongs to the SAME Git repository. The official root worktree stays on v2 so existing preview servers retain their code/templates. The new PR stacks on PR #59 and must remain open until review. Main, parent heads and existing PR targets remain unchanged.
