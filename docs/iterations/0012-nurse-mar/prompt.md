We are ready to begin the next development phase of CareFlow EHR.

**I approve actual implementation of Phase 4B — Medication Administration Record (MAR).**

This is a functional full-stack Django development task, not a documentation-only design exercise.

Repository: KateK77/careflow-ehr

Local directory:
D:\AI-Workspace\Personal\careflow-ehr

Expected starting main commit:
91b3a11806fe102bac0328348da594c9f4813ab5

Verify the current main HEAD, clean working tree, existing architecture, and merged Phase 4A functionality before beginning.

## 1. Development Plan

Divide Phase 4B into two implementation increments:

**Phase 4B-1 — Nurse MAR Workspace & Administration Recording**

**Phase 4B-2 — MAR Exceptions, Corrections & Chart Integration**

Use the established GitHub workflow:

Issue → Development Branch → Implementation → Tests → Documentation → Commit → PR → CI.

Create separate GitHub Issues, branches, and Pull Requests.

Use stacked PRs:
- 4B-1 targets main.
- 4B-2 targets the 4B-1 branch.

Implement both increments sequentially, with automated verification before continuing to the next.

Keep both PRs OPEN and UNMERGED.

The user will perform one consolidated manual UAT after development is complete.

Do not request intermediate manual testing.

## 2. Review Existing Implementation

Inspect:

- Phase 3A Nursing Workspace
- Phase 4A Medication Orders
- Phase 4A Pharmacy Review and Dispensing
- Patient and Encounter models
- Physician Workspace
- Signed SOAP notes
- Allergy and MedicationStatement history
- Role-based authorization
- Versioned domain events and audit history
- Existing UI templates, forms, browser workflows and tests

Maintain the existing Django 5.2 modular monolith, server-rendered templates and synthetic-only data boundary.

Do not create a disconnected MAR demo. Integrate with existing patient, Encounter, signed medication order, pharmacy and nursing records.

## 3. Phase 4B-1 — Nurse MAR Workspace

Implement a functional MAR workspace for authorized Nurse users.

Core functionality:

1. Display eligible simulated medication administration tasks.
2. Filter by assigned patient, Encounter, medication and status.
3. Display patient identity, MRN and relevant Encounter context.
4. Display immutable signed medication-order details.
5. Display current pharmacy verification and simulated dispensing status.
6. Display historical allergy assessment as context, without claiming medication safety.
7. Record a fictional administration event.
8. Capture simulated administered quantity, actual event time, nurse identity and optional fictional notes.
9. Display administration status and event history.
10. Integrate MAR into the existing Nursing Workspace.

Establish an explicit, documented policy for MAR eligibility and task creation.

At minimum, require a valid signed, noncancelled medication order and any pharmacy prerequisites defined by the approved simulation workflow.

Pharmacy verification, simulated dispensing and medication administration must remain independent states.

Do not automatically mark medication as administered when the pharmacy records dispensing.

Do not derive real administration schedules or medical dosing decisions from free-text frequency or duration.

If a simulated scheduled-dose model is introduced, use explicitly configured fictional task slots with stable identifiers, not inferred clinical schedules.

Prevent duplicate administration of the same task or administration slot.

## 4. Phase 4B-1 — Permissions and Validation

Only appropriately authorized Nurse users may record simulated administration events.

Physicians may view authorized MAR records but cannot impersonate a nurse or silently create administration events.

Pharmacists may view only MAR-related information explicitly needed for the approved workflow; they must not inherit broad clinical-chart permissions.

FrontDesk and Lab Staff must not access MAR clinical details.

Administrator access alone must not permit nursing administration actions.

Enforce:
- Patient and Encounter relationship validation.
- Signed medication-order eligibility.
- Pharmacy prerequisites.
- Valid fictional quantity and timestamp.
- Explicit confirmation before a simulated administration.
- Server-side authorization and CSRF.
- Optimistic version checks.
- Duplicate-request and stale-form protections.
- Transactional persistence and audit logging.

Use synthetic values only.

## 5. Phase 4B-2 — Exceptions, Corrections & Chart Integration

Implement additional MAR workflows:

- Administered
- Held
- Refused
- Omitted / Not given

Require an appropriate fictional reason for exceptions.

Record the actor, timestamp, Encounter, linked medication order and task reference.

Define allowed transitions and terminal states explicitly.

Support corrections to inaccurate MAR documentation through an auditable correction mechanism.

Corrections must preserve the original recorded event, original author, timestamps and the reason for correction.

Do not silently overwrite, erase or delete historical MAR events.

Distinguish a corrected historical record from the currently effective administration status.

Integrate MAR history into:

- Patient Chart
- Encounter detail
- Physician Workspace
- Nursing Workspace
- Relevant medication-order detail/history pages

Show readable statuses, chronology, order identifiers and audit provenance.

Preserve signed medication orders and signed SOAP notes unchanged.

## 6. Encounter Completion Boundaries

Define explicit behavior for completed Encounters.

A completed Encounter must not be reopened or silently modified by MAR actions.

For this increment, prioritize recording simulated administrations during an eligible active Encounter.

Do not automatically create new administration events for completed Encounters.

If an amendment or late-entry workflow is needed, design it as a separately authorized, provenance-preserving action rather than bypassing Encounter state restrictions.

Existing Phase 4A pharmacy processing after Encounter completion must continue to work unchanged.

## 7. User Interface

Build actual functional Django views and templates.

Include:

- Nurse MAR worklist
- Patient-specific MAR
- Administration detail
- Record simulated administration
- Held / Refused / Omitted workflows
- Correction workflow
- MAR history and audit trail
- Physician read-only MAR summary
- Navigation from the existing Nursing and Physician workspaces

Use the current CareFlow EHR design system.

Ensure:
- Readable table labels
- Clear patient identity
- Clear medication-order identifiers
- Explicit fictional-data confirmation
- Useful validation messages
- Responsive tables
- Keyboard-accessible controls
- No nonfunctional placeholder actions
- No raw Python dictionaries or internal event codes in ordinary UI

Every clinical screen must display DEMO — NOT FOR CLINICAL USE.

## 8. Database Models and Migrations

Design suitable domain models, potentially including:

- MedicationAdministrationTask
- MedicationAdministrationEvent
- MedicationAdministrationCorrection

Choose the final structure based on the existing architecture.

Use additive migrations and protected relationships.

Support immutable event provenance and reliable duplicate prevention.

Do not modify existing signed medication-order or SOAP records.

Database safety requirements:

- Never migrate the original db.sqlite3.
- Never reset or reseed existing databases.
- Never overwrite Phase 3B or Phase 4A preview databases.
- Never overwrite the Phase 4A UAT or smoke databases.
- Preserve all existing synthetic patients, appointments, encounters, medication orders, pharmacy history and audit events.
- Use newly created isolated test databases for automated tests.
- Use a separate, consistently backed-up preview clone for the new MAR implementation.
- Verify integrity, foreign keys and existing data preservation before and after additive migrations.

The prior Phase 4A user-performed UAT records must remain intact.

## 9. Automated Verification

Add regression tests for:

- MAR task eligibility
- Signed medication-order relationship
- Pharmacy prerequisites
- Successful administration recording
- Held, Refused and Omitted states
- Required exception reasons
- Incorrect patient or Encounter links
- Duplicate administration prevention
- Stale submissions and version conflicts
- Unauthorized access by role
- Audit rollback and event preservation
- Corrections and immutable history
- Encounter completion boundaries
- Physician read-only views
- Existing Pharmacy and Medication Order workflows
- Signed SOAP preservation

Run:

- Django system checks
- Migration consistency checks
- Full Django regression suite
- Existing relevant Chromium workflows
- New MAR Chromium workflows
- GitHub Actions CI

Use isolated test databases.

Report exact test counts and any failures.

Do not report automated tests as manual UAT.

## 10. Scope Restrictions

This remains an educational synthetic EHR prototype.

Do not implement:

- Real medication administration
- Real clinical dosing calculations
- Real barcode medication administration
- Automated medication safety clearance
- Real prescribing or pharmacy integrations
- Medication pumps or bedside devices
- Controlled-substance handling
- Automated treatment recommendations
- Production deployment
- Billing or insurance features
- Unrelated hospital modules

Any future clinical decision support or barcode workflow requires separately approved scope and validation.

## 11. GitHub Deliverables

For each increment:

1. Create an English GitHub Issue.
2. Create a development branch.
3. Implement the approved functionality.
4. Add migrations, tests and documentation.
5. Run automated verification.
6. Commit and push the changes.
7. Open an English Pull Request.
8. Confirm GitHub Actions passes.

Maintain the existing English documentation and iteration history.

Do not rewrite historical commits.

Do not force-push.

Do not merge either PR.

Do not start another phase.

## 12. Final Report

After completing both increments, provide:

1. GitHub Issue and PR links.
2. Branch names and exact commit SHAs.
3. Implemented MAR functionality.
4. New models and migrations.
5. Django test results.
6. Chromium results.
7. GitHub Actions CI links.
8. Database preservation evidence.
9. Remaining limitations.
10. Safe local preview startup instructions.
11. A consolidated, step-by-step manual UAT checklist using existing synthetic accounts.

Stop after both increments are implemented, published and automatically verified.

Wait for user-performed consolidated manual UAT and explicit merge approval.