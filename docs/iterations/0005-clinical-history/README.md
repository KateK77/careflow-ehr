# Iteration 0005 — Phase 2B clinical history v1.0

- [Issue #9](https://github.com/KateK77/careflow-ehr/issues/9)
- Branch: `phase/0005-clinical-history`
- Base: `phase/0004-physician-workspace` at `eff5a2b94891e5deae8304ac2e9036c6dc8eaf43`
- PR is stacked on Phase 2A, never directly on main. Phase 2A PR #8 remains open.
- [Approved prompt](prompt.md), [architecture decision](../../decisions/0005-clinical-history.md), [verification](verification.md), [feedback](feedback.md), [acceptance guide](acceptance.md), [changed files](changed-files.md).
- English baseline v1.0 / translation 1.0.0: longitudinal subset of S06–S08, S11 and S12. This approved increment takes precedence over the broader future baseline.

## Requirements and acceptance criteria

Persist medical/surgical/family/social history; active/resolved/inactive problems; primary/secondary encounter diagnoses optionally linked to patient problems; allergy entries and consistent summary states; active/stopped/historical medication statements with provenance. Provide real create/view/edit/review flows, date/status validation, preserved authorship, version conflicts and transactional before/after audit history. Retain inactive/resolved records rather than deleting them.

All new pages enforce clinical authorization and patient context on GET/POST. Treating Physicians maintain longitudinal data; Nurse/Administrator read access remains; FrontDesk cannot see detailed records. Diagnosis writes require the assigned Physician and an in-progress encounter. Completed diagnoses and signed SOAP notes remain protected. Chart navigation, summaries and timeline link to implemented pages only.

## Development report

Added the history domain with five clinical record models, allergy assessment, patient serialization and history events; typed ModelForms; transactional services; scoped views/routes; paginated lists, detail/edit/review pages and chart integration. Added one additive migration. Each record keeps original author, current source, last editor, review identity/time and integer version. Edits invalidate the previous review; prior clinical values remain in authorized audit history.

Longitudinal writes require an assigned scheduled/arrived appointment without a started encounter, or an in-progress own encounter. A completed encounter's arrived appointment does not independently extend write access. Historical assignments still allow chart reads. At most one primary diagnosis exists per encounter; users explicitly demote a prior primary before assigning another. Diagnosis edits never automatically update linked problems.

Allergy creation/reactivation atomically changes the summary to Documented allergies. Inactivation of the last active allergy produces Not reviewed, never an inferred No known allergies. Explicit no-known/unknown assessments require no active allergies. Inactive/refuted historical entries remain visible. Medication statements cannot prescribe, dispense or administer anything.

Browser verification exposed an existing encounter-template failure when an arrived appointment lacked a check-in recorder. The display now handles missing provenance explicitly, without inventing a recorder or modifying stored data. A focused regression test covers it. Date validation was also corrected to inspect only date fields during ModelForm construction; no excluded author relation is dereferenced before service assignment.

## Limitations and review boundary

Single synthetic clinic, local SQLite and application-service concurrency guarantees only. No controlled terminology catalog, allergy interaction checking, medication dosing validation, prescribing, medication administration, external exchange, deletion, diagnosis amendment/reopening, bulk import or deployment. Patient/family/documented source labels are assertions rather than independently verified evidence. Original authorship persists; corrections to provenance are retained in revision history.

At most one primary diagnosis, with any number of secondary diagnoses; a primary diagnosis is optional. Phase 2A completion still requires a signed SOAP note, without adding mandatory diagnoses. Longitudinal updates never rewrite signed notes. Record event detail displays the latest 100 events; lists paginate by 20 and chart timeline remains bounded. Direct database/bulk ORM operators can bypass service rules; no database immutability, production readiness, comprehensive security or clinical safety certification is claimed.

The user authorized beginning Phase 2B before Phase 2A manual UAT. Neither phase has passed manual UAT. Keep both PRs open and unmerged; no Phase 3 work, release or deployment.
