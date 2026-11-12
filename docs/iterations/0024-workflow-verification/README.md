# Issue #50 workflow verification

[Issue #50](https://github.com/KateK77/careflow-ehr/issues/50) · [Approved prompt](prompt.md) · [Issue requirements](requirements.md) · [Computer Use Agent acceptance log](computer-use.md)

Branch `test/issue-50-workflow-coverage` starts from open landing PR #49 at `041bc910650b6ea203d1f8b4b00125780d6222ae`. The test PR targets that branch so its diff contains only Issue #50 changes. Main was at `a9e0913b626b88908ad2ca3041d2ec9497ba7d15`.

## Inventory and coverage

| Test group | New cases | Scope |
| --- | ---: | --- |
| `test_workflow_boundaries.py` | 97 | Explicit route and role contracts. Includes 29 allowed and 68 denied GET requests across 17 staff and patient entry points. |
| `test_portal_sessions.py` | 12 | Nine actual credential submissions and destination checks, patient deactivation, in-session billing role revocation, and patient denial on an admission POST. |
| `test_workflow_handoffs.py` | 15 | Registration and audit, booking token patient binding, check-in cancellation provenance, nursing validation and handoff, chart and history, SOAP URL binding, lab release and correction, pharmacy-to-MAR scope, imaging withdrawal, and ED admission history. |
| **Total** | **124** | Existing tests and application code are unchanged. |

The pre-change checkout had 346 Django tests and 24 Chromium workflows in 22 modules. Browser workflows are counted separately from new Django tests. The new coverage adds selected state, actor and context invariants to existing module suites. It is not an exhaustive endpoint-by-role or invalid-input matrix.

## Verification

- `python manage.py check` passed. `python manage.py makemigrations --check --dry-run` found no changes.
- `python manage.py test --noinput` passed **470 tests**, zero failures, errors or skips.
- `python manage.py test <all 22 browser test modules> --noinput` passed **24 Chromium workflows**, zero failures, errors or skips.
- Git whitespace checks passed. Tests ran against Django's isolated in-memory SQLite databases. SHA-256 comparison verified all 48 pre-existing SQLite files were unchanged.
- Computer Use Agent execution and manual review remain pending. Chromium is separate automated evidence. The PR is a draft while the agent acceptance gate is outstanding.
