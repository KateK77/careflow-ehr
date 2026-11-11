We have completed the Phase 3B laboratory design review.

**I now approve the implementation of Phase 3B-1 — Laboratory Catalog & Physician Orders only.**

This is an actual application development task, not another design-only task.

Project directory:
D:\AI-Workspace\Personal\careflow-ehr

Repository:
KateK77/careflow-ehr

Current main baseline:
56ea8b332525926b02759b2afefa93166bd52d31

Latest approved reference for this implementation scope:
Phase 3B design v0.2 at commit bea741de88fd0c719eb4ed39cf70ec7fd2959f3b

Design PR:
https://github.com/KateK77/careflow-ehr/pull/16

Read the v0.1 specification together with the v0.2 overrides, especially `v0.2/increments.md`. Follow the 3B-1 scope precisely.

## 1. Start the Implementation Workflow

1. Verify the latest main commit and clean Git working tree.
2. Create a new GitHub implementation Issue for Phase 3B-1.
3. Create a new feature branch from the verified latest main.
4. Record the approved implementation scope and acceptance criteria in English.
5. Preserve existing Issues, branches, requirements, historical prompts and documentation.
6. Keep design PR #16 open and unmerged. Reference its exact v0.2 commit; do not merge it as part of this task.

## 2. Implement the Laboratory Django Module

Create a new `careflow/labs` application consistent with the existing Django modular-monolith architecture.

Implement the Phase 3B-1 models and infrastructure:

- LabTestCatalog
- LabOrder
- LabSpecimen (pending state and submission dependency only)
- LabEvent and durable idempotency receipts

Do not implement LabResult, LabResultReview, LabReviewAssignment or laboratory result publishing in this increment.

Follow the planned additive migration boundaries in v0.2.

## 3. Laboratory Catalog

Implement a functional synthetic test catalog.

Requirements:
- Fictional test codes and names.
- Explicit specimen types.
- Versioned, immutable component definitions.
- Active/inactive catalog revisions.
- Administrator-only management actions.
- Physician catalog browsing.
- Appropriate validation, permissions and audit records.

No real laboratory terminology or clinical decision rules.

## 4. Physician Lab Orders

Implement these working features:

- Create an order from an authorized in-progress Encounter.
- Derive Patient, Encounter and ordering Physician server-side.
- Select an active test panel.
- Save and reopen a draft.
- Edit the draft with version checks.
- Preview and explicitly confirm submission.
- Submit the order with an atomic pending specimen record.
- View submitted orders and independent status information.
- Cancel eligible draft/submitted orders with a reason.
- View patient and encounter laboratory order history.

Implement `Draft`, `Submitted`, and `Cancelled` order behavior for this increment. Do not fake downstream fulfilled/result states.

Submitting an order must create exactly one pending specimen attempt with proper provenance and transactional audit.

No collection or receipt workflow is implemented yet.

## 5. Application Integrity

Reuse existing patterns for:

- Role-based access and Physician ownership.
- Patient/Encounter relationship validation.
- Provider serialization and optimistic versions.
- Durable command UUIDs and idempotent POST handling.
- Duplicate-order warning and explicit repeat-test confirmation.
- CSRF, safe errors and server-side validation.
- Transactional AuditEvent/LabEvent recording.
- Clinic-local timestamps and UTC persistence.

Orders submitted before Encounter completion must remain accessible afterward.

Do not change completed Encounter records, Appointment provenance, signed SOAP notes, existing history or nursing records.

## 6. UI Integration

Implement actual Django templates and URLs using the existing CareFlow design.

Add:
- Laboratory Catalog page.
- Create Lab Order page.
- Edit Draft page.
- Review and Confirm Order page.
- Lab Order Detail page.
- Patient Lab Order History page.
- Appropriate links from Physician Workspace, Encounter Detail and Patient Chart.

Maintain the existing DEMO — NOT FOR CLINICAL USE notice, patient banner, navigation, readable forms and responsive layout.

Do not create nonfunctional placeholder buttons.

Clearly show that specimen collection and laboratory results are not available until a future increment.

## 7. Migration and Database Safety

Before any local migration:
- Inventory current tables, migrations and record counts.
- Prepare and verify a consistent backup.
- Verify SQLite integrity and foreign keys.
- Review the additive migration plan.
- Ensure existing patient, scheduling, clinical, history, nursing and audit data will be preserved.

Generate application migrations and test them against isolated test databases.

**Do not apply migrations to the user's existing local SQLite database without separate approval.**

Never reset, reseed, replace, or delete the existing database.

## 8. Testing

Add automated tests for:

- Catalog versions, validation and access.
- Physician draft creation, edit and persistence.
- Submission and pending specimen creation.
- Cancellation and invalid transitions.
- Duplicate-order confirmation.
- Idempotent command replay.
- Wrong-patient and wrong-encounter protection.
- Role and direct-URL denials.
- Stale versions and competing submissions.
- Encounter completion interaction.
- Atomic audit events and rollback behavior.
- Preservation of signed SOAP and existing clinical records.

Run existing Django system checks, migration consistency and the full regression suite.

Run relevant Chromium tests using isolated test data.

Do not change existing tests merely to conceal regressions.

## 9. GitHub Publication

Complete the implementation and prepare:

- New implementation Issue.
- Phase 3B-1 development branch.
- Application code and additive migration files.
- Automated tests.
- Updated English iteration documentation.
- Pull Request targeting main.
- GitHub Actions CI results.

Do not merge the implementation PR.

## 10. Final Report

Provide:

1. Implementation Issue URL.
2. Branch name.
3. Pull Request URL.
4. Implemented functional pages and routes.
5. New models and migrations.
6. Automated test and CI results.
7. Database backup/migration status.
8. Exact local setup instructions.
9. Step-by-step manual UAT instructions using existing synthetic patients and accounts.
10. Remaining limitations and known issues.

Do not start Phase 3B-2 or Phase 3B-3.

Stop after publishing the working Phase 3B-1 implementation PR for user testing.