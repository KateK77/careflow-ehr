# Phase 3A manual acceptance checklist v1.0

Status: pending user execution. Phase 2A/2B UAT remains postponed; the following are proposed checks, not reported passes.

## Local startup

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

The nursing migration has been applied locally before delivery; repeating migrate is safe. Keep existing SQLite data and do not reseed/reset. Sign in at http://127.0.0.1:8000/login/ using existing nurse.demo, physician.demo, administrator.demo or frontdesk.demo passwords. No credentials were changed or committed. Use `python manage.py changepassword nurse.demo` locally only if its password is forgotten. Ensure the server runs the Phase 3A branch.

## Nursing workflow

1. As FrontDesk, select/create a synthetic appointment assigned to physician.demo for today and mark Arrived using the existing check-in workflow. Confirm actor/time and that no encounter exists automatically.
2. As nurse.demo, open Nursing workspace at `/app/nursing/`. Verify patient/MRN, physician, appointment interval/status. Filter by date, patient name/MRN and status. Invalid filters should show errors and no misleading results. Cross-midnight appointments should appear on both applicable local dates.
3. Open Nursing record. Before entry, assessment and vitals show clear missing-data states. Choose Record assessment, enter a fictional chief complaint, pain 0–10, observations and clinic-local assessment time; save. Refresh and verify original Nurse/time. Correct the assessment, mark Ready for provider and inspect previous values/actor/time. Appointment state must remain unchanged and no encounter should be created.
4. Record vitals: BP pair, heart/respiratory rate, temperature/unit, oxygen saturation, height/unit, weight/unit, pain, observation time and measured/patient-reported source. Partial panels are permitted, but an empty panel, a single BP value, malformed/fractional integer, nonfinite value, missing unit, invalid unit/range, future time or pre-birth time must be rejected. See ADR 0006 for the demo bounds; no interpretation or treatment advice should appear.
5. Refresh and verify persistence. Open Correct documentation, change a synthetic value and save. Original Nurse identity must persist, with last editor/version and before/after audit values recorded. A stale save from another tab must not overwrite the newer value and must retain submitted input for review.
6. Add another observation time, including a partial panel. Open Nursing flowsheet. Verify measurement rows, time columns, units, chronology and explicit missing values. Open an observation from a column and correct it through the permitted detail/edit flow. Check horizontal scrolling and keyboard focus at a narrow viewport; time pages should retain the appointment filter.

## Physician, state and isolation checks

7. As physician.demo, review the authorized chart, latest accessible nursing panel, rooming state, flowsheet and timeline events. An unrelated Physician must not see other physicians' appointment nursing data. The chart identifies source appointment/time and does not synthesize a complete panel from separate times.
8. Only the assigned Physician may explicitly start the clinical encounter. Appointment-linked nursing information recorded before start must appear in its encounter context. A new record may optionally select that matching encounter; a different patient/appointment encounter must be rejected. Existing nursing record encounter association is fixed.
9. Save/sign a fictional SOAP note, update permitted nursing documentation and compare the signed note's text/authorship/signature time: unchanged. Complete the encounter. Nursing history remains readable but new nursing records/corrections for that appointment are denied. Scheduled/cancelled/no-show appointments are also read-only for nursing writes.
10. Administrator and Physician alone can read within their scopes but cannot author nursing records through GET or POST. FrontDesk must be denied detailed nursing content. Active Nurse membership is required even for an Administrator account; a Nurse may correct another Nurse's permitted clinic record, preserving original authorship. Existing history/diagnosis/SOAP permissions remain unchanged.
11. Test forged patient/appointment/record IDs, foreign encounter selection, direct edit URLs and stale version requests. Confirm no cross-patient content leakage or association changes. Check DEMO — NOT FOR CLINICAL USE, labels, focus, worklist pagination, empty states and later refresh persistence.

Record actual observations, expected/actual results and non-sensitive reproduction steps in feedback.md. Never enter real patient information.
