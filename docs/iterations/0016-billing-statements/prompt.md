We are ready to continue CareFlow EHR development.

**I approve implementation of Phase 6 — Billing & Insurance.**

This is a full-stack Django implementation task, not documentation-only work.

Repository: KateK77/careflow-ehr

Local directory:
D:\AI-Workspace\Personal\careflow-ehr

## 1. Starting Baseline and GitHub Workflow

The current approved main baseline is:

00c624553cc265e6275a9d2750ab0041a7e6d97f

Phase 5 is implemented but awaiting consolidated manual UAT:

- PR #32 — Phase 5A Patient Portal
- PR #34 — Phase 5B Messaging & Appointment Requests

The expected Phase 5B head is:

1d1cc8fa1da38d65c728f5403237bd7abd15b6e6

Verify all actual branch heads, PR states, local working-tree cleanliness and CI before proceeding. Stop if the baseline has changed unexpectedly.

Implement two new increments:

- Phase 6A — Billing, Coverage & Patient Statements
- Phase 6B — Simulated Claims, Denials, Appeals & Payments

Create a separate English GitHub Issue, development branch, documentation record and PR for each increment.

Use this stacked structure:

- PR #32: Phase 5A → main
- PR #34: Phase 5B → Phase 5A
- Phase 6A → phase/0015-portal-messaging-requests
- Phase 6B → Phase 6A branch

Implement Phase 6A completely before starting Phase 6B.

Run automated verification after each increment.

All Phase 5 and Phase 6 PRs must remain OPEN and UNMERGED.

The user explicitly requests postponing Phase 5 manual UAT and performing one consolidated Phase 5 + Phase 6 UAT after both Phase 6 increments are implemented.

Do not request intermediate manual testing.

## 2. Review Existing Architecture

Inspect the existing modules and conventions:

- Patient Management
- Clinical Encounters and signed SOAP documentation
- Scheduling and appointment history
- Patient Portal and patient-account ownership
- Patient messages and appointment requests
- Medication Orders, Pharmacy and MAR
- Laboratory Orders and Results
- Staff authentication and role policies
- Domain services, versioning, transactions and AuditEvent
- Existing migrations, automated tests, Chromium workflows and GitHub CI

Maintain the current Django modular monolith, server-rendered UI, SQLite development environment and synthetic-data boundaries.

Do not create an isolated billing demo disconnected from existing Patient, Encounter or Patient Portal records.

Reference the original W10 Billing loop requirement:

Completed visit → mock charges → statement → patient views statement → simulated payment → paid state.

## 3. Phase 6A — Billing Staff Workspace

Implement a functional Billing Workspace for authorized BillingStaff users.

Features:

- Billing worklist
- Completed-Encounter billing eligibility
- Synthetic charge catalog
- Versioned charge catalog entries
- Mock charge codes and descriptions
- Fixed fictional prices
- Add charge items to eligible Encounters
- Edit eligible draft charge items
- Remove or void draft charges with appropriate history
- Review and finalize a billing statement
- Generate an itemized patient statement
- Display billing and statement history
- Search and filter by permitted patient, Encounter, status and date
- Audit every relevant write

Only completed Encounters should be eligible for ordinary charge capture in this increment.

Never reopen Encounters or modify signed SOAP notes.

Do not automatically infer charges from clinical diagnoses, laboratory results, medication orders or MAR events.

Charges must require an explicit authorized billing action.

Use fictional charge codes instead of representing unverified CPT, HCPCS, DRG or insurer prices as authoritative.

Implement an explicit statement lifecycle such as:

Draft → Finalized → Released to Patient

with documented void, correction and adjustment policies.

Finalize immutable monetary snapshots.

Historical finalized statements must not be silently rewritten.

## 4. Phase 6A — Synthetic Insurance Coverage

Implement patient-linked fictional insurance coverage records.

Features:

- Fictional payer name
- Synthetic policy identifier
- Coverage type
- Coverage effective dates
- Active / inactive / historical status
- Explicit coverage version history
- Authorized staff management
- Patient-facing coverage summary if permitted

Do not implement:

- Real insurer eligibility checks
- Real policy verification
- Real member identification lookups
- External payer APIs
- Real insurance cards
- Real patient financial information

Coverage must be explicitly associated with a Patient.

Prevent cross-patient coverage assignment and unauthorized changes.

An insurance record must not imply genuine coverage or payment eligibility.

## 5. Phase 6A — Charges and Financial Integrity

Use Decimal or integer minor units for monetary calculations.

Never use binary floating-point arithmetic for stored amounts.

Implement:

- Quantity
- Unit price
- Line subtotal
- Statement subtotal
- Explicit mock adjustments where approved
- Total
- Patient balance
- Financial status

Define and enforce clear financial invariants.

Prevent:

- Negative quantities
- Invalid monetary precision
- Unauthorized price changes
- Duplicate charge commands
- Incorrect patient or Encounter links
- Stale-version writes
- Silent modification of finalized statements
- Inconsistent statement totals

Use transactional services and optimistic concurrency control.

Preserve versioned event history and audit provenance.

If corrections to finalized financial records are required, use documented adjustment or superseding records instead of overwriting the original statement.

## 6. Phase 6A — Patient Portal Billing

Integrate Billing with the existing Phase 5 Patient Portal.

Add working patient-facing views for:

- Released statements
- Itemized fictional charges
- Statement dates
- Mock insurance information where appropriate
- Current simulated balance
- Statement history

A patient must only see statements belonging to their explicitly linked Patient record.

Never display unreleased drafts or internal staff billing notes.

Do not expose billing details through guessed statement IDs or direct URL changes.

Keep patient billing separate from medical records and clinician documentation.

Use a mobile-friendly layout consistent with Phase 5.

## 7. Phase 6B — Simulated Insurance Claims

Implement an internal mock claim workflow.

Features:

- Generate a draft mock claim from eligible finalized billing records
- Select a synthetic patient coverage record
- Review charge items and total
- Explicitly submit the claim to an INTERNAL simulator
- Record simulated adjudication outcomes
- Track claim status
- Preserve claim versions and history
- Display assigned financial responsibility
- Link claim history to the originating statement and Encounter

Suggested claim lifecycle:

Draft → Submitted to Simulator → Pending Adjudication → Approved / Partially Approved / Denied

Design the exact state machine and validation rules before implementation.

A claim submission must NEVER communicate with a real payer.

Do not generate, transmit or export genuine EDI 837 transactions.

Do not implement real clearinghouse or insurer integrations.

Use fictional payer identifiers and simulated claim outcomes only.

Adjudication should be an explicit authorized action or deterministic configured simulation, not an AI-generated insurance coverage decision.

Clearly label the status as simulated.

## 8. Phase 6B — Denials and Appeals

Implement a complete fictional denial-and-appeal workflow.

Features:

- Mock denial reasons
- Clear denial status
- Denial history
- Create an appeal draft
- Add fictional explanation and supporting internal record references
- Explicitly submit the appeal to the INTERNAL simulator
- Review an appeal
- Approve or uphold the original denial
- Record the resulting simulated claim status
- Preserve full history and provenance

Use fictional denial categories and codes unless a separate validated code source is explicitly approved.

Do not create real legal or insurance representations.

Do not automatically invent clinical evidence.

If supporting records are linked, enforce their existing access controls and record precise source references.

Do not modify signed clinical documentation to justify an appeal.

An appeal should not automatically change claim status or create payment without an authorized simulated adjudication action.

Preserve the denied claim and all appeal revisions.

Do not implement an AI denial-analysis or appeal-writing agent in this phase.

## 9. Phase 6B — Simulated Payments

Implement an internal payment-recording workflow.

Features:

- Simulated payer payments
- Simulated patient payments
- Payment amount
- Payment source classification
- Fictional transaction reference
- Payment date and recorder
- Partial or full simulated payment
- Remaining balance
- Payment history
- Patient-visible payment status
- Adjustments or reversals using auditable events

Never collect or store:

- Credit card numbers
- CVV
- Bank account numbers
- Real payment credentials
- Real insurance payment information

Do not connect Stripe, PayPal, bank APIs, insurers or actual payment processors.

No real money may move through the application.

Enforce:

- Nonnegative balances unless explicitly modeled credits are supported
- Idempotent transaction recording
- No unexplained overpayments
- Atomic balance updates
- Server-side authorization
- Audit and immutable historical payment records

A simulated payment must be clearly labelled as fictional.

## 10. Roles and Permissions

Introduce or reuse narrowly scoped BillingStaff permissions.

Define explicit permissions for:

- BillingStaff
- Administrator
- FrontDesk
- Physician
- Nurse
- Pharmacist
- Lab Staff
- Patient Portal users

BillingStaff should have only the minimum patient and Encounter information required for mock billing.

BillingStaff must not automatically receive unrestricted clinical-note, MAR or laboratory-result editing permissions.

Administrator access alone should not silently bypass billing-specific approval rules.

FrontDesk should not gain unrestricted financial-adjudication permissions.

Physicians may view authorized encounter billing summaries if appropriate but may not alter simulated claims or payments without an explicitly approved role.

Patients must only see their own released statements and payment summaries.

Backend permissions must enforce these boundaries independently of UI navigation.

Test direct URL and POST access.

## 11. Database Models and Migrations

Design additive domain models based on existing architecture.

Candidate concepts:

- SyntheticPayer
- PatientCoverage
- SyntheticChargeCatalog
- EncounterCharge
- PatientStatement
- StatementLineSnapshot
- MockInsuranceClaim
- MockClaimAdjudication
- MockClaimDenial
- MockAppeal
- SimulatedPayment
- BillingEvent

These are conceptual candidates, not a mandate to create unnecessary tables.

Choose a clean schema with explicit ownership, immutable snapshots, versioning and transactional audit records.

Use protected relationships and database constraints.

Preserve monetary precision and internal referential integrity.

Create only additive migrations.

Never remove or rewrite existing clinical migrations.

## 12. Database Preservation — Critical

Do not run migrations against the original db.sqlite3.

Do not modify, reset, reseed, overwrite or restore any existing Phase 3B, 4A, 4B or Phase 5 preview database.

Preserve all original clinical and UAT data.

Use a freshly named, consistently backed-up clone of the Phase 5B integrated preview for the Phase 6 development preview.

If an existing Phase 5 preview contains synthetic portal accounts, retain their account links and credentials rather than overwriting them.

Before migrating a new clone:

- Verify source and target paths.
- Create a consistent SQLite backup.
- Record source integrity and foreign-key results.
- Record table and row baselines.
- Verify the migration plan.
- Apply only the approved additive migrations to the new clone.
- Recheck integrity and preservation afterward.

Never claim all files are unchanged if the newly created Phase 6 preview is intentionally modified.

Use isolated databases for automated tests.

## 13. User Interface

Build functional Django pages following the current CareFlow design system.

Staff-facing pages should include:

- Billing Workspace
- Synthetic Charge Catalog
- Coverage Management
- Encounter Charge Capture
- Statement Preview and Finalization
- Statements and Financial History
- Mock Claims Worklist
- Claim Review and Adjudication
- Denial and Appeal History
- Simulated Payments

Patient Portal pages should include:

- Billing / Statements
- Statement Detail
- Mock Coverage Summary
- Simulated Payment History

Use clear links, actionable workflows and readable statuses.

No nonfunctional buttons, fake submission results or placeholder screens.

No raw Python dictionaries or internal event codes in ordinary user-facing text.

Every page must clearly indicate:

DEMO — NOT FOR CLINICAL USE

Include a separate notice that all amounts and transactions are fictitious.

## 14. Automated Verification

Add regression tests covering:

- Charge catalog revisions
- Completed-Encounter billing eligibility
- Charge creation and editing
- Monetary arithmetic and rounding
- Statement finalization and immutability
- Patient statement release
- Patient-account and billing isolation
- Role and URL access denial
- Duplicate command protection
- Stale submissions and optimistic versions
- Atomic rollback with audit failure
- Coverage validation
- Claim creation and internal submission
- Simulated adjudication
- Claim denial
- Appeal draft, submission and review
- Claim and statement history preservation
- Simulated partial and full payments
- Reversals and balance invariants
- Cross-patient isolation
- Portal billing visibility
- Preservation of prior Phase 5 messaging, appointment requests and clinical workflows

Run:

- Django system checks
- Migration consistency checks
- Full Django regression suite
- Relevant Chromium workflows
- New billing and claims Chromium workflows
- GitHub Actions CI

Use newly created isolated test databases.

Do not remove earlier regression tests.

Do not report unperformed manual UAT as passed.

## 15. GitHub Workflow and Documentation

For Phase 6A:

1. Create an English Issue.
2. Create a new branch from the verified Phase 5B head.
3. Implement Billing, Coverage and Patient Statements.
4. Add tests, migrations and documentation.
5. Run automated verification.
6. Commit and push.
7. Open a PR targeting the Phase 5B branch.
8. Confirm GitHub Actions passes.

For Phase 6B:

1. Create an English Issue.
2. Branch from the verified Phase 6A head.
3. Implement Claims, Denials, Appeals and Simulated Payments.
4. Integrate with Phase 6A statements and Phase 5 Patient Portal.
5. Add tests, migrations and documentation.
6. Run complete verification.
7. Commit and push.
8. Open a PR targeting the Phase 6A branch.
9. Confirm CI passes.

Do not force-push or rewrite shared history.

Do not automatically merge any Phase 5 or Phase 6 PR.

Do not start Phase 7.

Do not deploy the application or create a release.

## 16. Consolidated Phase 5 + Phase 6 UAT

After both increments are implemented, prepare one combined manual acceptance guide.

It must include:

1. Two linked synthetic Patient Portal accounts.
2. Cross-patient data-isolation tests.
3. Patient appointment and medical-record visibility.
4. Laboratory result release visibility.
5. Patient messaging and physician replies.
6. Patient appointment requests and staff review.
7. BillingStaff account provisioning.
8. Completed Encounter charge capture.
9. Statement finalization and patient release.
10. Patient viewing the released bill.
11. Synthetic insurance claim creation and adjudication.
12. Denial, appeal and re-adjudication.
13. Simulated patient and payer payments.
14. Balance and statement-status reconciliation.
15. Direct unauthorized URL tests.
16. Preservation of signed SOAP, lab, medication, pharmacy and MAR histories.

Clearly distinguish manually untested scenarios from passing automated test evidence.

Do not ask the user to repeat previous Phase 4B manual UAT.

## 17. Final Deliverables

After both increments are complete, return:

1. Phase 6A and 6B GitHub Issue links.
2. Both PR links.
3. Exact branch names and head SHAs.
4. Implemented functionality and working routes.
5. New models and migration names.
6. Django regression test counts.
7. Chromium workflow results.
8. GitHub Actions CI links.
9. Database preservation evidence.
10. Known defects and scope limitations.
11. Safe integrated-preview startup instructions.
12. One consolidated Phase 5 + Phase 6 manual UAT checklist.

Stop after both increments have been implemented, published and automatically verified.

The user will perform consolidated manual UAT afterward and explicitly approve any PR merges.