# Permission proposal v0.1

**Design proposal; the Lab Staff role, phase name and implementation are not approved.** All permissions require an authenticated active user, server-side scope and current state. Administrator is not a clinical superuser by implication.

## Existing baseline findings

`patients.access.roles_for()` filters group membership through the four-element READ_ROLES tuple (Administrator, Physician, Nurse, FrontDesk). Adding Lab Staff to that tuple would also grant demographic patient access and change seeding; it is not a safe role-only addition. `clinical_access` permits only Administrator/Physician/Nurse; Administrator/Nurse read the clinic, Physicians read assigned-patient charts and their own encounters. Existing nursing authoring requires Nurse plus an arrived appointment with no completed encounter. Clinical-history authoring requires current treating context; encounter diagnoses and SOAP are owned/in-progress only.

Recommended future approach: lab-specific active-group/capability helpers recognize a Django Group named **Lab Staff**, without adding it to demographic READ_ROLES or clinical_access. Separate lab identity/navigation context displays the role and routes standalone Lab Staff to the lab workspace after login; inspect dashboard/post-login fallback so it does not redirect into a denied patient page. The existing four roles and their permissions remain unchanged outside explicit lab capabilities. No role/group/form is actually added in this design.

## Proposed matrix

| Action / information | Administrator alone | FrontDesk alone | Physician | Nurse alone | Lab Staff alone |
| --- | --- | --- | --- | --- | --- |
| Existing patient registration/demographics | Existing read/write | Existing read/write | Existing read | Existing read | Denied; minimum identity only within assigned requisition |
| Existing charts/notes/history/nursing | Existing clinic read | Denied detailed clinical content | Existing assigned-chart and own-encounter rules | Existing clinic read; rooming/vitals only by existing guards | Denied, including direct URLs and hidden context endpoints |
| Active synthetic catalog | Read/manage new immutable revisions and active flags | Denied | Read | Read required specimen definition | Read definition for authorized work; no manage |
| Create/edit/submit order | Denied | Denied | Own in-progress encounter only | Denied | Denied |
| View unsubmitted order draft | Clinic lab read for support; no authoring | Denied | Ordering owner only | Denied | Denied |
| Cancel order | Denied | Denied | Owner, subject to pre-receipt/publication guards; may act after completion | Denied | Denied |
| Read submitted requisition/specimen | Clinic lab read | Denied | Owner full; other chart-authorized physicians only minimal published context | Clinic lab/specimen read for collection | Assigned order only; unassigned queue excludes patient detail |
| Collect / correct pre-receipt / recollect specimen | Denied | Denied | Denied | Submitted order and permitted specimen state, including after encounter completion | Denied |
| Claim unassigned submitted order | May explicitly assign active Lab Staff, with reason | Denied | Denied | Denied | Self-claim only via minimal queue + atomic version |
| Reassign claimed/fulfilled order | Explicit active-Lab-Staff reassignment, reason/audit | Denied | Denied | Denied | Denied; request administrative reassignment |
| Receive/reject specimen | Denied | Denied | Denied | Denied | Current assignee with state guards |
| View unpublished result draft | Clinic lab read; visibly unpublished | Denied | Denied | Denied | Current assignee only |
| Enter/finalize/correct/abandon report | Denied | Denied | Denied | Denied | Current assignee, explicit actions and state/version checks |
| Read published results / versions | Clinic lab read | Denied | Existing patient chart scope; own orders remain available after encounter completion | Clinic lab read | Assigned order only, including own fulfilled orders for correction |
| Physician acknowledgement | Denied | Denied | Ordering active physician only, exact current revision | Denied | Denied |
| Lab audit snapshots | Authorized lab read; no edit | Denied clinical audit | Owner lifecycle; other patient readers published report history only | Submitted-order/specimen and published report events; no unpublished result-value snapshots | Assigned-order lab history only; no unrelated chart events |

## Assignment and minimum disclosure

The single synthetic lab's unassigned submitted-order queue exposes public order identifier, panel/specimen type, submission time and workflow badges. It does not expose patient-wide search, chart links, DOB, reason or results. Explicit claim is the authorized operational assignment action; after it succeeds, the staff member may see patient name/MRN/DOB for specimen identity and the bounded order reason, specimen and report history for that order. Other patients/encounters are not reachable by guessing an identifier. Assigned fulfilled orders remain in that assignee's history for corrections; cancelled orders already assigned are read-only. A cancelled unassigned order cannot be claimed.

No self-reassignment of another person's work, shared Lab Staff login or unrestricted result query. Administrative reassignment is audited and does not modify original entry/finalizer identities. A Lab Staff account deactivation immediately denies writes. No automatic reassignment/clinical escalation service is proposed.

## Multi-role and endpoint rules

Evaluate each lab write capability explicitly; Administrator membership alone does not imply Nurse/Physician/Lab Staff authoring. For intentionally provisioned multiple roles, capability union applies only to individually satisfied roles and object scopes. A Lab Staff+Physician user may access their own physician charts because of the explicit Physician role, not Lab Staff; a lab assignment must not expand physician chart scope to unrelated patients. Test each single role and representative mixed-role combinations. Whether to prohibit same-person ordering/finalization or dual-role accounts is an unresolved approval question; default v0.1 permits explicit union and records the acting capability.

All querysets must enforce scope, not merely navigation visibility. Return 403 for missing capability and 404 for an out-of-scope object when doing so avoids existence disclosure. GET is read-only except permitted access audit. POST requires CSRF, synthetic confirmation where applicable, expected versions and idempotency key. Recheck group activity, assignment and state inside the write transaction. Do not trust patient/order/encounter/actor/status values from form hidden fields. Lab-only responses render a restricted requisition header instead of the full clinical header; suppress full sidebar links and result-draft values in chart summaries, search, audit payloads and errors.
