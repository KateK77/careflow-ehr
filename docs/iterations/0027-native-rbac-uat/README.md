# Native Computer Use Security and RBAC acceptance

Tracks [Issue #50](https://github.com/KateK77/careflow-ehr/issues/50). This separate branch starts from the existing native harness, including its portal navigation synchronization. Registration Batch 1 remains paused.

## Offline results

| Session | Observed outcome |
| --- | --- |
| Anonymous | Staff directory and Patient dashboard each returned 302 to their respective visible sign-in pages. |
| Patient without result ownership | Own dashboard returned 200. Staff directory returned 403. The other patient's released result URL returned 404. |
| Result owner | The same released result URL returned 200 and displayed the synthetic result component. |
| Physician | Staff directory returned 200. The direct demographic edit route returned 403. |

All eight probes passed in offline Chromium through local `ComputerToolset.execute` dispatch. On denied routes the verifier checked the response body and visible page for synthetic protected markers. The suite also exercises rejection of unexpected query strings, write attempts and denied response leakage.

Each session uses a fresh temporary SQLite database with synthetic fixtures and a private Chromium context. For authenticated probes, the QA server creates the Django session and the harness adds its cookie to Chromium privately. This tests the authenticated permission boundary and leaves interactive sign-in outside this batch. The QA launcher exposes only the selected read-only links. The destination is synchronized before capture. The policy permits the exact anonymous redirects and rejects browser writes. Existing project databases are outside the harness.

## Proposed first paid batch

The combined live attempt verified the staff redirect (HTTP 302) and reached the four-response step limit before the patient checkpoint. All seven requested actions completed, including waits. Reported estimated cost was $0.041282. The combined entry point has been replaced by two independent runs, each with its own fresh fixture and evidence directory. Authenticated probes await separate live approval. The user subsequently reported that both split anonymous live runs passed, along with both portal entry smoke runs.

```powershell
tools/cua/.venv/Scripts/python.exe tools/cua/smoke.py --scenario rbac-anonymous-staff --mode native --model gpt-5.4 --approve-api-call --evidence-dir .venv/uat-followup/cua-rbac-anonymous-staff-native-01
tools/cua/.venv/Scripts/python.exe tools/cua/smoke.py --scenario rbac-anonymous-patient --mode native --model gpt-5.4 --approve-api-call --evidence-dir .venv/uat-followup/cua-rbac-anonymous-patient-native-01
```

Per-run limits are four Responses API requests, 12 requested actions, 512 output tokens per request, a 90-second cooperative session deadline and a 15-second HTTP timeout with retries disabled. Measured estimated token cost of $0.10 or missing usage blocks the next call. The estimate can exceed that threshold on the final in-flight request and excludes separate fees. At 20,000 cumulative input tokens and 2,048 output tokens the illustrative token cost is about $0.081. [GPT-5.4 rates](https://developers.openai.com/api/docs/models/gpt-5.4)

The local evidence directory contains screenshots, completed action types, status codes, visible outcome checks and token usage. Keep it outside Git. The first live anonymous attempt was blocked after two responses because the model requested `wait`, which the RBAC allowlist refused. The driver now permits a fixed 250 ms wait with policy and cancellation checks before and after it. The wait consumes one action from the existing budget. All four RBAC Chromium rehearsals passed after the change, covering eight probes. All sixteen offline CUA tests passed on this branch. No paid retry was performed during that offline fix.

## Authenticated single-probe batch

Each run exposes exactly one QA link. The fixture obtains its session by submitting valid synthetic credentials and a CSRF token to the existing Django login view before launching Chromium. It transfers only the resulting cookie privately. This verifies authenticated navigation and authorization. Interactive sign-in is outside the browser probe. Native browser form submissions remain blocked.

| Scenario | Expected status | Final path |
| --- | --- | --- |
| `rbac-patient-dashboard` | 200 | `/portal/` with the linked patient identity |
| `rbac-patient-other-result` | 404 | `/portal/results/1/` with a generic denial |
| `rbac-owner-result` | 200 | `/portal/results/1/` with owner identity and synthetic result |
| `rbac-physician-directory` | 200 | `/app/patients/` |
| `rbac-physician-demographic-denial` | 403 | `/app/patients/1/edit/` with a permission message |

All 24 offline CUA tests passed, including five authenticated and two anonymous Chromium rehearsals. The same synthetic released result is created independently in both result fixtures. Denied responses and visible pages are checked for protected fixture markers. The same per-run API, action, time and estimated-cost limits apply. Registration Batch 1 remains paused.
