# Revised acceptance plan v0.2

**Design proposal; implementation is not approved.** These tests are future obligations, not executed laboratory verification or manual UAT. Retain [v0.1 AT-01–AT-33](../v0.1/acceptance.md) for unchanged behavior; use the precedence table below for revised expectations.

## New / revised functional and negative cases

| Case | Requirement | Planned evidence / pass criteria |
| --- | --- | --- |
| R2-01 | V2-01 | Assigned active Lab Staff enters/previews/finalizes their own valid report with explicit confirmation; original entry and actual finalizer/times/versions/audit retained. No independent-verification label. |
| R2-02 | V2-01 | Inactive/unassigned Lab Staff, Administrator/Physician/Nurse/FrontDesk alone, missing confirmation or stale draft/order version cannot finalize. Entry-actor mismatch alone is not a denial when current assignee is authorized. |
| R2-03 | V2-02 | Current responsible physician ineligible; permitted active Administrator previews/reassigns to active Physician with reason, expected assignment/order and command UUID. One new immutable sequence/event; ordering_physician/encounter/patient and old acknowledgements unchanged. |
| R2-04 | V2-02 | Deny reassignment by Administrator without explicit permission, other roles, missing reason, inactive/non-Physician target, draft/cancelled order or currently eligible responsible physician. Forged actor/ordering physician/assignment values do not bypass guards. |
| R2-05 | V2-02, V2-07 | New covering Physician must acknowledge current publication even if they previously reviewed it in an older assignment epoch. Unique publication+assignment; no reuse of user-only prior acknowledgement. Original physician reactivation does not change responsibility. |
| R2-06 | V2-02, V2-06 | Covering Physician without existing chart rights can access only their bounded lab context; direct SOAP/chart/history/nursing/other-encounter/order-create/cancel paths remain denied by existing rules. No appointment or physician-owner mutation grants access. |
| R2-07 | V2-02, V2-07 | Reassign before publication, after final acknowledgement and after withdrawal. Derived worklist always follows latest publication+assignment. No automatic acknowledgement, impersonation or silent responsibility transfer when no active target exists. |
| R2-08 | V2-03 | Cancel original draft/submitted pre-receipt with reason, including after collection/completion; collected history remains. Any historical received_at permanently blocks cancellation even after rejection. Cancelled is terminal. |
| R2-09 | V2-03 | At most one non-rejected specimen; preserve rejected attempt/accession/actor/time. Explicit recollection creates next attempt on submitted orders, including completed encounters; no reset/reuse or publication on rejected specimen. |
| R2-10 | V2-03 | Active result draft blocks rejection until explicit abandonment. After first publication or withdrawal, deny specimen editing/rejection/recollection, order cancellation or silent unwithdrawal. Completed encounter alone does not block still-submitted lab work. |
| R2-11 | V2-04 | Strict numeric strings/codes/exact units, size/precision/bounds, duplicate/unknown keys, bool/float/nonfinite/exponent/localized numbers and absent/value exclusivity tested. Unknown schema/kind rejected; schema columns/envelope must agree. No silent rounding, conversion or normal-value inference. |
| R2-12 | V2-04 | Catalog edits/new schema do not reinterpret published snapshots; old decoders retained. All-not-performed report has explicit reasons and no invented performed time. Withdrawal payload cannot masquerade as not-performed or a numeric/coded report. |
| R2-13 | V2-04 | DB constraints independently enforce unique order/revision, original final, active draft and published successor including withdrawal. Direct service attempts fail cross-order/predecessor/pointer/assignment/JSON validation. JSON is not claimed to be fully validated by DB CHECKs. |
| R2-14 | V2-05 | Assigned Lab Staff withdraws exact current final/corrected publication with reason/confirmation. One notice revision/event, pointer at notice, order withdrawn, first fulfilled_at retained. Old report/status/content/source, specimen, all reviews and signed notes unchanged. |
| R2-15 | V2-05 | Deny withdrawal by wrong role/assignee, before publication, from a stale/superseded target, with missing reason, with active correction draft or after prior withdrawal. Explicit abandon precedes retry; no implicit draft loss. |
| R2-16 | V2-05, V2-06 | All current chart/encounter/history summaries render withdrawn warning and no usable value, negative/absent substitute or fallback. Routine historical values require explicit withdrawn-history warning; acknowledgement never restores values/order. |
| R2-17 | V2-06 | context_error restricts prior values, before/after snapshots, old comment/reason text in ordinary chart/review/history/search/compare/error responses. Only scoped assigned Lab Staff or explicitly permitted Administrator can inspect; notice/provenance/review metadata retained. No patient/report reassignment. |
| R2-18 | V2-05, V2-07 | Withdrawal of already acknowledged result creates a new notice obligation for current responsible Physician. Old result acknowledgement remains; new notice review_kind correct. No auto-review/normal-negative result. Cover reassignment after notice review requires fresh epoch-specific notice acknowledgement. |
| R2-19 | V2-07 | Acknowledge versus reassignment: old-ack-first remains historical and new assignment unreviewed; reassign-first denies old reviewer. A prior successful command cannot recover current sensitive scope after responsibility is lost. |
| R2-20 | V2-05, V2-07 | Acknowledge versus withdrawal/correction: old acknowledgement never covers new publication; publication-first rejects stale pair. Two withdrawals yield one notice; exact UUID replay no duplicate clinical event; different stale command 409. |
| R2-21 | V2-03, V2-07 | Cancellation/receipt race: receipt-first denies cancellation permanently; cancel-first denies receipt. Collection-first may permit cancellation only after fresh reload/version. Reject/recollect races obey one-active-attempt and received-ever guards. |
| R2-22 | V2-05, V2-07 | Correction draft-first blocks withdrawal until abandon; corrected publication-first makes old withdrawal stale; withdrawal-first blocks correction. No forked successor chain, silent discard or old-report promotion. |
| R2-23 | V2-02, V2-07 | Concurrent reassignments have one winner; target eligibility checked inside transaction. Later deactivation shows unresolved responsibility; no fallback or auto-ack. Reassign/publication races leave obligation on latest pair. |
| R2-24 | V2-01, V2-07 | Forced assignment/publication/review audit failure rolls back all writes; busy/stale errors preserve input and no duplicate events. Actual acting capability and identity recorded; no Administrator reviewer impersonation. |
| R2-25 | V2-08 | Each stage's additive migrations preserve protected existing rows, signed SOAP and explicit expected deltas. Responsibility backfill attributes original ordering identity with system/backfill provenance only; inactive originals unresolved; no fabricated past review/clinical assignment action. |
| R2-26 | V2-08 | Distinct stage PR/CI/manual UAT gates; no unimplemented screens exposed, no stage acceptance automatically authorizes next stage. All original exclusions and regression suites remain. This design revision creates no implementation Issue/branch/migration. |

## v0.1 precedence / retained coverage

- AT-19–AT-21 now use current review-assignment + publication identity, explicit covering workflow, preserved prior reviews and distinct withdrawal notice review; ordering-physician-only acknowledgement and unresolved coverage as the sole behavior are superseded.
- AT-07–AT-10/AT-12 use received-ever cancellation and immutable rejected history, plus explicit no-publication recollection boundaries.
- AT-17–AT-18 retain append-only corrections and wrong-context denial, adding immutable withdrawal notices and quarantine instead of treating withdrawal as unimplemented.
- AT-24–AT-29 and AT-32 incorporate the v0.2 access matrix, assignment/publication races, seventh model and backfill policy. Keep CSRF, escaping, browser responsiveness, original-context isolation and atomic audit tests.
- Preserve existing patient/appointment/encounter/signed SOAP/history/nursing/audit data and the entire current regression/browser baseline. No real clinical readiness, database immutability or production concurrency is established by passing tests.

## Future Chromium/UAT checkpoints

1. 3B-1: catalog/order draft→review→submit/cancel, repeat-command behavior and forbidden-role URLs; pending specimen exists without claiming collection implementation.
2. 3B-2: Nurse collection/rejection/recollection, claimed Lab Staff receipt→typed entry→same-person explicit finalization; late processing after completed encounter; verify identity/time/unit and signed-note preservation.
3. 3B-3: original physician becomes ineligible → permitted Administrator reassigns → covering Physician reviews bounded lab context without chart/SOAP expansion → correction requires new review → withdrawal becomes notice, no fallback → notice acknowledgement preserves withdrawn state. Include a context-error quarantine denial/authorized inspection case, direct URLs, stale versions, retries and multiple sessions.

These workflows require actual future execution and user observations at each gate; no result is claimed now. Production independent verification, active-physician handover, unwithdrawal, numeric trend analytics and pre-publication post-receipt discontinuation remain outside this MVP plan unless separately approved.
