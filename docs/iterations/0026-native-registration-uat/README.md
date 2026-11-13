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

Use the command and limits in the [CUA operator guide](../../../tools/cua/README.md). The expected visible outcome is an Arrived appointment and its appointment history. Read-only verification in the temporary database checks the linked patient, appointment, check-in actor and event history. The evidence directory holds screenshots, requested and completed action types, checkpoints, actual token usage, an estimated token cost, and a sanitized failure stage for reproduction. Keep evidence local and exclude it from Git.

## First live attempt and offline follow-up

The first live attempt failed during the screenshot after the portal click, before any write checkpoint. Two API requests returned HTTP 200. The recorded usage was 5,599 input tokens and 46 output tokens, estimated at $0.014687. The reported error was `Route.fetch: Request context disposed`. The failing request URL and the event that disposed the context were unavailable.

Screenshots now wait for a bounded document load and in-flight route handlers. Teardown keeps interception active, rejects new traffic and drains pending fetches before closing the context. Active fetch errors still fail the driver. Offline tests exercised a delayed asset, teardown with a pending fetch, and an injected disposal failure during capture. All ten CUA tests passed. The second paid attempt on `cea59e0` returned the same action counts and token usage and failed at the same SDK screenshot stage. Its saved diagnostic recorded only the exception class `Error`.

## Navigation regression follow-up

An offline replay through `ComputerToolset.execute` reproduced the registration failure in eight of eight runs on `cea59e0`. Both read-only portal variants passed eight of eight. The registration capture raised `Page.screenshot: Execution context was destroyed, most likely because of a navigation`, before PNG encoding, evidence writing or SDK output validation. The click returned before the landing document was replaced. The existing load-state check could still see the loaded landing page. Registration also supplies a password mask locator, a difference from the read-only portal captures.

The driver now waits for the known destination document after a coordinate click on a landing-page portal link. The allowlist and password mask remain in force. The synthetic registration test now goes through this click and capture before entering credentials, verifies the login route and visible fields, and takes another capture after navigation. It failed before the change and passed afterward. All 24 comparison replays and all 11 CUA tests passed after the change.

The retained paid-run evidence lacks the exception detail required to confirm that the second paid attempt raised the same exception as the offline replay. Future evidence records the screenshot substage, exception classes and recognized browser signatures without raw exception text. No live API request was sent during this investigation.

## Post-sign-in capture follow-up

The third paid attempt reached the sign-in checkpoint. Its diagnostic identified `capture_document_replaced` during Playwright capture after the form submission. The earlier portal-link wait did not cover form redirects. The driver now waits for the destination of an approved write redirect and retries only the recognized document-replacement error, with three total capture attempts. No browser action or write is replayed. Fourteen offline tests passed, including the synthetic registration workflow with capture immediately after submitting sign-in. No paid retry was performed.

## Front Desk retry readiness

The complete registration-branch CUA suite passed 14 tests. The offline Chromium rehearsal followed the visible Patients and Schedule links and used ComputerToolset coordinate clicks for navigation and form submission, capturing after each click. Field entry was scripted. Twelve screenshots and a JSON verification record were saved locally. All five checkpoints and all three database checks passed, including Arrived and the ordered audit history. Browser capture now waits for the destination of scoped links as well as approved form redirects. One paid retry is ready for separate approval under the existing limits. Live model field entry, especially date and time input, remains unverified.

The subsequent independent batches will start with a checked-in synthetic appointment for the Physician encounter and signed SOAP workflow, a scoped nursing visit for vitals and flowsheets, a synthetic lab order through released results, a signed synthetic medication order for simulated pharmacy processing, and a linked Patient Portal account for authorized records and results. Each batch needs its own fixtures, write policy where applicable, offline regression and evidence before live approval.

## Fourth paid attempt and form-entry regression

The fourth attempt on `3ae31ff` received eight API responses and completed 37 tool actions, with estimated token cost of $0.14366. The saved screenshots show the landing page, staff sign-in, the authenticated Front Desk dashboard, and the Register synthetic patient form. The final capture shows the date in Email, a blank Date of birth, a placeholder Sex selection, and both confirmation checkboxes selected. The screenshots do not retain click coordinates or a browser navigation trace. No server validation response or successful registration POST was recorded. The invalid form blocks submission in the offline reproduction. Only sign-in completed. There is no evidence of appointment creation or check-in.

The final observed page corresponds to `/app/patients/new/` on the ephemeral QA origin. The stage labeled `login_verification` first waited five seconds for `/app/appointments/1/` and timed out there. The subsequent Arrived, Appointment history, and appointment_arrive checks were never reached. This stage has been split into registration checkpoint, Arrived UI and database verification. An incomplete sequence now reports the allowlisted path and whether the registration form is invalid.

Exact fixture dates are entered only into their focused date or time controls. The prompt specifies keyboard selection for Unknown and leaves optional fields empty. The Chromium regression reproduced the invalid Email and missing fields, verified that only sign-in was recorded, then corrected the form and completed patient creation, appointment creation and check-in. The UI showed Arrived and the audit event. The read-only QA database verifier confirmed all three checks. All 14 offline CUA tests passed. No paid retry was run.
