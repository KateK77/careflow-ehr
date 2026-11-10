# Proposed Phase 3B — Laboratory Orders & Results: v0.2

Design-review revision, 2026-11-10. **Implementation and the proposed phase name are not approved.** The user authorized this documentation revision only. Keep [PR #16](https://github.com/KateK77/careflow-ehr/pull/16) open and unmerged; use existing [design Issue #15](https://github.com/KateK77/careflow-ehr/issues/15), not a new functional Issue.

- Branch: `docs/phase-3b-laboratory-design`; reviewed parent `8bbf3aa18f67faa22e68973bbb27e4eb97e6b5ff`; main baseline `56ea8b332525926b02759b2afefa93166bd52d31`.
- [Original v0.1](../v0.1/README.md) and its [prompt](../v0.1/prompt.md) remain byte-identical. [This revision's prompt](prompt.md) is preserved separately.
- [Requirements/decision disposition](specification.md), [architecture](architecture.md), [models/JSON contract](models.md), [states and races](states.md), [permissions](permissions.md), [UI/workflows](ui.md), [implementation checkpoints](increments.md), [acceptance](acceptance.md), [feedback](feedback.md), [verification](verification.md).

## Decisions incorporated for review

| Requested decision | v0.2 disposition |
| --- | --- |
| Laboratory finalization | Assigned active Lab Staff may enter and explicitly finalize their own work for the synthetic MVP. Retain entry/finalizer identities, times, revisions, edit versions and audit. This is not production-grade independent verification. |
| Inactive ordering physician | Administrator with an explicit review-reassignment permission may assign an active covering Physician when the current responsible physician is no longer eligible. New immutable review-assignment epoch; original ordering physician and all acknowledgements preserved. New assignee must acknowledge the current publication, with lab-only scope. |
| Specimen/cancellation | At most one non-rejected attempt, with retained rejection history. Cancellation stops permanently after any receipt or publication. Recollection is explicit and pre-publication only. Encounter completion does not stop already-submitted lab follow-up. |
| Storage | Strict typed JSON snapshots are preferred for MVP. Pin schema version/kind and catalog content, publish immutably, document relational constraint boundaries and numeric-query limitations. Normalized components remain future work. |
| Erroneous report | Append an immutable withdrawal notice, point current publication at that notice, mark order withdrawn, preserve history and prior acknowledgements, and require notice review. No deletion, reassignment, normal-negative/absent substitution, restoration or silent fallback. Context-error withdrawals quarantine prior values from ordinary clinical views. |
| Delivery | Propose 3B-1, 3B-2 and 3B-3 with explicit dependencies, additive migration boundaries and separate future PR/UAT approvals. No implementation branch or functional Issue is created now. |

## Version precedence and unchanged scope

v0.1 LAB-01–LAB-16 remain the baseline except as expressly overridden by V2-01–V2-08. In particular, v0.1's ordering-physician-only acknowledgement, unresolved coverage/withdrawal policies, six-model count, current_result pointer semantics and published-successor constraint are superseded by the v0.2 responsibility/publication rules. The updated model set has seven proposed models, including LabReviewAssignment. v0.1 planned tests AT-19–AT-21 and related completed-encounter/chart cases must be interpreted through the new assignment/withdrawal cases, not run as contradictory expectations.

Unchanged: synthetic panels and mock units, one panel/order, owned in-progress encounter for creating/submitting, original four-role permissions outside explicit lab capabilities, independent lifecycle axes, preserved signed SOAP, server-rendered Django, protected relationships, durable command keys, provider-first serialization and audited writes. All v0.1 exclusions remain: no real patients, interfaces, clinical CDS, prescribing/administration, automatic diagnosis/treatment, billing, production deployment, AI/LLMs or FHIR implementation. No clinical functionality is tested or implemented here.

## Remaining review questions and explicit limits

1. Confirm the proposed phase label and detailed scope before implementation. The three suggested increments are planning units, not authorizations.
2. MVP review reassignment is limited to an ineligible current responsible physician (inactive account or missing Physician role). Planned leave/active-physician handovers, escalation and multiple concurrent reviewers remain out of scope unless separately approved.
3. After receipt but before publication, an unresultable/rejected order remains submitted for resolution/recollection; there is no hidden post-receipt cancellation. An explicit not-performed report is allowed only under the ordinary received-specimen rules. A separate pre-publication discontinuation policy would require approval.
4. Withdrawal is terminal for usable reporting on that order. Replacement work needs a new order in a currently authorized in-progress encounter; standalone/reopened encounters and unwithdrawal are not introduced.
5. Lab Staff naming/provisioning, optional production two-person verification, response-time/coverage staffing, retention/access review and PostgreSQL validation require future review. No monitored clinical alerting or production readiness is claimed.

All new documents are confined to v0.2 plus the new parent revision registry. Existing v0.1, historical requirements/translations, prompts, application files and SQLite remain unchanged. Exact publication commit and CI evidence are recorded on the existing PR.
