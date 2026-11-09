# 0003 — Phase 1B scheduling and check-in

- [Issue #5](https://github.com/KateK77/careflow-ehr/issues/5)
- Branch: `phase/0003-scheduling-checkin`, from `030761a09b7257fdf1c9215c917d4cf604f1791c`
- [Implementation commit 9b8f884](https://github.com/KateK77/careflow-ehr/commit/9b8f884bef583aa338d490eb9cf4a3b9785a90b6)
- [PR #6](https://github.com/KateK77/careflow-ehr/pull/6)
- [Approved prompt](prompt.md), [verification](verification.md), [feedback](feedback.md)
- [Architecture decision and states](../../decisions/0003-scheduling-and-checkin.md)
- Requirements baseline v1.0, S05, scheduling context in S06 and W06

## Scope and acceptance

Create, review, confirm, reschedule, cancel and check in appointments using existing synthetic patients and physician accounts. Provide daily/weekly calendars, physician/date filters, patient lookup, appointment details and a date-based check-in worklist. Persist every change with audit history and enforce role restrictions on direct URL/POST access.

Backend validation must prevent overlapping reservations and stale edits, preserve UTC/local-time consistency and handle invalid/duplicate transitions. Concurrent booking must leave only one reservation. Preserve all existing patient records and Phase 1A behavior. User acceptance remains pending.

## Implementation report

Added the scheduling domain, transactional write services, signed review forms, scoped views, calendar/worklist/detail pages, tests and an additive migration. Reused existing authentication and staff-role helpers, and linked appointment events to the existing audit domain. Added navigation, dashboard links and a scoped patient-context appointment table.

The before-migration database was copied to an ignored local SQLite backup. Existing patient rows are checked using a read-only table digest before and after migration. Application dependencies remain unchanged.

## Known limitations

Single-clinic access applies. Physicians see their own appointments, while Nurse and scheduling staff can read clinic appointments. There is no provider leave/working-hours configuration, recurring scheduling, waitlist, room allocation or clinical encounter creation. An unfiltered patient selector is clinic-wide and server search narrows its choices.

SQLite serializes writers, and busy requests can require an explicit retry. The browser calendar groups bookings by their start hour and is not a proportional duration/drag-and-drop editor. The agenda and detail pages show full intervals. General overlapping interval protection depends on the service write path. See ADR 0003 for concurrency and time-zone policy.

The five Phase 1A UX groups remain future, non-blocking backlog items. This iteration implements only navigation and presentation required for scheduling.

## Review boundary

Publish the implementation and evidence for review, verify CI and stop for hands-on user acceptance. A merge or subsequent increment requires approval.

## Changed files

- `careflow/core/static/core/app.css`
- `careflow/core/templates/core/base.html`
- `careflow/patients/templates/patients/dashboard.html`
- `careflow/patients/templates/patients/detail.html`
- `careflow/patients/views.py`
- `careflow/scheduling/__init__.py`
- `careflow/scheduling/access.py`
- `careflow/scheduling/browser_tests.py`
- `careflow/scheduling/forms.py`
- `careflow/scheduling/migrations/__init__.py`
- `careflow/scheduling/migrations/0001_initial.py`
- `careflow/scheduling/models.py`
- `careflow/scheduling/services.py`
- `careflow/scheduling/templates/scheduling/appointment_table.html`
- `careflow/scheduling/templates/scheduling/detail.html`
- `careflow/scheduling/templates/scheduling/form.html`
- `careflow/scheduling/templates/scheduling/review.html`
- `careflow/scheduling/templates/scheduling/schedule.html`
- `careflow/scheduling/tests.py`
- `careflow/scheduling/urls.py`
- `careflow/scheduling/views.py`
- `careflow/settings.py`
- `careflow/urls.py`
- `CHANGELOG.md`
- `docs/architecture.md`
- `docs/decisions/0003-scheduling-and-checkin.md`
- `docs/iterations/0003-scheduling-checkin/feedback.md`
- `docs/iterations/0003-scheduling-checkin/prompt.md`
- `docs/iterations/0003-scheduling-checkin/README.md`
- `docs/iterations/0003-scheduling-checkin/verification.md`
- `docs/README.md`
- `docs/roadmap.md`
- `README.md`
