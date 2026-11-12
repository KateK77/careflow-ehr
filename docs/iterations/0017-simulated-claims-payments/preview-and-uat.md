# Consolidated Phase 5 and Phase 6 manual UAT

## Start the integrated preview

Use the Phase 6B branch and its new SQLite clone. The approved Phase 5B source and earlier previews are preserved. Choose an unused loopback port. Use only fictional inputs.

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = (Resolve-Path '.venv\phase6-b-preview.sqlite3').Path
.venv\Scripts\python.exe manage.py provision_billing_staff --username synthetic-billing --confirm-preview
.venv\Scripts\python.exe manage.py provision_portal_patient --username portal-a --patient-id 31 --confirm-preview
.venv\Scripts\python.exe manage.py provision_portal_patient --username portal-b --patient-id 2 --confirm-preview
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8016
```

Provision each account once in an interactive terminal and enter a unique demo password at the hidden prompt. Existing accounts and links are reused where present. Patient A is TEST-0001 and Patient B is DEMO-0002. Use separate browser profiles for the two patients and staff. Other staff accounts come from the integrated preview.

| Role | Entry point |
| --- | --- |
| Patient | `/portal/login/`, `/portal/` |
| Patient records | `/portal/appointments/`, `/portal/results/`, `/portal/medications/`, `/portal/visits/` |
| Patient conversations and requests | `/portal/messages/`, `/portal/requests/` |
| Ordering physician and assigned physician | `/app/portal/releases/`, `/app/portal/messages/` |
| Administrator or FrontDesk | `/app/portal/requests/` |
| BillingStaff | `/login/`, `/app/billing/`, `/app/billing/catalog/`, `/app/billing/coverage/`, `/app/billing/claims/` |
| Patient billing | `/portal/billing/`, then follow a released statement to its payment history |

## Manual observations to record

1. **Access and ownership.** Sign in separately as Patient A and B. Compare portal dashboards and appointment lists. Open Patient A's saved report, conversation, appointment request, statement, and payment history URLs while signed in as Patient B. Expect unavailable responses. Try a staff route while signed in as a patient. Verify logout clears access to bookmarked portal pages.
2. **Records and release.** Check clinic-local appointment dates, distinct appointment and encounter statuses, medication history and signed medication orders. Check the completed visit notice about unpublished patient summaries. Confirm SOAP, internal MAR and staff lab review details remain outside the portal. As the ordering physician, explicitly release an eligible lab result for Patient A. Check that acknowledgement alone did not release it, then check the corrected revision and withdrawn report boundaries using synthetic scenarios.
3. **Messaging and scheduling.** Send a fictional message as Patient A, mark it read and reply as the assigned physician, then verify the unread indicator, history and reply as Patient A. Submit new, reschedule and cancellation requests for eligible synthetic appointments. Check that pending requests leave appointments unchanged. Approve or reject through the Administrator or FrontDesk workspace and inspect the separate request and scheduling states.
4. **Billing scope.** Sign in as BillingStaff. Verify the worklist shows completed encounters. Search by MRN or encounter number. Try a billing URL while signed in as Administrator, Physician or FrontDesk without BillingStaff membership. Try clinical, MAR and laboratory staff edit URLs as the BillingStaff-only account.
5. **Coverage, charges and release.** Create a fictional active coverage record with a SYN- policy and a payer name beginning with Synthetic. Use an effective period that includes the completed encounter date. Create charge code SYN-VISIT at 1255 cents and add quantity 3 to a completed Patient A encounter, such as Encounter #3. Try draft edits and a void on an extra line. Confirm the remaining total is $37.65. Finalize the statement, confirm it remains hidden in the portal, and release it explicitly. Check itemization, coverage history and the released date as Patient A.
6. **Claim and appeal.** Create the claim from the finalized statement and select the effective coverage revision. Submit it to the internal simulator, queue it and record a denial with zero payer cents and a fictional denial category. Create an appeal, optionally link a finalized statement line, then submit. Verify the denial stays in effect until adjudication. Overturn with partial simulated approval and payer responsibility of 2000 cents. Check the earlier denial, appeal revisions and the $17.65 patient responsibility.
7. **Simulated payment reconciliation.** As BillingStaff, record a partial patient payment, the remainder and the simulated payer payment. Use distinct SYN- references. Check that an overpayment is rejected and that the combined balance reaches zero with Paid status. Reverse one payment with a reason, then confirm its original entry remains visible and the correct balance reopens. Compare the patient portal summary with staff history and check that internal references stay staff-only.
8. **Clinical preservation.** Reopen an existing signed SOAP note and the associated lab, medication, pharmacy and MAR histories in authorized staff views. Confirm their contents and history remain as expected. This is a preservation check during the new workflow and requires no repetition of prior Phase 4B manual UAT.

These are pending manual checks. Automated Django, Chromium and GitHub results are recorded separately.
