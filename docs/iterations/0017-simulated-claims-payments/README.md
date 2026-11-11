# Phase 6B — Simulated Claims, Denials, Appeals & Payments

[Issue #37](https://github.com/KateK77/careflow-ehr/issues/37) · [Approved prompt](../0016-billing-statements/prompt.md) · [Phase 6A PR #36](https://github.com/KateK77/careflow-ehr/pull/36)

## Design

A mock claim references an immutable finalized or released statement and one exact revision of synthetic coverage for the same patient, effective on the encounter's clinic-local date. The internal simulator uses explicit authorized steps: Draft → Submitted → Pending adjudication → Approved, Partially approved, or Denied. Outcomes append adjudication rows with payer allocation in cents. The patient's responsibility is the statement total less the payer allocation. A denial requires a fictional category and zero payer allocation.

A denied claim can receive an appeal. Staff create or revise a draft, link an optional immutable statement line from that claim, submit the appeal, then explicitly uphold or overturn the denial. The earlier denial and appeal revisions remain available. An appeal outcome that conflicts with already recorded payments is rejected.

Payments are immutable, classified as simulated payer or patient payments, and reference a released statement. Reversals are separate full offset entries linked to the original. Staff use a balance version derived from the claim version and ledger length. The service serializes writes and checks each source's responsibility before posting. Outstanding balances are derived from immutable amounts and net payments. No external financial systems are involved.

## Review

[Combined Phase 5 and 6 preview and UAT](preview-and-uat.md) · [Verification](verification.md)

This increment adds `MockClaim`, `MockAdjudication`, `MockAppeal` and `SimulatedPayment` in the additive `billing.0002_mockclaim_mockappeal_mockadjudication_and_more` migration. It extends the billing worklist and statement views with simulator and payment routes, staff history, and patient-scoped payment summaries.

The prototype supports one claim per statement and full offset reversals. It has no credits, secondary payer coordination, post-finalization charge adjustments or patient self-payment. BillingStaff record synthetic payments. Appeals can reference an existing statement line within the claim and have no clinical-evidence access. Existing coverage revisions, statement snapshots and signed clinical records remain outside simulator mutations. Application-level immutability assumes supported services and does not prevent direct SQLite administration.
