# Deferred acceptance checklist — Phase 3B-2

Use only a separately selected preview, never the original database. Set CAREFLOW_DB_PATH to `.venv/phase3b2-preview.sqlite3`; this prepared clone is already migrated. Existing synthetic account passwords remain unchanged.

Provision a separate Lab Staff account only in the preview with `python manage.py provision_lab_staff --username lab.demo`; a secure password prompt is used (or process-local CAREFLOW_LAB_PASSWORD). The command refuses the original database and existing accounts. No account provisioning has been run on the user's databases by the agent.

1. Physician submits a synthetic order; Nurse opens Laboratory workspace and confirms MRN/DOB and collection time.
2. Correct collection before receipt with a reason. Reject a collected attempt and explicitly prepare recollection; verify retained rejected history and a distinct accession.
3. Lab Staff sees minimal unassigned requisitions, explicitly claims one with reason, receives a collected specimen and enters typed demo values or explicit not-performed reasons.
4. Preview and explicitly confirm publication. Check author, finalizer, timestamps, versions and immutable report. Same-person finalization is an MVP limitation.
5. Confirm no cancellation after any receipt, even after rejection. Explicitly abandon a draft before rejection. Verify no specimen mutation after publication.
6. Test stale requests, duplicate submission, wrong identifiers, invalid values/units and direct-URL role denials. Standalone Lab Staff cannot view clinical charts, SOAP, nursing records or other assigned patients.
7. Complete encounter before results; continue submitted processing and verify signed documentation is unchanged.

Routes: `/app/lab/workspace/`, `/app/lab/processing/<order_uuid>/`, action forms under `/app/lab/processing/<order_uuid>/<action>/`. Do not treat unperformed manual cases as passed. Consolidated 3B-3 acceptance will extend this checklist.
