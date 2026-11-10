# Project roadmap

The completed delivery increments and current proposal are recorded below. [Current project status](project-status.md) provides merge commits, evidence, deferred enhancements and limitations. Existing phase names are retained.

## Completed delivery increments

| Phase | Current disposition | Delivered scope |
| --- | --- | --- |
| Phase 0 | Completed and merged | Repository/documentation foundation and development workflow. |
| Phase 1A | Completed and merged | Staff authentication, patient registration and demographic management. |
| Phase 1B | Completed and merged | Scheduling, calendars and check-in. |
| Phase 2A — Physician Workspace | Completed approved local-prototype review; merged in PR #8 | Patient charts, explicit encounters, SOAP drafts/signing and completion. |
| Phase 2B — Clinical History | Completed approved local-prototype review; merged in PR #10 | Medical history, problems, allergies, medication statements and encounter diagnoses. |
| Phase 3A — Nursing Workspace | Completed approved local-prototype review; merged in PR #12 | Nursing worklists, assessments/readiness, vital panels, flowsheets and chart integration. |

## Proposed next increment

**Orders & Laboratory Results** is the proposed next development increment, pending separate approval. Its detailed workflows, access policy, state model, acceptance criteria and phase identifier require approval before implementation. This proposal does not authorize external laboratory connections, prescribing, cloud deployment, or any other new functional scope. No such implementation is included in the documentation closeout.

## Original broad planning categories

The following original planning categories are retained for context. They are not the current delivery phase names or authorization to start work; in particular, the broad category numbered 3 does not rename the completed Phase 3A — Nursing Workspace.

| Phase | Scope | First demonstrable outcome |
| --- | --- | --- |
| 0. Foundation | Repository, local application, architecture, and smoke tests | Landing page and health endpoint run locally. |
| 1. Patient access and scheduling | Staff identity, role-based access, audit events, synthetic patient registration and management, appointments and calendars | Staff can register a synthetic patient and book an appointment, with authorization and audit coverage. |
| 2. Clinical encounters | Patient charts, doctor and nurse worklists, clinical documentation and progress notes | A clinician opens an encounter, reviews chart history, and signs a note. |
| 3. Orders, medications, and labs | Medication management, simulated prescriptions, clinical orders, laboratory tests and results | An order moves from placement to result review, with status and provenance. |
| 4. Hospital operations and patient engagement | Administrative dashboards, operational worklists, patient portal, and secure messaging | Staff can see an operations queue and a synthetic patient account can exchange a message with staff. |
| 5. Revenue cycle | Billing, insurance coverage, claims, and simulated payment workflows | A synthetic encounter progresses through charge capture and simulated claim adjudication. |
| 6. Interoperability and decision support | HL7 FHIR profiles and exchange, clinical decision support, and clinician-reviewed AI assistance | Selected synthetic data passes FHIR conformance checks and a clinician reviews a traceable suggestion. |

Design identifiers, provenance, and audit events from the first clinical increment. Keep external exchanges and AI evaluation in synthetic sandboxes.

## Phase 1 split

Phase 1A delivered staff login and demographic patient management through Issue #3 and merged PR #4. Scheduling/check-in subsequently completed in Phase 1B. See the preserved [Phase 1A report](iterations/0002-patient-registration/README.md) for its original evidence and feedback; historical pending statements do not supersede the current disposition.

## Phase 1B scheduling and check-in

The scheduling increment completed through Issue #5 and merged PR #6. See the preserved [Phase 1B report](iterations/0003-scheduling-checkin/README.md). Clinical encounters subsequently completed in Phase 2A; the earlier UX backlog remains separately scoped and is not automatically authorized.

## Approved Phase 2A increment

Phase 2A — Physician Workspace completed its approved local-prototype review and merged in [PR #8](https://github.com/KateK77/careflow-ehr/pull/8). [Iteration 0004](iterations/0004-physician-workspace/README.md) preserves its original scope, reported UAT and targeted retests. It is no longer awaiting merge or the review required for that merge.

## Completed Phase 2B — Clinical History

[Iteration 0005](iterations/0005-clinical-history/README.md) preserves the original stacked development history. Phase 2B — Clinical History subsequently completed review, was retargeted to main and merged in [PR #10](https://github.com/KateK77/careflow-ehr/pull/10). No new functional authorization follows from recording this completed status.

## Completed Phase 3A — Nursing Workspace

[Iteration 0006](iterations/0006-nursing-workspace/README.md) preserves the original stacked development and integration evidence. Phase 3A — Nursing Workspace subsequently completed its approved review, was retargeted to main and merged in [PR #12](https://github.com/KateK77/careflow-ehr/pull/12). Broader unperformed manual/security checks remain unverified; completed review does not imply clinical readiness. No MAR, clinical decision rules, deployment or next phase is approved by this closeout.
