Please perform a design-review revision for the existing CareFlow EHR Phase 3B laboratory proposal.

Repository: KateK77/careflow-ehr

Existing design Issue: #15\
Existing design PR: #16\
Branch: docs/phase-3b-laboratory-design\
Current reviewed HEAD: 8bbf3aa18f67faa22e68973bbb27e4eb97e6b5ff

The v0.1 proposal has completed initial review. Keep the existing design intact, but prepare a clearly versioned v0.2 revision addressing the following architectural decisions.

## 1. Laboratory Finalization

For the local synthetic-data MVP, permit the assigned Lab Staff member to enter and finalize results with an explicit confirmation step.

Record original entry identity, finalizer identity, timestamps, versions, and audit events.

Clearly state that this is not production-grade independent verification.

## 2. Inactive Ordering Physician

Design a minimal, explicitly authorized covering-physician reassignment workflow.

Requirements:

- No automatic acknowledgement.
- No Administrator impersonation.
- Explicit authorized reassignment with a reason.
- Preserve the original ordering physician.
- Preserve existing report acknowledgements.
- Require the new responsible Physician to review the current report revision.
- Do not expand unrelated chart or SOAP permissions.

Document the required data-model and access-control changes.

## 3. Specimen and Cancellation

Retain one active specimen attempt per order, with permanent histories of rejected attempts.

Clarify all cancellation and recollection boundaries, especially after specimen receipt, publication, and encounter completion.

Specify race-condition outcomes.

## 4. Report Storage

Use strictly validated typed JSON snapshots as the preferred MVP design.

Document the validation contracts, schema versioning, immutable publication policy, database constraints, and limitations for longitudinal numeric queries.

Keep normalized result components as a documented future alternative.

## 5. Erroneous Published Reports

Design a non-destructive entered-in-error or withdrawal workflow.

Never delete, silently replace, or reassign a published report.

Preserve provenance, previous report versions, and acknowledgements.

Clarify the effect on the current-report pointer, order status, physician-review worklist, and authorized chart presentation.

Do not equate a withdrawn report with a normal negative or absent result.

## 6. Implementation Increments

Recommend smaller future implementation increments under the proposed Phase 3B umbrella:

- 3B-1: Lab catalog, order creation, submission, cancellation and permissions.
- 3B-2: Specimen collection, lab assignment, result entry and publication.
- 3B-3: Corrections, withdrawals, physician acknowledgement, chart integration and final hardening.

Identify dependencies, migration boundaries, measurable acceptance criteria and separate GitHub PR/UAT checkpoints.

Do not create implementation branches or approve these increments automatically.

## 7. Documentation and Verification

Update the design documents, state diagrams, model proposals, permissions matrix, workflows and acceptance cases consistently.

Preserve v0.1 as historical design evidence. Add a clearly linked v0.2 revision rather than silently replacing the original approved design prompt.

Run documentation checks, commit and push the revision to the existing design branch, and update PR #16.

Verify GitHub CI.

Do not:

- Merge PR #16.
- Write application code.
- Generate migrations.
- Modify or reset the SQLite database.
- Create a new functional development Issue.
- Start implementation, deploy or release.

## Final Report

Provide the revised design commit, updated PR link, resolved design decisions, remaining questions, documentation changes, CI results and preservation evidence.

Stop after publishing the v0.2 design revision for review.
