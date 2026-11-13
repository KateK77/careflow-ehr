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

No paid requests were sent. Each split scenario has passed offline and awaits separate approval for any native run.
