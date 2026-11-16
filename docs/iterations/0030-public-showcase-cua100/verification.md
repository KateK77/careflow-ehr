# Verification — CUA-100 v1.0

## Offline qualification

All 100 task definitions completed their deterministic Chromium rehearsal with independent database assertions after correcting test-only fixture/expectation errors. This is not native AI acceptance.

The initial complete run passed 87/100. Corrections covered append-only denied-access audit recognition; required history provenance and allergy severity; the confirmation-only pharmacy claim form; the actual laboratory assignee field; and explicit laboratory acknowledgement confirmation. Two intermittent browser-start failures had no API traffic and passed isolated preflight reruns. Their exact underlying browser exception was not recovered; safe exception-chain diagnostics now preserve subsequent failures without raw sensitive content.

Original rehearsal results are retained privately; corrected cases use separate evidence directories. No failed native attempt is silently replaced by an offline pass.

The integrated Django regression suite passed 536 tests. System and migration checks passed against isolated settings. Final offline harness and native results will be appended after execution.

## Native evaluation protocol

Every native task uses the official Responses API computer tool through ComputerToolset, model-driven screen observations and actions. Authentication for role-specific cases is prepared through real login as fixture setup, and is not claimed as model-performed login. Each task uses a new synthetic database.

Three initial native tasks passed, followed by 17 further passes. One task was blocked before any API call during browser initialization. Preserve that raw result and classify it as infrastructure-blocked rather than an evaluated model failure. A separately recorded preflight-qualified attempt may complete the previously unexecuted task.

There are no automatic paid retries. Per-task request/action/runtime limits and an estimated USD 0.80 stop apply; the initial batch estimate stops below USD 20 with a reserve. Token estimates are not billing receipts or guaranteed hard monetary caps.

## Readiness race follow-up

The new redacted route trace for CF-035 showed GET /, no query, but a mismatched origin before the first API request. The fixture publisher created server-port before writing its contents; the reader treated file existence as readiness. A deterministic regression with an initially empty port file failed against the old code: it yielded http://127.0.0.1: instead of the expected explicit loopback port. This reproduces the observed origin-policy rejection mechanism; earlier raw failures did not retain the port value.

The test fixture now publishes the port atomically, and the reader waits for a validated port in 1–65535 under the existing startup deadline. Network restrictions are unchanged. Both the empty-file and invalid-port regressions pass. All 44 offline CUA tests pass; CF-002, CF-031 and CF-035 pass post-fix isolated Chromium preflight. Their original zero-request failures remain in the ledger. Subsequent execution is their first paid native attempt, not a paid failure retry.

Source manifests now retain module SHA-256 hashes and the Git baseline loaded at process startup, rather than reading a potentially changed HEAD for each task. No application behavior or existing database was modified.

## Final native outcome and preservation

100 unique tasks received native API execution: **85 PASS / 15 FAIL**, **85%**. Read/authorization **69/70 (98.57%)**; validation/write/clinical **16/30 (53.33%)**. The original first-launch ledger was 82 PASS / 15 FAIL / 3 pre-API BLOCKED; the blocked cases later received their first paid attempts after the offline fix. No paid failed case was retried.

336 requests received 336 responses, with **1,279,839 input tokens** and **12,025 output tokens**. Conservative estimated token cost: **USD 3.379979**. See [results](../../testing/cua100-v1/results.md), [findings](../../testing/cua100-v1/findings.md), and [machine-readable outcomes](../../testing/cua100-v1/results.json).

All **62 existing SQLite files** matched the pre-run SHA-256 manifest. No existing database was migrated, seeded or reset; temporary synthetic fixture migrations are distinct. The hosted database was not used by this evaluation. Historical source documents and the previous README snapshot are preserved. No application business logic changed.

Local main remains 00c624553cc265e6275a9d2750ab0041a7e6d97f; remote main baseline is a9e0913b626b88908ad2ca3041d2ec9497ba7d15. Neither was synchronized or modified as part of this task. Main remains the repository default.

Documentation verification passed: executable catalog equals versioned JSON/Markdown; 100 unique native contracts each have matching request/response counts; 203 published evidence artifacts match SHA-256; current-document relative links resolve; Git whitespace check passed. Reviewed new public text artifacts contained no matches for the tested OpenAI/GitHub/private-key signatures. This scoped scan is not comprehensive secret certification.
