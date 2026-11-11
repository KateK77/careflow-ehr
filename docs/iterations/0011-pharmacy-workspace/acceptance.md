# Phase 4A consolidated manual UAT

Status: two scenarios passed in user-reported manual UAT. Other checklist items have no recorded manual outcome here. Run on `phase/0011-pharmacy-workspace`. The prepared preview is a separate migrated clone of the verified Phase 3B backup.

## Passed user-reported manual UAT

- **Pharmacy follow-up after Encounter completion.** Encounter #3 completed on November 11, 2026 at 01:41:39 CST. For order `8c82d26f-ef6f-4786-83e1-5a2bf83820db`, pharmacy claim occurred at 01:43:15 CST, verification approval at 01:44:31 CST and simulated dispensing at 01:45:06 CST.
- **Encounter and signed SOAP preservation.** The before-and-after comparison confirmed Encounter #3 remained Completed at version 2. SOAP Note #3 remained Signed and read-only at version 2. The original signing time remained 01:41:27 CST and all four SOAP sections were unchanged.

These completed scenarios require no repeat manual run. The scope of the observations is the stated Encounter, note and order.

## Start the integrated preview

In a new PowerShell terminal:

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = Join-Path (Get-Location) '.venv/phase4a-2-preview.sqlite3'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py provision_pharmacist --username pharmacist.demo --confirm-preview
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Provision the new account once and enter its password at the hidden prompt. An existing username is refused. The preview already has the Phase 4A schema. Use the existing passwords for `administrator.demo`, `physician.demo`, `nurse.demo` and `frontdesk.demo` or their equivalents in the preview. Open [staff login](http://127.0.0.1:8001/login/). The prepared preview contains copied synthetic data. Use a fresh in-progress Encounter assigned to the physician for ordering.

## Scenarios

1. As Administrator, open Medication Catalog at `/app/medications/catalog/`. Create revision 1 for `SYN-AMBER`, name `Synthetic Amber`, Demo tablet, strength `10 demo units`, oral and daily. Activate it. Try activating a competing revision of the same code while revision 1 is active. Verify the readable conflict. Later retire revision 1 and activate revision 2, then verify that an existing signed order still shows revision 1.
2. As the assigned Physician, open the Encounter and choose Create medication order. Enter `1 demo units`, oral, daily, two days, two simulated units and fictional instructions. Save and reopen the draft. Edit it and verify the version. Open Review and Sign, check the fixed patient context and complete order, then confirm the synthetic signature.
3. Compare Patient Chart and Encounter summaries and full medication history. Confirm the author, signature, time and earlier draft versions. Check historical allergy context. Nurse can read the signed order. FrontDesk and Lab Staff cannot open it. Administrator cannot sign. An unrelated physician cannot edit or sign.
4. On a separate signed order, cancel before pharmacy claim and enter a reason. Verify signature and signed content remain visible in history. On another draft, try signing after Encounter completion and confirm the action is denied.
5. As Pharmacist, open `/app/pharmacy/`. The unclaimed queue shows requisition references and synthetic medication without patient identity. Claim a signed order, then verify the assigned detail shows name, MRN, signed instructions and historical allergy assessment. Try direct links to Patient Chart, patient directory and clinical notes. Confirm access is denied for the Pharmacist-only account.
6. Request clarification with a fictional reason. Check the Physician order detail for the reason and respond. Verify the original signed content and signature. The Pharmacist can approve once the review is pending again.
7. Record simulated dispensing for the full signed quantity. Verify Approved remains the verification state and the dispensing receipt has quantity, actor and time. Refresh or submit a stale form to check that another receipt is not created. Confirm the Physician sees the result in chart and Encounter views.
8. Use a separate signed order to reject with a reason. Verify approval and dispensing are unavailable for that review. Check that a claimed order cannot be cancelled and that an unsigned draft is absent from the pharmacy queue.
9. **Passed for post-completion pharmacy processing and preservation of the Encounter and signed SOAP note.** See the recorded observations above.
10. Check keyboard navigation, validation messages and responsive tables at the widths you use. Record exact observations and any defects before approving merges.

The prototype supports one claim per order and a single full-quantity simulated receipt. Claims have no transfer workflow. A clarification response adds an audited explanation. Changed medication content requires a new signed order. There is no real dosing, safety certification, physical dispensing or MAR in this phase.
