# Iteration 0008 — Phase 3B-2: Specimen Collection & Lab Processing

Requirements v0.2: [approved design commit](https://github.com/KateK77/careflow-ehr/commit/bea741de88fd0c719eb4ed39cf70ec7fd2959f3b). [Issue #19](https://github.com/KateK77/careflow-ehr/issues/19). Branch `phase/0008-lab-processing` stacks on `phase/0007-lab-catalog-orders`, verified parent `544f43dbb3b286632a8a3440129b3254c452b17a`. [Implementation commits](https://github.com/KateK77/careflow-ehr/commits/phase/0008-lab-processing). PR and actual CI run links are recorded in the implementation PR description; no merge is authorized.

The [approved prompt](prompt.md) explicitly supersedes the design's former separate manual-UAT-before-next-increment gate: complete automated verification and CI before 3B-3, then consolidate manual UAT. Neither increment is manually accepted.

## Development report

Extends the existing labs app with Nurse identity-confirmed collection/correction, rejection and new recollection attempts; restricted Lab Staff claim/Administrator assignment, receipt/rejection; typed JSON result drafts and explicit preview/finalization. Lab processing continues after encounter completion without changing clinical models or signed SOAP. Original entry, editor and finalizer identities remain separate provenance fields; same-person entry/finalization is an explicitly labelled local MVP decision, not independent verification.

Lab Staff is deliberately absent from global demographic/chart role whitelists. Its login opens the laboratory workspace; only assigned orders expose patient context. Unassigned worklist requisitions contain order/panel identifiers only. Collection uses MRN plus DOB confirmation, not a checkbox alone. Writes use original-provider serialization, aggregate/child versions and durable actor-bound UUID receipts. Received-ever cancellation locks include rejected attempts. Rejection requires abandoning a draft; recollection appends rather than resetting an attempt.

[Verification](verification.md), [feedback](feedback.md), [acceptance](acceptance.md), [changed files](changed-files.md). Result correction, withdrawal, physician acknowledgement and cover assignment are excluded until 3B-3. Original DB migration remains withheld.
