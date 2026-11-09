You are the senior software engineer responsible for CareFlow EHR.

Phase 1A has been successfully merged into main and all 34 automated tests passed.

I formally approve starting **Phase 1B — Scheduling, Appointments, and Patient Check-in**.

Project directory:
D:\AI-Workspace\Personal\careflow-ehr

GitHub repository:
https://github.com/KateK77/careflow-ehr

## 1. Project Preparation

1. Verify that the local main branch matches origin/main.
2. Confirm the working tree is clean before making changes.
3. Read AGENTS.md, the English requirements baseline, architecture decisions, roadmap, and Phase 1A implementation.
4. Preserve the existing Django architecture, authentication system, patient database, and functionality.
5. Create a new GitHub Issue for Phase 1B, with scope and acceptance criteria written in English.
6. Create a development branch named `phase/0003-scheduling-checkin` from the latest main.
7. Create `docs/iterations/0003-scheduling-checkin/` following the existing development documentation standard.
8. Preserve this approved development prompt verbatim.

## 2. Scheduling and Appointment Management

Implement a fully functional outpatient appointment scheduling system.

### A. Physician Schedules

- Display physician schedules in daily and weekly views.
- Filter by physician and date.
- Display appointment start/end times, patient, appointment type, and status.
- Provide a clear calendar interface with readable time slots.
- Allow authorized administrative staff to manage appointments.
- Use existing synthetic physician accounts where applicable.

### B. Appointment Creation

Allow authorized staff to:

- Search and select an existing synthetic patient.
- Select an available physician.
- Choose appointment date, start time, and duration.
- Enter an appointment type and optional synthetic visit reason.
- Review appointment information before confirming.
- Save the appointment to the database.

A successful appointment must be visible in both the patient context and the physician schedule.

### C. Appointment Editing and Cancellation

Implement:

- Appointment rescheduling.
- Appointment cancellation.
- Status changes with validation.
- Prevention of conflicting physician appointments.
- Clear error messages for unavailable time slots or invalid date/time input.
- Audit records for creation, rescheduling, cancellation, and status changes.

Document appointment state transitions explicitly and reject invalid transitions.

### D. Patient Check-in

Create a Front Desk workflow allowing staff to:

- View scheduled appointments for a selected date.
- Search for an arriving patient.
- Open the related appointment.
- Mark the patient as Arrived.
- Display the updated status immediately.
- Record the timestamp and staff member responsible for check-in.

This phase should not automatically create a full clinical encounter. Clinical encounter management belongs to a later phase.

## 3. User Interface Requirements

Design an original, professional EHR scheduling interface consistent with the existing CareFlow EHR visual identity.

Include:

- Scheduling navigation
- Daily and weekly calendar views
- Physician filters
- Appointment creation form
- Appointment detail view
- Appointment editing and cancellation controls
- Patient check-in worklist
- Appointment status indicators
- Success and error notifications

The UI must be responsive, keyboard accessible where practical, and suitable for a high-information-density clinical workspace.

Do not copy Epic proprietary assets, branding, or exact interface designs.

All screens must display:
DEMO — NOT FOR CLINICAL USE.

## 4. Database and Backend

Use Django models and migrations.

Define clear relationships between appointments, patients, physicians, and audit events.

Requirements:

- Persist all appointment changes in the database.
- Validate provider/time conflicts on the backend.
- Reject invalid or duplicate appointment transitions.
- Handle date and time zones consistently, storing timestamps in UTC and displaying clinic-local time.
- Consider concurrent scheduling conflicts and document any SQLite limitations.
- Do not reset or overwrite existing patient records.
- Use synthetic data only.

## 5. Role-Based Access Control

Preserve existing Phase 1A permissions.

Proposed Phase 1B permissions:

- Administrator: Manage all appointments.
- FrontDesk: Create, edit, cancel, and check in appointments.
- Physician: View appropriate physician schedules and appointment details.
- Nurse: Read relevant appointment and arrival information.

Enforce permissions in Django backend views, including direct URL requests and POST actions.

Document the access policy and its current single-clinic limitations.

## 6. Automated Testing

Write and run tests covering:

1. Appointment creation.
2. Appointment persistence.
3. Physician schedule display.
4. Appointment rescheduling.
5. Appointment cancellation.
6. Patient check-in.
7. Time-slot conflicts.
8. Invalid date/time input.
9. Invalid status transitions.
10. Unauthorized access.
11. Audit event creation.
12. Existing Phase 1A regression tests.

Run:

- python manage.py check
- python manage.py makemigrations --check --dry-run
- python manage.py test

Perform browser-level testing of the primary scheduling workflow where feasible.

Report actual results and clearly identify anything not tested.

## 7. GitHub Development Traceability

Maintain our approved workflow:

Issue → Branch → Development → Testing → Commit → Push → Pull Request → Review → Merge.

All new GitHub documentation, Issue descriptions, PRs, commit messages, and development reports must be written in professional English.

Preserve original historical Chinese documents and their English translations.

Record:

- Approved requirements and prompt
- Architecture and database decisions
- Files created or modified
- Commands executed
- Tests performed and actual results
- Known limitations
- Issue, Commit, and PR references
- User acceptance status

## 8. Constraints

- Do not rewrite the existing application.
- Do not modify the C drive backup.
- Do not reset the local SQLite database.
- Do not introduce real clinical integrations.
- Do not deploy to cloud services.
- Do not implement pharmacy, laboratory, clinical notes, or AI modules in this phase.
- Keep previously recorded UX improvements in the future backlog unless directly required for scheduling.

## 9. Final Delivery

After implementation:

1. Commit and push changes to the Phase 1B branch.
2. Create a GitHub Pull Request targeting main.
3. Verify GitHub Actions CI.
4. Provide exact local application startup instructions.
5. Explain how to test the appointment scheduling workflow.
6. Provide a detailed implementation and test report.
7. Provide Issue, Commit, and PR links.

Do not merge the PR automatically.

Stop after Phase 1B implementation and wait for my hands-on user acceptance testing.