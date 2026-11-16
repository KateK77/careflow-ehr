# Native CUA evidence audit

Audit date: November 16, 2026 (America/Chicago). This is a read-only assessment of the existing CUA-100 v1.0 artifacts, not a new test run. Original outcomes, costs, difficulties, screenshots and action traces are unchanged.

## Conclusion and scope

The recorded native path uses the official OpenAI Responses computer tool, and the 100 saved native records are internally consistent with that execution. They are distinct from deterministic Playwright rehearsals. However, the public evidence is not a complete provider-correlated request/response audit trail and does not establish that every setup, login or navigation action was autonomously selected by the model.

## Model and execution path

- Requested model: gpt-5.4. The exact served model/snapshot was not persisted for each API response.
- Configured endpoint: https://api.openai.com/v1/responses.
- Tool: computer through the official ComputerToolset helper, OpenAI Python SDK 3.31.0.
- The SDK calls client.responses.create; Playwright implements the browser driver.
- Native and offline branches are separate. Native execution does not invoke the scripted rehearsal function.

[Evaluated runner](https://github.com/KateK77/careflow-ehr/blob/563b5b879e85ce664aecc3d9a3d78042191e52f4/tools/cua/benchmark.py#L222) · [Usage diagnostics](https://github.com/KateK77/careflow-ehr/blob/563b5b879e85ce664aecc3d9a3d78042191e52f4/tools/cua/diagnostics.py#L87).

The framework seeds accounts and business prerequisites, performs applicable authentication through the real UI, opens the starting page, mediates password/date inputs and runs independent assertions. Seventy tasks primarily probe entry/read/authorization behavior; thirty address validation/write/clinical workflows. Many read probes start from a labelled direct-route launcher. This is not 100 independently completed, zero-script clinical journeys.

## Public evidence verified

| Artifact / check | Finding |
| --- | --- |
| Unique native result files | 100, all with mode native |
| Outcomes | 85 PASS / 15 FAIL |
| Request / response counters | 336 / 336 |
| Responses with usage, as recorded | 336; all task usage summaries marked complete |
| Nonempty action/completion traces | 100 tasks |
| Last successfully captured public screenshots | 100 |
| Integrity manifest | 203 evidence artifacts, verified against published Git blobs |
| Records containing a tested Commit | 97 |
| Records containing source SHA-256 values | 40 |

Completed-action totals: 236 screenshots, 194 clicks, 76 waits, 40 typing actions, 17 keypresses and 23 scrolls. These counts come from SDK diagnostic callbacks, not preserved raw tool-call messages. Additional framework screenshots are not model actions.

Full intermediate captures remain in ignored local evidence (413 in native-first and 12 in the preflight-qualified runs at audit time), not all on GitHub. Captures do not provide a one-to-one mapping to API responses. Failure images can precede the failure.

## Missing proof and provenance exceptions

Public records do not retain per-response response_id, x-request-id, original computer_call/call_id messages, complete API request/response bodies, or per-response usage records. The result JSON's http field describes CareFlow page navigation, not OpenAI HTTP traffic.

The per-task counters and action logs are client-generated execution evidence. Hashes establish file consistency, not independent proof of an OpenAI response's origin. Exact provider billing and the served model cannot be independently verified from these artifacts.

CF-032, CF-033 and CF-034 record a benchmark.py source digest that does not match the file in their named commit 6187ce8, even allowing LF/CRLF normalization. This is consistent with an intermediate uncommitted diagnostic revision, but the named commit alone cannot reproduce those exact runner bytes. Preserve this discrepancy; do not rewrite their recorded commit or digest. The earliest three pilot results predate per-task Commit recording and use a separately disclosed work-log annotation.

## Cost reconciliation

Input tokens: 1,279,839. Output tokens: 12,025.

At the runner's fixed estimate of USD 2.50/million input and USD 15.00/million output:

- Input estimate: USD 3.1995975.
- Output estimate: USD 0.180375.
- Aggregate before per-task rounding: USD 3.3799725.
- Sum of six-decimal per-task estimates: USD 3.379979, displayed as USD 3.38.

This is not a verified invoice. Cached-token details, billing adjustments and provider charges were not reconciled. Three initial startup blocks had zero API requests; each later received its first paid attempt after an offline readiness fix. No failed paid task was retried.

## Interpretation

Read/authorization success was 69/70 (98.57%); write/clinical success was 16/30 (53.33%). One failed rejection task approved the synthetic applicant instead. Other failures include unsupported actions, out-of-bounds coordinates and incomplete forms. Do not translate the 85% aggregate into clinical readiness, security certification or suitability for unsupervised consequential writes.

[Original tasks](../../testing/cua100-v1/tasks.md) · [Results](../../testing/cua100-v1/results.md) · [Failures](../../testing/cua100-v1/findings.md) · [Manifest](../../testing/cua100-v1/evidence-sha256.json)
