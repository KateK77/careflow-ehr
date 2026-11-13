# Native Computer Use UAT, batch 1

This record tracks [Issue #50](https://github.com/KateK77/careflow-ehr/issues/50). Branch `test/native-registration-uat` builds on the [Patient Portal smoke harness](https://github.com/KateK77/careflow-ehr/pull/53). The user reports both portal smoke tests passed previously.

| Scenario | Live status | Scope |
| --- | --- | --- |
| 1. Registration and scheduling | BLOCKED pending batch approval | Front Desk sign-in, synthetic registration, appointment review and confirmation, check-in, visible history, database linkage and audit checks |
| 2. Physician | BLOCKED pending harness extension and approval | Encounter, SOAP creation, signing, and signed-note write denial |
| 3. Nursing | BLOCKED pending harness extension and approval | Vitals, assessment, physician visibility |
| 4. Laboratory | BLOCKED pending harness extension and approval | Clinical order, Lab Staff processing and publication, physician review |
| 5. Pharmacy | BLOCKED pending harness extension and approval | Synthetic medication order, verification and simulated processing |
| 6. Patient Portal | BLOCKED pending harness extension and approval | Linked account, authorized appointments and records, results, cross-patient denial |
| 7. Security and RBAC | BLOCKED pending harness extension and approval | Direct routes, role and patient isolation, and audit events |

The first batch covers registration and check-in only. The later connected journey will need an explicit fixture handoff between scenarios with dedicated accounts, narrowly scoped routes and write payloads, and verification of the records each scenario inherits.

## Offline verification

Ran `tools/cua/.venv/Scripts/python.exe -m unittest discover -s tools/cua -v`. All seven tests passed. The Chromium rehearsal submitted real Django forms against a fresh temporary database and verified the patient, appointment, check-in and audit events. Scope and budget tests exercised denied writes, wrong credentials, missing usage, and request and cost thresholds. Mock API tests exercised native SDK dispatch and diagnostics. Zero paid requests were sent.

## Live evidence and approval

Use the command and limits in the [CUA operator guide](../../../tools/cua/README.md). The expected visible outcome is an Arrived appointment and its appointment history. Read-only verification in the temporary database checks the linked patient, appointment, check-in actor and event history. The evidence directory holds screenshots, requested and completed action types, checkpoints, actual token usage, an estimated token cost, and a sanitized failure stage for reproduction. No live screenshots, actions, token usage, or defects have been recorded for batch 1. Keep evidence local and exclude it from Git.
