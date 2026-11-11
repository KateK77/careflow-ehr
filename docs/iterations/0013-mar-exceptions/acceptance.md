# Phase 4B consolidated manual UAT

Status: the consolidated user-reported manual UAT observations below passed. Use the 4B-2 branch `phase/0013-mar-exceptions` and the prepared, separately named preview. Existing synthetic accounts and passwords were copied with the Phase 4A UAT data.

## Passed user-reported manual UAT

The user tested in the separate Phase 4B integrated preview with synthetic patient Alice Testpatient (TEST-0001), Appointment #7 and Encounter #4. All times below are CST.

| Task and medication order | Observed outcome and history |
| --- | --- |
| #3 · `3456e76e-c7dd-4481-be4f-470b62b70229` | The Physician created and signed the order. The Pharmacist approved it and dispensed 2 simulated units at 02:51:51. The task appeared Pending in Encounter #4. Nurse `nurse.demo` recorded Administered v1 at 02:55:09 for event time 02:54:02. The Nurse corrected fictional wording at 02:59:03 without changing quantity, outcome or event time. Version 1 stayed Superseded. Version 2 showed Effective record · Correction and retained the correction reason. |
| #4 · `f865055c-891b-40ad-a9d2-c9c9d51ccb4f` | The Pharmacist approved it and dispensed 1 simulated unit at 03:04:12. Held v1 had event time 03:08:24 and retained its reason. Administered v2 had event time 03:09:30. Held v1 remained in history as Superseded. |
| #5 · `7e800e36-0310-4dba-98f7-a5ad967eb75d` | The Pharmacist approved it and dispensed 1 simulated unit at 03:14:08. The Nurse recorded Refused v1 at 03:15:31 for event time 03:15:06. The exception reason remained visible. Administration quantity was blank, and the ordinary administration action was absent. |
| #6 · `34b23d5d-e6ba-479b-bebc-53c0183b56b4` | The Pharmacist approved it and dispensed 1 simulated unit at 03:19:53. The Nurse recorded Omitted / Not given v1 at 03:21:37 for event time 03:21:22. The exception reason remained visible, and the ordinary administration action was absent. |

Encounter #4 completed on November 11, 2026 at 03:23:42 CST and remained Completed, version 2. Its SOAP note remained Signed and read-only, version 2, with the original signing time of 03:22:54 CST. All four synthetic SOAP sections remained unchanged. The completed Encounter displayed Tasks #3–#6 with their effective states. The Nurse reopened Task #3 and inspected both revisions. Its direct correction URL returned HTTP 403 after completion, and recorded content stayed readable.

## Additional observations and manual limits

- A separate signed order rejected by Pharmacy produced no MAR task. This is distinct from the Nurse's Refused outcome on Task #5.
- An unsigned draft remained at Encounter completion. Post-completion signing was outside the reported manual run.
- On port 8001 the user saw `OperationalError: no such table: mar_medicationadministrationevent`. Subsequent read-only inspection confirmed the intended preview path, the MAR table and both applied migrations. The Nursing and MAR workspaces loaded after restarting on port 8002 with `--noreload`. The error was no longer reproducible on the verified server. The cause remains undetermined.
- Comprehensive role denials, direct POST replay and duplicate submissions, concurrency and stale-version races, missing exception reasons, correction to an exception outcome, late pharmacy dispensing, keyboard and accessibility review, cross-device responsiveness and penetration testing are outside the reported manual scope.

## Verified preview startup

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = Join-Path (Get-Location) '.venv/phase4b-2-preview.sqlite3'
if (-not (Test-Path -LiteralPath $env:CAREFLOW_DB_PATH -PathType Leaf)) { throw 'Expected MAR preview database is missing.' }
$marMigrations = .\.venv\Scripts\python.exe manage.py showmigrations mar
$marMigrations
if ($LASTEXITCODE -ne 0 -or ($marMigrations | Where-Object { $_ -match '\[ \]' })) { throw 'MAR preview migration verification failed.' }
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8002 --noreload
```

Open [staff login](http://127.0.0.1:8002/login/). Use `administrator.demo`, `physician.demo`, `nurse.demo`, `pharmacist.demo` and `frontdesk.demo` or the equivalent existing accounts. The clone is already migrated.

## Original scenario checklist

The recorded passes above are complete. The original checklist below also includes steps beyond the reported evidence.

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
