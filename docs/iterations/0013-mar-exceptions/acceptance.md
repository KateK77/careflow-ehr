# Phase 4B consolidated manual UAT

Status: pending user execution. Use the 4B-2 branch `phase/0013-mar-exceptions` and the prepared, separately named preview. Existing synthetic accounts and passwords were copied with the Phase 4A UAT data.

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = Join-Path (Get-Location) '.venv/phase4b-2-preview.sqlite3'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Open [staff login](http://127.0.0.1:8001/login/). Use `administrator.demo`, `physician.demo`, `nurse.demo`, `pharmacist.demo` and `frontdesk.demo` or the equivalent existing accounts. The clone is already migrated.

1. Use an existing synthetic patient. As Administrator or FrontDesk, make an appointment for the synthetic Physician and check in. Start its Encounter as that Physician. Keep it active while recording MAR outcomes.
2. As the assigned Physician, create and sign a fictional order from an active catalog revision. As Pharmacist, claim and approve it. Confirm the Nurse MAR worklist at `/app/mar/` has no task until you record simulated dispensing.
3. Dispense the full simulated quantity. As Nurse, open MAR from Nursing Workspace. Filter by patient ID, Encounter ID, medication and Pending. Open the task and confirm MRN, order reference, signed details, pharmacy status and historical allergy context.
4. Record a simulated administration using the full receipt quantity, an actual clinic-local event time at or after dispensing, optional fictional notes and explicit confirmation. Verify the effective state, actor, event time and recorded time. Reload and confirm the task has one outcome.
5. Prepare another signed, approved and dispensed order in the same active Encounter. Record Held with a fictional reason. Resolve it with an administration or another permitted outcome. On separate eligible tasks, verify Refused and Omitted with reasons and blank administration quantity. Check that missing reasons are rejected and terminal outcomes have no ordinary recording action.
6. Correct a recorded outcome with a fictional explanation. Verify the new effective revision and the earlier status, actor, event time and recording time in history. A correction to an exception requires its own exception reason.
7. As Physician, verify Patient Chart, Encounter, Physician Workspace, medication detail and history show the MAR state and a link to its history. Verify writing is denied. As Administrator, verify access does not grant Nurse actions. Verify direct MAR URLs deny FrontDesk, Lab Staff, Pharmacist-only and an unrelated Physician as appropriate.
8. Preserve the signed medication order. Sign the synthetic SOAP note and complete the Encounter. Verify prior MAR history is still readable and recording or corrections are blocked. Phase 4A late pharmacy verification and simulated dispensing for a different order signed before completion should continue. The late receipt supplies no actionable MAR task.
9. Check keyboard navigation, labels and responsive tables at the widths you use. Report exact observations and any defects before approving merges.

Each approved dispensing receipt supplies one fictional full-quantity task. The model has no scheduled-dose generator, partial administrations or post-completion amendment workflow.
