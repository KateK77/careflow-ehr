We are ready to begin the next CareFlow EHR development phase.

**I approve actual implementation of Phase 5 — Patient Portal.**

This is a functional full-stack Django development task, not a documentation-only exercise.

Repository: KateK77/careflow-ehr

Local directory:
D:\AI-Workspace\Personal\careflow-ehr

Expected starting main commit:
00c624553cc265e6275a9d2750ab0041a7e6d97f

Verify the actual current main HEAD and clean working tree before starting.

## 1. Development Strategy

Implement two increments:

**Phase 5A — Patient Authentication, Portal Dashboard & Medical Records**

**Phase 5B — Patient Messaging & Appointment Requests**

Use the established workflow:

GitHub Issue → Development Branch → Implementation → Automated Tests → Documentation → Pull Request → CI.

Create one Issue and one PR per increment.

Use stacked branches:
- Phase 5A targets main.
- Phase 5B targets the Phase 5A branch.

Finish automated verification for 5A before beginning 5B.

Implement working features, not placeholder pages.

Keep both PRs OPEN and UNMERGED.

The user will perform consolidated manual UAT only after both increments are finished.

## 2. Review Existing Architecture

Inspect the integrated application, especially:

- Patient models and demographic management
- Django authentication and staff roles
- Scheduling and appointment status transitions
- Physician encounters and signed SOAP notes
- Clinical History and MedicationStatement
- Medication Orders and Pharmacy
- Laboratory results, publication, correction, withdrawal and quarantine
- MAR and nursing records
- Shared audit events
- Current Django templates, UI conventions and test framework

Reuse the existing domain data and services safely.

Do not build a disconnected patient portal with separate fabricated clinical records.

Maintain synthetic-only data boundaries and CareFlow's original branding.

## 3. Phase 5A — Patient Accounts and Authentication

Implement a separate patient-facing authentication experience.

Required features:

- Patient Portal login and logout
- Dedicated /portal/ navigation
- Patient dashboard
- Explicit account-to-Patient linkage
- Synthetic patient account provisioning
- Session-based authentication
- Appropriate password validation
- Secure account and patient mapping
- Patient-only authorization checks

Create a dedicated Patient Portal role or equivalent isolated authorization mechanism.

Do not grant patient accounts any staff role.

Patient accounts must not access:
- Staff dashboard
- Patient directory
- Physician or Nursing workspaces
- Pharmacy Workspace
- MAR editing
- Clinical orders
- Staff audit and administration screens

Staff accounts must not automatically impersonate patient accounts.

Do not expose patient records merely by matching usernames, email addresses or MRNs.

Use explicit persisted ownership relationships.

Create a safe preview-only provisioning command for synthetic patient accounts. It must refuse destructive modification of existing accounts or patient links.

Avoid self-service public registration in this increment.

## 4. Phase 5A — Portal Dashboard

Build a patient-facing dashboard at:

/portal/

Display information for the authenticated linked patient only.

Include:

- Synthetic patient name
- Upcoming and historical appointments
- Recent patient-visible laboratory results
- Current and historical medication information
- Completed visit records
- Unread patient messages when Phase 5B is implemented

Use a responsive, mobile-friendly layout distinct from the staff EHR interface.

Every page must clearly indicate:
DEMO — NOT FOR CLINICAL USE.

Never show other patients' data.

## 5. Phase 5A — Appointment History

Allow patients to view their own:

- Appointments
- Appointment dates and clinic-local times
- Assigned synthetic clinician
- Appointment type
- Scheduled, arrived, completed or cancelled information as represented in the existing models
- Relevant visit details

Preserve the existing distinction between Appointment status and Encounter status.

Do not allow patients to directly mutate staff appointment records in Phase 5A.

Appointment requests will be handled separately in Phase 5B.

## 6. Phase 5A — Laboratory Results

Implement an appropriately restricted patient-facing laboratory results view.

Reuse the existing laboratory module without modifying its signed or published records.

Important visibility boundaries:

- Do not expose internal laboratory drafts.
- Do not expose unpublished reports.
- Do not expose withdrawn or quarantined content.
- Never expose context_error or report_error restricted report values through the portal.
- Do not expose internal laboratory audit notes or private staff review data.
- Do not treat physician acknowledgement as automatically equivalent to patient release.

Define an explicit patient-visible release policy or patient-release state if required.

Use an auditable, authorized staff release workflow where necessary.

Display only eligible patient-visible report components, units, report dates and appropriate status information.

Do not automatically interpret abnormal results or generate treatment recommendations.

Test every withdrawal, correction and patient-release boundary, including direct URL access and historical revisions.

## 7. Phase 5A — Medications and Visits

Implement a patient-facing medication view that distinguishes:

- Patient medication history statements
- Signed synthetic medication orders
- Historical or cancelled orders
- Pharmacy processing status where appropriate

Do not incorrectly describe pharmacy dispensing as confirmed medication administration.

Do not expose internal MAR nursing documentation automatically.

Provide completed Encounter summaries using only explicitly permitted, existing data.

Do not generate or imply an authorized After Visit Summary from SOAP content alone.

If there is no separately patient-released clinical summary, display a clear visit-record view and explain that no patient-facing visit summary has been published.

Do not silently make signed SOAP notes publicly visible to the portal.

## 8. Phase 5B — Secure Synthetic Messages

Implement actual persisted, patient-linked demonstration messaging.

Patient features:

- Compose nonurgent synthetic messages
- Send messages to the fictional care team
- View sent messages
- View staff replies
- View conversation history
- Track unread/read status

Staff features:

- Restricted staff message worklist
- View assigned patient conversations
- Reply to patient messages
- Mark appropriately scoped messages as read
- Preserve sender, recipient, timestamps and audit history

Staff message access must follow explicit permissions and patient scope.

Do not grant a general staff account unrestricted access to every patient conversation without an approved access policy.

Patient users must only access their own threads.

Messages must be clearly labelled as simulated and nonurgent.

Include a notice that the portal is not for emergencies and is not monitored as a clinical communication channel.

No real email, SMS, push notifications or external delivery services.

No real healthcare communication or PHI.

Do not create AI-generated clinical replies.

## 9. Phase 5B — Appointment Requests

Allow patient accounts to submit synthetic appointment requests.

Implement:

- Request new appointment
- Request rescheduling
- Request cancellation
- View request status
- Staff review and approval/rejection
- Staff explanation or response
- Auditable request history

A patient request is NOT a confirmed appointment.

Do not directly create, reschedule or cancel real Appointment records from an unreviewed patient request.

If staff approves a request, reuse existing authorized Scheduling services with conflict detection, state validation, confirmation and audit logging.

Preserve separation between patient-request status and actual Appointment status.

An approved request must not bypass appointment conflicts or existing Encounter rules.

Prevent duplicate requests, stale reviews and unauthorized state transitions.

## 10. Security and Authorization

Patient isolation is a critical acceptance requirement.

Implement backend authorization for every portal view and service.

Test:

- Patient A cannot read Patient B's information.
- Patient A cannot change URL identifiers to access Patient B.
- Patient A cannot access staff clinical notes, pharmacy, MAR or laboratory quarantine data.
- Staff-only routes reject patient accounts.
- Patient messages cannot be read by unrelated patient accounts.
- Staff replies cannot be forged by patient accounts.
- Cross-patient appointment requests are rejected.
- Direct GET and POST access are protected.
- CSRF is enforced.
- Stale commands and duplicate submissions are handled.
- Audit events preserve actor, patient, time and action.
- No sensitive clinical data appears through navigation, templates, exception pages or serialized responses.

Use server-side queryset restrictions, not merely hidden buttons.

Avoid leaking patient existence through unscoped object lookups.

## 11. Database and Data Preservation

Create only the additive models and migrations needed.

Potential concepts include:

- PatientPortalAccount
- PatientVisibleResultRelease
- PatientMessageThread
- PatientMessage
- PatientAppointmentRequest
- PatientPortalEvent

Adjust these concepts to fit the existing architecture rather than creating unnecessary duplicate data.

Database rules:

- Do not migrate original db.sqlite3.
- Do not reset, reseed or overwrite any existing database.
- Do not modify existing Phase 3B, 4A or 4B UAT previews.
- Do not overwrite smoke-test databases.
- Preserve all synthetic patient data, signed notes, laboratory reports, pharmacy records, MAR events and audit history.
- Use newly named preview clones and isolated test databases.
- Verify SQLite integrity, foreign keys and source-data preservation.
- Back up before any additive preview migration.

All existing clinical records must retain their original IDs, authors, versions and timestamps.

## 12. User Interface

Implement a cohesive, mobile-friendly patient portal.

Create working pages for:

- Patient login
- Dashboard
- Appointments
- Laboratory results
- Medications
- Completed visits
- Messages
- New message
- Appointment requests
- Request status and history

Create the necessary staff-facing message and appointment-request worklists.

All links and forms must work.

Use clear empty states, readable dates, accessible forms and consistent validation feedback.

Do not create decorative links or nonfunctional buttons.

Do not copy Epic or MyChart branding, screenshots or proprietary visual assets.

## 13. Automated Testing

Add regression and Chromium coverage for both increments.

Required scenarios include:

- Patient login and logout
- Patient account ownership
- Cross-patient isolation
- Staff versus patient authorization
- Appointment visibility
- Laboratory release/withdrawal/quarantine boundaries
- Signed versus draft clinical-record visibility
- Medication history and order distinctions
- Patient messages and staff replies
- Conversation access control
- Appointment request submission and status
- Staff approval/rejection
- Scheduling conflicts
- Idempotency and stale submissions
- Audit rollback and version integrity
- Preservation of all existing clinical workflows

Run the full existing regression suite, Django checks, migration consistency checks, and all relevant Chromium workflows.

Do not remove existing tests or weaken existing security assertions.

Report exact counts, failures and CI links.

## 14. GitHub and Documentation

For each increment:

1. Create a scoped English Issue.
2. Create the development branch.
3. Implement functional code and templates.
4. Add tests and additive migrations.
5. Document design decisions, limitations and behavior.
6. Run automated verification.
7. Commit and push.
8. Open a PR with an accurate changed-file summary.
9. Verify GitHub Actions passes.

Keep both PRs open.

Do not merge automatically.

Do not deploy.

Do not start Billing, Insurance or unrelated features.

## 15. Final Deliverables

After implementing Phase 5A and 5B, provide:

1. Both GitHub Issue and PR links.
2. Exact branch names and head commit SHAs.
3. Implemented patient and staff-facing features.
4. Working routes and test account setup.
5. New models and migrations.
6. Regression test results.
7. Chromium workflow results.
8. CI links.
9. Database preservation verification.
10. Known limitations and remaining risks.
11. Safe preview startup instructions.
12. Consolidated manual UAT checklist.

The checklist should include at least two separately linked synthetic patient accounts to verify cross-patient isolation.

Stop after publishing and verifying both increments.

The user will perform consolidated manual UAT and explicitly approve any PR merges afterward.