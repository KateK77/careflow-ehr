# Version description consolidation — revision 1.0

Date: November 16, 2026 (America/Chicago).
Issue: [#66](https://github.com/KateK77/careflow-ehr/issues/66).
Branch: `docs/version-descriptions`, based on main `f3cbb59`.
Scope: documentation only; no application, migration, database, credential, deployment or paid API changes.

## Owner instruction

Original Chinese instruction, kept outside the complete product descriptions:

> 我要的是每个版本修改后的一份完整 description，不是把反馈、聊天原话和旧 prompt 叠在一起。你把每个版本的discription分别整理成可独立阅读的完整需求文档，然后直接 push 到 GitHub

English translation revision 1.0:

> I want a complete description of each version after its revisions, not feedback, verbatim chat and old prompts piled together. Organize each version's description into a complete, independently readable requirements document, then push it directly to GitHub.

## Editorial decisions

1. Describe the three product generations, not each historical prompt revision as another release.
2. Repeat the complete clinical/administrative scope in each file so the reader does not need earlier descriptions.
3. Write the final resolved requirements rather than chronological deltas.
4. State each version's UI/account lifecycle explicitly and add measurable acceptance criteria.
5. Apply final username-only v3 registration and pending-staff guidance; exclude the abandoned email design.
6. Distinguish staff-created clinical patient records from self-registered patient user accounts.
7. Separate historical evidence, deferred functionality, prototype limits and deployment/source status.
8. Preserve the other worktree's uncommitted public-demo design proposal. Do not publish passwords or approve new functionality.
9. Preserve the owner's latest main README change. Add discovery links only to the requirements registry.

## Verification scope

Check local links and headings, source GitHub file paths against committed trees, requirement IDs, common-workflow completeness, final no-email wording and the absence of chat/prompt dumps in the product descriptions. Check whitespace and a documentation-only diff before publication.

Original requirements, translations, prompts and CUA benchmark evidence must remain unchanged. GitHub CI runs its configured Django checks on the new head; local documentation checks are not a rerun of the historical application/browser/CUA suites.

The PR and commit provide Git traceability. Push this branch and open a PR. Do not merge a documentation PR or the functional stack without separate approval.

## Actual local verification

- Three complete descriptions: 4,095 / 4,571 / 4,959 words for v1 / v2 / v3.
- Each file includes 56 common requirement IDs and 14 connected acceptance journeys, plus its version-specific scope.
- 31 Markdown links checked; all 11 immutable source-file targets verified against actual committed Git objects.
- No chat quotations, Chinese source text or encoding artifacts in the three English product descriptions. The original request is preserved only in this separate record.
- Original requirements-registry content retained with an additive navigation section; Git LF-normalized comparison passed.
- Owner README, application, original requirements/translations, iteration history and CUA evidence remain unchanged.
- Git whitespace checks passed. No local application/browser/native-CUA suite was rerun for this documentation-only change. CI results are recorded in the PR.
