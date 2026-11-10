# Phase 3A changed files v1.0

The nursing app owns models/migration, permission/state policies, forms, transactional services, worklist/record/correction/flowsheet pages, presentation and tests. Existing files register the app and add scoped nursing chart/encounter summaries, actual timeline events and functional navigation. Project documents track the increment. Historical sources/iteration records remain unchanged.

- `CHANGELOG.md`
- `README.md`
- `careflow/clinical/templates/clinical/chart.html`
- `careflow/clinical/templates/clinical/encounter.html`
- `careflow/clinical/templates/clinical/header.html`
- `careflow/clinical/views.py`
- `careflow/core/static/core/app.css`
- `careflow/core/templates/core/base.html`
- `careflow/nursing/__init__.py`
- `careflow/nursing/access.py`
- `careflow/nursing/browser_tests.py`
- `careflow/nursing/forms.py`
- `careflow/nursing/migrations/0001_initial.py`
- `careflow/nursing/migrations/__init__.py`
- `careflow/nursing/models.py`
- `careflow/nursing/presentation.py`
- `careflow/nursing/services.py`
- `careflow/nursing/templates/nursing/appointment.html`
- `careflow/nursing/templates/nursing/chart_summary.html`
- `careflow/nursing/templates/nursing/context.html`
- `careflow/nursing/templates/nursing/detail.html`
- `careflow/nursing/templates/nursing/flowsheet.html`
- `careflow/nursing/templates/nursing/form.html`
- `careflow/nursing/templates/nursing/workspace.html`
- `careflow/nursing/tests.py`
- `careflow/nursing/urls.py`
- `careflow/nursing/views.py`
- `careflow/scheduling/templates/scheduling/detail.html`
- `careflow/settings.py`
- `careflow/urls.py`
- `docs/README.md`
- `docs/architecture.md`
- `docs/decisions/0006-nursing-rooming-and-vitals.md`
- `docs/iterations/0006-nursing-workspace/README.md`
- `docs/iterations/0006-nursing-workspace/acceptance.md`
- `docs/iterations/0006-nursing-workspace/changed-files.md`
- `docs/iterations/0006-nursing-workspace/feedback.md`
- `docs/iterations/0006-nursing-workspace/prompt.md`
- `docs/iterations/0006-nursing-workspace/verification.md`
- `docs/roadmap.md`

## Cross-phase integration review follow-up

Nine files are added/updated for this review; the original 40-file implementation list above remains intact. The combined Phase 3A PR therefore contains 45 distinct changed files.

- `careflow/nursing/integration_support.py`: isolated synthetic staff/payload helpers and test-only clinic time-zone choice.
- `careflow/nursing/test_integration.py`: four HTTP integration regressions spanning the existing domain boundaries.
- `careflow/nursing/integration_browser_tests.py`: one full UI journey from actual registration through encounter completion.
- `docs/iterations/0006-nursing-workspace/integration-review-prompt.md`: original approved review request.
- `docs/iterations/0006-nursing-workspace/integration-readiness.md`: consolidated findings, evidence boundaries, risks and future merge sequence.
- Current iteration `README.md`, `verification.md`, `feedback.md` and `changed-files.md`: review traceability and results.

No application logic, settings, dependency or migration files are modified by the integration review. No prior iteration or historical source document is rewritten.
