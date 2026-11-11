We are beginning the requirements and architecture design for the next CareFlow EHR increment.

Project directory:\
D:\AI-Workspace\Personal\careflow-ehr

Repository:\
KateK77/careflow-ehr

Current verified main baseline:\
56ea8b332525926b02759b2afefa93166bd52d31

Proposed increment:\
**Phase 3B — Laboratory Orders & Results**

This phase name and implementation scope are proposals only. Do not treat them as approved for implementation.

## Objective

Design an end-to-end synthetic laboratory workflow integrated with the existing Patient, Appointment, Encounter, Physician Workspace, Clinical History, Nursing Workspace and audit architecture.

Target workflow:

Physician creates lab order → Nurse records specimen collection → Laboratory staff enters and finalizes results → Physician reviews results → Patient chart displays history.

## 1. Review Existing Architecture

Inspect the current Django modules, models, permissions, workflow services, migrations, versioning rules, audit infrastructure, UI conventions and existing iteration documents.

Identify integration constraints and dependencies.

## 2. Define Functional Requirements

Prepare detailed requirements for:

- Laboratory test catalog with small synthetic test panels.
- Physician order creation, draft, submission and cancellation.
- Specimen collection documentation.
- Laboratory staff worklist and result entry.
- Result validation and finalization.
- Corrected results with preserved prior versions.
- Physician result review and acknowledgement.
- Patient chart, encounter and longitudinal results integration.
- Role-based permissions and auditable events.

Clearly distinguish order status, specimen status, result status and physician review status.

Include the scenario where an encounter is completed before laboratory results become available.

## 3. Design Roles and Permissions

Review the existing four staff roles.

Evaluate introducing a narrowly scoped Lab Staff role.

Define read/write permissions and restrictions for Administrator, FrontDesk, Physician, Nurse and Lab Staff.

Prevent unintended access to clinical notes, unrelated patients and other sensitive chart sections.

## 4. Propose Data Models

Evaluate the following candidate models:

- LabTestCatalog
- LabOrder
- LabSpecimen
- LabResult
- LabResultReview
- LabEvent

Specify field types, relationships, uniqueness constraints, versioning, state transitions and provenance.

Use synthetic terminology and test data only.

Explain future mapping considerations for HL7 FHIR R4 ServiceRequest, Observation and DiagnosticReport without implementing FHIR integration.

## 5. Design User Interface

Propose the pages, navigation and user workflows for:

- Physician laboratory ordering
- Patient laboratory order history
- Nursing specimen collection
- Laboratory results workspace
- Result details and correction history
- Physician review and acknowledgement
- Patient chart result summaries

Follow the existing CareFlow design system and server-rendered Django templates.

## 6. Acceptance Criteria and Testing

Specify functional and negative test cases covering:

- Valid order lifecycle.
- Permission denials.
- Wrong-patient and wrong-encounter prevention.
- Duplicate submissions.
- Invalid result values and units.
- Stale version conflicts.
- Post-encounter-completion result workflows.
- Finalized-result correction and auditability.
- Review acknowledgement against the correct result version.
- Existing database and signed SOAP preservation.
- Django regression and Chromium workflows.

## 7. Explicit Exclusions

Do not include:

- Real patient data.
- External laboratory connections.
- Real clinical decision support.
- Medication prescribing or administration.
- Automatic diagnosis or treatment recommendations.
- Insurance billing.
- Production deployment.
- AI agents or LLM functionality.

## 8. GitHub Workflow

1. Verify the latest main baseline and clean worktree.
2. Create a design-only GitHub Issue.
3. Create a documentation branch from main.
4. Write the proposed specification, architecture, state diagrams, permissions matrix and acceptance checklist.
5. Preserve all existing historical requirements and iteration documents.
6. Run documentation checks.
7. Commit and push the design documents.
8. Open a documentation-only Pull Request against main.

Do not merge the PR.

## 9. Final Report

Provide:

- Design Issue URL.
- Branch name.
- Design PR URL.
- Proposed phase name.
- Summary of features, pages and database models.
- Main architectural decisions.
- Unresolved design questions.
- Verification results.

Do not write application code, generate migrations, modify the existing database, implement the proposed phase, or merge the design PR.

Stop after publishing the design proposal for user review.
