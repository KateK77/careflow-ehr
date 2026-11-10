# Revised workflows and presentation v0.2

**Design proposal; implementation is not approved.** Keep original CareFlow server-rendered pages, DEMO — NOT FOR CLINICAL USE, roles, clear actions, full-value readable tables, contained scroll/focus behavior and validated bound forms. These are planned pages/actions, not implemented routes.

## Enter and finalize

Assigned Lab Staff opens their scoped received-specimen order, saves typed draft, previews patient/order/specimen/revision/values/units, then confirms Finalize this report revision. Display original entry identity, current editor and actual finalizer separately even when the same person. Confirmation explains that MVP entry/finalization by one assignee is not independent verification. Only published revisions enter clinical current-result summaries. Retain explicit absence reasons and no performed time for all-not-performed reports.

## Reassign inactive review responsibility

An authorized Administrator opens a lab responsibility queue, which shows ineligible current responsible physicians and unresolved lab review items. Select an affected submitted/fulfilled/withdrawn order → inspect original ordering physician, current responsible physician/assignment sequence, current publication and review metadata → choose active covering Physician → enter reason → preview scope → confirm reassignment with current versions. No impersonation, acknowledgement button or automatic account switch appears in this flow.

The new assignee's lab worklist shows Review required — responsibility assigned, with original ordering identity and assignment reason/actor/time. They open the bounded lab report or withdrawal notice and explicitly acknowledge that publication+assignment. Hide patient-chart/SOAP/history/other-encounter links unless separately authorized through existing scope. They cannot cancel/reopen/order on behalf of the original physician. Historical reviews show their original actors and assignment epochs; reactivation of the original physician does not return responsibility automatically.

## Specimen and cancellation

Keep separate order and attempt badges. Cancel is available to the original owner only while draft/submitted and never received/published; after reload, an already collected but never received order can still cancel with preserved collection history. Received-ever is a permanent prohibition, even if that attempt was later rejected. Show Cancellation unavailable — specimen was received rather than a misleading generic conflict.

Nurse recollection requires submitted order plus rejected prior attempt and no publication; display old rejection reason/accession/time alongside a new attempt, never a reset. Before rejection, Lab Staff must explicitly abandon any draft. After publication/withdrawal, collection, specimen correction/rejection and recollection controls are absent and direct writes denied. Completed encounter is informational: allowed existing-order lab work continues without making rooming/SOAP edits available.

## Correct or withdraw published report

Correction continues to create a new draft; the prior publication remains current until the new report is explicitly published. Withdrawal is a distinct action, not a correction with blank values. Assigned Lab Staff selects Withdraw current report → sees exact current revision, predecessor history and any active correction draft blocker → enters report_error/context_error plus reason → previews consequences → explicitly confirms. Require abandon/reload first if a draft exists; never discard it silently.

The preview states that the order becomes withdrawn, the notice becomes current, all prior versions/reviews remain, no previous report is promoted, and replacement testing needs a new authorized order. After success, show a prominent **Report withdrawn — not a usable result** banner with notice revision/time and review status. No numeric result, negative code, blank-as-normal result or not-performed badge is shown as current.

Ordinary report-error historical values require opening an explicitly marked Historical withdrawn report. Context-error withdrawals instead hide historical values/free-text in standard clinical views and comparisons, including old review comments; show safe category and audit/review metadata. Assigned Lab Staff and explicitly permitted Administrator inspectors use a separately gated quarantine audit view, never reassignment of the report to another patient.

## Physician worklist and acknowledgement

Include current final/corrected reports **and withdrawal notices**, including orders from completed encounters. The pending key is publication+assignment. New correction, withdrawal or review reassignment creates a fresh obligation; old acknowledgements remain visible as historical. Acknowledge this withdrawal notice clearly attests receipt of an error notice, not clinical approval or restoration. After acknowledgement the notice can leave the default pending list, but every chart/encounter/history summary remains withdrawn. An ineligible current responsible physician shows Responsibility unresolved until explicit reassignment; no silent disappearance or auto-review.

Current summaries retain independent order/specimen/publication/review states, server timestamps, original ordering/entry/finalizer identities and current review responsibility. Results never get copied into signed SOAP. Existing deferred allergy-error/audit-label/global responsive enhancements remain deferred; new lab design does not authorize changing those screens.
