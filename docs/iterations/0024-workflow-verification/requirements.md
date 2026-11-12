# Issue #50 approved scope

## Goal
Expand the CareFlow EHR v1.0.0 verification suite with **at least 100 new, meaningful automated test cases**, then conduct real UI acceptance testing using **Codex Computer Use Agent** after the code has passed all checks.

## Scope
- Start from the current approved code state; review open PR #49 (unified Staff/Patient landing page) and avoid assuming it has merged.
- Inventory existing Django tests and Chromium workflows. Do not count pre-existing tests among the 100 new cases, and avoid redundant assertions.
- Cover staff and patient authentication; role-based authorization; patient/encounter isolation; patient registration; scheduling/check-in; physician encounter and signed SOAP; history; nursing/vitals; labs; pharmacy/MAR; inpatient/ED; radiology; patient portal; audits and cross-module handoffs.
- Each relevant module must test successful actions, invalid inputs, unauthorized access, conflicting state transitions, and data isolation.
- Run on a **separate test database** with synthetic fixtures. Preserve all existing local SQLite files and their contents.
- Run Django system checks, the full test suite, and selected browser workflows; record exact pass/fail/skip results and reproduce failures.

## Computer Use Agent acceptance
Only after automated checks pass, use the actual Computer Use Agent capability (not HTTP or unit-test substitutes) to operate the running site:
1. Open the home page and verify both login entries, CSS, accessibility and responsive layout.
2. Log in as each configured staff role and as a patient using distinct sessions.
3. Exercise a synthetic patient journey from scheduling/check-in through physician/nursing/lab/pharmacy actions and patient result visibility.
4. Check backend permissions through visible denial scenarios, account isolation and cross-role handoffs.
5. Capture screenshots, exact reproduction steps, expected/actual behavior, severity, and test environment.
6. Explicitly state if the agent/browser or the application is inaccessible; never claim agent testing without evidence.

## Deliverables
- 100+ new test cases with descriptive names and assertions, plus existing tests untouched where possible.
- Test inventory and coverage matrix with actual counts.
- Computer Use Agent scenario log, screenshots, and defect report.
- English iteration report, commands/results, and known limitations.
- Dedicated feature branch, commits, and a PR for review. Do not merge into main without owner approval.

## Safety
English-only new code/docs/GitHub records. Synthetic data only. No destructive git commands, database resets, or modifications to existing production-like data. Do not mark the feature complete until execution and manual review evidence are available.
