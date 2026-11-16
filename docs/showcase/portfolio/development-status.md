# Source, deployment and integration status

Verified November 16, 2026 (America/Chicago). Detailed history is kept here so the portfolio introduction can focus on the product.

## Current refs

- Application baseline on main before the documentation publication: a9e0913b626b88908ad2ca3041d2ec9497ba7d15, the v1.0 integration.
- Hosted v3 source recorded by deployment: a9ae1885ee9a98fad6687697db1fcb2581540c75. This task does not redeploy or independently certify the entire hosted filesystem against that historical snapshot.
- Original portfolio branch: docs/public-showcase-cua100, PR #63. [PR #64](https://github.com/KateK77/careflow-ehr/pull/64), docs/portfolio-main, publishes documentation from the main baseline without importing the functional stack.
- PR #63 remains a draft/open PR targeting feature/v3-account-registration, not main. GitHub reports mergeable against its present base; no discussion/review entries were returned by the PR timeline check.
- The local main pointer is older than remote main and has not been changed as part of this documentation work.

## Open dependency stack

| PR | Branch | Current base |
| --- | --- | --- |
| #49 | ui/unified-portal-landing | main |
| #51 | test/issue-50-workflow-coverage | ui/unified-portal-landing |
| #52 | test/native-computer-use | test/issue-50-workflow-coverage |
| #53 | test/native-patient-portal-smoke | test/native-computer-use |
| #54 | test/native-registration-uat | test/native-patient-portal-smoke |
| #55 | fix/appointment-form-guidance | test/native-registration-uat |
| #57 | ui/unified-workspace-upgrade | fix/appointment-form-guidance |
| #59 | feature/v2-website | ui/unified-workspace-upgrade |
| #61 | feature/v3-account-registration | feature/v2-website |
| #63 | docs/public-showcase-cua100 | feature/v3-account-registration |

These PRs were all open at inspection. References here report actual state, not a stale assertion that merged phases remain pending.

## Default-branch publication gate

Before this update, retargeting PR #63 directly to main would introduce 388 changed files, including 78 application files from the unmerged ancestors. That is not a documentation-only diff. Merging its current base would update the v3 branch, not the repository homepage.

Do not force-push, rewrite parents, automatically merge the functional stack or hide it with bulk reverts. The user's permission to merge a safe portfolio PR does not resolve this expanded application integration scope.

Owner-approved publication plan: retain PR #63 as the complete stacked record and create a narrowly scoped documentation publication PR from latest main containing the reviewed README, gallery, unchanged benchmark evidence and audit/status documents. Link evaluated source files to immutable existing commits. Verify the diff contains no application/harness behavior changes before merging. This is a necessary different-base publication path, not a second implementation of the same feature.

Alternative: separately approve review/integration of the full functional stack before merging PR #63. That requires wider diff, CI, dependency and migration review and is outside this documentation round. Only the documentation-only publication plan is approved. The functional stack remains unmerged.

## Local setup

For the v3 application, use the source branch linked by [PR #61](https://github.com/KateK77/careflow-ehr/pull/61), or a verified descendant, with Python and the project's requirements. The [v3 launcher guide](https://github.com/KateK77/careflow-ehr/blob/3ae015ec5155ccbb9ca44766f0d13e2a3a8d2070/docs/iterations/0029-v3-email-access/README.md) creates a fresh isolated preview; never reset, seed or migrate an existing database as a setup shortcut.

The default branch and hosted UI are different source snapshots until integration is approved. Do not assume that cloning main alone produces every v3 signup/layout feature shown in screenshots.

[Architecture](../../architecture.md) · [Development history](../../iterations/) · [Deployment evidence](https://github.com/KateK77/careflow-ehr/blob/3ae015ec5155ccbb9ca44766f0d13e2a3a8d2070/docs/iterations/0029-v3-email-access/public-deployment.md) · [Shared account proposal](demo-access-plan.md)
