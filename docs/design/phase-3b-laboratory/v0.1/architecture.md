# Architecture proposal v0.1

**Proposal only; implementation and phase name are not approved.** Reviewed against main `56ea8b332525926b02759b2afefa93166bd52d31`, not an assumed greenfield application. All named future files/services below are planning, not changes made by this PR.

## Existing architecture and dependencies

| Inspected baseline | Relevant finding / integration constraint |
| --- | --- |
| `careflow/patients/models.py`, `access.py` | Patient/AuditEvent are existing shared entities. AuditEvent action ≤40 characters, outcome, actor, patient, occurred_at and changed_fields; no before/after field. Four-role resolver also drives demographic authorization and synthetic seeding. |
| `careflow/scheduling/models.py`, `services.py` | Appointment owns patient/physician and check-in provenance. `_lock_providers` performs an initial serialization write to ProviderScheduleLock, in stable provider order. Do not create another encounter/appointment or alter their states for labs. |
| `careflow/clinical/models.py`, `access.py`, `services.py` | One encounter per appointment; one SOAP note per encounter. Physician authoring requires ownership/in-progress; completed encounter has a timestamp/version. Signed Note.save rejects updates; service rules also protect signing/completion. Existing completion needs a signed note, not resolved orders. |
| `careflow/history/models.py`, `access.py`, `services.py` | Longitudinal history uses patient serialization, versions, protected provenance and transactional before/after HistoryEvent linked to AuditEvent. Its current-maintenance gate is unsuitable for late-result follow-up. Do not reuse HistoryEvent as an unrelated lab record store. |
| `careflow/nursing/models.py`, `access.py`, `services.py`, `presentation.py` | Nursing is appointment-linked, optional encounter association; authoring stops after completion. Values retain units/time and chart summaries use scoped appointments. Lab collection is a distinct capability with a different lifecycle, not a rooming/vitals mutation. |
| Existing migrations | Patient initial; scheduling initial; clinical initial and note-section alteration; history initial; nursing initial. Proposed lab migration dependencies must reference their actual migration names as needed, not recreate these apps. |
| Core templates/static UI/templatetags and existing browser tests | Reuse base layout, DEMO badge, human-readable event/field filter pattern, form-error summaries, messages, ISO input and scroll affordances. Lab-only staff need a restricted header/navigation context. |
| Original English requirements and current closeout/status | Laboratory baseline S13–S16/W02 provides broader context; original names include LabTech, whereas this proposal evaluates Lab Staff. This explicit role-naming decision requires approval; original requirements are not silently revised. Current main has no lab app, lab tables, lab permission group or generic Inbox. |

## Proposed module boundary

After approval only, a `careflow/labs` app would own catalog/order/specimen/report/review/event models, forms, query scopes, transactional services and Django templates. Existing core auth and Patient/Encounter/AuditEvent remain authoritative. A small read-presentation adapter supplies authorized lab summaries and timeline items to existing chart/encounter templates; no lab value is copied into SOAP or diagnoses, history problems or nursing observations.

Planned integration touchpoints: add the approved app/URL/context processor; new lab-specific roles/queries; minimal login/dashboard routing for Lab Staff; guarded lab navigation; chart/encounter summary adapter and human-readable lab action labels. Existing seed behavior must not be expanded by adding Lab Staff to READ_ROLES. Any separate opt-in Lab Staff/catalog initialization must preserve all existing records/passwords and never embed passwords. No such source changes occur now.

## Domain service transaction boundary

Every write authenticates and scopes first, then rechecks inside `transaction.atomic()`. Acquire the existing ordering-physician ProviderScheduleLock first, then catalog row for submission if needed, then order, specimen, draft/current result and review rows in that order. Catalog-only administration locks catalog rows in code/revision order and never subsequently acquires provider/order locks. Assignment actions also use the order's ordering-physician lock. Do not invert the established provider-first order or add a dependency on the history patient lock for operations that do not write history.

Within the lock: recheck activity/role/assignment/context and current state, detect durable command replay, validate expected aggregate and child edit versions, validate canonical payload, apply allowed transition, update aggregate version/pointer as needed and commit one AuditEvent/LabEvent receipt with domain writes. The creation-key constraint guards a race before an order PK exists. A replay may touch the operational serialization counter but must create no second clinical row or event. HTTP 409 preserves input and requests reload; denied/invalid commands create no partial domain state. Existing access-denial audits remain possible, but must not disclose unauthorized patient details.

SQLite ignores the intended PostgreSQL row-lock semantics of select_for_update; the existing initial serialization write and uniqueness/CAS/version guards therefore matter. Test real contention with TransactionTestCase/separate connections, not just mocked locks. Later PostgreSQL/shared deployment requires separate verification. Do not promise production concurrency based on SQLite tests.

Durable command receipts and partial unique constraints are proposed safeguards, not currently implemented guarantees. A successful command UUID cannot be repurposed with different payload/context; the actor must still be authorized to receive the existing outcome. No automatic retry loop silently creates another order/publication on busy/replayed requests.

## Immutable publication and review responsibility

Order owns patient/encounter/ordering physician forever. Report revisions own typed value snapshots; only the current draft edits. Publish once, append correction revisions, and update the current-published pointer atomically. Old reports/reviews remain inspectable under the original scope. Read APIs/templates derive current report/review state from those rows rather than a separate editable reviewed flag.

The ordering physician retains lab responsibility after encounter completion because the order itself establishes that responsibility. This does not grant a new care-team membership or another physician's note access. A second physician already authorized for the patient's longitudinal chart may read published results, but cannot acknowledge as the ordering physician. Reviewer delegation, inactive-user coverage and erroneous-report withdrawal are explicit unresolved policies; show unreviewed/responsibility-unresolved states rather than infer resolution.

## Migration and preservation plan for a future implementation

1. Capture a consistent SQLite online backup with the application quiescent, integrity/FK checks, schema/applied-migration list and snapshots of all existing table rows. Inventory original documents and Git state.
2. Generate/review additive lab migrations only after implementation approval; create new lab tables/constraints/content types/permissions. Do not reset/rebuild existing patient, appointment, encounter, note, history or nursing tables. Resolve circular new-lab FKs within new-table operations.
3. Verify old rows, signed SOAP field values/signature/version and appointment/encounter provenance unchanged immediately after migration; integrity ok, no FK violations. New auth metadata is an expected additive delta.
4. Use disposable synthetic test databases. Runtime lab actions add lab/audit rows and may update serialization counters; preservation tests compare protected clinical rows and expected deltas, not an impossible unchanged whole-file hash across intentional schema/data additions.
5. Failed migration planning uses the untouched backup and a documented review decision; no automatic rollback/destructive action is authorized. Never run reset/reseed against the user's current database.

For this **design PR**, no migration/runtime action occurs: compare the entire local SQLite file hash and every pre-existing tracked-file hash before/after documentation work. CI runs the unchanged existing Django suite, not future lab acceptance tests.

## Future HL7 FHIR R4 mapping considerations — no integration

Reviewed official R4 v4.0.1 references on 2026-11-10. The following is a conceptual mapping proposal, not a conformant profile, exporter, endpoint or terminology license. No FHIR package, transport, external service or database resource copy is introduced.

| Local concept | Candidate future R4 mapping / caution |
| --- | --- |
| LabOrder | [ServiceRequest](https://hl7.org/fhir/R4/servicerequest.html): order identifier, subject, encounter, requester, authored time, code and requested specimen context. Candidate status mapping: draft→draft, submitted→active, cancelled→revoked, fulfilled→completed. Submitted orders have order intent. A panel is one request; separate panels remain separate requests. Local specimen/review states must not be overloaded into ServiceRequest.status. |
| Typed component value | [Observation](https://hl7.org/fhir/R4/observation.html): one analyte code/value or explicit dataAbsentReason, unit, effective time, performer and specimen/context references. Numeric strings become properly validated Quantity values; coded results need an approved code system. Do not export `demo-U` as if it were UCUM or label synthetic codes as LOINC. Absent results are not zero. |
| Published LabResult revision | [DiagnosticReport](https://hl7.org/fhir/R4/diagnosticreport.html): report identifier/status, subject/encounter, basedOn ServiceRequest, specimen and result references to Observations, issued/performed times. Final/corrected are publication states, not physician-read states. Each historical report/revision remains traceable; a longitudinal history page is not itself one DiagnosticReport. |
| Correction lineage and acknowledgement | Preserve original identifiers and correction provenance. A future FHIR server controls its own meta.versionId; local revision numbers are not automatically those resource history IDs. Versioned report/Observation references, Provenance and any Task/extension approach for acknowledgement require approved profiles. Do not invent DiagnosticReport status `reviewed` or claim acknowledgement is covered by changing report status. |

The [official ServiceRequest definitions](https://hl7.org/fhir/R4/servicerequest-definitions.html), [Observation definitions](https://hl7.org/fhir/R4/observation-definitions.html) and [DiagnosticReport definitions](https://hl7.org/fhir/R4/diagnosticreport-definitions.html) define the relevant status/value/reference boundaries. A future implementation must resolve specimen resource representation, identifiers, terminology bindings, missing-value mapping, correction history, authorization and conformance tests separately. None is implemented or approved here.
