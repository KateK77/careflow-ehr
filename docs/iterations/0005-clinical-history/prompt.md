Phase 2A automated verification is complete. I approve starting Phase 2B immediately without waiting for Phase 2A manual UAT.

**Project:** D:\AI-Workspace\Personal\careflow-ehr

**Repository:** KateK77/careflow-ehr

**Phase 2A branch:** phase/0004-physician-workspace

**Phase 2A latest commit:** eff5a2b94891e5deae8304ac2e9036c6dc8eaf43

## 1. Start Phase 2B

Implement **Phase 2B — Longitudinal Medical History, Problems, Allergies, Medications, and Encounter Diagnoses**.

Read the existing English product specification, AGENTS.md, Phase 2A implementation, and architecture decisions before coding.

Create:

- A dedicated Phase 2B GitHub Issue.
- Branch `phase/0005-clinical-history` from the latest Phase 2A branch.
- A stacked Pull Request targeting `phase/0004-physician-workspace`, NOT main.
- Versioned English iteration documentation.

Preserve this approved prompt verbatim.

## 2. Functional Requirements

Implement fully functional, database-backed modules for:

**Medical History**

- Past medical and surgical history
- Family and social history
- Dates, comments, provenance, author and review status
- Create, view, edit and audit functionality

**Longitudinal Problem List**

- Active, resolved and inactive conditions
- Onset and resolution dates
- Optional mock terminology codes
- Clinical status, history and review records
- Preserve resolved problems

**Encounter Diagnoses**

- Primary and secondary diagnoses
- Correct patient and encounter relationships
- Optional association with longitudinal problems
- Physician-only authoring within authorized, in-progress encounters
- Prevent modification of completed encounter diagnoses

**Allergies**

- Allergen, reaction and severity
- Clinical and verification status
- Recording/reviewing staff and timestamps
- Distinguish unknown, not reviewed, no known allergies and documented allergies
- Prevent contradictory allergy status displays

**Medication History**

- Current and historical medication statements
- Name, dose description, route, frequency and dates
- Active, stopped and historical states
- Patient-reported versus documented sources
- Medication review and audit history
- No real prescribing, dispensing or administration

## 3. Patient Chart Integration

Integrate these modules into the existing Phase 2A Physician Workspace and Patient Chart.

Provide functional tabs, clear empty states, consistent patient/encounter context, authorized create/edit actions and longitudinal clinical timeline events.

Maintain the existing CareFlow EHR interface and the DEMO — NOT FOR CLINICAL USE notice.

Do not introduce cosmetic-only functionality.

## 4. Safety and Compatibility

Preserve existing patients, appointments, encounters, SOAP notes and signed documentation.

Use additive Django migrations only, with a safe local backup and database integrity checks.

Enforce backend authorization, patient/encounter isolation, input validation, optimistic concurrency where appropriate, and auditable writes.

Respect the existing role policy: treating physicians maintain authorized clinical data; Nurse and Administrator retain their documented read access; FrontDesk cannot access detailed clinical records.

Never silently modify signed SOAP notes.

Use synthetic data only.

## 5. Testing and Documentation

Run Django system checks, migration checks, the complete automated regression suite and browser tests where feasible.

Test record creation, editing, clinical states, invalid input, cross-patient isolation, access denial, audit events, and preservation of Phase 2A behavior.

Maintain all GitHub Issues, documentation, Commit messages and PR descriptions in professional English.

Preserve historical Chinese source documents and English translations.

## 6. Autonomous Execution

Within the available security permissions, continue coding, testing, committing, pushing and updating the Phase 2B PR without unnecessary interruptions.

Do not bypass enforced approvals.

Do not merge PR #8 or the new Phase 2B PR, force-push, delete data, deploy, or begin Phase 3.

Do not claim either phase has passed manual UAT.

## 7. Final Delivery

After implementation, provide:

- GitHub Issue and stacked PR links
- Implementation Commit SHA
- Complete changed-file summary
- Database migration and preservation report
- Automated test and GitHub CI results
- Local startup instructions
- Manual acceptance checklist for later testing
- Known limitations

Stop once Phase 2B implementation and automated verification are complete. Leave both PRs open for later user acceptance.
