# Proposed future delivery increments v0.2

**Planning proposal only; implementation is not approved.** 3B-1, 3B-2 and 3B-3 are proposed subdivisions under the proposed Phase 3B umbrella, not newly approved phases. Do not create implementation branches/functional Issues now. Each future increment needs explicit scope approval, its own linked Issue/branch/PR, CI evidence and user UAT/merge checkpoint. No automatic transition between increments or automatic merge.

## 3B-1 — Catalog, orders and permissions

**Dependencies:** reviewed v0.2 decisions and verified Phase 3A main; existing Patient, Encounter, Authentication, provider serialization and AuditEvent.

**Scope:** immutable synthetic catalog revisions/activation; original-Physician draft/create/edit/preview/submit/cancel; protected context; idempotency, versions, role denials and audits. Explicitly no result entry/publication/review, FHIR, staffing automation or clinical interpretation.

**Proposed additive migration boundary:** create LabTestCatalog, LabOrder and LabEvent. Also create LabSpecimen with its full planned pending-capable schema/constraints **as a technical dependency of submission**; submitting creates exactly one pending attempt atomically. Collection/receipt/recollection routes remain unimplemented and denied until 3B-2. Do not use fake specimen controls or silently weaken the final atomic submit contract. Result/assignment pointers and child event FKs are added only when their models exist in later increments. No existing business-table rewrite.

**Measurable checkpoint:** catalog uniqueness/immutability; one submitted order+pending specimen+audit receipt per command; exact replay has no duplicate; repeat clinical test requires explicit fresh reason; original owner/context/method/CSRF denials; stale/submit-completion races; pre-receipt cancellation. Existing regression suite passes. User UAT demonstrates create/draft/submit/cancel and wrong-role denial, with an explicit **Collection/results are not available in this increment** empty state. Open a separate 3B-1 PR only after approval and wait for its review/UAT/merge decision.

## 3B-2 — Collection, lab processing and first publication

**Dependencies:** approved and verified 3B-1 outcome; active lab-role provisioning policy and explicit submitted/pending records. Branch from the agreed verified base, not an automatically assumed unmerged implementation branch.

**Scope:** Nurse collection/correction-before-receipt/recollection, independent Lab Staff assignment/claim, received/rejected specimens, strict typed JSON report drafts, abandoned drafts and explicit first finalization. Permit same assigned entry/finalizer as reviewed MVP decision. Exclude correction, withdrawal, covering responsibility and acknowledgement UI until 3B-3. Published report is explicitly awaiting physician-review capability, not marked reviewed.

**Proposed additive migration boundary:** create LabResult with schema_version+publication_kind, draft/final/abandoned reporting, original entry/finalizer metadata and uniqueness. Add Order.current_publication/fulfilled_at and LabEvent.specimen/result protected links as needed (specimen link may already exist in 3B-1). Activate fulfilled-state constraints only once publication model exists. The kind registry initially enables report snapshots; do not reinterpret or rewrite old payloads in the next increment. Catalog/order/specimen/old application rows remain intact.

**Measurable checkpoint:** one active attempt, permanent rejection history, received-ever cancellation lock, correct lab assignment, no wrong-role/patient access, finite exact-unit values, missing/absent semantics, no fabricated performed time, one final publication per command, retained finalizer/source and immutable finalized row. Test collection after encounter completion with unchanged signed SOAP. A focused Chromium/UAT loop covers submit→collect→receive→enter→explicit finalize and forbidden-role URLs. Retain pending-review limitations until 3B-3. Separate 3B-2 PR/CI/UAT decision required.

## 3B-3 — Corrections, withdrawals, review and chart integration

**Dependencies:** approved verified 3B-2 schema/behavior and explicit review/withdrawal/administrative permission policy. This increment closes the full clinical lab loop; earlier checkpoints are intentionally partial local prototypes, not production-ready laboratories.

**Scope:** linear correction publications; append-only withdrawals/quarantine and terminal order behavior; immutable LabReviewAssignment and exact-publication/assignment LabResultReview; ineligible-reviewer administrative reassignment; physician review worklist; chart/encounter/longitudinal summaries; final permission/serialization/idempotency hardening and responsive workflows.

**Proposed additive migration boundary:** create LabReviewAssignment and LabResultReview; add order assignment pointer, event assignment/review links, withdrawn kind/status/constraints and permission codenames. Extend published-successor uniqueness to include withdrawn. Register withdrawal payload validator by its separate kind; preserve all prior report-kind schema meanings and published JSON bytes. Add current-assignment checks only after an explicit backfill creates initial original-physician assignments for existing submitted/fulfilled orders, with source=migration_backfill, actor NULL, recorded migration time and provenance. Inactive originals remain unresolved, not auto-covered. No past acknowledgement or clinical action is fabricated. Draft/cancelled orders need no current assignment. Review/publish guards become the full v0.2 contract after the backfill.

**Measurable checkpoint:** all [v0.2 acceptance cases](acceptance.md), revised v0.1 tests and pre-existing regression/browser suites pass; complete multi-role Chromium lifecycle includes completion-before-results, reassignment, correction, withdrawal, notice acknowledgement and quarantine denial. Verify old publication/review/assignment history, signed SOAP, existing clinical rows and allowed audit deltas. User UAT separately records the full journey and negative role/context cases. Separate 3B-3 PR/CI/UAT/merge approval required.

## Preservation and staging controls

Before each future migration, capture a consistent backup, old-row/schema/migration/source snapshots, SQLite integrity/FK results and the approved base. Review new-lab-only operations and any lab-row backfill. Compare protected old clinical rows and explicit new lab/audit/auth deltas afterward; never claim an unchanged whole-file hash across intentional schema/data changes. Do not reset/reseed the user's database or mutate signed documentation. Failure handling and any restore require review, not an automatic destructive rollback.

New routes/capabilities are exposed only at their implementation checkpoint; missing downstream work is labelled unavailable, not simulated with static rows. Earlier submit creation of a pending specimen is a deliberate schema dependency, not collection feature approval. CI/manual acceptance of one increment never approves the next one. This design PR creates none of the proposed implementation artifacts and remains unmerged for review.
