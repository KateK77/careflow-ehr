# Phase 2A manual acceptance guide

Status: awaiting user execution and feedback. The following are proposed checks, not completed manual observations.

## Start locally (PowerShell)

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

The migration is already applied on this computer; repeating migrate is safe. Keep the existing SQLite file and credentials; do not seed/reset it. Sign in at http://127.0.0.1:8000/login/. Existing usernames are physician.demo, frontdesk.demo, nurse.demo and administrator.demo. Use the user's existing passwords; none are committed. If forgotten, run `python manage.py changepassword physician.demo` locally (repeat for the specific account as needed).

## Primary workflow

1. As FrontDesk, select or create a synthetic appointment assigned to physician.demo for today. Mark Arrived using the existing check-in workflow. Verify the actor/time/history and that no encounter was created automatically.
2. Sign in as physician.demo. Open Physician workspace at `/app/physician/`; select the appointment's clinic-local date. Verify patient/MRN, appointment state and encounter status.
3. Open View chart. Check the identity banner, overview, encounter/note history, appointments and timeline. Only implemented sections have navigation.
4. Return to the appointment/worklist, choose Start encounter and Confirm encounter start. Verify the correct patient/appointment/physician and start timestamp. Reload or repeat the start POST: there must still be one encounter.
5. Choose Create SOAP draft. Enter fictional text in Subjective, Objective, Assessment and Plan, confirm synthetic content and Save draft. Refresh, reopen Edit SOAP draft, change text and save. Verify persistence and audit field names/actor/time.
6. Try signing an incomplete draft: it must be rejected. Restore all four sections, choose Review and sign, inspect the preview, select the explicit confirmation and Confirm and sign note.
7. Verify author/signing timestamp, read-only SOAP content and signing history. Attempt the saved edit URL directly: it must reject modification. A stale second-tab save/sign must not overwrite current content.
8. Complete encounter. Verify status and completion time survive refresh. The appointment remains Arrived and its check-in provenance is unchanged. Appointment cancellation is unavailable after encounter start.
9. Verify chart links open the same patient context and the timeline includes appointment, check-in and clinical events where recorded. Check keyboard focus, narrow viewport and the DEMO — NOT FOR CLINICAL USE banner.

## Role and isolation checks

- Physician: own worklist/encounters; an unrelated physician's encounter URL or mismatched patient/encounter URL must not reveal clinical content. Prior appointments also authorize longitudinal patient charts, but encounters/notes remain scoped to that physician unless another read role applies.
- Nurse: clinic chart/encounter/note read access; direct author/sign/complete requests denied.
- Administrator: clinic clinical read access; no implicit signing privileges. Combined Administrator+Physician still cannot sign another physician's note.
- FrontDesk: registration/scheduling continues; direct chart, encounter and note requests denied, without clinical text leakage.

Record actual pass/fail observations, account role, expected/actual results and non-sensitive reproduction steps in feedback.md. Do not enter real patient information. Existing default tests and optional developer browser checks are separate evidence.
