# Candidate data model v0.1

**Design proposal; implementation and phase name are not approved.** No Django classes or migrations are generated. Types below name proposed Django field equivalents. New patient/domain/user relationships use `on_delete=PROTECT`; no cascade deletes. IDs are BigAutoField internally; public order/accession identifiers are UUIDs, never authorization credentials. All timestamps are timezone-aware, stored UTC and displayed clinic-local.

## LabTestCatalog

| Fields | Proposed types / rules |
| --- | --- |
| `code`, `revision`, `display_name` | CharField(40), PositiveIntegerField ≥1, CharField(160); `SYN-` code namespace only. Unique `(code, revision)`. |
| `specimen_type`, `components` | CharField(40) controlled synthetic choice; JSONField list of ≤10 unique component definitions: code, label, numeric/coded type, fixed mock unit, decimal precision/bounds or allowed codes, required flag. Strict schema; no arbitrary executable expressions. |
| `is_active`, `edit_version` | BooleanField, PositiveIntegerField starting 1. Conditional unique code where active; active-flag changes require expected version. |
| `created_by`, `created_at` | User FK, DateTimeField server-assigned. Content immutable after creation; changes create a new catalog revision. Activation/deactivation audited. |

Retain catalog revisions referenced by any order; no deletes. Submission snapshots exact content so later activation cannot reinterpret historical values. Older inactive drafts require explicit reselection before submission. Active-catalog selection and concurrent deactivation must serialize/lock the catalog row during submit; catalog administration acquires that row lock and version check too. No old order is auto-updated.

## LabOrder

| Fields | Proposed types / rules |
| --- | --- |
| `public_id`, `creation_key` | Unique UUIDField for public identity and unique UUIDField for draft-creation idempotency. Store canonical creation fingerprint in its LabEvent; reusing a key with different actor/context/payload is conflict, not access. |
| `patient`, `encounter`, `ordering_physician` | Required Patient FK, Encounter FK and User FK; derive from authorized Encounter. Require patient and ordering physician to match encounter; never editable. Appointment is reached via encounter, avoiding a conflicting duplicate FK. |
| `catalog`, `catalog_snapshot`, `identity_snapshot` | Required LabTestCatalog FK; JSONFields for validated catalog content and minimal submission-time identity/provenance. Snapshot is frozen on submit; draft catalog changes are versioned. Snapshot identity never replaces the authoritative patient FK. |
| `reason`, `priority`, `status`, `version` | CharField(1000); CharField routine-only; CharField choices draft/submitted/cancelled/fulfilled; PositiveIntegerField starting 1. Aggregate version increments on each successful lab mutation. |
| `assigned_lab_staff`, `assigned_at` | Nullable User FK and DateTimeField. Active Lab Staff only. Claim/reassignment recorded in events; no general patient access follows from assignment. |
| `current_result` | Nullable FK to LabResult; must reference a published revision of this order. NULL before first publication. Change only atomically during final/corrected publication. |
| `created_at`, `updated_at`, `submitted_at`, `cancelled_at`, `fulfilled_at` | Server timestamps, latter three nullable. Check status/timestamp consistency: draft has no terminal/submission times; submitted requires submitted time; cancelled requires cancellation time; fulfilled requires submission/first-final time and current_result. |
| `cancelled_by`, `cancellation_reason`, `repeat_reason` | Nullable User FK and bounded text, required where applicable; no cancellation after receipt/publication. |

No unique `(encounter, catalog)` constraint: repeated testing is legitimate with explicit confirmation/reason. Index `(ordering_physician, status, submitted_at)`, `(patient, created_at)` and `(assigned_lab_staff, status)`. `fulfilled_at` retains first publication time across corrections; newer report timestamps come from the result row. Existing patient/encounter/version rows are never incremented by lab writes. Changing live demographics does not rewrite submission identity; collection must confirm the currently displayed patient identity/version, with a visible historical-identity difference if needed.

## LabSpecimen

| Fields | Proposed types / rules |
| --- | --- |
| `order`, `attempt`, `accession` | Required LabOrder FK, PositiveIntegerField ≥1, unique UUIDField; unique `(order, attempt)`. Patient/encounter derive from order only. |
| `specimen_type`, `status`, `version` | Synthetic type copied from frozen catalog; pending/collected/received/rejected; PositiveIntegerField starting 1. Partial unique order for statuses pending/collected/received permits one active attempt. |
| `collected_at`, `collected_by`, `received_at`, `received_by` | Nullable DateTimeFields/User FKs; required as respective states are reached. `recorded_at` server time differs from observed collection time. Original collector retained across pre-receipt corrections. |
| `rejected_at`, `rejected_by`, `rejection_reason` | Nullable timestamp/User FK, bounded text; required for rejected state. Preserve preceding collection/receipt provenance when present. |
| `created_at`, `updated_at`, `updated_by`, `comments` | Server timestamps, User FK, bounded text ≤1000. Every correction/recollection event records reason and before/after values. |

No specimen sharing across orders, aliquots, pooled specimens or instrument barcodes in v0.1. Received is the acceptance gate for entry. A rejected attempt remains rejected; create a new attempt, never reset it. Cancelling an order does not pretend an actually collected specimen was never collected.

## LabResult

Treat this as a panel-report **revision**, not an individual analyte and not a mutable finalized report.

| Fields | Proposed types / rules |
| --- | --- |
| `order`, `specimen`, `revision` | Required FKs, PositiveIntegerField ≥1; unique `(order, revision)`; specimen.order must equal order and be received. Allocate revision under aggregate lock; abandoned numbers are not reused. |
| `status`, `edit_version`, `supersedes` | draft/final/corrected/abandoned; PositiveIntegerField starting 1; nullable self FK. Original publication has no supersedes; a correction points to latest published revision of same order/specimen. |
| `values`, `catalog_snapshot` | JSONFields with strict typed component schema/canonical decimal strings. Copy catalog snapshot, not current live configuration. Each required component has exactly one typed value+appropriate unit OR `not_performed` with explanation and no value/unit. Missing/unknown/duplicate components cannot be finalized. |
| `performed_at`, `created_at`, `updated_at`, `published_at` | Timezone-aware fields; performed time required at publication when any component was performed, null for an all-not-performed report. Published time server-only; null for drafts/abandoned. |
| `entered_by`, `updated_by`, `published_by` | User FKs; original entry actor retained; last draft editor separately recorded; published actor immutable. |
| `correction_reason`, `abandonment_reason`, `comments` | Bounded text (1000/1000/4000); required for corresponding action. Human reasons are not automated clinical interpretation. |

Partial unique order where status=draft; conditional unique nonnull `supersedes` for statuses final/corrected prevents two published successors of one report while allowing abandoned correction drafts. Check status/publication timestamp and correction-predecessor consistency. Cross-row same-order/specimen/chain rules need service/model validation under lock; SQLite CHECK cannot enforce those joins.

Only draft rows can edit content, bumping edit_version and aggregate order.version. Published final/corrected rows and abandoned drafts are immutable through supported services; do not update old rows to a stored superseded status. Current versus superseded is derived from `LabOrder.current_result`. A correction draft does not change that pointer or its physician acknowledgement. The pointer is an aggregate navigation aid, not a second independently editable result state.

The six-model design chooses JSON snapshots to keep panel revisions atomic; per-component numeric/type validation is enforced by schemas/forms/services, not DB columns. A normalized `LabResultValue` table is a documented alternative needing scope approval, not an omitted seventh model silently expected in implementation. Future analytics/FHIR export must parse the validated snapshot; no JSON-to-code execution.

## LabResultReview

`result` FK, `reviewer` User FK, server `reviewed_at` DateTimeField, `comment` CharField(2000, blank=True). Unique `(result, reviewer)`. Immutable record; only the active ordering physician may create it after confirming that result remains the current published revision under the order lock. No generic reviewed Boolean on order. Old reviews remain attached to old revisions; current review status is derived for the responsible physician. Identical command replay returns the existing receipt. A different command for an already acknowledged revision returns a friendly already-acknowledged conflict, not another review/event. No delegated acknowledgement, removal, or post-hoc comment editing in v0.1.

## LabEvent

`order` nullable FK, `catalog` nullable FK, `specimen`/`result`/`review` nullable FKs, `audit` OneToOneField to existing AuditEvent, `before`/`after` JSONFields, `reason` CharField(1000), nullable `command_key` UUIDField, `request_fingerprint` CharField(64), `outcome_reference` JSONField of opaque record IDs/revision. Require exactly one order or catalog scope. Optional linked children must belong to that scope. Unique `(audit actor, command_key)` cannot traverse AuditEvent in a DB constraint: therefore include a required immutable `command_actor` User FK for command events, validate it equals audit.actor, and use UniqueConstraint `(command_actor, command_key)` for nonnull keys. No duplicated clinical patient FK here; AuditEvent.patient is derived from order, null for catalog-only actions.

Successful writes create one domain event plus existing AuditEvent atomically, with explicit `lab_order_submit`, `lab_specimen_collect`, `lab_result_finalize`, `lab_result_correct`, `lab_result_ack` etc. All action names fit AuditEvent's 40-character limit; display labels use the current human-readable filter pattern. Decimal values serialize as strings and timestamps as ISO values. View/denial audits may use existing AuditEvent alone and do not need command receipts. Restrict historical snapshots by viewer policy; Lab Staff must not receive unrelated event fields or signed-note content. Audit rows are append-only by supported application policy, not guaranteed immutable to database operators.

## Consistency/retention boundary

Use DB constraints for uniqueness/local checks plus explicit service checks for relationships and state transitions. No client-writable author, current-result pointer, server timestamp, revision, snapshot schema or status shortcut. No delete endpoint for any clinical lab row. Future migrations must be additive, with protected links to existing models; circular new order/result relations may require operations adding a field to a newly created lab table, never a rewrite of an existing business table. All existing records and signed SOAP must remain unchanged.
