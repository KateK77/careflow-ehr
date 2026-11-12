# Phase 7A — Imaging Catalog, Physician Orders & Scheduling

[Issue #39](https://github.com/KateK77/careflow-ehr/issues/39) · [Approved prompt](prompt.md) · [Verification](verification.md)

Base: independent main commit `00c624553cc265e6275a9d2750ab0041a7e6d97f`. Requirements baseline: S17 and the radiology and imaging order workflows. Phase 5 and Phase 6 remain separate.

Administrators append synthetic catalog revisions and select whether each revision is active. Only the latest active revision is available for ordering. The catalog supports X-ray, CT, MRI and ultrasound. Signed orders preserve the selected revision.

The treating physician creates, edits and signs drafts in an authorized in-progress encounter. The order derives patient identity from its encounter, checks appointment consistency and records priority and indication. Once signed, the physician can schedule or reschedule an exam and can cancel with a reason. An already signed order can be scheduled after encounter completion. Order data and exam scheduling use separate records. The encounter and SOAP remain read-only to imaging services.

Administrator and Nurse see previously signed orders in the staff chart. Other physicians see only their own orders. The history records the actor, time, version, draft changes and cancellation. A shared provider lock, optimistic order versions, command fingerprints and transactional audit rows protect supported writes.

## Routes and boundaries

- Administrator catalog at `/app/imaging/catalog/`.
- Treating physician uses Create imaging order on the encounter page, or `/app/patients/<patient>/encounters/<encounter>/imaging/new/`.
- Chart and encounter summaries link to `/app/imaging/orders/<order>/`. Longitudinal imaging is at `/app/patients/<patient>/imaging/`.

The additive `imaging.0001_initial` migration creates ImagingCatalog, ImagingOrder, ImagingExam and ImagingEvent. Changes are limited to the imaging app and staff route, navigation and chart integrations. Scheduling records a fictional exam time and does not allocate room or equipment capacity. Manual UAT is pending for the combined Phase 7 workflow.
