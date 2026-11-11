# Functional specification v0.1

**Design proposal only; phase name and implementation scope are not approved.** Requirements below are proposed acceptance obligations for a later authorized implementation. Synthetic data only; every future page retains DEMO — NOT FOR CLINICAL USE.

### LAB-01 — Bounded synthetic test catalog

Provide versioned catalog rows with synthetic codes, display names, specimen type and strict component definitions. Demonstration examples:

| Panel code / name | Specimen | Required components / exact mock units | Demo validation |
| --- | --- | --- | --- |
| SYN-CHEM-01 / Demo chemistry | Mock serum | SYN-A and SYN-B numeric; `demo-U` | Decimal, 0–9999, up to four decimal places. |
| SYN-COUNT-01 / Demo count panel | Mock whole blood | SYN-C numeric; `demo-count` | Decimal, 0–100000, up to four decimal places. |
| SYN-SCREEN-01 / Demo screen | Mock swab | SYN-D coded, no unit | `detected`, `not_detected`, `indeterminate`. |

These are fictional analytes, units and input bounds, not normal ranges, validated clinical terminology or recommendations. No age/sex reference ranges, abnormal flags, critical alerts, calculations or auto-diagnoses. Store decimals canonically as strings, never floating-point clinical values. At most ten components per catalog revision. Administrator creates immutable content revisions and activates/deactivates them; previous revisions/order snapshots remain accessible. Future opt-in synthetic initialization must be repeatable and preserve existing data/passwords; this design runs no seed.

### LAB-02 — Context-bound order draft

Only the assigned active Physician creates an order from an authorized in-progress encounter. Derive patient and appointment from Encounter; reject forged patient/encounter/author values. One catalog panel per order; a second panel is a separate order. Fields include catalog choice, routine priority (the only v0.1 priority), bounded synthetic reason and confirmation. Save/reopen/edit the owner's draft with version checks; patient/encounter/ordering physician are immutable after creation. No UI hard deletion. Inactive catalog versions cannot be newly submitted; choosing a replacement requires an explicit draft edit and audit.

### LAB-03 — Explicit submission and duplicate handling

Show a read-only confirmation of patient MRN/name, encounter, panel, specimen requirement and reason. Submit by POST with CSRF, current order version, durable command UUID and explicit synthetic confirmation; GET does not submit. Inside the serialized transaction recheck ownership and in-progress encounter, freeze the catalog snapshot, mark order submitted, create its first pending specimen and write audits atomically. If another non-cancelled order for the same encounter/panel exists, show a warning and require explicit repeat-test confirmation plus reason; do not impose a permanent uniqueness rule that prevents legitimate repeat testing. A repeated HTTP command is idempotent, not a second clinical order.

### LAB-04 — Cancellation

Ordering Physician may cancel their draft or submitted order with reason, version and confirmation, including after encounter completion, provided no specimen has been received and no result published. Preserve collected/pending specimen history; display cancelled order separately from its last specimen state. Cancelled orders are terminal; a new order needs a currently authorized in-progress encounter. Nurse, Lab Staff and Administrator alone cannot cancel physician orders. Receipt racing cancellation has one serialized winner; do not create an unsupported partly-cancelled state.

### LAB-05 — Collection and recollection

Active Nurse membership permits collection against a submitted order, independently of whether the originating encounter is now completed. This is a new lab capability, not a relaxation of existing rooming/vital rules. Confirm patient MRN and name/date of birth in a bounded requisition, record specimen mock type, unique accession, collected-at clinic-local time, original collector and synthetic confirmation. Time must be timezone-aware, at/after submission, no earlier than DOB, and not future. No auto encounter/check-in/readiness update. Corrections before receipt require a reason and retained before/after audit; original recording identity remains. After receipt, collection metadata is locked. A rejected attempt stays visible; a Nurse may explicitly create/collect the next numbered attempt. Only one non-rejected attempt exists at a time.

### LAB-06 — Lab assignment, receipt and rejection

Lab Staff may see a minimal submitted-order queue and atomically claim an unassigned active order. Only the assigned active Lab Staff member may view the full minimal requisition and enter receipt/results. Administrator may assign/reassign to another active Lab Staff member with a reason and audit; this grants no result-authoring permission. Reassignment invalidates old actor permissions immediately and bumps the order version. Receive a collected specimen with actor/time and accession confirmation; reject collected/received specimens before any publication with a required reason. A result draft must first be abandoned with reason before rejecting its specimen. No new result may use a rejected or pending specimen.

### LAB-07 — Typed result draft entry

Only assigned Lab Staff enter/edit the current report draft against a received specimen. A revision contains one panel's complete value snapshot, component codes, canonical numeric strings or enumerated values, exact catalog units, performed-at time and bounded comments. Drafts may be partial but are visibly unpublished; non-Lab staff cannot mistake them for final results. Reject unknown/missing component identifiers, duplicate components, wrong types, nonfinite numbers, overflow/precision violations, mismatched units, extra JSON keys and text over limits. No automatic unit conversion. One active draft per order. Preserve draft changes through audit, even though the draft row is mutable.

### LAB-08 — Finalization

An assigned Lab Staff member explicitly previews and finalizes the current draft using order version, draft edit version, command key and confirmation. Revalidate all required components, or record an explicit per-component `not_performed` absence reason with a nonblank explanation and no value/unit. A blank component is not zero, normal or performed. Check specimen receipt and event-time ordering: collection ≤ receipt ≤ publication, with receipt ≤ performed ≤ publication when any component was performed, all not future. An all-not-performed report has no invented performed timestamp; retain publication time and absence reasons. No provisional clinical result publication in v0.1. Finalization atomically publishes the revision, updates the order's current-published pointer/status to fulfilled and creates audit/history. It never signs or edits SOAP or waits for encounter completion.

### LAB-09 — Corrected published results

Published revisions cannot be edited or deleted through supported application paths. Explicit Correct result creates a new draft revision copied from the latest published snapshot; a required correction reason explains the intended change. The original result remains the current report while this draft is edited. Publish the correction atomically as a new `corrected` revision, linked to its immediate predecessor. Preserve every prior value, performer, finalizer, timestamp, reason and acknowledgement. Superseded is a derived display label, not a mutation of the original final row. No branching correction chain or patient/specimen reassignment. Abandoning a correction draft preserves its history and leaves the prior report current. Withdrawal/entered-in-error is a separate unresolved policy, not silently approximated by overwriting values.

### LAB-10 — Version-specific physician review

The ordering active Physician sees a results worklist for their published reports regardless of encounter status. Acknowledge only the displayed current published revision, with explicit confirmation and current order version. Store physician, result FK/revision, time and optional bounded comment; acknowledgement is an attestation, not editing clinical content or making a diagnosis. One acknowledgement per physician/result revision; exact repeats are idempotent. If a correction publishes before acknowledgement commits, reject the stale acknowledgement and require review of the new version. Old acknowledgements remain attached to the old revision. Corrections create a fresh unreviewed item. An inactive ordering physician does not make a result reviewed; unresolved reviewer coverage is shown explicitly.

### LAB-11 — Encounter completion and late results

Creation/edit/submission of orders stops at encounter completion, but cancellation under LAB-04, collection/recollection, receipt, result entry/publication/correction and acknowledgement may continue for already submitted orders. Do not reuse the in-progress clinical-note/history maintenance gate for these lab operations. Encounter completion retains its existing signed-SOAP requirement and is not blocked by pending labs or silently modified by lab state. A saved draft still present at completion becomes read-only for edit/submit, with an owner cancellation action; it is not auto-submitted or deleted. Display both completed encounter and pending/unreviewed lab states. Never reopen an encounter, change its completion provenance or append new results to its signed SOAP text.

### LAB-12 — Chart, encounter and longitudinal integration

Provide authorized patient lab history, per-encounter order list, current published results and revision history. Ordering Physicians see their order lifecycle; other Physicians with existing chart access see published longitudinal results and minimal order context, not another Physician's private order drafts/reasons or encounter notes. Existing Nurse/Administrator clinical readers can read clinic lab data under the matrix; FrontDesk and standalone Lab Staff cannot open detailed charts. Avoid links to an encounter the current viewer cannot access. No result chart view broadens existing clinical permissions or generates a generic Inbox/portal feature.

### LAB-13 — Durable state and provenance

Order, specimen, result and physician-review states are separate ([state proposal](states.md)). Derive summary badges from authoritative rows; no static frontend worklists or manual status syncing. Every successful command and permitted correction commits its domain writes with one linked LabEvent/AuditEvent in the same transaction. Record source actor/time, changed fields and structured before/after values for authorized history. Audit viewing/denials follows existing patterns without leaking unauthorized patient data; don't log result/requisition text into ordinary process logs. No destructive endpoints or audit editing UI.

### LAB-14 — Versioning, idempotency and concurrency

All mutating POSTs require current role/scope, versions and actor-bound command UUIDs. Durable successful command receipts distinguish identical replay from UUID reuse with different normalized input; check authorization before returning an earlier outcome. Identical replay returns the existing outcome without another clinical row/event; changed-payload replay returns conflict. Use serialized backend transactions, DB uniqueness and explicit HTTP 409 conflicts; UI submission guards are supplementary. Save/finalize, cancellation/receipt, simultaneous corrections and acknowledgement/correction races must be tested. Database busy errors must not silently retry with duplicate writes or overwrite newer values.

### LAB-15 — Safe validation and original interface

Use existing Django Authentication/CSRF, server-rendered templates, DEMO notice, patient banner, readable action labels, messages, error summaries, full-text responsive tables and contained keyboard-accessible overflow. Preserve bound form input on validation/version failures; show plain-language messages, not constraint names or `__all__`. Do not introduce browser-only authorization or cosmetic inactive controls. Retain UTC storage with clinic-local labels and reject ambiguous/nonexistent local-time input. Dates/times and decimals require server validation even when browser controls appear valid.

### LAB-16 — Compatibility and exclusions

Only a later approved implementation may add lab tables via additive migrations, with a consistent backup and row/hash/integrity checks. Preserve all existing application features, patients, appointments, encounters, signed notes, history, nursing and audit data. No real patient data, external lab connections, real clinical decision support, medication prescribing/administration, automatic diagnosis/treatment, insurance billing, production deployment, AI agents or LLM functionality. No migration, schema generation, application code, local database write, seed or implementation is part of this design task.
