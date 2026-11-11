# Consolidated Phase 3B manual UAT and safe startup

The user reported successful execution of the main end-to-end workflows below. The observations in this section record the scope of that manual run. The full checklist remains a reference for follow-up testing.

| Area | User-reported manual observation |
| --- | --- |
| Catalog | Created and activated a laboratory catalog item. |
| Orders | Created, edited and submitted an order as a Physician. Confirmed an intentional repeat. |
| Collection | Collected a specimen as a Nurse and observed rejection of an incorrect MRN. |
| Processing | Claimed an order as Lab Staff, received the specimen and finalized a report. |
| Review and correction | Acknowledged a specific report revision. Published an append-only correction and reviewed the corrected revision. |
| Withdrawal | Withdrew a report and acknowledged the withdrawal notice. |
| Coverage | Reassigned responsibility to a covering Physician and observed restricted chart access. |
| Quarantine | Observed context-error quarantine in the tested Physician, Administrator and Nurse report views. |
| Encounter completion | Processed and acknowledged laboratory results after Encounter completion. |
| Signed SOAP | Observed preservation of signed content, version and signing time. |

The manual run covered the roles, views and workflows listed above. Comprehensive security, concurrency, accessibility and the remaining negative cases were outside the reported manual scope. Automated evidence is recorded separately in [verification.md](verification.md).

### Targeted manual UI retest

1. Open Dashboard and the laboratory catalog. Check that guidance and links match the role and current workspace.
2. Open a submitted order and its processing page. Check separators, action headings and audit labels.
3. Open an unpublished correction draft. Verify that the draft and current publication have distinct labels.
4. Preview a result before publication. Check the report revision, accession, performed time and component table with keyboard navigation.
5. Open the acknowledgement form and check its action label. Compare the existing acknowledgement history without editing the recorded comment.

## Prepared integrated preview on this Windows computer

The active development branch is `phase/0009-lab-review-integration`. The independent clone `.venv/phase3b3-preview.sqlite3` is already migrated through labs.0005. It contains the copied pre-existing synthetic patients, appointments, encounters, signed SOAP, clinical/nursing history and password hashes. Lab tables are initially empty. Original database, consistent backup and both earlier previews are preserved.

Open a new PowerShell terminal:

```powershell
Set-Location 'D:\AI-Workspace\Personal\careflow-ehr'
$env:CAREFLOW_DB_PATH = Join-Path (Get-Location) '.venv/phase3b3-preview.sqlite3'
.\.venv\Scripts\python.exe manage.py shell -c "from django.conf import settings; from pathlib import Path; assert Path(settings.DATABASES['default']['NAME']).resolve() == (settings.BASE_DIR / '.venv/phase3b3-preview.sqlite3').resolve(); print('Integrated preview selected')"
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py provision_lab_staff --username lab.demo
.\.venv\Scripts\python.exe manage.py grant_lab_preview_permissions --username administrator.demo --reassign-review --confirm-preview
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

The Lab Staff command securely prompts for a new password, validates it and refuses existing usernames; run it only once. If an account already exists, reuse its known password rather than resetting/reseeding. Existing `administrator.demo`, `physician.demo`, `nurse.demo` and `frontdesk.demo` retain their existing passwords; substitute your equivalent account names if needed. Permission grant requires an existing active Administrator and explicit preview confirmation. It does not grant quarantine inspection by default. No provisioning/grant has been executed against your prepared preview by the agent.

Open [staff login](http://127.0.0.1:8001/login/). Lab Staff is directed to `/app/lab/workspace/`; other roles retain existing dashboards. To stop, Ctrl+C, then `Remove-Item Env:CAREFLOW_DB_PATH -ErrorAction SilentlyContinue`. Stop the server before removing the override. Do not launch this feature branch against the original unmigrated database, migrate/reseed it, or overwrite an earlier preview.

A fresh checkout needs Python/virtual environment, `pip install -r requirements.txt`, and an explicitly selected **new disposable synthetic database**. Existing-data previews require a consistent SQLite online backup to a new file that does not exist, followed by migrations only with CAREFLOW_DB_PATH pointing at that clone. Do not copy an actively written database with an ordinary file copy or overwrite a populated preview. No instructions here authorize original-database migration.

## Functional manual checklist

1. **Catalog:** Administrator creates an immutable fictional SYN- panel revision and explicitly activates it. Verify one active revision per code, clear validation and retained historical revisions. Use demo units only.
2. **Ordering:** choose an existing synthetic patient. FrontDesk creates/arrives a suitable appointment for the intended Physician if needed; Physician starts its encounter. Create, reopen/edit and persist a lab draft. Patient/encounter/ordering identity must stay fixed.
3. **Submission:** review/confirm the draft. Verify submitted order, one pending attempt, accession and auditable original identity. Retry the same command without a second specimen. A fresh intentional repeated panel requires a new confirmation/reason.
4. **Collection:** Nurse opens laboratory workspace. Deliberately test wrong MRN/DOB and missing confirmation, then collect with both correct identifiers and valid timestamp. Correct collection before receipt with reason; verify original collector and audit history.
5. **Recollection:** reject a collected attempt with reason, prepare recollection and collect its new attempt. Verify rejected history is permanent, accessions differ and only one attempt is active.
6. **Assignment/receipt:** Lab Staff sees only minimal unassigned requisitions, claims explicitly, then verifies accession and receives the collected specimen. Test wrong accession and a different unassigned Lab Staff direct URL. Administrator assignment must not authorize Administrator result entry.
7. **Draft/validation:** assigned Lab Staff starts a result draft and enters typed components. Test wrong units, nonfinite/exponent/overprecision values, unknown keys, duplicate codes, missing required values and explicit not-performed reasons. Drafts remain unpublished and withheld from clinical readers. Active draft must be abandoned before specimen rejection.
8. **First publication:** preview then explicitly finalize. Verify frozen snapshot, entry/finalizer identities and publication timestamps; same-person finalization is a labelled MVP limitation. Verify published result/specimen cannot be edited, cancelled or recollected.
9. **Late results:** in a separate suitable order, sign/complete the encounter through normal clinical workflow before publication. Process the already-submitted order afterward. Verify encounter stays completed, signed SOAP and appointment/check-in provenance remain unchanged.
10. **Physician review:** results worklist and chart/encounter summaries show current revision and review required. Acknowledge explicitly; verify exact publication/assignment, actor/time and persisted status. No clinical recommendations are generated.
11. **Correction:** assigned Lab Staff creates a reasoned correction draft from current report. Old report remains current while drafting. Publish corrected revision, confirm old values/reviews remain and a new acknowledgement is required. Abandon a different correction and verify it does not replace the current publication.
12. **Coverage:** prepare an ineligible responsible Physician and an active covering Physician in the isolated preview only (see setup below). Administrator with explicit reassignment capability previews/confirms a reasoned assignment. Verify original order/previous reviews unchanged; covering Physician can review the exact lab report but cannot access unrelated chart, SOAP, other orders, author an original order or cancel on the original owner's behalf. Fresh acknowledgement is required, including when responsibility later returns to the same Physician.
13. **Withdrawal:** abandon any correction draft, then assigned Lab Staff previews/confirms report-error withdrawal. Verify append-only no-value notice, preserved prior reports/reviews, current pointer at notice, terminal order and notice-review requirement. Historical values must be labelled unusable history; no fallback/negative/absent current result.
14. **Quarantine:** use a separate report and context-error withdrawal. Ordinary Physician/Nurse/Administrator must not receive previous measurements, component comments, review comments or unrestricted withdrawal reasons through chart, history, processing, old order or acknowledgement routes. Assigned Lab Staff can inspect within its order. Optionally grant Administrator inspection explicitly with `grant_lab_preview_permissions --username administrator.demo --inspect-quarantine --confirm-preview`; verify it is a separate capability. Notice acknowledgement never restores reporting.
15. **Negative/UI checks:** FrontDesk detailed lab denial; Nurse/Administrator result-write denial; wrong patient/encounter/result/assignment targets; stale tabs; duplicate commands; failed writes leave no partial audit/publication; readable responsive tables and navigation. Observe the DEMO notice on all pages. Test keyboard operation and narrower viewports beyond automated 390/700/1440 coverage.

## Covering-physician test preparation

There is no new general account-administration UI in this scope. Automated tests prepare eligibility changes explicitly. For optional human coverage testing, stop the preview server, retain/verify the explicit preview override, and use `python manage.py shell` as a local test administrator. Create a **new** synthetic covering account (never overwrite an existing one) with a password supplied by `getpass`, validated through Django password validation, and Physician group only. Mark only the selected preview ordering Physician inactive after finishing its clinical setup. Then restart the preview server and perform the actual assignment through the Administrator laboratory UI. Do not modify the original database, original account passwords or signed documentation. Record these as test setup, not application-generated auto-routing or user impersonation.

## Pages / URLs

- Catalog: `/app/lab/catalog/`; contextual composer: `/app/patients/<patient_id>/encounters/<encounter_id>/lab-orders/new/`.
- Specimen/processing workspace: `/app/lab/workspace/`; bounded detail/actions: `/app/lab/processing/<order_uuid>/`.
- Physician worklist: `/app/lab/results/`; report revisions/review/correction/withdrawal: `/app/lab/reports/<order_uuid>/` and action suffixes.
- Longitudinal history: `/app/patients/<patient_id>/lab-orders/`; encounter history adds `/encounters/<encounter_id>/lab-orders/`.
- Existing patient charts and encounter pages include safe laboratory summaries and metadata timeline navigation. Covering assignment does not create general chart access.

Use the reported observations above as the manual UAT record. Record the targeted UI retest and any additional observations separately.


## Final Phase 3B UAT closeout

The user reported successful catalog creation and activation, physician order creation, editing and submission, and duplicate-order validation. The Nurse collected the specimen and observed incorrect-MRN rejection. Lab Staff claimed the order, received the specimen and published the report. The user observed version-specific physician acknowledgement, immutable correction and renewed review, and withdrawal with notice acknowledgement. After reassignment, a covering physician independently acknowledged the report and had restricted patient-chart access. The user observed context-error quarantine in the tested Physician, Administrator and Nurse report views. Laboratory processing and acknowledgement continued after Encounter completion. Signed SOAP content, version and signing time were preserved in the reported workflow.

The following targeted UI retests passed:

- Dashboard current feature guidance.
- Laboratory Catalog current guidance.
- Processing page separator encoding.
- Human-readable audit labels.
- Laboratory Report History presentation.
- Human-readable correction action title.
- Responsive laboratory workspace at the tested widths.

The unpublished draft label and structured finalization preview have automated evidence. Their manual retests remain outstanding. The first acknowledgement comment was unusually long. Investigation found no reproducible saving defect and preserved the original comment.

The reported manual UAT was limited to the listed workflows, roles, views and widths. Full security, accessibility, concurrency and comprehensive negative-case manual verification remain outstanding.
