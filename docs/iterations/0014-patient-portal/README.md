# Phase 5A — Patient Portal records

[Issue #31](https://github.com/KateK77/careflow-ehr/issues/31). Base `00c624553cc265e6275a9d2750ab0041a7e6d97f`. Requirements S24, W01, W02 and W07.

A protected one-to-one link binds a dedicated login to an existing Patient. Group-free linked accounts use a separate portal login and staff routes reject linked sessions. Local preview provisioning creates new credentials and refuses existing usernames or links. The portal derives patient ownership from the session.

The ordering Physician may explicitly release a current final or corrected publication. Each release identifies that specific immutable revision and records an audit event. A correction requires a new release and a withdrawal immediately removes portal visibility. Reports with error markers or withdrawal state are withheld. Portal results display typed values and units without private comments, review data or audit notes.

Portal appointments show scheduling and Encounter statuses separately. Medication statements and signed orders appear in separate lists. Completed visits use dates, clinician and appointment type. No SOAP, AVS or MAR content is projected.

Consolidated manual UAT follows both increments.

[Approved prompt](prompt.md) · [Verification](verification.md)

## Preview

Set `CAREFLOW_DB_PATH` to the existing `.venv/phase5-a-preview.sqlite3` clone from the project root. Run `python manage.py provision_portal_patient --username portal-a --patient-id <synthetic-id> --confirm-preview` in an interactive terminal. Repeat with a distinct synthetic patient and username for isolation testing. Enter passwords at the hidden prompt. Run `python manage.py runserver 127.0.0.1:8001` and visit `/portal/login/`. The ordering physician uses `/app/portal/releases/` to release an eligible publication explicitly.

The preview has no self-registration, password recovery, external delivery or production controls. A corrected publication supersedes portal access to the previous revision immediately. A visit record contains administrative context only. A separate release mechanism would be required for visit summaries.
