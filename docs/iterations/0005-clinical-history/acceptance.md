# Phase 2B manual acceptance checklist v1.0

Status: pending user execution. These are proposed checks, not reported passes. Phase 2A UAT is also pending.

## Start the existing local project

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Sign in at http://127.0.0.1:8000/login/ with the existing local demo accounts/passwords. No passwords were changed or committed. No seed/reset command is needed. If a local password is forgotten, use `python manage.py changepassword physician.demo` for the specific account. Existing accounts are physician.demo, nurse.demo, administrator.demo and frontdesk.demo. Ensure the running server uses the Phase 2B branch. The additive history migration is already applied on this computer; migrate is idempotent.

## Patient history and provenance

1. As FrontDesk, select/create a synthetic appointment assigned to physician.demo, then mark it Arrived. As physician.demo, open the existing workspace/chart and explicitly start an encounter. No encounter is created at check-in.
2. Open Medical history. Create medical, surgical, family and social entries with fictional descriptions, dates, comments and source. Refresh to verify persistence. Open a detail, edit it, record a review and verify actor/time/history. Edit again: current review must clear while the prior review remains in history.
3. Open Problems. Create an active problem with optional mock code/onset. Resolve it using a valid resolution date, then verify it remains visible. Try a missing resolution date, future date and reversed date interval: reject them without changing saved data. Test inactive/reactivated states and stale edits from two tabs.

## Allergy consistency

4. A patient without an assessment must show Not reviewed, not No known allergies. Explicitly record Unknown, then No known allergies, checking reviewer/time.
5. Add an active fictional allergen/reaction/severity/source/verification. The summary must become Documented allergies and clear the previous summary review. Attempt No known allergies or Unknown while an active entry exists: reject it.
6. Inactivate/resolve the last active allergy. The entry remains visible and the summary becomes Not reviewed. Refuted/entered-in-error entries cannot be active. Reactivating a valid allergy restores Documented allergies. Review the record and assessment separately; confirm timestamps and history.

## Medication statements and diagnoses

7. Add a fictional active medication statement with dose description, route, frequency, source and dates. Review/edit it, then stop it with an end date and retain it as historical. Verify persistence/history and invalid end-date errors. No prescription, dispense or administration action should exist.
8. From the in-progress encounter, open Encounter diagnoses. Add a primary and secondary diagnosis, optionally linking this patient's problem. A second primary must be rejected; explicitly demote the existing primary before replacing it. Verify diagnoses do not automatically create/change longitudinal problems.
9. Save/sign a synthetic SOAP note and compare the signed content before/after history updates. Complete the encounter. Diagnosis edits/reviews/creation must be denied thereafter; historical diagnoses remain readable. If no other active treatment assignment exists, longitudinal history becomes read-only while the historical chart remains readable.

## Role and context isolation

10. Nurse and Administrator may read clinic longitudinal data and authorized encounter diagnoses, with create/edit/review POSTs denied unless separately qualified as a treating Physician. Administrator status alone grants no clinical authoring privilege. FrontDesk detail/history/diagnosis URLs must reveal no clinical content.
11. Another unassigned Physician must not access this patient's chart/history; an assigned Physician may see shared longitudinal records but only their authorized encounters/diagnoses. Mismatched patient/encounter/record IDs and a foreign patient's problem must be rejected. Stale edits/reviews must preserve newer content.
12. Verify chart summary/navigation/timeline links, empty states, keyboard labels/focus, 390-pixel layout and DEMO — NOT FOR CLINICAL USE notices. Do not enter real patient information.

Record actual outcomes and non-sensitive reproduction steps in feedback.md. Do not treat developer-run tests as user acceptance.
