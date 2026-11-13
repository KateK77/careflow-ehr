# Front Desk offline stability verification

The baseline was `64e5c46ea3ca5fbce67b5b5f30bb45dd925757b1`. The baseline series passed 19 of 20 runs (95%). Run 12 completed registration, then the screenshot after opening Schedule waited five seconds for the earlier patient-detail redirect. The write response could arrive after the pre-capture redirect check, leaving a destination queued even after the browser reached the patient page. The next capture could then wait for that stale destination.

The deterministic regression reproduces a write redirect arriving during screenshot capture. It failed before the fix and passed afterward. The driver now waits for the late redirect and discards the potentially stale image before recapturing within the same three-attempt limit. No action or write is replayed. All 17 offline CUA tests passed.

Each run launched Chromium and a fresh temporary SQLite database. The existing ComputerToolset regression used coordinate clicks and scripted field entry, exercised a blocked invalid form, then verified sign-in, registration, appointment review and confirmation, check-in, visible Arrived status and audit history. The read-only database verifier independently checked the synthetic patient, linked Arrived appointment and ordered patient creation, appointment creation and arrival events attributed to Front Desk.

| Run | Baseline status | Baseline failure stage | Fixed status | Fixed failure stage | Fixed screenshots |
| --- | --- | --- | --- | --- | --- |
| 01 | PASS | — | PASS | — | 13 |
| 02 | PASS | — | PASS | — | 13 |
| 03 | PASS | — | PASS | — | 13 |
| 04 | PASS | — | PASS | — | 13 |
| 05 | PASS | — | PASS | — | 13 |
| 06 | PASS | — | PASS | — | 13 |
| 07 | PASS | — | PASS | — | 13 |
| 08 | PASS | — | PASS | — | 13 |
| 09 | PASS | — | PASS | — | 13 |
| 10 | PASS | — | PASS | — | 13 |
| 11 | PASS | — | PASS | — | 13 |
| 12 | FAIL | Schedule capture → write redirect wait | PASS | — | 13 |
| 13 | PASS | — | PASS | — | 13 |
| 14 | PASS | — | PASS | — | 13 |
| 15 | PASS | — | PASS | — | 13 |
| 16 | PASS | — | PASS | — | 13 |
| 17 | PASS | — | PASS | — | 13 |
| 18 | PASS | — | PASS | — | 13 |
| 19 | PASS | — | PASS | — | 13 |
| 20 | PASS | — | PASS | — | 13 |

The fixed series passed **20 of 20 runs (100%)** and saved **260 screenshots**, with per-run logs and JSON results in the ignored local QA evidence directory. No existing SQLite database was opened by the rehearsals. No paid requests were sent. These results support one bounded model-driven attempt with separate approval. Paid acceptance remains paused and model-driven field entry remains unverified.
