We are ready to begin developing the next CareFlow EHR functionality.

**I approve implementation of Phase 4A — Medication Orders & Pharmacy, divided into two controlled development increments: 4A-1 and 4A-2.**

This is an actual Django application development task, not a documentation-only design exercise.

Project directory:
D:\AI-Workspace\Personal\careflow-ehr

GitHub repository:
KateK77/careflow-ehr

Verified starting main commit:
ea477e305a94e57aa8ba7c5390bc2def07f79cb8

Verify the current main HEAD before beginning.

## 1. Development Strategy

Implement the following increments sequentially:

**Phase 4A-1 — Medication Catalog & Physician Orders**

**Phase 4A-2 — Pharmacy Verification & Simulated Dispensing**

Create a separate GitHub Issue, development branch, iteration record and Pull Request for each increment.

Use stacked branches:

- Phase 4A-1 → main
- Phase 4A-2 → Phase 4A-1 branch

Keep both PRs open and unmerged.

The user explicitly wants consolidated manual UAT after both increments are implemented.

Automated tests, CI and technical verification must still pass at each increment.

Do not mark unperformed manual tests as passed.

## 2. Review Existing Architecture

Inspect the latest integrated codebase, including:

- Patient management
- Physician Workspace and Encounter
- Clinical History and MedicationStatement
- Allergy records and review status
- Existing laboratory ordering architecture
- Nursing Workspace
- Authentication and permissions
- AuditEvent and domain events
- Transactional services, concurrency and versioning
- Current GitHub development workflow

Reference the existing original requirements, especially Medication Orders and Pharmacy workflows.

Preserve all completed functionality.

Do not treat MedicationStatement as an executable prescription or automatically overwrite patient-reported medication history.

## 3. Phase 4A-1 — Medication Catalog & Physician Orders

Create a dedicated Django medication-ordering module consistent with the existing modular-monolith architecture.

Implement a working synthetic medication catalog with:

- Fictional medication identifiers using a SYN- namespace
- Synthetic display names
- Fictional dosage forms and strengths
- Controlled route and frequency choices
- Catalog revisions and activation
- Administrator management
- Appropriate Physician browsing permissions
- Immutable historical catalog snapshots

Implement Physician medication ordering:

- Create an order from an authorized in-progress Encounter.
- Select a synthetic medication.
- Enter proposed dose, route, frequency, duration, quantity and fictional instructions.
- Save and reopen a draft.
- Edit the draft with optimistic version checks.
- Preview the complete order.
- Explicitly confirm and sign the order.
- Preserve original author, signature, timestamp and ordered content.
- Cancel an eligible order with a required reason.
- View medication-order history in Patient Chart and Encounter.
- Maintain transactional audit and version history.

Keep the medication order lifecycle separate from pharmacy verification and dispensing.

Propose and document explicit state transitions before implementing them.

Use fictional medication configurations only. Do not calculate real-world doses, recommend treatments or claim clinical safety validation.

## 4. Phase 4A-1 Permissions and Integrity

- Only the authorized assigned Physician can create, edit or sign their own medication orders.
- Administrator alone cannot sign prescriptions.
- FrontDesk cannot access detailed medication orders.
- Nurse may have appropriately scoped read-only access.
- Lab Staff must not inherit medication or pharmacy permissions.
- Preserve signed-note immutability and Encounter provenance.
- Prevent wrong-patient and wrong-encounter relationships.
- Enforce server-side validation and CSRF.
- Handle stale updates, double submission and durable idempotency.
- Signatures must not be silently changed or removed.
- Preserve all actions through atomic domain and audit events.

Do not implement real electronic prescribing.

## 5. Phase 4A-2 — Pharmacy Workspace

After Phase 4A-1 implementation passes its automated verification gates, continue with Phase 4A-2.

Introduce a narrowly scoped Pharmacist role without expanding existing clinical or demographic access.

Implement a functional Pharmacy Workspace:

- Pharmacy verification worklist
- Signed medication-order queue
- Explicit order assignment or claim
- Restricted requisition and order details
- Review of synthetic medication instructions
- Verification approval
- Request clarification with a reason
- Reject an order with a reason
- Simulated dispensing after the permitted verification state
- Dispensing quantity and event provenance
- Status and audit history
- Physician-visible pharmacy status and clarification information
- Patient Chart and Encounter integration

Preserve independent medication-order, pharmacy-review and simulated-dispensing states.

Support pharmacy follow-up after Encounter completion for orders signed before completion, using explicit state guards.

Do not reopen completed Encounters or alter signed SOAP content.

A Pharmacist must not gain unrelated clinical-note or patient-directory permissions through pharmacy assignment.

## 6. Medication Safety and Scope Restrictions

This is a synthetic educational prototype.

- No real prescriptions.
- No e-prescribing, EPCS or real pharmacy networks.
- No controlled-substance processing.
- No physical medication dispensing.
- No clinical dosing recommendations.
- No automated diagnosis or treatment advice.
- No real interaction-checking or medication-safety certification.
- No automatic allergy-clearance claims.
- No billing or insurance claims.
- No medication administration record (MAR) in this phase.
- No external services or production deployment.

Existing Allergy and MedicationStatement data may be shown as authorized context, clearly labelled as historical/unverified where appropriate.

Do not silently infer drug safety from the absence of recorded allergies.

Any simulated warning must be clearly identified as a non-clinical demonstration, not an authoritative clinical decision-support result.

## 7. Data Models and Migrations

Design and implement only the models required for each approved increment.

Evaluate candidate concepts such as:

- SyntheticMedicationCatalog
- MedicationOrder
- MedicationOrderEvent
- PharmacyReview
- PharmacyDispenseEvent

Adjust the model structure where needed for correctness, auditability and clean module ownership.

Use protected relationships, integer versions, explicit state constraints, immutable signatures and append-only history.

Create additive migrations only.

Before any migration against an existing preview or copied database:

1. Verify the exact database path.
2. Capture a consistent backup.
3. Record integrity and foreign-key results.
4. Record existing clinical row and schema baselines.
5. Review the migration plan.
6. Verify protected records after migration.

IMPORTANT:

The original db.sqlite3 has not received the Phase 3B laboratory migrations.

Do not run any migration against the original database.

Preserve the existing Phase 3B previews, smoke-test databases, account passwords and backups.

Create new, separately named disposable databases or verified clones for Phase 4A testing.

Never reset, reseed, delete or overwrite an existing database.

## 8. User Interface

Build actual functional Django templates following the existing CareFlow design system.

Include:

- Medication Catalog
- Physician Medication Order Composer
- Draft Order Detail/Edit
- Review and Sign
- Medication Order History
- Pharmacy Workspace
- Pharmacy Verification Detail
- Clarification and Rejection Workflows
- Simulated Dispensing Record
- Patient Chart and Encounter Summaries

Maintain:

- DEMO — NOT FOR CLINICAL USE
- Fixed patient identity context
- Clear current state and provenance
- Readable labels and validation errors
- Accessible tables and responsive layouts
- Complete audit and version history

Do not expose raw Python dictionaries, internal constraint names or raw action identifiers as normal user-facing content.

Do not create nonfunctional placeholder buttons.

## 9. Automated Testing

For Phase 4A-1, test:

- Catalog revision/activation
- Medication order creation/editing
- Physician ownership and context
- Review/signature immutability
- Cancellation
- Duplicate commands
- Stale versions and concurrency
- Role denials
- Audit rollback
- Encounter completion boundaries
- Existing feature preservation

For Phase 4A-2, additionally test:

- Pharmacist assignment
- Minimum-necessary access
- Verification and clarification
- Rejection and prohibited transitions
- Simulated dispensing
- Independent state transitions
- Unauthorized pharmacy actions
- Duplicate dispensing prevention
- Completed-Encounter follow-up
- Audit and provenance preservation

Run the complete existing regression suite, new tests, migration checks and relevant Chromium workflows.

Retain existing tests unless a separately reviewed integration change is required.

Do not claim unexecuted browser tests or manual UAT passed.

## 10. GitHub Workflow

For each increment:

1. Create a properly scoped English GitHub Issue.
2. Create a branch from its authorized base.
3. Implement working application functionality.
4. Document design decisions and implementation.
5. Run all applicable verification.
6. Commit and push changes.
7. Open a Pull Request.
8. Verify GitHub Actions CI.
9. Record exact commit SHAs and changed files.

Proceed to 4A-2 only if 4A-1's automated technical gates pass.

Propagate parent changes through normal history-preserving merges where needed.

Do not merge either implementation PR automatically.

## 11. Final Deliverables

Provide:

1. Phase 4A-1 Issue, branch and PR.
2. Phase 4A-2 Issue, branch and PR.
3. Commit SHAs.
4. Implemented features and URLs.
5. New models and migrations.
6. Automated regression test counts.
7. Chromium workflow results.
8. GitHub Actions CI results.
9. Database preservation evidence.
10. Known defects and limitations.
11. Safe integrated-preview startup instructions.
12. Consolidated manual UAT checklist with existing synthetic accounts and the new Pharmacist role.

Do not deploy, create a release, merge the PRs or start MAR development.

Stop after publishing both implementation increments and their verification reports.

The user will perform consolidated manual UAT before approving merges.