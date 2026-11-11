# Phase 7 preview and consolidated manual UAT

Use the Phase 7B branch. The new clone is based on the main-compatible Phase 4B UAT preview. Use a free loopback port.

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = (Resolve-Path '.venv\phase7-b-preview.sqlite3').Path
.venv\Scripts\python.exe manage.py provision_radiology_staff --username synthetic-radiology --confirm-preview
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8017
```

Create the RadiologyStaff account once in an interactive terminal. Use the hidden password prompt. Existing synthetic Administrator, Physician and Nurse accounts are available in the clone. Use separate browser profiles and provision a second distinct RadiologyStaff username for isolation testing.

- Sign in at `/login/`. Administrator opens `/app/imaging/catalog/`. Physicians use `/app/physician/` and the encounter order link. RadiologyStaff open `/app/radiology/`. The ordering physician reviews at `/app/imaging/review/`.
- Create an active fictional catalog revision. Add an inactive revision and check ordering eligibility and history. From an authorized active encounter, create, edit, sign and schedule an order. Cancel a separate order with a reason.
- Confirm the unassigned queue withholds patient identity. Assign an order and test its direct URL as an unrelated radiology account. Verify a RadiologyStaff-only user cannot open the clinical chart.
- Schedule, start and perform an exam with a fictional SYN- study ID. Check that rescheduling and cancellation are denied once started. Save draft findings and impression and confirm they remain hidden from clinical viewers.
- Publish preliminary, complete the exam, then publish final. Confirm preliminary content is available to the ordering physician. Verify the Nurse can view final content but cannot acknowledge it. Acknowledge the exact revision as the ordering physician.
- Correct a final report, check the previous acknowledgement and review the correction separately. Withdraw it and verify clinical content is withheld. Use a separate context-error case and verify findings, impression and study metadata are also withheld in the assigned radiology view.
- Sign an order before finishing another encounter, then finish the exam and publish afterward. Compare the encounter state, signed SOAP sections, version and signing time before and after.
- Verify keyboard navigation and narrow-screen layouts. Record only observations actually made.

Manual acceptance remains pending. Automated evidence is recorded in the verification document.
