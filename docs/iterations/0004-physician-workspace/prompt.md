You are the senior software engineer and technical lead for CareFlow EHR.

Phase 1B has been successfully merged into main. The merged main branch passed all 66 automated tests.

I approve starting **Phase 2A — Physician Workspace, Patient Chart, Clinical Encounters, and SOAP Documentation**.

**Project directory:**
D:\AI-Workspace\Personal\careflow-ehr

**GitHub repository:**
https://github.com/KateK77/careflow-ehr

## 1. Preparation and Version Control

1. Verify that local main, origin/main, and GitHub main point to merge commit `9e04a80498303d588972394c90eb35028d766228`.
2. Confirm that the working tree is clean.
3. Read AGENTS.md, the English product requirements baseline, existing architecture decisions, and Phase 1A/1B implementation records.
4. Create a new GitHub Issue for Phase 2A, documenting its scope, exclusions, and acceptance criteria.
5. Create branch `phase/0004-physician-workspace` from main.
6. Create `docs/iterations/0004-physician-workspace/` and preserve this approved prompt verbatim.
7. Continue using Django, server-rendered templates, and SQLite for local development. Do not rebuild the application.

## 2. Patient Chart

Implement a functional longitudinal patient chart using the existing Patient model.

The interface should include:

- Patient identity banner with name, MRN, age, sex, and encounter context.
- Patient overview.
- Encounter history.
- Clinical notes.
- Relevant recent appointment information.
- A chronological timeline of available clinical events.
- Clear navigation between patient demographics, appointments, encounters, and notes.

Design the application to accommodate future medical history, medications, allergies, diagnoses, laboratory results, and imaging without implementing those modules prematurely.

Do not present non-functional navigation or empty clinical sections as completed features.

## 3. Physician Workspace

Create a physician-focused worklist showing relevant appointments and encounters.

Requirements:

- Physicians can view their authorized patients and encounters.
- Show appointment and encounter status.
- Provide a clear action to open a patient's chart.
- Link the existing appointment workflow to the physician workspace.
- Preserve existing Patient and Appointment records.

Use an original, professional, high-information-density clinical layout with a patient header, chart navigator, main documentation workspace, and contextual information.

## 4. Clinical Encounter Management

Introduce an Encounter model with appropriate relationships to the existing Patient, Appointment, and Physician records.

Implement:

- Explicitly starting a clinical encounter from an arrived appointment.
- Encounter detail and status.
- Encounter start and completion timestamps.
- Encounter history.
- Audit events for important actions.
- Prevention of duplicate encounters for the same appointment.
- Validated state transitions and protection against stale updates.

Do not automatically create encounters during patient check-in. The clinician must explicitly start the encounter.

Preserve Phase 1B appointment history and existing check-in provenance. Document how appointment and encounter states relate before implementing state changes.

## 5. SOAP Clinical Documentation

Implement structured SOAP notes with four sections:

- Subjective
- Objective
- Assessment
- Plan

Required functionality:

- Create a note linked to the correct Patient and Encounter.
- Edit and save drafts.
- Reopen saved drafts without losing content.
- Display note author and timestamps.
- Validate note completeness before signing according to documented demo rules.
- Sign a completed note through an explicit confirmation action.
- Prevent changes to signed note content.
- Preserve signed-note authorship and signing timestamp.
- Include an audit history for note creation, editing, and signing.

Do not overwrite signed notes. A future addendum workflow may be implemented separately.

Clinical notes must contain synthetic information only. The system must not automatically generate diagnoses or treatment recommendations.

## 6. Permissions and Security

Preserve all existing patient-management and scheduling permissions.

For this phase:

- Administrator: Administrative access according to a documented policy; not automatically authorized to sign clinical notes.
- Physician: View authorized patient charts, manage their own encounters, and create/sign their own clinical notes.
- Nurse: Read relevant patient and encounter information according to the current single-clinic scope, without physician signing privileges.
- FrontDesk: Continue registration and scheduling duties without access to clinical note content unless explicitly authorized.

Enforce authorization on the backend for GET and POST requests.

Prevent cross-patient and cross-encounter data leakage, unauthorized signing, duplicate encounter creation, and improper modification of signed notes.

## 7. Database and Testing

Use additive Django migrations. Never reset existing data.

Before migrations, take a safe local backup and record baseline patient, appointment, and database integrity checks.

Verify preservation of the existing 31 synthetic patients and 4 appointments, along with any subsequently created local records.

Add automated tests for:

- Patient chart visibility and access control.
- Physician worklists.
- Encounter creation and persistence.
- Duplicate encounter prevention.
- Valid and invalid encounter state transitions.
- SOAP note creation and draft persistence.
- Note editing.
- Note signing and immutability.
- Unauthorized access and signing.
- Patient/encounter isolation.
- Audit event creation.
- Existing Phase 1A and Phase 1B regression behavior.

Run Django system checks, migration consistency checks, and the full automated test suite.

Perform browser-based verification of the primary physician workflow where feasible.

## 8. UI/UX Requirements

Use the existing CareFlow EHR visual identity while improving the clinical workspace's information hierarchy.

The interface should be original, responsive, readable, and keyboard accessible where practical.

Every clinical screen must display:

DEMO — NOT FOR CLINICAL USE

Avoid copying Epic proprietary designs or branded assets.

Do not implement cosmetic-only buttons that imply unimplemented clinical functionality.

## 9. Out of Scope

Do not implement the following in Phase 2A:

- Real prescriptions or pharmacy workflows.
- Laboratory orders and results.
- Imaging and radiology.
- Comprehensive medication reconciliation.
- Full allergy and longitudinal problem management.
- Nursing flowsheets.
- Insurance and billing.
- AI-generated clinical documentation.
- Cloud deployment.

These belong to future approved increments.

## 10. GitHub Traceability and Delivery

All new GitHub Issues, Pull Requests, commit messages, and project documents must be written in professional English.

Preserve historical Chinese source documents and linked English translations.

Follow:

Issue → Branch → Implementation → Tests → Commit → Push → Pull Request → Review → Merge.

After completing implementation:

1. Run and record relevant tests.
2. Commit and push to the Phase 2A branch.
3. Create a PR targeting main.
4. Verify GitHub Actions CI.
5. Provide exact local startup and migration instructions.
6. Document the complete physician workflow for manual acceptance.
7. Report changed files, database migrations, test outcomes, known limitations, Issue, Commit SHA, and PR link.

Do not merge the PR, deploy the application, or begin Phase 2B.

Stop after implementation and wait for my manual acceptance testing.