# Consolidated Phase 5–8 manual UAT

## Start the unified preview

Use the Phase 8B branch. The preview is a consistent clone of the Phase 5–7 integration database, which was backed up from Phase 6B and received the two imaging migrations. The final clone adds the two hospital migrations. It contains the chosen source's records. Imaging data entered in separate Phase 7 previews remains in those previews.

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = (Resolve-Path '.venv\phase8-final-preview.sqlite3').Path
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8018
```

Staff sign in at `http://127.0.0.1:8018/login/`. Patients sign in at `http://127.0.0.1:8018/portal/login/`. If the server is already running on port 8018, use that instance. Use separate browser profiles to verify role boundaries.

## Accounts

Reuse existing synthetic staff and patient accounts where available. With the same database environment variable set, run the command below once per new account. Use a unique username and enter a new password at the interactive prompt.

```powershell
.venv\Scripts\python.exe manage.py provision_integrated_user --username synthetic-ops --role HospitalOperations --confirm-preview
.venv\Scripts\python.exe manage.py provision_integrated_user --username portal-a --role PatientPortal --patient-id 31 --confirm-preview
.venv\Scripts\python.exe manage.py provision_integrated_user --username portal-b --role PatientPortal --patient-id 2 --confirm-preview
```

The other supported roles are Administrator, Physician, Nurse, RadiologyStaff and BillingStaff. Substitute the role and a distinct username for the operations example. Omit patient ID for staff. A new Physician account only sees charts and episodes assigned to that account. The command rejects existing usernames and patient links.

## Acceptance checklist

1. **Phase 5 account ownership and records.** Verify the two linked patients see their own visits, appointments and medication records. Explicitly release a current laboratory report as the ordering physician. Check that acknowledgement alone does not release results and that corrected or withdrawn reports obey the release policy. Try the first patient's report and conversation URLs as the second patient. Try staff URLs while signed into the portal.
2. **Phase 5 messaging and appointment requests.** Send a synthetic message, mark it read and reply as the assigned Physician, then check the patient's unread status and history. Submit new, reschedule and cancellation requests. Confirm requests do not change scheduling until Administrator or FrontDesk reviews them. Verify separate request and appointment histories and conflict handling.
3. **Phase 6 Billing and Claims.** As BillingStaff open `/app/billing/`. Add a fictional active coverage revision effective on a completed encounter, then capture itemized charges. Finalize and release the statement, verify only the linked patient sees it, then submit a mock claim through `/app/billing/claims/`. Deny, appeal and record a revised allocation. Record patient and payer payments, verify balances and Paid status, and reverse a payment. Check that the original remains in history.
4. **Phase 7 Imaging.** In `/app/imaging/catalog/`, create and activate a fictional code. Create, edit and sign an imaging order from an active encounter. In `/app/radiology/`, confirm the unassigned order withholds identity, self-assign, then schedule, start, perform and complete the exam. Publish preliminary and final reports, acknowledge the final in `/app/imaging/review/`, correct and re-acknowledge, and withdraw in a separate case. Confirm the context-error policy hides values and metadata. Try the same assigned exam URL as another radiology account.
5. **Phase 8A Admissions and beds.** Open `/app/inpatient/` as HospitalOperations. Create a synthetic department, two inpatient wards, rooms and beds in Ward and Room Management. From the Admission Worklist create a request, admit with an attending physician, check occupancy, transfer with a reason and verify both historical beds. As the attending Physician save a discharge plan. As operations staff confirm discharge with a synthetic summary. Check bed release and read-only history. Try a conflicting allocation and a direct transfer POST as Nurse.
6. **Phase 8B ED discharge.** Add an Emergency ward and room in facility management. Register a synthetic arrival in `/app/ed/`. As Nurse record and revise a fictional triage label, then room and assign a physician. As that physician begin provider review, enter observation, and explicitly discharge with a synthetic disposition summary. Verify elapsed wait, room release and the timeline.
7. **Phase 8B ED admission.** Run a second ED case through provider review and admit from the ED as operations staff. Confirm the linked inpatient stay uses the selected bed and assigned clinician, the ED room is released and a second admission or occupied bed is rejected. Test a wrong-patient URL and try ED and inpatient URLs as BillingStaff, RadiologyStaff, Pharmacist and FrontDesk.
8. **Clinical history and isolation.** Compare existing signed SOAP content, version and signing time, lab publication history, nursing records, medications, pharmacy and MAR before and after the new workflows. Confirm hospital episode pages honor Patient Chart permissions and preserve outpatient encounter context. Record only observed results and any deferred scenarios.

Manual UAT remains pending. The linked verification documents report automated evidence separately.
