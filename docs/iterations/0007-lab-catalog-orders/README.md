# Iteration 0007 — Phase 3B-1: Laboratory Catalog & Physician Orders

- [Implementation Issue #17](https://github.com/KateK77/careflow-ehr/issues/17).
- Branch `phase/0007-lab-catalog-orders`, created from verified main `56ea8b332525926b02759b2afefa93166bd52d31`.
- Approved design reference: [v0.2 at bea741d](https://github.com/KateK77/careflow-ehr/tree/bea741de88fd0c719eb4ed39cf70ec7fd2959f3b/docs/design/phase-3b-laboratory/v0.2), with v0.1 foundation and v0.2/increments.md precedence. [Design PR #16](https://github.com/KateK77/careflow-ehr/pull/16) remains open/unmerged; it was not copied or merged into this feature branch.
- [Approved implementation prompt verbatim](prompt.md), [feedback/scope](feedback.md), [verification](verification.md), [startup and manual UAT](acceptance.md), [changed files](changed-files.md).
- [Branch comparison / PR entry](https://github.com/KateK77/careflow-ehr/compare/main...phase/0007-lab-catalog-orders) and [commit history](https://github.com/KateK77/careflow-ehr/commits/phase/0007-lab-catalog-orders). The published PR links the exact implementation SHA, Issue and CI runs.

## Implemented scope and acceptance boundary

Functional synthetic catalog revisions, immutable definitions and explicit Administrator activation; Physician draft creation/editing in owned in-progress encounters; review/confirmation before submission; exactly one atomic pending specimen; eligible reasoned cancellation; role/context-scoped patient/encounter history, detail and audit presentation; durable actor-bound UUID receipts, provider serialization and optimistic versions. Original UI, DEMO notice, readable forms and contained responsive tables remain.

Scope maps to design LAB-01–LAB-05 (pending preparation only), LAB-12–LAB-16 and v0.2's explicit 3B-1 checkpoint. There is no collection/receipt/result/review/cover-assignment workflow, new staff role, prescribing, FHIR interface, AI or deployment. States exposed for orders are Draft, Submitted and Cancelled only. Future specimen columns exist as planned schema dependency, but supported saves reject non-pending state/collection metadata and no downstream routes/buttons exist.

**The user's original db.sqlite3 is deliberately not migrated.** A consistent verified backup and separate migrated preview clone are prepared under ignored `.venv/`. Use [the exact preview startup](acceptance.md); do not run migrations against the original database without separate approval. Existing accounts/passwords and synthetic records are preserved in the clone without reseeding.

## Decisions and remaining review

See [ADR 0007](../../decisions/0007-lab-catalog-orders.md). Same-name/panel duplicates require explicit intentional-repeat confirmation/reason, whereas HTTP replay returns its existing outcome without another clinical write. Submitted orders remain accessible after completion; cancellation may continue before receipt while draft editing/submission stops. No signed note or original encounter/appointment provenance is changed by laboratory operations.

Manual UAT is **pending**. Do not merge this feature PR or start 3B-2/3B-3 until separately approved. Broader original UX backlog remains deferred. Direct SQL/bulk ORM operators can bypass application guards; no production security, clinical validity or PostgreSQL concurrency claim is made.
