# UAT follow-up publication receipt v1.0

Recorded 2026-11-09 after implementation publication and actual GitHub Actions completion. This receipt is a documentation-only follow-up to the implementation commits below; its own final branch HEAD and checks are visible on PR #12.

| Owner | Implementation commit | Actual Push CI | Actual PR CI |
| --- | --- | --- | --- |
| Phase 2A / PR #8 | [6490841ab18e67b14c9409552a619f1279f1fcf0](https://github.com/KateK77/careflow-ehr/commit/6490841ab18e67b14c9409552a619f1279f1fcf0) | [Passed](https://github.com/KateK77/careflow-ehr/actions/runs/42741609207) | [Passed](https://github.com/KateK77/careflow-ehr/actions/runs/42741615233) |
| Phase 2B / PR #10 | [dfe412a0f2e2f54126e7c33f93d489b46b941010](https://github.com/KateK77/careflow-ehr/commit/dfe412a0f2e2f54126e7c33f93d489b46b941010) | [Passed](https://github.com/KateK77/careflow-ehr/actions/runs/42742435730) | [Passed](https://github.com/KateK77/careflow-ehr/actions/runs/42742441527) |
| Phase 3A / PR #12 | [7ad72bf12be648cd31ef8660152cfe5cee3defad](https://github.com/KateK77/careflow-ehr/commit/7ad72bf12be648cd31ef8660152cfe5cee3defad) | [Passed](https://github.com/KateK77/careflow-ehr/actions/runs/42743074619) | [Passed](https://github.com/KateK77/careflow-ehr/actions/runs/42743078988) |

Each CI run above completed successfully for the exact owner implementation HEAD. CI runs Django system checks, the default automated suite and migration consistency on an isolated runner; optional Chromium workflows were run locally, not in GitHub Actions.

Local verification: Phase 2A **102 tests / four Chromium workflows**; Phase 2B **133 tests / five Chromium workflows**; integrated Phase 3A **164 tests / seven Chromium workflows**. System and migration checks passed; no migration changes. Final documentation link/scope checks passed. The final documentation-only receipt does not change tested application code.

All local SQLite table counts matched the baseline; integrity and foreign-key checks passed. The whole-file SHA-256 remained `71514333f66b3107d62a7458ba4289f2936b78c1a87a17487f09b340c0d54c93`. This preserves existing patients, appointments, nursing/history records, encounters and signed SOAP content. All 23 baseline tracked historical requirement/source/translation, Phase 0 and prompt files matched their original bytes. The new approved request matches the attachment text verbatim. No reset, reseed, migration, C-drive-backup change or production configuration change occurred.

Issues #7, #9 and #11 remain open. PRs #8, #10 and #12 remain open and unmerged with their original stacked bases. Parent propagation used ordinary merge commits with both parents; no force push or history rewrite. Local Phase 3A and its remote tracking ref match after publication, and the index/worktree are clean.

User observations (12 / 20 / 9) are documented separately from automated checks. Follow-up UI retests and broader manual/security scenarios remain pending as listed in [the consolidated report](uat-followup.md). No comprehensive manual acceptance, security certification, release, deployment or next-phase approval is inferred.
