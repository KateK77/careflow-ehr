# Phase 2B feedback v1.0

2026-11-09: the user explicitly approved Phase 2B before Phase 2A manual UAT and required a stacked branch/PR. [Original prompt](prompt.md) is the approved source. This supersedes the earlier instruction to wait before beginning the next increment, only for the stated Phase 2B scope.

No Phase 2B user-reported manual acceptance observations have been received. Automated and developer browser results are recorded separately. Phase 2A UAT remains postponed. Previous Phase 1A/1B UX backlog remains deferred and was not reclassified as current defects or implemented as unrelated work.

## Manual UAT follow-up v1.0 — 2026-11-09

The previous pending-UAT status above is historical. The user has now reported 20 passing observations across medical history, problems, allergies, medications and encounter diagnoses. [Detailed observations, fixes and remaining retest gaps](uat-followup.md) distinguish these results from automated coverage. No comprehensive acceptance or merge approval is inferred.

## Targeted manual retest addendum v1.0

The user reported Retest 01 duplicate-primary rejection with a clear message and no internal constraint name; Retest 02 contradictory allergy rejection without __all__, with submitted status/confirmation retained; and Retest 03 linked Essential hypertension (Resolved) with the Problem List still Resolved. All three passed. The user did not intentionally change saved allergy records; no independent before/after database comparison across the manual session is claimed. Retest 04 date entry was user-reported acceptable, without additional evidenced malformed-date cases. The prior 20 reported workflow passes remain recorded.

See [the retest evidence and limits](uat-retest.md). Deferred, non-blocking enhancements: consolidate duplicated allergy summary/inline errors; resolve numeric audit IDs to authorized readable labels; monitor narrower responsive layouts. No enhancement is implemented now. Earlier pending statements are historical and are superseded only for explicitly reported checks.
