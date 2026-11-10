# Revised model and JSON contract v0.2

**Proposal only; implementation is not approved.** These are model specifications, not Django classes or generated migrations. Apply the [v0.1 model definitions](../v0.1/models.md) only where not amended here. The proposal now has **seven** models: the six earlier candidates plus immutable **LabReviewAssignment**. All patient/order/publication/user relationships use PROTECT and backend cross-context validation.

## Model changes

| Model | v0.2 fields / constraints / invariants |
| --- | --- |
| LabTestCatalog | Retain unique `(code, revision)`, one active code revision, immutable component definitions and audited activation version. Add positive `schema_version` for component-definition decoding; pin catalog content/version in report payloads. No clinical reference-range engine. |
| LabOrder | Keep immutable Patient/Encounter/ordering_physician and original submission identity. Replace the proposed `current_result` name with nullable `current_publication` FK to LabResult; published final/corrected/**withdrawn** rows are possible targets. Add nullable `current_review_assignment` FK to LabReviewAssignment. Add `withdrawn` status to draft/submitted/cancelled/fulfilled. Aggregate `version` still increments on every successful mutation. Fulfilled requires first fulfilled_at and a usable current final/corrected publication; withdrawn retains fulfilled_at and points to a withdrawal notice, never NULL or an older report. Cross-row checks are service/model checks, not SQL join CHECK constraints. Draft has no assignment; full v0.2 submitted/fulfilled/withdrawn states require an assignment row, even if its physician is now ineligible. |
| LabSpecimen | Same fields/statuses and protected provenance. Unique `(order, attempt)`, unique accession and partial unique order for pending/collected/received. `received_at` is permanent receipt evidence even after rejected state; cancellation queries **all attempts' received_at**, not only the active status. No correction/reset of rejected attempts. |
| LabResult | Keep order/specimen, monotonic revision, mutable-draft edit_version, supersedes and original entry/last editor/finalizer/time fields. Preferred payload is a single strict `payload` JSONField plus positive `schema_version` and `publication_kind` columns (`report`, `withdrawal`), replacing the two proposed values/catalog_snapshot JSON fields. Statuses: draft/final/corrected/abandoned for report, **withdrawn** for withdrawal. Final/corrected/withdrawn publications are immutable. Add controlled withdrawal reason code and bounded reason text; notice points to exact predecessor and contains no result values. |
| LabResultReview | Point to `publication` FK (LabResult) and **review_assignment** FK. Keep immutable reviewer FK, reviewed_at, bounded comment; add server-derived `review_kind` (`result_review`, `withdrawal_notice`). Unique `(publication, review_assignment)` replaces v0.1's `(result, reviewer)`. Require reviewer=assignment.physician and assignment.order=publication.order. Only the current pair may newly acknowledge. Historical acknowledgements never change on reassignment/publication. |
| LabEvent | Retain linked AuditEvent, immutable reason/before/after/provenance, actor-bound command UUID and payload fingerprint. Add nullable review_assignment FK, validated against order; record assignment sequence and publication target in command receipts. Include withdrawal and reassignment events with distinct acting actor/capability. No result text in ordinary logs. Existing command uniqueness remains. |

## New LabReviewAssignment

| Field | Proposed type / contract |
| --- | --- |
| `order`, `sequence` | Required LabOrder FK, PositiveIntegerField ≥1, unique `(order, sequence)`. Allocate under aggregate lock; no reuse of sequences. |
| `physician` | Required User FK; an active Physician at manual assignment time. Original submission sequence 1 uses original ordering_physician. An account may later become ineligible without erasing this row. |
| `assigned_by`, `assigned_at`, `reason` | User FK and server DateTimeField, CharField(1000), required for user commands. Initial submission actor is the ordering Physician; manual reassignment actor is the authorized Administrator, never the assignee by impersonation. |
| `supersedes`, `source` | Nullable self FK, unique nonnull predecessor (linear chain); controlled source `initial_submission`, `manual_reassignment`, `migration_backfill`. Same order, previous current sequence+1. No cycle or mutable end-time required: current is derived from Order.current_review_assignment. |

Rows are immutable. For the proposed 3B-3 backfill only, assigned_by may be NULL with source=migration_backfill, recorded server migration time and explicit reason. It attributes responsibility to the existing ordering physician, not a historical action that physician never performed. Audit actor/command actor may be NULL only for this system-provenance event with no command UUID. Never create a covering assignment or acknowledgement automatically during backfill. Inactive initial physicians show unresolved responsibility until explicit reassignment.

No separate assignment epoch counter is editable on LabOrder: the assignment PK/sequence identifies the epoch. A Physician returning as sequence 3 must freshly acknowledge, even if they reviewed the same report under sequence 1. Permission is not inferred from ordering_physician after review responsibility has changed. Original ordering identity and order-writing rights remain separate.

## Published-report and withdrawal constraints

- Unique `(order, revision)`; revision≥1; one active draft per order; one original final report per order; one published successor per nonnull supersedes across **final/corrected/withdrawn** states.
- Local CHECKs bind kind/status, publication timestamp, predecessor and reason fields: report kind permits draft/final/corrected/abandoned; withdrawal kind permits only withdrawn with published_at, predecessor, reason code/text and no performed_at. Correction/withdrawal require predecessor; original final does not.
- Every predecessor/specimen/assignment/pointer belongs to the same immutable order. Report corrections retain the original received specimen; a withdrawal notice retains that specimen reference for provenance but copies no measurements.
- Final/corrected publication pointer is usable only when order fulfilled. Withdrawn pointer is a notice only when order withdrawn. Never automatically clear the pointer, restore an old report or reactivate an order. Withdrawn is terminal for report processing, though explicit review reassignment/notice acknowledgement remain allowed.
- Immutability is enforced by supported forms/model/services and tests. Direct SQL/bulk ORM operators can bypass application controls; no database-level tamper-proof claim.

## Strict typed JSON contract (preferred MVP)

Validate before every draft save, preview and publication. Register immutable validators by `(schema_version, publication_kind)`; column values and payload envelope must agree. Reject unsupported versions/kinds, unknown keys, duplicate component codes, wrong types and canonical payloads over **64 KiB**. No arbitrary evaluator, formula, HTML attachment or clinical interpretation engine.

| Payload area | Contract |
| --- | --- |
| Common envelope | Positive integer schema_version, controlled kind, stable catalog code/revision and immutable order/specimen identifiers; server derives identifiers. Context mismatches are errors, not reassignment requests. |
| Report snapshot | Frozen catalog definitions and ≤10 uniquely coded components; each component has exactly one typed value with the exact declared mock unit OR not_performed code+nonblank reason and no value/unit. Missing is not zero/negative. Required-component completeness checked at publication; partial drafts remain visibly unpublished. |
| Numeric value | Canonical ASCII decimal **string**, parsed using Decimal; no JSON numeric float, bool, NaN/infinity, exponent, comma/localized separators, excess precision or out-of-bound value. At most 12 total digits/four fractional digits and catalog bounds apply. Do not silently round or convert units. |
| Coded value | Exact code from the frozen allowed set, no numeric unit. Free-text comments are bounded and escaped, not substitutes for typed values. |
| Time | UTC storage, clinic-local display and existing DST checks. Receipt≤performed≤publication when any component performed; all-not-performed report has no invented performed time. |
| Withdrawal notice | Kind=withdrawal, target publication identifier, reason code (`report_error` or `context_error`), reason text and schema version; no components/numeric values, negative code, not_performed substitute or performed timestamp. Publication/actor/assignment provenance remains in protected relational fields/events. |

Schema version 1 report decoding does not change when a withdrawal-kind validator is added: the registry key includes kind. A structural/semantic change to an existing kind requires a new schema version; retain old readers for historical revisions. Catalog content changes require new catalog revision and explicit new-order/draft selection; never reinterpret old snapshots. An unsupported historical schema must show Unavailable for decoding with metadata preserved, not guessed normal values.

The proposed schema-1 allowed key sets are explicit:

- Report envelope: `schema_version`, `kind`, `context`, `catalog`, `components`. Context contains only `order_id` and `specimen_id` (server-derived public identifiers). Catalog contains `code`, `revision`, `display_name`, `specimen_type`, `definitions`; each definition allows `code`, `label`, `type`, `required` and the numeric `unit`/`precision`/`minimum`/`maximum` OR coded `allowed_codes` fields. Bounds are canonical decimal strings. No irrelevant variant fields.
- Report component: `code`, `value_kind` and its required branch fields, plus optional bounded `comment` (400 characters). Numeric branch: `value` canonical string and exact `unit`; coded branch: `value` controlled code and no unit; absent branch: `absence_reason=not_performed` and `absence_explanation` (1–1000 characters), no value/unit. Reject unknown keys rather than dropping them. Definitions/values must agree and every required component must be accounted for before publication.
- Withdrawal envelope: `schema_version`, `kind`, `context`, `catalog` (code/revision only), `target_revision`, `reason_code`, `reason`. Target revision is a positive integer matching the current predecessor in the same order; reason text is 1–1000 characters. No definitions/components/value/unit/performed fields. Kind/schema match relational columns and the notice's supersedes FK.

These are design contracts, not implemented JSON Schema code. Future size limits use canonical UTF-8 byte count; application form strings/comments are escaped and validated independently of any browser widget.

Relational FKs, unique keys, status/time constraints and current-pointer validation are outside JSON. SQLite cannot guarantee nested schema semantics; services must reject invalid direct write attempts. Signed/published snapshot bytes are never migrated in place to a new schema.

## Query limitations and future alternative

JSON is appropriate for a small synthetic panel/report loop, not a general indexed analyte warehouse. Decimal strings must not be lexicographically sorted or naively cast to SQLite floating-point for longitudinal numeric interpretation. MVP history may list exact values with panel/component/unit/schema context; cross-panel trends, aggregation, range interpretation and clinical calculations remain outside scope.

A later normalized LabResultComponent table or validated read projection can improve typed numeric indexing/querying. It must retain source publication IDs, revision/schema/unit identity, preserve immutable JSON originals, validate conversions and migration deltas, and receive its own approval. No such table, query engine or migration is included now.
