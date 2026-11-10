# ADR 0007 — Phase 3B-1 catalog and physician orders

Status: implemented on a feature branch for review/UAT; not merged or manually accepted. Source: approved implementation prompt and design v0.2 bea741de88fd0c719eb4ed39cf70ec7fd2959f3b. No design PR merge or future lab increment is implied.

## Boundary and persistence

Create only LabTestCatalog, LabOrder, pending-capable LabSpecimen and LabEvent. The initial migration creates four new lab tables, their indexes/constraints and a catalog FK between new tables; dependencies reference existing clinical/patient/auth migrations without rewriting them. No result, review, assignment or fulfillment model/status is introduced. Future specimen fields are nullable schema dependencies; supported saves refuse collection/receipt/rejection and no workflow routes exist.

Catalog content is immutable; Administrator creates inactive revisions and explicitly activates/deactivates using a versioned command. A partial unique constraint permits only one active revision per code. A strict, bounded JSON validator accepts only fictional SYN- numeric/coded definitions, canonical finite demo bounds/units and known schema version. Orders freeze exact definitions and submission identity. Deactivation prevents new commands/submission; historical definitions remain readable.

## Transactions and authorization

Only an active Physician owning an in-progress encounter can create/edit/submit. Derive patient, ordering identity and encounter from the authorized server context. Administrator alone cannot sign/submit a physician order. FrontDesk and standalone Lab Staff have no lab access; no new role is provisioned. Administrator reads clinic orders; Nurse reads submitted/cancelled-after-submission orders, not private drafts; Physicians read their own orders regardless of later encounter completion. Existing chart/encounter guards remain unchanged.

Use existing provider serialization first for physician commands, then lock/recheck encounter/order/catalog as needed. Submission and completion share the provider lock. Catalog-only commands reserve the SQLite writer with an empty-row UPDATE before lookup and lock the relevant existing catalog row on activation; unique catalog constraints guard creation/activation races. SQLite behavior is not PostgreSQL/production certification.

Successful commands store an actor-bound UUID, canonical SHA-256 input fingerprint and immutable LabEvent linked to one AuditEvent in the same transaction. Exact authorized replay returns its existing outcome, with no new clinical record/audit. A changed payload/action/context under the same UUID conflicts. Draft creation has a unique creation UUID as additional protection. Authorization precedes receipt disclosure; role revocation does not permit replay access. Operational provider serialization counters may advance on a replay, but domain rows/events do not duplicate.

Draft version changes invalidate stale editing and reviewed submission. Submission requires an actor/order/version/repeat-input signed preview token valid for ten minutes, plus explicit confirmation. Exact successful durable replay does not depend on a token still being unexpired. Every confirmation rechecks activation, versions, encounter state and duplicates under lock. Existing non-cancelled same-panel/code orders across catalog revisions require explicit intentional-repeat confirmation and reason; no clinical uniqueness rule prevents legitimate repeats.

Submission saves parent status, frozen content, one pending specimen and audit atomically. Pending provenance describes preparation by the ordering actor, never invented collection. A submitted order's content/context is immutable; eligible owner cancellation records reason/actor/time and preserves pending rows. Cancellation after any received_at is denied as a future-compatible boundary. No return to draft or resubmission after cancellation. Busy/unique/version races return safe retryable conflicts rather than silent overwrite.

## Database safety and local operation

The original SQLite database is backed up consistently and verified, but **not migrated**. `CAREFLOW_DB_PATH` is a local SQLite path override retaining the unchanged original default. It enables a separately named preview clone with existing synthetic records/accounts; only that clone and disposable test databases receive the additive migration. All original rows, database hash and historical document hashes are checked. Original migration application requires separate user approval.

Existing clinical pages gain navigation links only and do not query lab tables as part of their ordinary context rendering. New lab routes need the approved-migration preview database; no automatic migrate, seed, password change or fallback database replacement occurs. Preserve original signed notes, completion versions and appointment/check-in provenance. No clinical workflow mutates earlier history/nursing rows.

## Limits

Manual UAT pending; DEBUG-only single-clinic synthetic prototype. No real clinical terminology/reference rules, collection/results, clinical review/coverage, integrations, AI, deployment or production independent verification. Direct SQL/bulk ORM may bypass application guards; audit/model immutability is supported-path policy, not database-operator resistance.
