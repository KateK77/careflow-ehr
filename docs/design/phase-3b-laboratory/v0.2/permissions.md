# Revised permission matrix v0.2

**Proposal only; implementation is not approved.** Unchanged v0.1 capabilities apply unless overridden here. Standalone Lab Staff is still separate from existing demographic/chart role whitelists. No new global chart permissions, role membership, account, permission record or application guard is created now.

## Changed / clarified capabilities

| Operation | Authorized actor and scope | Explicit denials |
| --- | --- | --- |
| Enter and finalize report | Current assigned active Lab Staff, correct order/specimen, expected versions and explicit preview/confirmation. May be the same person. | Administrator/Physician/Nurse/FrontDesk alone cannot finalize. No independent-verification or production-safety claim. |
| Replace ineligible review assignee | Active Administrator **and** explicit `labs.reassign_review_responsibility` permission, current assignee ineligible, target active Physician, reason/confirmation/current order+assignment. | No self-claim by Physician, Lab Staff delegation, Nurse/FrontDesk reassignment, auto-routing, Administrator impersonation or arbitrary active-assignee replacement. |
| Read current covering-assigned lab order | Active current review-assignment Physician; minimum requisition, published revisions/notice, specimen provenance and review history for that order. | Assignment does not grant patient-chart/history/nursing/SOAP/other-encounter read or authoring, order creation or original-order cancellation. No links implying those rights. |
| Acknowledge current publication | Current eligible review-assignment Physician only, exact current publication+assignment, explicit confirmation. Includes withdrawal notice with distinct review kind. | Original ordering physician is denied new acknowledgement after replacement unless a later explicit assignment returns responsibility. Administrator never acts as the reviewer. Old reviews do not satisfy the new assignment. |
| Withdraw erroneous published report | Current assigned active Lab Staff; latest usable publication, no active correction draft, reason category/text and explicit confirmation/version checks. | Administrator alone, any Physician, Nurse or FrontDesk cannot withdraw. An inactive lab assignee must first be explicitly replaced using existing lab-assignment policy. |
| Read routine withdrawn history | Existing authorized lab/chart reader, with explicit historical-withdrawn warning; covering Physician only within assigned lab context. | No current-value rendering, normal/negative badge, automatic fallback, unwithdrawal or reassignment of published report/patient. |
| Inspect context-error quarantined payloads | Assigned Lab Staff within that order OR active Administrator with explicit `labs.view_quarantined_report` permission. | Ordinary chart readers, Nurse and ordering/covering Physicians receive withdrawal/provenance/review metadata, **not** old value payloads through chart/history/search/compare/audit/error routes. Other Lab Staff and FrontDesk denied. |
| Cancel / collect / recollect | Original active ordering Physician cancels only before any receipt/publication; Nurse acts on submitted orders under specimen guards, including after encounter completion. | Cover assignment confers no cancel right. Received-ever, fulfilled, withdrawn and cancelled orders cannot become cancellable through rejection or pointer changes. No recollection after publication. |

Existing Administrator catalog and lab-staff assignment capabilities remain, but do not imply these new explicit permissions. Grant/revoke the two named permission codenames only through a future reviewed provisioning/migration policy; do not treat is_staff/is_superuser or a hidden button as a substitute. Intentionally assigned multiple roles retain explicit capability union, with all object/state restrictions and no incidental scope expansion.

## Backend access-control changes proposed

1. Add a lab-order review scope for current eligible LabReviewAssignment.physician, independent of `clinical.access.charts_for`, `encounters_for`, rooming guards and history can_maintain. Do not add appointments, edit encounter.physician, mutate ordering_physician or widen patient READ_ROLES to make coverage work.
2. Keep ordering identity as read provenance and original ordering/cancellation authority; keep lab-processing assignment independent. A Physician already having chart access uses their existing permissions; a lab covering assignment adds only the bounded lab context.
3. Gate reassignment by actor role+explicit permission, current-assignee eligibility and target membership at commit time. Lock/order-version checks ensure a stale Administrator cannot replace a newer assignment.
4. Gate acknowledgement by current publication+assignment and current active Physician capability. Recheck after locking and before any receipt disclosure; an old assignee cannot replay a prior command to recover broader current access.
5. Gate withdrawal/quarantine before serializing payloads, not after a template renders. A context-error marker applies to the entire chain's value payloads. Review metadata remains immutable and visible only within allowed scope; it is not a loophole for before/after values.
6. Preserve 403/404 non-disclosure, CSRF/POST-only writes, escaped bounded forms, current versions and command UUIDs. Denial audits must not expose unauthorized patient or quarantined text.

No permission allows clinical action under another person's identity. Audit actor for reassignment is the Administrator; actor for notice/result acknowledgement is the actual responsible Physician; withdrawal/finalization actor is the actual assigned Lab Staff. Existing signed documentation and original encounter/appointment context are never changed.
