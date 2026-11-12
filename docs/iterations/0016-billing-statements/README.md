# Phase 6A — Billing, Coverage & Patient Statements

[Issue #35](https://github.com/KateK77/careflow-ehr/issues/35) · [Approved prompt](prompt.md) · [Verification](verification.md)

Implements the charge capture and statement release portion of W10. The branch starts at Phase 5B PR #34, commit `1d1cc8fa1da38d65c728f5403237bd7abd15b6e6`.

BillingStaff membership is required for the billing worklist, catalog, coverage and statement actions. Other staff roles confer no billing access. BillingStaff receive demographic identifiers and encounter completion context needed for billing, with no clinical role assignment. Patients only see released statements and a summary of their own synthetic coverage through explicit portal ownership.

Catalog and coverage edits append immutable revisions. A charge references the selected catalog revision and quantity. A draft statement can have charges added, edited or voided. Voiding an entire draft is terminal in this preview and preserves the charges and history. A finalized statement snapshots the active lines and total in integer cents, followed by a separate release action. Finalized and released amounts remain fixed. Post-finalization charge corrections and financial credits require a future adjustment policy. Phase 6B will handle payment reversals independently of statement amounts.

The global billing writer row serializes the prototype's billing mutations. An actor-bound command key and payload digest protect replay. Statement versions reject stale writes, and successful audit events commit atomically with the mutation.

## Routes and preview

- Billing staff sign in at `/login/` and use `/app/billing/`, `/app/billing/catalog/`, `/app/billing/coverage/` and the encounter links on the worklist.
- Patient portal users navigate to `/portal/billing/`.
- Set `CAREFLOW_DB_PATH` explicitly to `.venv/phase6-a-preview.sqlite3` and use `python manage.py provision_billing_staff --username synthetic-billing --confirm-preview` in an interactive terminal. Existing accounts are preserved. Manual UAT is deferred until Phase 6B is available.

Application changes are confined to the new billing app, a workspace link and staff login routing, plus portal integration. The only migration is `billing.0001_initial`.
