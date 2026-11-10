# Proposed acceptance and testing plan v0.1

**Design proposal; implementation is not approved.** Every case below is planned, not executed evidence or manual acceptance of lab functionality. Resolve the README's open decisions before converting these checks into an approved implementation acceptance baseline.

## Requirement-to-test matrix

| ID | Requirements | Future test / expected evidence |
| --- | --- | --- |
| AT-01 | LAB-01 | Create/activate synthetic catalog revisions; reject duplicate code/revision and two active revisions of one code; deactivation retains old order/report interpretation. No real terminology/unit claims. |
| AT-02 | LAB-02 | Owner creates/saves/reopens/edits a draft from their in-progress encounter; persisted context, source identity and versions correct. No order exists merely from GET composer. |
| AT-03 | LAB-02, LAB-15 | Forge patient, encounter, physician, status, snapshot, revision and author fields; backend derives/validates context and rejects mismatches without unauthorized row/event changes. |
| AT-04 | LAB-03, LAB-14 | One submit creates one submitted order, pending specimen and atomic audit receipt. Same command replay yields same record/outcome, not another specimen/event. Reused UUID with changed payload/context/actor cannot disclose or duplicate data. |
| AT-05 | LAB-03 | Same encounter/panel existing order produces repeat-test warning; explicit fresh command, confirmation and reason permits legitimate repeat. A retry is not treated as an intentional clinical repeat. |
| AT-06 | LAB-03, LAB-11, LAB-14 | Submit races encounter completion under shared provider serialization: one valid ordering of operations; completed-first blocks submit, submitted-first survives completion. Existing signed-note completion rules remain unchanged. |
| AT-07 | LAB-04 | Owner cancels draft/submitted pre-receipt with reason; records retained. Missing reason, foreign physician, cancelled resubmission, cancellation after receipt/publication all denied. Collected specimen remains historically collected after allowed cancellation. |
| AT-08 | LAB-05 | Nurse confirms correct patient and records collection with explicit actor/time/accession. Duplicate/foreign accession or wrong specimen type rejected. No change to appointment, rooming, encounter or SOAP. |
| AT-09 | LAB-05, LAB-15 | Reject future/pre-submission/pre-DOB/naive or ambiguous/nonexistent local times. Pre-receipt correction keeps original collector and before/after reason; receipt-first blocks correction. Check changed live patient identity/version before confirming collection. |
| AT-10 | LAB-05, LAB-06 | Rejected specimen retained; no result entry on it. Explicit recollection creates next attempt and unique active accession; parallel recollections cannot create two active attempts. |
| AT-11 | LAB-06, LAB-14 | Two Lab Staff claim the same unassigned order: one winner and one conflict. Administrative reassignment requires active Lab Staff, reason/version; old assignee immediately loses entry rights. |
| AT-12 | LAB-06 | Receive only collected specimen for assigned order; reject with reason before publication and no active draft. Unreceived/rejected/wrong-order specimen cannot be used for result entry. |
| AT-13 | LAB-07 | Partial result draft persists only for assigned staff, source/specimen and edit version correct; clinical readers cannot see draft values via direct URL, chart, history, errors or audit snapshots. Administrator read-only support may see visibly unpublished drafts. |
| AT-14 | LAB-07, LAB-08 | Reject NaN/infinity, booleans-as-numbers, nonnumeric text, excessive precision/length, out-of-demo-bounds values, wrong/missing units, unexpected codes/keys and duplicate components. Exact mock units required; no conversion or automatic interpretation. |
| AT-15 | LAB-08 | Complete typed panel finalizes once after explicit confirmation. Missing components blocked unless explicit not-performed+reason; absent values never zero/normal. Enforce collection≤receipt≤publication and receipt≤performed≤publication when any component was performed. All-not-performed report has no invented performed timestamp. |
| AT-16 | LAB-08, LAB-14 | Two saves/finalizations, stale edit_version or stale order.version yield one current draft/publication and friendly 409; input retained. Unique constraints catch direct duplicate attempts; busy transaction failure leaves no partial state. |
| AT-17 | LAB-09 | Direct POST/model-service edit of published report rejected. Correction creates new draft/predecessor/reason, leaves old report current until publish, then advances one linear chain. Old values/authors/times/reviews unchanged. |
| AT-18 | LAB-09, LAB-14 | Parallel correction drafts/publications have one winner. Abandoning a draft preserves its history and prior report pointer; rejected/new specimen cannot silently replace the original report's specimen. Wrong-patient reassignment is rejected. |
| AT-19 | LAB-10 | Only ordering active physician acknowledges exact current published revision; store immutable actor/time/revision. No GET acknowledgement. Same successful command replay yields no extra row/event; new key on already acknowledged revision returns friendly conflict. |
| AT-20 | LAB-09, LAB-10, LAB-14 | Race acknowledgement versus correction: acknowledgement-first remains only on old revision; correction-first rejects stale acknowledgement. New current revision is unreviewed. A correction draft alone does not reset current acknowledgement. |
| AT-21 | LAB-10, LAB-11 | Inactive ordering physician cannot acknowledge; report remains visibly unreviewed/responsibility unresolved. No Administrator impersonation or automatic transfer of responsibility. |
| AT-22 | LAB-11 | Complete signed encounter with submitted/pending lab; later collect, receive, publish, correct and acknowledge successfully through lab guards. Snapshot all signed-note fields, encounter/appointment versions and timestamps before/after; they remain unchanged. |
| AT-23 | LAB-11 | Encounter completes with unsubmitted draft: draft stays visible/read-only for edit/submit; owner may cancel. No automatic submit, deletion or reopening. |
| AT-24 | LAB-12 | Chart/encounter/lab history render current published revision, independent badges, correct patient, explicit superseded history and scoped timeline; links do not expose another physician's encounter. Patient A/order A IDs cannot retrieve Patient B/report B. |
| AT-25 | LAB-12, LAB-15 | Role matrix GET/POST tests for Administrator, FrontDesk, Physician owner/other/unrelated, Nurse, assigned/unassigned Lab Staff, inactive and anonymous users. Include catalog administration, collection, receipt, draft entry, finalization/correction and acknowledgement. |
| AT-26 | LAB-12 | Standalone Lab Staff denied existing patient directory/registration/detail, clinical notes/history/nursing/scheduling sensitive endpoints and unrelated order/specimen/report/review URLs. Their queue contains only minimal operational data; claiming is explicit and audited. |
| AT-27 | LAB-12, LAB-15 | Mixed Lab Staff+Physician, Lab Staff+Administrator and Nurse+Administrator use explicit capability union without scope leakage. Being in Lab Staff never adds the group to patient READ_ROLES or grants charts for assigned lab patients. |
| AT-28 | LAB-13 | Every successful write has matching actor, action, time, patient scope, changed fields and before/after LabEvent/AuditEvent. Forced event failure rolls back domain writes. Access/denial logging contains no unauthorized clinical text. No ordinary audit edit/delete endpoint. |
| AT-29 | LAB-14 | Creation, collection, receipt, finalization, correction and acknowledgement UUID replay tests across tabs/processes. UUID fingerprint mismatch conflicts. Revoked/inactive actor cannot recover sensitive receipt content after losing scope. Failed validation stores no success receipt. |
| AT-30 | LAB-15 | CSRF missing/invalid token, HTML/script payloads, malicious state parameters and wrong methods rejected/escaped. Retain bound input and readable field/non-field errors without internal identifiers. |
| AT-31 | LAB-15 | Full text/units/reasons accessible at 1440, 900, 700 and 390 px; contained overflow, keyboard access, clear focus/labels and no whole-page overflow. Browser date/decimal controls supplement server validation. Accessibility inspection is scoped evidence, not comprehensive certification. |
| AT-32 | LAB-16 | On a disposable clone, additive migration creates only approved lab schema/permissions; all existing clinical rows and signed SOAP unchanged, integrity/FK pass. Repeated authorized synthetic initialization preserves records/passwords and avoids duplicate catalog revisions. Never run these destructive setup tests against the user's database. |
| AT-33 | LAB-16 | Full pre-existing 164-test baseline plus new approved lab tests pass; existing seven browser modules still pass. Do not change fixtures/assertions merely to hide a regression. External interfaces/AI/prescribing/billing code and dependencies absent. |

## Future automated execution plan

- Model/form/service/HTTP tests for success, invalid input, relationships, permissions, methods, audit rollback and immutable snapshots. Test database constraints separately from UI validation.
- TransactionTestCase with separate DB connections for cancellation/receipt, order submission/completion, claim/reassignment, collection/recollection, stale result updates, two corrections and review/publication races. Record SQLite busy behavior; no unsupported production-concurrency claim.
- Django commands: system check, migration consistency and full `manage.py test`. Existing tests must remain unchanged unless a separately reviewed integration adaptation is required. No test may operate on the local user database.

## Proposed Chromium workflows

1. **Complete lifecycle:** Physician draft/review/submit → Nurse identity/collection → Lab Staff claim/receive/type values/preview/finalize → Physician acknowledge → chart/encounter/history. Refresh each boundary to verify persistence and independent states.
2. **Late result and correction:** submit, sign SOAP and complete encounter before collection; finish lab lifecycle; acknowledge revision 1; publish correction revision 2; confirm review required again and old report/ack preserved. Compare signed note/completion/check-in provenance unchanged.
3. **Negative roles and context:** separate actor sessions including FrontDesk and standalone Lab Staff, direct forbidden URLs/POSTs, unrelated order/patient and draft leakage checks, stale version/replay errors, invalid values/units and retained input. Include scoped responsive screenshots/keyboard inspection.

Retain all seven existing Chromium workflows. Do not call these new workflows passed until implemented and actually executed. Future manual UAT should follow the same lifecycle and negative checklist, record exact observations/browser/widths, and keep unperformed scenarios explicitly unverified. Successful tests do not constitute real clinical validation.

## Design-review acceptance now

Review the proposed scope, matrix, six models, JSON-vs-normalized tradeoff, state diagrams, late-result policy, idempotency/concurrency approach and unresolved questions. Verify documentation links/IDs/fences, new-Markdown-only diff and unchanged old-file/database hashes. This design task passes only documentation/publication checks, not AT-01–AT-33 or lab manual UAT. The design PR remains unmerged and implementation awaits separate explicit approval.
