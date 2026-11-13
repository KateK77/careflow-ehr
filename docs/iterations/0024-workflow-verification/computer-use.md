# Computer Use Agent acceptance log

Status: blocked. The active Codex session exposes no Computer Use Agent capability. Local Playwright Chromium ran separately as automated evidence. No agent-operated sessions, screenshots, observations, or defect findings were recorded.

| Pending scenario | Steps | Expected evidence |
| --- | --- | --- |
| Landing, keyboard and responsive UI | Open the root page, inspect styling, resize to mobile, tab to both sign-in controls and follow each link | Both login forms open. Controls are visible and usable. Capture desktop and mobile screenshots. |
| Distinct role sessions | Use separately provisioned synthetic accounts for Administrator, FrontDesk, Physician, Nurse, Lab Staff, Pharmacist, RadiologyStaff, BillingStaff, HospitalOperations and two patients | Record each successful sign-in and destination. Verify denied direct routes in the relevant sessions. |
| Cross-module synthetic journey | Book and check in, record nursing observations, start the encounter and sign SOAP. Process a lab order and release the current result. Verify pharmacy handoff and the linked patient's result visibility. | Record UI steps, expected and actual states, actor and timestamp evidence, and screenshots without credentials. |
| Patient and staff isolation | Try another patient's result and a protected staff route as a patient. Try the patient portal as staff. | Record the observed denials and confirm no foreign result is rendered. |

Use a newly named isolated QA database with synthetic fixtures. Record the exact commit, browser and viewport, steps, expected and actual results, severity, and screenshot paths. Keep Issue #50 open until agent execution and review evidence are available.

## Native harness follow-up

The user reported a successful live Staff Portal entry smoke. The Patient Portal entry smoke passed offline against a freshly migrated temporary QA database. Both offline portal rehearsals and all four CUA tests passed. The mocked Patient Portal Responses exchange covered screenshot feedback, browser continuity and usage totals. A mocked quota error stopped after one attempted request. No live Patient Portal requests were sent. Live patient smoke approval and the authenticated Issue #50 journey remain pending. [Commands and scenario plan](../../../tools/cua/README.md)
