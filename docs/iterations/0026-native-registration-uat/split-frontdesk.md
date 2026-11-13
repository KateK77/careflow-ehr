# Front Desk independent acceptance scenarios

## Run 06 evidence

The run on `8170f4e` completed sign-in only and stopped at `/app/patients/new/`. It received seven API responses, completed 23 actions and estimated $0.112405 in token cost. Screens 06 and 07 show the expected MRN, name, date of birth and Unknown sex. The required synthetic-data confirmation checkbox is unchecked. The optional duplicate confirmation is also unchecked. No registration POST checkpoint was recorded, and the saved evidence does not show a Save click or server validation response. The offline regression verifies that an unchecked required confirmation is reported as `synthetic_only/valueMissing`. Diagnostics record allowlisted field names and browser validity flags only.

## Offline verification

All 20 CUA tests passed, including the combined regression and three separate Chromium rehearsals. Each split rehearsal was also rerun with local screenshot and JSON evidence enabled. Coordinate clicks went through ComputerToolset. Offline field entry used scripted fixture values. Live runs leave navigation, field focus, entry, confirmation and submission to native model actions.

| Scenario | Pre-existing fixture beyond staff accounts | Verified UI and database result | Screenshots | Request / action / session limits | Estimated-cost stop |
| --- | --- | --- | --- | --- | --- |
| registration-only | None | Saved demographic summary, exactly one synthetic patient, no appointment, creation audit | 8 | 10 / 40 / 120 seconds | $0.25 |
| appointment-only | One synthetic patient | Scheduled appointment linked to patient and physician, no check-in, creation audit | 8 | 10 / 38 / 120 seconds | $0.25 |
| checkin-only | One synthetic patient and a same-day Scheduled appointment | Visible Arrived and appointment history, linked appointment, check-in actor and arrival audit | 7 | 7 / 24 / 90 seconds | $0.15 |

Every run uses a new temporary database and actual Staff Portal authentication. The fixture does not pre-create audit events for the action under test. Writes are restricted to the scenario's expected requests. The native runner keeps the existing 768 output-token cap per request, 15-second HTTP timeout, zero retries and explicit approval requirement. The estimated-cost threshold blocks the next request and can be exceeded by the final in-flight request. Local evidence contains screenshots, checkpoint records and actual usage when available. Existing SQLite databases were outside the rehearsals.

## Registration-only accessibility follow-up

The first paid registration-only run on `f71853c` completed sign-in and stopped at the registration form after five responses (estimated $0.063473). Its last screenshot showed the blank Sex dropdown focused with Chromium's “Please select an item in the list” message. The synthetic-data checkbox was unchecked. Sanitized diagnostics confirmed `valueMissing` for both fields. The recording does not identify which individual keypresses caused the selection to remain blank. No registration write checkpoint completed.

The registration form now renders visible Recorded sex radio options, including Unknown, in a labeled group with guidance. The required synthetic-data checkbox is grouped separately above Save, with a larger label target. Both start unset. The edit form retains its existing layout. Existing Django validation and the CUA payload policy remain in force.

All 20 offline CUA tests passed. Chromium verified the empty controls, accessible group names and help association, keyboard radio selection and checkbox activation, rejection of the invalid form, and successful registration. The read-only temporary database check verified the patient and creation audit. All 32 Django patient tests passed, including missing Sex and missing synthetic confirmation. No paid call was sent during this follow-up. One bounded registration-only run is justified with separate approval. Live model interaction with the revised controls remains unverified at that revision.

## Required confirmation follow-up

The next native registration-only run stopped after seven HTTP responses and 28 completed actions, with an estimated token cost of $0.110875. The final capture showed Unknown selected, the optional duplicate-review checkbox checked and the required synthetic-data checkbox unchecked. The required checkbox was fully in view and unobstructed in the saved frame. The action log recorded types without coordinates, so it does not establish whether the required control was clicked. Sign-in was the only completed checkpoint. Browser validity reported only `synthetic_only: valueMissing`.

The form now shows duplicate review only when matching records are detected. Chromium verified that the required confirmation starts unchecked and enabled, that clicking the box or its associated label toggles it, and that saving while unchecked leaves registration incomplete. Explicit Space activation allowed the subsequent save. A read-only check of the isolated database verified the saved patient and creation audit. The Django duplicate regression verified that a real match still displays its review checkbox and requires separate confirmation.

All 20 offline CUA tests and all 32 Django patient tests passed. No paid requests were sent during verification. Paid registration retries remain paused pending separate approval.

## Third registration-only attempt

The run on `1c6a957` stopped on the 21st requested action with `driver_failed/keypress` and a `ValueError`. All six requests received responses. Only sign-in completed. Estimated token cost was $0.08513. The final saved screenshot showed the date control focused, with the fixture date present and the radio options unset. Neither the screenshot nor the action log records the rejected key or combination. The driver uppercases recognized aliases and rejects unsupported keys and combinations through the same baseline error path. The historical evidence cannot distinguish an alias mismatch from an intentional shortcut restriction.

The driver now records a fixed rejection category for unrecognized single keys, disallowed combinations and empty key lists. It never records the input key text. The baseline failed the three diagnostic assertions and the revised driver passed them, with no rejected input reaching the browser. No key aliases or allowed combinations changed. The exact historical keypress remains unavailable and was not recreated. The full offline suite passed 21 tests, including the Chromium registration rehearsal with radio selection, explicit confirmation, and an independent synthetic patient and audit check. Paid registration remains paused while the exact driver issue is unconfirmed.

## First native appointment-only attempt

The run ended at `/app/appointments/new/` after seven responses and 18 completed actions, with estimated token cost $0.10724. The final captures show blank Patient, Physician and Appointment start controls. Duration and appointment type were populated with defaults. No review page or server validation error is visible. Only sign-in was recorded. The action evidence lacks click coordinates and POST traces, so it does not establish whether Review was clicked. The original QA database was removed at teardown, and the saved evidence contains no database snapshot or counts. A historical independent database check is unavailable.

The driver now labels incomplete appointment and check-in runs with their own checkpoint stages. Appointment diagnostics record allowlisted field names, validity flags, a visible server error indicator and independent read-only appointment and creation-audit counts from the temporary fixture. The prompt directs the model to the two selectors below patient search and asks it to confirm the displayed selections and start before review. The offline Chromium regression clicked Review with the three fields empty, verified their missing-value flags and zero database counts, then completed review and confirmation and verified the scheduled appointment and creation audit. All 21 offline CUA tests and the dedicated appointment rehearsal passed. No paid requests were sent.
