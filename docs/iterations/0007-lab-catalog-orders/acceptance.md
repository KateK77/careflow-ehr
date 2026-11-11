# Local startup and manual UAT — Phase 3B-1

Manual acceptance is pending. Use synthetic data only. This feature branch includes a new lab migration, but the original `db.sqlite3` is **unmigrated and must not be migrated without separate approval**.

## Prepared preview on this Windows computer

The ignored preview `.venv/phase3b1-preview.sqlite3` is a consistent clone of the verified original backup. Only labs.0001_initial was applied there. Existing synthetic patients, appointments, encounters, notes, history, nursing records and account password hashes were preserved. New lab tables start empty; no clinical data or catalog was seeded. Backup: `.venv/backups/phase3b1/before.sqlite3`.

In a **new PowerShell terminal**, run:

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = Join-Path (Get-Location) '.venv/phase3b1-preview.sqlite3'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Open [staff login](http://127.0.0.1:8001/login/). Continue using the existing local passwords for `administrator.demo`, `physician.demo`, `nurse.demo` and `frontdesk.demo` (or your existing equivalent-role accounts). No password is embedded in Git and none was changed. If you do not know a password, resolve that explicitly rather than reseeding accounts. To stop, press Ctrl+C and remove the override with `Remove-Item Env:CAREFLOW_DB_PATH -ErrorAction SilentlyContinue`.

Do **not** run the application's migration/seed commands without the explicit preview path. Default configuration still points to original db.sqlite3; the new lab pages require the isolated migrated preview until original migration approval. Existing non-lab features do not issue lab-table queries merely from rendering their navigation.

For a fresh checkout, create a virtual environment and install requirements.txt; use a separately chosen synthetic test/preview database and migrate it explicitly. To recreate a preview from current original data, first obtain a consistent verified backup and choose a **new** file; never overwrite/reset either existing database. No reproduction step here authorizes original-database migration.

## Step-by-step user testing

1. Administrator: open **Laboratory catalog** at `/app/lab/catalog/`. Choose **Create catalog revision**. Keep the fictional SYN-CHEM-01/Demo chemistry example, mock serum and provided typed `demo-U` definitions; confirm synthetic information and create. It starts inactive. Confirm the synthetic action and **Activate** it. Physicians see active revisions; only Administrators see management controls.
2. Create another revision of the same SYN- code to test immutability/versioning. Attempt activation while the first revision is active: expect a readable error. Deactivate the first, then activate the second. Historical definitions are retained, not edited. For remaining steps choose an active revision.
3. FrontDesk/Administrator: choose an existing synthetic patient and create a future appointment later on the clinic's current date if no suitable arrived visit exists. Review/confirm the appointment and mark Arrived. Physician: open the assigned arrived appointment and explicitly start an encounter. Existing completed visits must remain untouched; do not reopen them.
4. Assigned Physician: open that in-progress encounter and **Create lab order**. Patient/encounter/physician context is fixed. Select an active panel, enter a synthetic reason, confirm synthetic data and **Save draft**. Refresh, **Edit draft**, change reason and save; verify persistence and incremented version/audit.
5. Choose **Review and submit**, confirm synthetic data, then **Review order**. Verify the fixed patient, panel/revision/specimen and reason. **Confirm submission**. Expect Submitted and exactly one Pending specimen with accession, preparation actor/time and no collection/receipt. Results/collection are explicitly unavailable.
6. Open **Laboratory orders** from the patient chart and **Encounter laboratory orders** from the encounter/order detail. Verify rows, role scope, status, audit actor/time and retained content. Review at desktop and split-screen/mobile widths; scroll hints expose full table content without truncating values.
7. Create a second draft for the same panel/encounter. Attempt review without repeat confirmation/reason: expect rejection with input retained. Confirm intentional repeat testing and enter a reason, review and submit; a distinct clinical order is now legitimate.
8. Cancel that eligible draft/submitted repeat order using **Cancel order**, a synthetic reason and confirmation. Confirm Cancelled, retained audit and retained pending preparation when previously submitted. Cancelled orders cannot be edited/resubmitted. Do not use SQL or fabricate collection metadata.
9. Open a draft in two tabs, save in the first and attempt a stale save in the second: expect conflict, no overwrite and retained input. Submission double clicks/browser retry must not create a second pending specimen or duplicate submission event. Reload before a new action.
10. Nurse: read submitted order detail/history but verify no edit/submit/cancel controls; direct submitted-order edit URL must return access denied. Drafts are not visible to Nurse alone. Administrator can read drafts for support but cannot author a Physician's order. FrontDesk cannot access laboratory pages/details. A different Physician cannot open another owner's order merely by guessing its UUID.
11. In the preview only, sign the existing synthetic SOAP note through the normal workflow and complete an encounter with a submitted order. Verify lab order remains readable and may be cancelled before receipt; a leftover draft cannot be edited/submitted but may be cancelled. Compare signed SOAP, encounter completion and appointment/check-in provenance before/after lab actions. No lab action should rewrite them.

## Routes and boundaries

Catalog: `/app/lab/catalog/`, creation `/app/lab/catalog/new/`. Composer: `/app/patients/<patient_id>/encounters/<encounter_id>/lab-orders/new/`. Patient history: `/app/patients/<patient_id>/lab-orders/`; encounter history adds `/encounters/<encounter_id>/lab-orders/`. Detail/edit/submit/cancel: `/app/lab/orders/<order_uuid>/` with corresponding action suffix.

There are no collection, receipt, result publishing/review or covering-assignment pages. Do not treat pending-specimen preparation as actual collection. Automated tests are not user acceptance; record actual observations and any defects before requesting merge. Tests use isolated databases, not either user database.


## Cross-phase UAT follow-up

The user reported successful catalog creation and activation and physician order creation, editing, submission and intentional-repeat confirmation during integrated Phase 3B manual UAT. These observations supersede the earlier pending status for the listed workflows. The catalog and Dashboard presentation fixes await a targeted manual retest.


## Final Phase 3B UAT closeout

The user created and activated a laboratory catalog item and created, edited and submitted a physician order. Duplicate-order validation and intentional-repeat confirmation were observed. The user retested and passed current Dashboard and Laboratory Catalog guidance.
