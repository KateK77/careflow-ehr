# Proposed Phase 3B — Laboratory Orders & Results

Design proposal v0.1, 2026-11-10. **The phase name and implementation scope are not approved.** Permission to prepare/publish this design is not implementation approval. The PR must remain unmerged for review.

- Verified main baseline: `56ea8b332525926b02759b2afefa93166bd52d31`; clean worktree and index before branching.
- [Design Issue #15](https://github.com/KateK77/careflow-ehr/issues/15).
- Branch: `docs/phase-3b-laboratory-design`; [comparison / PR entry](https://github.com/KateK77/careflow-ehr/compare/main...docs/phase-3b-laboratory-design); [commit history](https://github.com/KateK77/careflow-ehr/commits/docs/phase-3b-laboratory-design). The published PR links exact HEAD and CI evidence.
- Source: [approved design-only prompt verbatim](prompt.md); [feedback and approval boundary](feedback.md); [verification](verification.md).
- Requirements source: [English baseline v1.0, translation revision 1.0.0](../../../requirements/v1.0-en/product-spec.md), especially laboratory section 1.5, Order Composer/Active Orders/Results Review S13–S16 and W02. This proposal narrows that long-term scope; it does not replace or rewrite the authoritative original/translation. Generic Inbox, AVS and portal features in the original baseline are not implicitly authorized here.

## Review package

1. [Functional requirements and synthetic catalog](specification.md).
2. [Architecture, baseline constraints and future FHIR considerations](architecture.md).
3. [Four independent state machines and transaction guards](states.md).
4. [Role/read/write matrix and restricted Lab Staff access](permissions.md).
5. [Six candidate models, field types and constraints](models.md).
6. [Server-rendered pages, navigation and workflows](ui.md).
7. [Traceable functional/negative/Chromium acceptance plan](acceptance.md).

The target is an explicit physician order → nursing collection → laboratory receipt/result publication → physician acknowledgement → patient-chart history loop, including results arriving after encounter completion. Recommended defaults are decisions for review, not approved features.

## Main recommendations

- Retain Django/server templates/SQLite for this local prototype; add a bounded lab module only after approval. Preserve patient, appointment, encounter, history, nursing and signed SOAP records.
- Use immutable published report revisions, a current-published pointer, and acknowledgements referencing the exact published revision. Corrections never silently replace or mark the old version reviewed.
- Separate order, specimen, result and review states. Result follow-up outlives encounter authoring; no reopening/signature mutation is needed.
- Introduce an active `Lab Staff` group only within lab-specific capabilities. Do not broaden existing demographic/chart role whitelists. Lab staff see minimum requisition data for claimed orders, not a general chart.
- Serialize writes with existing provider locks plus order versions, durable command keys and atomic AuditEvent/LabEvent writes. SQLite is not a production-concurrency guarantee.

## Decisions requiring user review

| Question | Recommended v0.1 default / consequence |
| --- | --- |
| Phase label and scope | Keep the proposed name above for discussion; obtain explicit approval before assigning an implementation iteration/branch. |
| Order context | One panel per order; an owned, in-progress encounter is required to create/submit. No standalone outpatient orders yet. |
| Lab staffing | Single synthetic lab queue with explicit self-claim; one active Lab Staff assignee per order, Administrator-controlled reassignment. Is a second-person finalizer needed? Default: same assignee may enter and finalize with explicit confirmation. |
| Specimen/cancellation policy | One active specimen attempt per order; rejected attempts retained; cancellation allowed only before receipt and first publication. Is later cancellation needed? |
| Late-result coverage | Ordering physician remains responsible after encounter completion. No reassignment of physician reviewer in v0.1; inactive/deleted physician leaves an explicitly unassigned-attention backlog requiring a future delegation policy, never auto-acknowledgement. |
| Report storage | Strictly validated typed JSON panel snapshots within six models. A normalized result-component table is an alternative if relational reporting/query needs justify a seventh model. |
| Invalid published report | Corrections append revisions for the same patient/order/specimen. Withdrawal/entered-in-error and wrong-patient report remediation require an explicit additional policy; do not silently reassign or erase a report. |
| Catalog and values | Fictional codes/analytes/units and broad demonstration input bounds; no reference-range interpretation or critical-result workflow. Confirm whether these small panels suffice. |
| Follow-up limits | No real-time alerts, unattended clinical inbox, external interface, FHIR transport or patient portal. In-app worklists require staff navigation/refresh. |

These questions must be resolved or explicitly accepted as limitations before implementation approval. The [acceptance plan](acceptance.md) is future verification work, not executed or manually accepted functionality.

## Deliverable and preservation

All new files are confined to this versioned design directory. Existing documents, application code, settings, workflows, migrations and database remain unchanged. New files are this README, specification, architecture, states, permissions, models, UI, acceptance, prompt, feedback and verification Markdown files. No clinical implementation, model classes, migration generation, seed or deployment occurs. Publish the design PR, verify documentation checks/CI, and stop for review.
