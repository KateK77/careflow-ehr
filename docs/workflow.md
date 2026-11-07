# GitHub development workflow

1. **Issue** — Record the baseline version, relevant requirement IDs, scope, exclusions, and acceptance checks. Capture user approval and subsequent scope changes.
2. **Branch** — Start from the agreed main commit. Name the branch for the iteration, for example `phase/0001-foundation`.
3. **Commit** — Stage only the intended paths and inspect the staged diff. Run applicable checks and record actual results. Reference the Issue in the commit message.
4. **PR** — Open a PR to main. Reference the Issue, link the iteration record, and identify the reviewed commit. Use a closing keyword when merging the PR would complete the Issue.
5. **Review** — Record feedback and follow-up changes. Rerun affected checks and record the user’s acceptance or remaining blockers.
6. **Merge** — Merge after review and acceptance. Record the PR, resulting commit, and final outcome in the Issue or PR, then close the iteration.

The iteration record identifies its Issue and branch. A branch-scoped PR link and the Git history of the iteration directory provide stable references before the PR number and commit SHA exist. Add permanent links to the Issue or PR when available. Never put secrets, patient data, or sensitive diagnostic output in these records.
