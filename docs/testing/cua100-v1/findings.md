# CUA-100 v1.0 — findings and limits

These are native model/harness observations against synthetic fixtures, not evidence of real clinical outcomes. Deterministic Chromium recipes passed for all 100 contracts. Native failures are not automatically application defects.

## Incomplete native read probe

CF-041 (patient denied pharmacy) stayed on the isolated launcher after a model click. No request reached the protected route; final-path and exact-status assertions failed. This is an incomplete native probe, not an observed authorization bypass. The model accurately reported that navigation had not happened.

## Confirmed native write failures

| Tasks | Evidence | Classification / next step |
| --- | --- | --- |
| CF-074, CF-077, CF-084, CF-087 | The driver rejected a multi-key combination. The sanitized log retains two unrecognized key tokens, not the original names. | Model/harness interaction limitation. Do not guess that it was Ctrl+A. Keep the existing keyboard policy; a future separately evaluated protocol can explain supported editing actions. |
| CF-075, CF-100 | Date-input validation rejected model text outside the scenario's explicit permitted fixture values. Raw typed values are intentionally absent from logs. | Model/harness value-contract mismatch. Do not infer the exact incorrect date. A future protocol should make the accepted literal format more prominent without silently changing dates. |
| CF-079 | Requested scroll anchor y=832 exceeds the 800-pixel viewport. | Out-of-bounds model action; correctly refused. |
| CF-080 | Requested click y=832 exceeds the 800-pixel viewport. | Out-of-bounds model action; correctly refused. |
| CF-086 | Requested click y=923 exceeds the 800-pixel viewport. | Out-of-bounds model action; correctly refused. |
| CF-099 | Requested click y=941 exceeds the 800-pixel viewport. | Out-of-bounds model action; correctly refused. |
| CF-082, CF-083 | Model reported it had not successfully selected Documented source or completed saving. Final URL, visible success and independent row assertions failed. | Incomplete UI task. The reports do not establish a server validation defect. |
| CF-085 | Execution failed at the driver's context check during a screenshot after the model clicked the left navigation. Last retained capture state was the medication statement form. | Context/navigation failure. The exact final URL was not retained; do not claim a complete root cause or successful write. |
| CF-089 | Intended Reject decision became Approved in both the visible applications list and independent database assertion. The model acknowledged the wrong outcome. | Confirmed wrong model decision in an isolated synthetic account. Human review is necessary for consequential AI writes. No existing or hosted account was affected. |

There were no paid retries of these failed tasks. Successful deterministic rehearsals do not replace these native failures.

## Infrastructure issue fixed before blocked cases could incur API usage

CF-002, CF-031 and CF-035 initially failed during browser initialization, with zero API requests. The old CF-002 raw result incorrectly used FAIL; the report annotates it as pre-API infrastructure BLOCKED while preserving the original JSON.

The added route trace showed GET / with no query and a mismatched origin. The fixture port file could exist before its content was written. A deterministic regression failed against the old reader by receiving an empty port, reproducing the origin-policy rejection mechanism. The publisher now replaces a completed temporary port file atomically; the reader also validates 1–65535 and waits under the startup timeout. Neither the origin allowlist nor redirect checks were relaxed.

All 44 offline CUA tests passed after this fix. Affected cases passed isolated offline browser preflight. Earlier logs did not retain the actual port, so the mechanism is reproduced rather than a claim that every older failure was individually proven.

## Scope and unresolved coverage

- One bounded native attempt per executed task; no statistical reliability or repeated-trial confidence interval.
- Seventy tasks are independent page/read/authorization probes; thirty are validation/write/clinical workflow tasks. The aggregate rate must be shown alongside these groups.
- Most authenticated scenarios start after the harness performs real login as fixture setup. They do not claim model-performed authentication.
- Read probes use a labelled local launcher for exact direct-route testing; they do not measure free-form navigation discovery.
- The catalog is broad but does not cover every billing, imaging, inpatient, emergency, accessibility, concurrency or production-security boundary.
- Native screenshots show selected moments. The published final image for a failed task may be the last successful capture before failure, not a completed outcome.
- The fixture's separate signed SOAP record is checked on completed verification paths. Early driver failures may not reach every preservation assertion; existing-database hashes are a separate global check.
- SQLite fixtures, synthetic users, strict route/POST restrictions and denied native safety approvals limit exposure. They do not justify unrestricted autonomous access to a real EHR.
- The hosted demonstration and existing local databases were not used for benchmark writes.
- No claim of clinical readiness, exhaustive security or human UAT acceptance is made.

## Recommendation

Use native CUA as supervised exploratory and regression assistance. It can complete selected real writes, including registration, check-in, pharmacy transitions and laboratory processing, but this run does not support unattended consequential administration. Preserve the failed first attempts, review exact task/action evidence, and design a separately versioned improvement round before paying for retries.
