# ADR 0008 — Synthetic laboratory processing and review

Status: implemented for review, manual UAT deferred. Sources: laboratory design v0.2 bea741de, continuation approval retained in iterations 0008/0009. Stacked 3B-2 depends on 3B-1; 3B-3 depends on the verified 3B-2 automated gate. No PR is merged automatically.

## Decisions

Retain the Django modular monolith and extend labs only. LabOrder retains immutable patient/encounter/original ordering identity and uses the original provider lock for all command transactions. LabSpecimen preserves attempts and received-ever evidence. LabResult stores strictly validated version-1 typed JSON snapshots pinned to the submitted catalog. Numeric values are finite bounded decimal strings in exact mock units; absent is not zero. Raw JSON editors reject duplicate keys/nonfinite constants. Relational checks/uniqueness complement service validation; SQLite cannot validate nested JSON or cross-row scope by CHECK joins.

Only assigned active Lab Staff process an order; unassigned claim previews omit patient context. Explicit Administrator lab assignment and role checks do not grant result-authoring capability. Standalone Lab Staff never enters the global clinical/demographic role whitelists. Same-person entry/finalization is explicitly confirmed and audited, and is not independent verification.

Published final/corrected revisions are immutable. Corrections append separate drafts/publications. Withdrawal appends a no-value notice, leaves current pointer on that notice, retains original fulfilled_at and freezes reporting/specimen actions. Context-error quarantine is applied before serializing report payloads and comments. Old order/audit routes cannot bypass the projection. Ordinary readers see safe notice/provenance, not hidden values or unrestricted reasons. Explicit quarantine permission plus Administrator role, or current assigned Lab Staff scope, is required to inspect.

LabReviewAssignment is immutable and separate from ordering/lab-processing identities. Explicit Administrator permission permits replacement only when the current review Physician is ineligible. Review is unique per publication+assignment, never auto-created or carried forward. Covering access is limited to the lab order/report and acknowledgement; chart/encounter/SOAP policies are not widened. is_staff/is_superuser is not a replacement for explicit capabilities.

The 3B-3 backfill uses source=migration_backfill with null actor/command UUID; it records initial responsibility, not a historical physician action. Existing reports and original ineligible physicians are preserved. A post-backfill migration adds stronger pointer/provenance checks.

## Safety and alternatives

Only fresh named preview/test clones receive migrations. Original database, previous preview and backup are preserved. Browser and regression workflows test completion-before-publication without changing signed SOAP. Direct SQL/bulk ORM, production concurrency/cross-service identity races and clinical correctness are not certified. PostgreSQL and production access hardening need separate work. Normalized result components and longitudinal numeric aggregation remain future alternatives; MVP history lists exact per-report values without unit conversion, clinical trending or diagnosis recommendations.
