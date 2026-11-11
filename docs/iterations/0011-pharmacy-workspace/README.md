# Phase 4A-2 — Pharmacy Verification & Simulated Dispensing

[Issue #25](https://github.com/KateK77/careflow-ehr/issues/25). Stacked on verified 4A-1 commit `9f4f3ce7c8d4afa95836ee946f1d77573c6e163e`. The [approved prompt](../0010-medication-orders/prompt.md) covers both increments. Requirements S22 and W03 and the pharmacy section of the English baseline guide this increment. MAR is outside the approved scope.

- Active Pharmacists see unclaimed signed requisitions by reference, medication and signing time. Claim grants the assigned Pharmacist a restricted view with patient name and MRN, signed instructions, historical allergy assessment and pharmacy activity. Existing patient, chart, SOAP, lab and nursing permissions still govern their own views.
- Order state stays signed throughout pharmacy processing. Only an unclaimed signed order may be cancelled by its author. A claim serializes against cancellation on the ordering provider lock.
- Claim opens a pending review. Pending review can be approved, rejected with reason or sent for clarification with reason. The original physician may respond without changing signed content. The response returns review to pending. Rejection is terminal.
- An approved review permits one simulated dispense for the exact ordered quantity. Dispense is recorded independently from verification. A unique immutable receipt and a transactional command event guard against duplicates.
- Processing can continue on a completed Encounter only for an order signed before completion. The service preserves signed content, SOAP, clinical history and Encounter state.
- Manual UAT is consolidated after publication. The [acceptance checklist](acceptance.md) describes the workflow.
