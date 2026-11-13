# CareFlow EHR — current project status

Snapshot: 2026-11-13 (America/Chicago). Local synthetic-data prototype only.

## Verified integration and open work

- Phases 0–8 are integrated through [PR #47](https://github.com/KateK77/careflow-ehr/pull/47), merged at [a9e0913b626b88908ad2ca3041d2ec9497ba7d15](https://github.com/KateK77/careflow-ehr/commit/a9e0913b626b88908ad2ca3041d2ec9497ba7d15).
- GitHub main was read-only verified at that merge commit during this upgrade. No release-tag claim is made by this check.
- Open PRs [#49](https://github.com/KateK77/careflow-ehr/pull/49), [#51](https://github.com/KateK77/careflow-ehr/pull/51), [#52](https://github.com/KateK77/careflow-ehr/pull/52), [#53](https://github.com/KateK77/careflow-ehr/pull/53), [#54](https://github.com/KateK77/careflow-ehr/pull/54) and [#55](https://github.com/KateK77/careflow-ehr/pull/55) retain the portal/verification/CUA/appointment stack.
- [Issue #56](https://github.com/KateK77/careflow-ehr/issues/56) upgrades presentation on `ui/unified-workspace-upgrade`, based on PR #55 at `214a309f52af642b4c59be85f3bc7ec646766815`.
- Local main remains at its pre-task `00c624553cc265e6275a9d2750ab0041a7e6d97f`. It was not switched, advanced or modified as part of this feature task.

## Delivered capabilities

Existing modules cover patients, scheduling/check-in, physician encounters and signed SOAP, longitudinal clinical history, nursing, laboratory orders and results, medication/pharmacy/MAR, patient portal communication, synthetic billing/claims/payments, imaging, inpatient ADT and ED tracking. Keep the original phase names and per-iteration acceptance history.

The current upgrade improves role-aware workspace links, patient density and demographics, appointment review visibility, readable audit presentation, allergy error feedback and portal navigation. It does not add clinical state transitions or migrations.

## Evidence

Historical user-reported core manual UAT for Phases 5–8 and earlier phases remains in the original iteration records. It does not certify exhaustive negative cases, concurrency, security or accessibility.

The release candidate previously reported 345 Django tests, 23 Chromium workflows and two audit probes. Later workflow coverage reported 124 additional cases and 470 passing Django tests. These are historical counts, not automatically the current branch's results.

Actual upgrade commands, results and evidence are recorded in [iteration 0027 verification](iterations/0027-workspace-upgrade/verification.md). New manual UAT is pending. No paid native CUA request was sent during this upgrade; registration paid retries remain paused.

## Limitations and deferred decisions

- Development settings, SQLite and synthetic data only; no clinical, regulatory or production certification.
- Application audit restrictions do not protect against privileged direct SQL or bulk ORM modifications.
- Comprehensive accessibility, concurrent production load, every role-revocation/session combination and every negative workflow boundary remain unverified.
- Optional appointment types, working hours, leave, check-in timing rules and additional provenance-label resolution remain future proposals.
- Authorized early imaging examination is an existing local simulation behavior, not a production scheduling policy.
- Paid API testing, PR merges, deployment, new clinical phases and release tagging need separate approval.

## Historical source

The [pre-update status snapshot](iterations/0027-workspace-upgrade/baseline-current-documents/project-status.md) preserves the original bytes. The [feedback register](iterations/0027-workspace-upgrade/feedback.md) distinguishes implemented improvements, existing fixes and deferred work.
