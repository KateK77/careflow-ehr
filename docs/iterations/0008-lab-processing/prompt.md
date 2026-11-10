We are changing the development sequence for CareFlow EHR Phase 3B.

**I approve continuing implementation through Phase 3B-2 and Phase 3B-3 before conducting manual UAT.**

Manual UAT for Phase 3B-1 is intentionally deferred. We will conduct consolidated end-to-end manual acceptance after all three increments are implemented.

Project directory:
D:\AI-Workspace\Personal\careflow-ehr

Repository:
KateK77/careflow-ehr

Existing implementation:
- Phase 3B-1 Issue #17
- Phase 3B-1 PR #18
- Branch: phase/0007-lab-catalog-orders
- Commit: 544f43dbb3b286632a8a3440129b3254c452b17a

Reference design:
- PR #16
- v0.2 commit: bea741de88fd0c719eb4ed39cf70ec7fd2959f3b
- Follow v0.2/increments.md and its accompanying specifications.

## 1. Development Strategy

Implement Phase 3B-2 first, followed by Phase 3B-3.

Use stacked development branches and Pull Requests:

- Phase 3B-1: existing PR #18 → main
- Phase 3B-2: new branch → Phase 3B-1 branch
- Phase 3B-3: new branch → Phase 3B-2 branch

Create a separate GitHub Issue, iteration record, development branch and Pull Request for each new increment.

Do not merge any PR automatically.

Manual UAT is deferred until all increments are complete. Automated tests, code review, migration verification and CI must still pass at each increment.

Do not mark deferred manual acceptance checks as passed.

## 2. Phase 3B-2 — Specimen Collection & Lab Processing

Implement working functionality for:

- Nurse specimen collection worklist.
- Patient identity confirmation.
- Collection timestamps and provenance.
- Specimen correction and rejection.
- Explicit recollection attempts.
- Lab Staff role with restricted permissions.
- Laboratory staff worklist and order assignment.
- Specimen receipt and rejection.
- Structured laboratory result drafts.
- Strict typed JSON result validation.
- Result preview and explicit finalization.
- Immutable first published laboratory reports.
- Independent specimen, order and publication statuses.
- Processing submitted orders after Encounter completion.

Use the existing Phase 3B-1 LabOrder and LabSpecimen models.

Create only the required additive schema changes.

Do not implement physician acknowledgement, corrections, withdrawal, covering-physician assignment or final longitudinal integration until Phase 3B-3.

## 3. Phase 3B-2 Verification Gate

Before beginning Phase 3B-3:

- Run Django system and migration checks.
- Run existing and new regression tests.
- Run relevant Chromium workflows.
- Verify role isolation and wrong-patient access denials.
- Test duplicate commands, stale versions and concurrent transitions.
- Verify published-result immutability and audit events.
- Verify signed SOAP and existing clinical records are preserved.
- Push the implementation and open its stacked PR.
- Verify GitHub Actions CI passes.

If blocking defects remain, fix them before proceeding.

Record automated verification accurately. Do not claim manual UAT was performed.

## 4. Phase 3B-3 — Results Review & Chart Integration

After Phase 3B-2 passes its automated verification gate, continue with Phase 3B-3.

Implement:

- Append-only laboratory result corrections.
- Preserved original result revisions and audit history.
- Non-destructive erroneous-report withdrawal.
- Restricted handling of context-error reports.
- Explicit covering-physician reassignment when the responsible physician becomes ineligible.
- Version-specific Physician acknowledgement.
- Withdrawal-notice review.
- Physician laboratory results worklist.
- Patient Chart laboratory summaries.
- Encounter laboratory order/result integration.
- Longitudinal laboratory history.
- Clear pending, final, corrected, withdrawn and unreviewed states.
- Accessible and responsive clinical interfaces.

Follow the v0.2 permissions, JSON schema, revision, withdrawal and responsibility policies.

Ensure completed Encounters remain completed. Never modify signed SOAP notes or silently reinterpret previous laboratory results.

## 5. Database Safety

The user's original SQLite database must remain unchanged.

Do not apply new migrations to the original database.

Preserve the verified backup and existing Phase 3B-1 preview.

For integrated development verification, create separately named database clones from a consistent verified backup. Apply migrations only to explicitly selected disposable test/preview databases.

Verify pre-existing patient, appointment, encounter, SOAP, history, nursing and audit records are preserved.

Never reset, delete, reseed or overwrite the original database.

Do not deploy the application.

## 6. Integrated Automated Testing

After Phase 3B-3 implementation, run the complete existing and new automated test suite.

Include Chromium workflows covering:

1. Physician creates and submits an order.
2. Nurse collects a specimen.
3. Lab Staff receives the specimen.
4. Lab Staff enters and finalizes results.
5. Physician reviews and acknowledges the report.
6. Corrected results require a fresh acknowledgement.
7. Withdrawal preserves prior versions and presents appropriate warnings.
8. Authorized covering-physician reassignment.
9. Results published after Encounter completion.
10. Role isolation, stale requests, concurrency and database preservation.

Verify GitHub Actions for both new PRs.

Do not misrepresent unexecuted tests as passed.

## 7. Final Deliverables

Provide:

- Phase 3B-2 Issue, branch and PR.
- Phase 3B-3 Issue, branch and PR.
- Commit SHAs.
- New application pages and URLs.
- Data models and migrations.
- Regression test counts.
- Chromium workflow results.
- GitHub Actions CI results.
- Database preservation evidence.
- Known issues and incomplete requirements.
- Consolidated manual UAT checklist.
- Safe integrated-preview startup instructions.

## Constraints

- Keep PR #16 and PR #18 unmerged.
- Do not merge the new implementation PRs.
- Do not conduct or claim user manual UAT.
- Do not modify existing historical records.
- Do not force-push or rewrite history.
- Do not deploy or create a release.
- Do not implement functionality outside the approved Phase 3B-2 and Phase 3B-3 scope.

Stop after publishing the implementations and their verification reports.

The user will conduct consolidated manual UAT before approving any implementation merges.