# Iteration 0030 — Public showcase and native CUA-100

[Issue #62](https://github.com/KateK77/careflow-ehr/issues/62).
Branch: docs/public-showcase-cua100, from v3 commit f7e171e0f25606b3635aae36fde1102493d68789.
Parent: PR #61. Main stays the default branch; no merges or releases.

## Approved scope

Publish the existing repository after a sensitive-artifact review, create a screenshot-led showcase inspired by the presentation of KateK77/mychart-clone, and design/execute about 100 native Computer Use tasks from simple to difficult. The owner explicitly approved necessary API expenses while prohibiting waste and chose to retain main as default, linking directly to the showcase branch.

[Original prompt and translation](prompt.md) · [100-task benchmark](../../testing/cua100-v1/README.md)

## Public visibility review

The owner explicitly authorized public visibility. Read-only checks covered 1,117 reachable historical blobs and 62 Issue/PR bodies plus 7 comments. No matches were found for the reviewed OpenAI/GitHub/AWS/private-key/credential-URL signatures or database/credential-artifact filenames. This is a scoped scan, not a guarantee against every possible secret format.

The repository is now public. Its About URL points to https://jiawen.pythonanywhere.com/. Main and all existing branch history remain intact. Private owner passwords, encrypted tokens, local SQLite files and raw QA artifacts remain excluded from Git.

## Implementation

The existing application's business logic is unchanged. New test-only modules provide a 100-task catalog, fresh synthetic fixtures, exact route/POST policies, native execution, offline rehearsal, independent SQLite assertions and honest result accounting. Existing offline test entry points accept an explicit Django interpreter for isolated worktrees.

The previous root README is preserved byte-for-byte under docs/showcase/v3/README.before-showcase.md. Original requirements and iteration records are retained. The showcase uses actual non-sensitive public homepage screenshots.

## Initial verification

Before live calls: 536 Django tests passed in 94.868 seconds; 40 offline CUA tests passed in 79.626 seconds. System check and migration consistency passed with an isolated database path. Full task rehearsals and native results are recorded separately as execution proceeds; these counts do not imply all 100 native tasks passed.

## Final evaluation

[PR #63](https://github.com/KateK77/careflow-ehr/pull/63) remains unmerged and stacked on PR #61.

Native CUA: **85/100 passed**; read/authorization **69/70**, write/clinical **16/30**. **336 API responses**, estimated token cost **USD 3.379979**, no paid failure retries. [Complete results](../../testing/cua100-v1/results.md) include per-task screenshots, action logs and independent assertions. [Findings](../../testing/cua100-v1/findings.md) preserve all 15 failures and the pre-API readiness race.

Final offline CUA suite: **44 passing tests**; all **100 deterministic task rehearsals** passed after correcting test definitions. **62 existing SQLite files** retained their SHA-256 hashes. Main/default branch, application code, historical requirements and public-host data were preserved.

Implementation commits: 875a406, 672809a, 6187ce8 and 563b5b8; the final report commit is the head of the linked PR. Full SHA provenance is included in individual result JSON where originally recorded.
