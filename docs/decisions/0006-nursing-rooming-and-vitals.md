# ADR 0006 — Nursing rooming, vital observations and flowsheets

Status: Phase 3A implementation policy; manual UAT remains pending for this and earlier unmerged clinical increments.

## Stack, access and state boundaries

Build on Phase 2B f5209f86dedc6ad7c3aa5e5b80b0c3039027b300, with a stacked PR targeting phase/0005-clinical-history. The approved Phase 3A prompt permits starting before earlier UAT; no merge or Phase 3B is approved.

This increment explicitly extends **active Nurse-group** permissions to nursing assessment/vital authoring in the single synthetic clinic. Nurses can maintain each other's records while preserving the original recording Nurse and tracking the last editor. Administrator alone has read access, not authoring. Physician reads nursing records for their own appointments; Nurse/Administrator read clinic nursing records. Multi-role read access is the existing union; writing always requires Nurse membership. FrontDesk alone cannot read detailed nursing content. Earlier demographic, history, diagnosis and SOAP permissions do not change.

New nursing documentation and corrections require an arrived appointment and no completed encounter for that appointment. Scheduled/cancelled/no-show appointments and completed encounters are read-only. Pre-encounter rooming is permitted; no check-in, rooming, vital entry or readiness action starts an encounter. Only the existing assigned-Physician action may start an encounter. Ready for provider is an explicit Nurse assertion on the assessment, not an appointment/encounter transition or a clinical adequacy algorithm. Worklist indicators derive only from saved assessments/readiness and vital counts.

## Persistence and context

One RoomingAssessment per appointment; multiple VitalObservation panels provide time points. Patient and appointment context are server-bound. An optional Encounter must match both and may be chosen only from that appointment; after creation the association is fixed. Records documented before encounter start remain appointment-linked and are still visible from its encounter. Observation and assessment times are timezone-aware, not future and not before the patient's date of birth. Local input/display uses the configured clinic zone; database storage is UTC.

All writes require synthetic-data confirmation and integer versions (zero for creation). They acquire the existing provider serialization row before checking current appointment/encounter state. This coordinates with scheduling cancellation and encounter completion. Assessment uniqueness is additionally enforced by its one-to-one database constraint. Every write and NursingEvent/AuditEvent commit atomically. Audit events retain actor/time/changed fields; authorized nursing history includes before/after values and original Nurse identity. There is no delete endpoint, automatic reseeding or modification of signed SOAP text. Direct SQL/bulk ORM can bypass service rules; no database immutability or production concurrency claim is made.

## Numeric and unit validation — demo input bounds

These are broad demo data-entry bounds, not normal ranges, alerts or clinical advice. Reject nonnumeric, nonfinite, malformed or out-of-bounds input without generating diagnoses or treatment recommendations.

| Measurement | Accepted input |
| --- | --- |
| Blood pressure | Integer systolic 20–350, diastolic 10–250 mmHg; both or neither, systolic greater than diastolic |
| Heart rate | Integer 10–350 beats/min |
| Respiratory rate | Integer 1–100 breaths/min |
| Temperature | 25–45 °C or 77–113 °F, explicit unit, at most two decimals |
| Oxygen saturation | 0–100 %, at most two decimals |
| Height | 20–300 cm, 0.2–3 m or 8–120 in, explicit unit, at most two decimals |
| Weight | 0.1–700 kg or 0.2–1544 lb, explicit unit, at most two decimals |
| Pain score | Integer 0–10 |

Partial vital panels are allowed, but at least one measurement is required. Temperature/height/weight require a corresponding unit exactly when a value exists. Numeric values and units are preserved as entered without conversion. Source is measured or patient-reported, plus optional source detail. Assessment pain and vital pain are separate observations with their own times; neither silently overwrites the other.

## Read presentation and compatibility

Nursing worklist filters date (1900–2100), patient name/MRN and appointment status. Half-open clinic-local day overlap includes cross-midnight appointments on both applicable dates. Flowsheet rows are measurements and columns are observation times; column labels include source/recording Nurse and link to permitted correction/detail pages. Pagination bounds time columns, with horizontal overflow contained in the flowsheet region. Chart summaries show the latest accessible vital panel, not an invented full panel merged from unrelated times. Nursing events enter the scoped chronological chart timeline. Encounter context shows appointment-linked rooming/vitals even when documented before encounter creation.

Use one additive migration after a consistent SQLite backup. Verify every prior application row and historical requirements/iteration file. Tests use isolated databases. No MAR, care-plan tasks, fall-risk scoring, prescriptions, labs/orders, clinical decision rules, AI, integrations or deployment are introduced.
