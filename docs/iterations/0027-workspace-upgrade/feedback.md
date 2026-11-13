# Consolidated feedback disposition — v1.0

Source: user feedback and approved upgrade discussion, repository iteration evidence, and inspection on 2026-11-13. This is a professional English consolidation, not a new manual acceptance claim.

| Feedback | Disposition / evidence |
| --- | --- |
| Unified staff/patient landing, actual login routes, static CSS, demo notice | Already implemented in PR #49. Retain and rerun landing/browser/session regressions. |
| Four-role staff login description | Already role-neutral. Refresh remaining registration-only introductory text and add return-to-portal links. |
| Different staff roles need clear workspace entry | Role-gated dashboard cards reuse existing context permissions. Lab Staff brand and identity corrected; backend access unchanged. |
| Patient directory excessive whitespace and ambiguous Open | Compact rows, wrapping clinical table and explicit View Patient action. No invented patient status/encounter-date fields. |
| Demographic hierarchy and excess whitespace | Identity precedes action links, compact grouped identity/contact definitions and mobile stacking. Existing clinical sections retained. |
| Registration Sex/Unknown, label and keyboard behavior | Upstream PR #54 uses accessible radio choices. Retain explicit selection and exercise its Chromium regression. |
| Required synthetic confirmation confused with optional duplicate review | Upstream conditional duplicate checkbox retained. No auto-fill or auto-check. Offline tests exercise checkbox, label, keyboard and no-write invalid submission. |
| Appointment optional search confused with required form | Preserve PR #55 disclosure. Reopen it when a query is active so applied filters stay visible. Compact form and verify four key controls in initial 1280x800 view. |
| Schedule filter height, cancellation history layout | Compact filters and wrapping appointment-history columns. Review and confirmation remain required. |
| Appointment types, working hours, leave and early check-in window | Deferred business-rule proposals; no implicit approval or new restrictions. |
| Registration/update audit labels, actor and fields | Reuse existing display filters; show username when no full name. Do not rewrite stored events or resolve IDs outside existing access scope. |
| Numeric identifiers in other historical event payloads | Deferred scoped provenance design; do not infer unrelated patient/staff identities or rewrite snapshots. |
| Duplicate primary diagnosis internal constraint | Existing readable validation retained; full regression suite covers it. |
| Allergy contradiction, __all__, submitted values | Existing validation retained. Remove duplicate as_p error rendering from retry page; one summary, retained input, no record mutation. |
| Resolved linked problem status | Existing fix retained with regression. |
| Date entry | Existing guidance/validation retained. Historical manual observation was user-reported acceptable behavior, not an exhaustive malformed-date test matrix. |
| Narrow physician tables and recent encounters | Existing clinical table behavior preserved; new shared presentation tested at narrow widths. Comprehensive accessibility remains unverified. |
| Outdated laboratory phases, mojibake, result_save, draft/history labels and raw report dictionaries | Prior fixes verified in current templates/helpers. Preserve structured component previews and version context. |
| Long first acknowledgement comment | Historical content and audit evidence untouched. No evidence-supported backend defect established. |
| Lab post-encounter processing, corrections, withdrawals, covering physician and quarantine | Preserve existing services, permissions, signed SOAP and version-specific reviews. Regression/browser suites exercise existing behavior. |
| Medication 1 days / 1 simulated units and fictional dose guidance | Already corrected; retain pluralization and existing pre-submission guidance. |
| Pharmacy after Encounter #3 completion and SOAP preservation | Prior user-reported observations remain in original Phase 4A records. Do not ask for duplicate manual tests or invent UUIDs/timestamps. |
| Imaging stale catalog revision | Existing code-specific stale/latest/reload message, idempotency and concurrency checks retained. |
| Early imaging examination | Existing documented local simulation behavior retained; no new timing rule. |
| Payment SYN- prefix, uniqueness and reversal references | Existing form guidance and ledger constraints retained. |
| Native screenshot races, bounded waits, keypress diagnostics | Harness safety, retry limit, network and budgets unchanged. Align only visible check-in assertion to the readable label; database action assertions unchanged. |
| Misleading registration_checkpoints on appointment scenario | Existing scenario-specific diagnostics retained. |
| Prior live registration/appointment failures | Offline success is not live model acceptance. Registration paid retries remain paused. |
| Outdated README/roadmap claim Phases 5–8 await merge | Verified PR #47 merged; correct current status and preserve byte-identical preimages in this iteration. |

## Evidence boundaries

Previously reported manual UAT is preserved as historical user-reported evidence. This upgrade has not been manually accepted. No new paid native CUA request is authorized or executed. Do not claim comprehensive security, concurrency, accessibility, production readiness or database-level tamper resistance.

## Later review checklist

- Open both portal entries and return links.
- Review role-appropriate dashboard and Lab Staff brand destination.
- Review patient density, demographics and readable audit labels.
- At 1280x800 verify Patient, Physician, Appointment start and Review appointment without scrolling.
- Filter patients, review and confirm a synthetic appointment; verify Scheduled and history.
- Check mobile horizontal table navigation and explicit registration confirmation.
- Confirm allergy conflict text appears once with submitted values retained.

Use a new isolated QA database for any further manual review.
