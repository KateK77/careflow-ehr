You are the senior software engineer and technical lead for CareFlow EHR.

I approve starting **Phase 3A — Nursing Workspace, Patient Rooming, Vital Signs, and Nursing Flowsheets**.

Manual UAT for Phase 2A and Phase 2B remains intentionally postponed. Continue automated verification, but do not claim manual acceptance.

Project directory:
D:\AI-Workspace\Personal\careflow-ehr

GitHub repository:
KateK77/careflow-ehr

## 1. Branching and Project Preparation

1. Inspect the current Git working tree and repository state.
2. Verify that Phase 2A PR #8 and Phase 2B PR #10 remain open and unmerged.
3. Read AGENTS.md, the English requirements baseline, Phase 2A/2B architecture decisions, and existing clinical models.
4. Create a Phase 3A GitHub Issue with scope and acceptance criteria in professional English.
5. Create `phase/0006-nursing-workspace` from the latest Phase 2B branch, `phase/0005-clinical-history`.
6. Use a stacked PR targeting the Phase 2B branch, not main.
7. Create `docs/iterations/0006-nursing-workspace/` and preserve this approved prompt verbatim.
8. Preserve existing Django architecture, clinical records, patient data, appointments, encounters, SOAP notes, and audit history.

## 2. Nurse Workspace

Implement a dedicated nursing dashboard with:

- Today's patient worklist, based on existing appointments.
- Patient name, MRN, assigned physician, appointment time and status.
- Search and filters by patient, date and appointment status.
- Links to authorized patient charts.
- Nursing task/status indicators backed by persisted records.
- Clear indications of rooming and vital-sign documentation progress.

Only show actionable controls for implemented workflows. Do not invent pending clinical tasks or display decorative buttons as functional.

## 3. Patient Rooming and Nursing Assessment

Implement basic outpatient rooming documentation.

Fields should include:

- Chief complaint
- Rooming or assessment timestamp
- Recorded nurse
- Pain score
- General nursing observations
- Ready-for-provider indicator

Keep nursing rooming state separate from existing appointment and encounter state machines unless a carefully documented compatibility change is necessary.

Check-in must not automatically start an encounter. Preserve the existing physician-only explicit encounter-start workflow.

Record actor, timestamp and relevant changed fields.

## 4. Vital Signs

Implement structured, persisted vital-sign observations:

- Blood pressure: systolic and diastolic
- Heart rate
- Respiratory rate
- Body temperature with unit
- Oxygen saturation
- Height and weight with units
- Pain score
- Observation time
- Recording nurse and source context

Validate numeric ranges, units and patient/appointment/encounter relationships on the backend.

Use validation to reject malformed values, not to provide clinical diagnosis or automatic treatment recommendations.

Allow corrections through versioned, audited edits. Preserve earlier values in the authorized audit history.

## 5. Nursing Flowsheets

Build a functional time-oriented flowsheet interface.

Requirements:

- Rows represent documented vital-sign measurements.
- Columns represent observation times.
- Show measurement values and units.
- Allow authorized nurses to open and edit permitted observations.
- Support chronological review.
- Display meaningful empty states.
- Ensure responsive overflow handling on smaller screens.

Do not build a visual-only table disconnected from the database.

## 6. Patient Chart Integration

Integrate nursing documentation with the existing clinical chart:

- Show the latest recorded vital signs.
- Display nursing assessments and rooming status.
- Include relevant events in the longitudinal timeline.
- Preserve correct patient and encounter context.
- Make nursing information available to authorized physicians for review.

Existing signed SOAP notes must remain unchanged when nursing documentation is updated.

## 7. Role-Based Permissions

Preserve existing permissions unless explicitly extended for nursing documentation.

- Nurse: Record and edit permitted nursing assessments and vital signs under the documented single-clinic scope.
- Physician: Read authorized nursing observations and clinical records.
- Administrator: Clinical read access; no automatic nursing authoring privilege.
- FrontDesk: Scheduling and demographics access only; no detailed nursing clinical content.

Enforce permissions on the backend for both GET and POST requests.

Prevent unauthorized access, cross-patient data leakage and forged patient/encounter associations.

Document the Phase 3A nursing-write permission extension clearly.

## 8. Database Integrity and Testing

Use additive Django migrations only.

Before migrations:

- Back up the local SQLite database.
- Check integrity and foreign keys.
- Record pre-existing row counts and preservation evidence.

After migrations, verify that existing patients, appointments, encounters, notes, diagnoses, allergies, medication records and audit events remain intact.

Write automated tests for:

- Nurse worklist access and filters
- Nursing assessment creation and editing
- Vital-sign validation and persistence
- Flowsheet rendering
- Role-based read/write restrictions
- Direct URL and unauthorized POST rejection
- Cross-patient/encounter isolation
- Stale updates and audit history
- Clinical timeline integration
- Preservation of signed notes
- Regression tests for all earlier phases

Run Django system checks, migration consistency checks, the complete regression suite, and Chromium browser tests where feasible.

## 9. Safety and Scope

Use synthetic data only.

Display DEMO — NOT FOR CLINICAL USE on clinical screens.

Do not implement real medication administration, MAR, pharmacy, prescribing, lab orders, clinical decision algorithms, billing, AI recommendations or external medical integrations.

Do not deploy to the cloud.

Do not modify historical Chinese source documents or their English translations.

Keep the Phase 1A/1B UX backlog deferred unless a change is necessary for this approved functionality.

## 10. Autonomous Implementation and GitHub Traceability

Within available permissions, perform routine development, testing, commits, pushes, Issue/PR updates and CI verification with minimal interruptions.

Do not bypass security controls or required approvals.

All new documentation, Issues, PRs and commit messages must be in professional English.

Follow the existing versioned iteration-record workflow.

## 11. Final Delivery

When implementation is complete:

1. Commit and push the dedicated Phase 3A branch.
2. Open a stacked PR targeting `phase/0005-clinical-history`.
3. Verify GitHub Actions CI.
4. Provide the Issue, PR and commit links.
5. Provide the changed-file summary.
6. Report migrations, data preservation and test results.
7. Document known limitations.
8. Prepare a manual acceptance checklist for later testing.

Do not merge PR #8, PR #10 or the new Phase 3A PR.

Do not mark any untested phase as manually accepted.

Do not create a release, deploy or begin Phase 3B.

Stop after the implementation and automated verification report.