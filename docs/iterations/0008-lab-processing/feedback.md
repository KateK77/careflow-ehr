# Feedback and scope disposition

2026-11-10: User approved sequential 3B-2 then 3B-3 stacked development with an automated/CI gate. Manual UAT for all 3B increments is intentionally deferred, not passed. Preserve the original database, backup and previous preview; use fresh named clones. No additional user observations or acceptance outcomes are claimed.

Automated development found a numeric report template incorrectly resolving the absent-value fallback, and Windows text rewriting introduced mojibake in modified presentation text. Both were corrected; a result form POST-and-follow regression now covers the template, and unchanged prior suites are rerun. Earlier failed runs are not represented as passing evidence. No existing tests were weakened.
