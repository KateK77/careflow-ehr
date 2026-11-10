# Project roadmap

Each phase is a proposed development increment. Refine its scope when workflow requirements are available.

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

Phase 1A implements staff login and demographic patient management, reviewed through Issue #3. Scheduling and check-in remain a later approved increment. See the [Phase 1A report](iterations/0002-patient-registration/README.md) for implementation evidence and outstanding user acceptance.

## Phase 1B scheduling and check-in

The approved scheduling increment follows merged Phase 1A and is tracked in Issue #5. See the [Phase 1B report](iterations/0003-scheduling-checkin/README.md). Clinical encounters and the Phase 1A future UX groups remain separately scoped.

## Approved Phase 2A increment

Physician workspace, scoped patient chart, explicit encounters and SOAP drafts/signing are implemented for review in [iteration 0004](iterations/0004-physician-workspace/README.md). Manual acceptance is pending. Full clinical modules and Phase 2B remain outside the approved increment.

## Approved Phase 2B stacked increment

[Iteration 0005](iterations/0005-clinical-history/README.md) implements longitudinal medical history, problems, allergies, medication statements and encounter diagnoses on the Phase 2A branch. The user approved proceeding before Phase 2A manual UAT. Both phases remain pending user acceptance; no Phase 3 is authorized.

## Approved Phase 3A stacked increment

[Iteration 0006](iterations/0006-nursing-workspace/README.md) adds nursing worklists, rooming, vitals and flowsheets on Phase 2B. The user subsequently approved Phase 3A while earlier clinical manual UAT remains postponed. No MAR, clinical decision rules, deployment or Phase 3B is authorized.
