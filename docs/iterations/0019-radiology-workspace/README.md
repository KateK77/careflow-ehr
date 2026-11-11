# Phase 7B — Radiology Workspace, Reports & Physician Review

[Issue #41](https://github.com/KateK77/careflow-ehr/issues/41) · [Approved prompt](../0018-imaging-orders/prompt.md) · [Phase 7A PR #40](https://github.com/KateK77/careflow-ehr/pull/40) · [Preview and UAT](preview-and-uat.md) · [Verification](verification.md)

RadiologyStaff see available signed orders with catalog and scheduling indicators. Explicit self-assignment reveals patient identity and indication to the assignee. The examination progresses from assigned to started, performed and completed. Performance requires a unique fictional SYN- study identifier and synthetic body site. The physician can cancel before the exam starts. Processing can continue after encounter completion while preserving the encounter and signed SOAP.

Report drafts append revisions. Preliminary publication requires examination performance. Final publication requires completion. Corrections append a publication with a reason. Withdrawal appends a terminal notice while preserving previous versions and acknowledgements. The ordering physician sees current preliminary, final and corrected reports and acknowledges an exact current final or corrected revision. Nurses see the current final or corrected report. Administrators can see order metadata. A context-error withdrawal hides report content and study metadata even from the assigned radiology user.

Order status, examination state, publication and review remain separate. An order version advances across commands. Provider locks, command receipts, protected relationships and transactional audit events coordinate writes. An automated contest test verifies one owner and event when two staff attempt assignment concurrently.

The additive migration `imaging.0002_imagingreport_imagingreview_examworkflow_and_more` creates ExamWorkflow, ImagingReport and ImagingReview. The prototype has no assignment transfer, independent reporting sign-off, equipment capacity management, real image files, DICOM/PACS, portal access or external delivery. Manual UAT is pending.
