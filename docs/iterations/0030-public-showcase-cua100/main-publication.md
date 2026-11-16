# Default-branch documentation publication

The owner approved a separate documentation-only PR because PR #63 targets the unmerged v3 feature branch. This publication branch, docs/portfolio-main, starts from remote main a9e0913b626b88908ad2ca3041d2ec9497ba7d15. It does not inherit or merge the application's open feature stack.

Scope: README and docs only. The selected showcase and CUA documents/evidence are copied from the reviewed showcase branch. The methodology's executable-source link uses an immutable GitHub revision because the harness is not added to main by this PR. Raw native results, difficulty, token counters/costs, action traces, screenshots and manifests retain their original published Git bytes.

The hosted v3 application remains a separate deployed snapshot. This publication does not deploy, migrate, provision accounts, publish passwords, make paid calls or change clinical software. The public demo sandbox remains a proposal.

Verification is recorded after static checks, evidence byte comparison, GitHub desktop/mobile rendering and main-baseline CI. PR #63 remains open as historical stacked work; only this documentation publication PR is conditionally approved for merge.

## Publication evidence

[PR #64](https://github.com/KateK77/careflow-ehr/pull/64) is the owner-approved default-branch publication. Actual GitHub Chromium rendering passed for this branch at 1280x1000 and 390x844: both HTTP 200, expected sections present, hero decoded, and no horizontal overflow (README widths 838 and 324 pixels). All active relative links resolve. All 203 evidence SHA-256 values and original task/result files match the source branch.

Only README.md and docs/ differ from the application baseline. CI and final merge state are recorded in [PR #64 checks](https://github.com/KateK77/careflow-ehr/pull/64/checks); the original stacked [PR #63](https://github.com/KateK77/careflow-ehr/pull/63) remains separate. No paid tests were run, and no public shared credentials were created or verified. The owner explicitly deferred that next-stage work.
