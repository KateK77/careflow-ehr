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
