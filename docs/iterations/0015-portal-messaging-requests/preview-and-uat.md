# Phase 5 preview and consolidated manual UAT

Use the Phase 5B branch for the combined workflow. The preview was cloned from the integrated Phase 4B UAT database and migrated separately. Use the existing synthetic staff accounts in the clone. Choose an unused port if a prior preview is running.

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = (Resolve-Path '.venv\phase5-b-preview.sqlite3').Path
.venv\Scripts\python.exe manage.py provision_portal_patient --username portal-a --patient-id 31 --confirm-preview
.venv\Scripts\python.exe manage.py provision_portal_patient --username portal-b --patient-id 2 --confirm-preview
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8015
```

The provisioning command asks for a password interactively and refuses to overwrite an existing account or link. Run each provisioning command once. Use separate browser profiles for the two synthetic patients and staff so their sessions stay independent. Patient A is TEST-0001 and Patient B is DEMO-0002 in this preview.

| Audience | Local route |
| --- | --- |
| Patient login and dashboard | `/portal/login/`, `/portal/` |
| Patient records | `/portal/appointments/`, `/portal/results/`, `/portal/medications/`, `/portal/visits/` |
| Patient messaging | `/portal/messages/`, `/portal/messages/new/` |
| Appointment requests and history | `/portal/requests/` |
| Ordering physician result release | `/app/portal/releases/` |
| Assigned physician messages | `/app/portal/messages/` |
| Administrator or FrontDesk scheduling review | `/app/portal/requests/` |

## Manual checklist

- Sign in as Patient A. Verify the dashboard, clinic-local appointment times, separate appointment and visit statuses, and the demo notice. Sign out and verify that a bookmarked page requires login. Confirm that the patient session is denied direct staff access.
- In the clone, release an eligible published lab report as the ordering physician. Verify that Patient A can see only the released values and units. Confirm physician acknowledgement alone does not release a report. Use separate synthetic scenarios for correction and withdrawal. Check the old URL after each change, and verify that the corrected revision requires its own release.
- Check that medication history and signed or cancelled orders appear separately. Verify simulated pharmacy dispensing is labelled as such. Open completed visit records and confirm the notice about unavailable patient-facing summaries. Check that draft orders, signed SOAP and MAR notes are absent from portal pages.
- Send a fictional nonurgent message as Patient A. Verify the assigned physician sees an unread thread and can mark it read and reply. Return as Patient A and confirm the unread count, reply, sender, time and preserved history.
- As Patient A, submit a new appointment request. Verify it stays pending without adding an appointment. Approve as scheduling staff and verify the separate request and appointment statuses, response and history. Repeat with rescheduling and cancellation on an eligible future synthetic appointment. Reject a separate request and verify the schedule is unchanged. Test a conflicting slot and confirm it cannot be approved.
- As Patient B, try Patient A's saved report, message and request URLs. Confirm they return unavailable and the navigation lists only Patient B's data. Try the message worklist as an unassigned physician and the scheduling review as an unauthorized staff role.
- Repeat representative pages at a narrow mobile width. Check keyboard focus, labels, validation errors and table scrolling. Record only observations actually made during UAT.
