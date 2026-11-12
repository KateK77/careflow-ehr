Continue developing CareFlow EHR.

I approve the next development round:

1. Integration of Phase 5, Phase 6 and Phase 7 into a separate development branch.
2. Phase 8A — Inpatient Admission, Discharge, Transfer & Bed Management.
3. Phase 8B — Emergency Department Tracking & Disposition.

The user wants implementation and automated verification first, followed by consolidated manual UAT at the end of this development round.

Do not request intermediate manual testing.

Repository: KateK77/careflow-ehr

Local directory:
D:\AI-Workspace\Personal\careflow-ehr

## 1. Verify the existing GitHub state

Expected main baseline:

00c624553cc265e6275a9d2750ab0041a7e6d97f

Currently open PRs:

- #32 — Phase 5A Patient Portal
- #34 — Phase 5B Messaging & Appointment Requests
- #36 — Phase 6A Billing & Statements
- #38 — Phase 6B Claims & Payments
- #40 — Phase 7A Imaging Orders
- #42 — Phase 7B Radiology Workspace

Expected terminal branch heads:

Phase 6B:
14220599b2d4c10668b42853d59e071212a33be7

Phase 7B:
9170ba388f38c59f13f98190eb3f48ff3477e2a5

Verify actual branch heads, current PR targets, CI and working-tree cleanliness before proceeding.

Do not modify, merge, close or retarget any of these six existing PRs.

Do not merge anything into main.

## 2. Create a unified integration branch

Create a new integration branch:

integration/phase5-7-unified

Start from the verified Phase 6B branch, which already contains Phase 5A, 5B, 6A and 6B.

Merge the Phase 7B branch into this integration branch using a history-preserving merge commit.

Phase 7B already contains Phase 7A.

Preserve both original branch histories.

Do not squash, force-push or rewrite existing commits.

Review and safely resolve any integration conflicts, particularly in:

- Django settings
- Root URL routing
- Authentication and role navigation
- Patient Chart and Encounter templates
- Patient Portal
- Shared audit and clinical services
- Database migrations
- UI templates and CSS
- Regression and Chromium test discovery

Do not simply select one side of a conflict if that would discard functionality from the other phase.

After integration, verify that all Phase 5, 6 and 7 modules are available together.

Run the complete Django regression suite, migration checks and all Chromium workflows against isolated test databases.

Push the integration branch and verify GitHub Actions CI.

Do not continue to Phase 8 until integration tests pass.

If a significant unresolved conflict or regression remains, stop and report it rather than building Phase 8 on a broken base.

## 3. Unified preview database

Create a NEW integrated preview database.

Use a consistent SQLite backup of the existing Phase 6B preview as the source, after verifying its path and integrity.

Apply any missing additive imaging migrations only to the NEW integrated clone.

Do not merge SQLite database files by copying tables between them.

Preserve the existing synthetic Patient, Encounter, SOAP, nursing, pharmacy, MAR, portal and billing records from the chosen source.

Do not assume Phase 7 preview records were transferred into the unified database.

Preserve all existing preview databases and backups.

Never migrate, reset, seed or overwrite the original db.sqlite3.

Validate:

- SQLite integrity
- Foreign keys
- Migration graph consistency
- Preservation of existing record IDs
- Signed SOAP content and timestamps
- Medication and MAR history
- Laboratory report history
- Patient account ownership
- Portal and billing records
- Role isolation

Use only fictional synthetic data.

Document the integration baseline and database provenance.

## 4. Phase 8A — Inpatient Admission, Discharge & Bed Management

Create a new Django hospital-operations module integrated with existing Patient, clinical, nursing and medication records.

Implement working functionality for:

- Fictional hospital departments
- Wards
- Rooms
- Beds
- Bed availability and occupancy
- Synthetic admission requests
- Authorized inpatient admission
- Attending-physician assignment
- Inpatient stay records
- Bed allocation
- Ward and bed transfers
- Transfer history
- Inpatient patient lists
- Length-of-stay display
- Inpatient status and provenance
- Discharge planning
- Synthetic discharge documentation
- Explicit discharge confirmation
- Bed release after discharge
- Read-only completed-stay history
- Patient Chart integration

Define a clear admission and discharge state machine.

Use a separate, explicit inpatient episode model where appropriate. Do not silently repurpose appointment-based outpatient Encounters as inpatient admissions.

If linking inpatient episodes to existing clinical Encounters, define and test that relationship explicitly.

Do not reopen or overwrite existing completed outpatient Encounters.

Implement transactional bed allocation to prevent two active patients from occupying the same bed.

Define permissions for admission/bed management staff, physicians, nurses and administrators.

Require appropriate documentation and authorization for transfers and discharge.

Maintain immutable historical bed assignments and discharge provenance.

## 5. Phase 8A — Inpatient Workspace

Implement real server-rendered Django pages for:

- Inpatient Dashboard
- Bed Capacity Board
- Ward and Room Management
- Admission Worklist
- Admit Patient
- Inpatient Stay Detail
- Transfer Patient
- Discharge Patient
- Admission and Transfer History

Include a Patient Chart link and appropriately scoped read-only information from existing modules.

Do not automatically create medication orders, laboratory orders, imaging orders or MAR events during admission.

Do not automatically assume that prior outpatient orders are active inpatient orders.

Do not invent vital signs, diagnoses or treatment instructions.

## 6. Phase 8B — Emergency Department

After Phase 8A passes its automated technical gates, create a second development increment.

Implement:

- Emergency Department Tracking Board
- Synthetic ED registration
- Arrival time and arrival method
- Fictional chief complaint
- Explicit manually entered triage category
- Triage history
- ED room assignment
- Waiting, Triage, Roomed, Provider and Observation states
- Assigned clinician
- ED visit detail
- ED event timeline
- Length-of-wait display
- ED disposition
- Discharged from ED
- Admitted to inpatient care
- ED-to-inpatient transfer linkage
- Patient Chart integration
- Audit and historical state tracking

Create a dedicated ED visit record linked to the existing Patient.

Do not automatically treat an ED visit as an outpatient Appointment or Encounter.

Define explicit relationships among ED visits, inpatient admissions and existing clinical records.

When an ED visit results in inpatient admission, reuse the authorized Phase 8A admission services.

Prevent duplicate active admissions and conflicting bed occupancy.

Require explicit authorized confirmation for ED disposition.

Keep all events and previous states available in history.

Triage categories must be fictional demonstration labels, not automated medical risk scoring.

Do not calculate clinical acuity, recommend emergency treatment or claim real patient safety validation.

## 7. Permissions and Audit

Enforce backend role-based authorization for all new features.

Test that:

- FrontDesk cannot perform physician-only clinical actions.
- Nurses cannot approve administrative discharge or bed transfer unless explicitly authorized.
- BillingStaff cannot access unrestricted inpatient clinical notes.
- RadiologyStaff and Pharmacist-only users cannot access unrelated ED or inpatient records.
- Patient Portal users cannot access staff hospital-operation pages.
- Unauthorized users cannot change Patient IDs or episode IDs to access another patient's records.
- Duplicate admissions and bed assignments are rejected.
- Stale versions and replayed commands are handled.
- Historical events and signed records are preserved.

Every write must use validated transactional services and auditable provenance.

## 8. Data Models and Migrations

Design appropriate models, potentially including:

- HospitalWard
- HospitalRoom
- HospitalBed
- InpatientStay
- AdmissionRequest
- BedAssignmentEvent
- InpatientTransferEvent
- InpatientDischargeEvent
- EmergencyVisit
- EmergencyTriage
- EmergencyTrackingEvent
- EmergencyDisposition

These are candidate concepts; choose the simplest correct domain structure.

Use additive migrations, protected relationships, explicit constraints and optimistic concurrency.

Do not modify historical clinical migrations.

Do not erase or rewrite any existing data.

## 9. UI and Integration

Maintain the CareFlow design system.

Build functional navigation between:

- Hospital Operations
- Inpatient Workspace
- ED Tracking Board
- Existing Patient Chart
- Physician and Nursing Workspaces
- Medication Orders
- Laboratory and Imaging Records

Do not break Patient Portal or Billing navigation.

Make statuses, timestamps, episode IDs and responsible staff clearly visible.

Use responsive tables, accessible labels and readable validation errors.

Every clinical page must show:

DEMO — NOT FOR CLINICAL USE

Do not create placeholder buttons or fake interactive pages.

## 10. Automated Testing

Add comprehensive Django regression coverage for:

- Admission state transitions
- Inpatient patient scope
- Bed allocation and double-booking prevention
- Ward transfers
- Discharge and bed release
- Historical bed assignment preservation
- Role denials
- Direct URL isolation
- Duplicate command handling
- Stale versions and concurrent writes
- ED registration and triage
- ED status transitions
- ED disposition
- ED-to-inpatient admission
- Patient and episode relationship integrity
- Audit transaction rollback
- Preservation of signed clinical records
- Existing Phase 5, 6 and 7 behavior

Create Chromium workflows for:

1. Inpatient admission → transfer → discharge.
2. ED arrival → triage → rooming → disposition.
3. ED-to-inpatient admission and bed allocation.

Run the full integrated regression suite, not only the new module tests.

Run Django system checks, migration consistency checks, all relevant Chromium workflows and GitHub Actions CI.

Report exact counts and failures.

Do not claim unperformed manual UAT passed.

## 11. GitHub Workflow

After the unified integration branch passes CI:

Create:

Phase 8A development branch from the integration branch.

Phase 8B development branch from the Phase 8A branch.

For each increment:

- Create an English GitHub Issue.
- Implement working functionality.
- Add migration files, tests and documentation.
- Run the complete automated verification.
- Commit and push.
- Open a Pull Request.
- Verify CI on the current PR head.

Phase 8A PR should target the integration branch.

Phase 8B PR should target the Phase 8A branch.

Keep both PRs OPEN and UNMERGED.

The integration branch is a temporary development baseline and must not be merged into main or used to replace the six existing PRs.

Do not create a duplicate aggregate PR against main unless separately approved.

Do not merge any Phase 5, 6, 7 or 8 PR.

## 12. Final Integrated Preview

After Phase 8B implementation, create one separate integrated preview with all Phase 5–8 modules.

Use a freshly named SQLite clone and apply only required additive migrations.

Preserve all previously recorded UAT data and backups.

Provide safe account provisioning for:

- Administrator
- Physician
- Nurse
- RadiologyStaff
- BillingStaff
- Two distinct synthetic Patient Portal accounts
- Authorized inpatient/ED operational staff

Do not overwrite existing accounts.

Provide one working local server URL where the user can experience all modules together.

Prepare a consolidated manual UAT checklist covering Phase 5, 6, 7 and 8, including cross-module access control, state transitions and clinical-record preservation.

The user does not want intermediate manual testing.

## 13. Final Deliverables

Report:

1. Unified integration branch and exact SHA.
2. Integration conflicts and how they were resolved.
3. Integrated regression and Chromium results.
4. Integration GitHub Actions CI link.
5. Phase 8A Issue, PR and head SHA.
6. Phase 8B Issue, PR and head SHA.
7. Implemented hospital and ED functionality.
8. New models and migrations.
9. Complete final integrated regression counts.
10. Chromium workflow results.
11. GitHub Actions links.
12. Database preservation evidence.
13. Safe integrated-preview startup instructions.
14. Outstanding limitations and known defects.
15. Consolidated Phase 5–8 manual UAT guide.

Stop after the development, automated verification and documentation are complete.

Do not merge into main.

Do not deploy or create a release.

Wait for the user's consolidated manual UAT and explicit merge approval.