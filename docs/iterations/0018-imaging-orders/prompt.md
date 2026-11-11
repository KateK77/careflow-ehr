Continue development of CareFlow EHR.

I approve Phase 7 — Radiology & Imaging.

Repository: KateK77/careflow-ehr

Local directory:
D:\AI-Workspace\Personal\careflow-ehr

Expected main baseline:
00c624553cc265e6275a9d2750ab0041a7e6d97f

Verify the actual repository state before proceeding.

IMPORTANT: Phase 5 and Phase 6 have four open, unmerged PRs (#32, #34, #36, #38). Preserve them exactly as they are.

Phase 7 must start independently from the latest verified main branch, NOT from the Phase 6B branch.

Implement two increments:

1. Phase 7A — Imaging Catalog, Physician Orders & Scheduling
2. Phase 7B — Radiology Workspace, Reports & Physician Review

Create separate GitHub Issues, branches and PRs.

Stack only the two new Phase 7 PRs:
- Phase 7A → main
- Phase 7B → Phase 7A branch

## Phase 7A

Implement a dedicated Radiology / Imaging Django module integrated with the existing Patient, Encounter and Physician Workspace.

Required functionality:

- Administrator-managed synthetic imaging catalog
- Fictional examination codes, names and modalities
- Example modalities: X-ray, CT, MRI and Ultrasound
- Catalog activation and revision history
- Physician imaging-order creation from an authorized active Encounter
- Draft editing and explicit order signing
- Order priority and fictional clinical indication
- Patient and Encounter association
- Radiology examination scheduling
- Order cancellation with reason
- Status transitions and complete audit history
- Patient Chart and Encounter order summaries

Use explicit authorization, optimistic versions, idempotent commands and transactional audit events.

Do not automatically recommend an imaging examination or infer clinical necessity.

## Phase 7B

Implement a functional Radiology Workspace.

Required functionality:

- Restricted RadiologyStaff role
- Imaging examination worklist
- Explicit order assignment
- Scheduling and workflow status
- Examination started / performed / completed states
- Fictional study identifiers
- Synthetic imaging metadata
- Draft radiology reports
- Preliminary and final report publication
- Structured findings and impression fields
- Published report corrections with immutable history
- Report withdrawal with reason and appropriate visibility restrictions
- Physician result review and acknowledgement
- Patient Chart and Encounter integration
- Report chronology, provenance and audit history
- Appropriate RadiologyStaff, Physician and Nurse access boundaries

Keep order, examination, report publication and physician review states separate.

Allow an already-authorized imaging workflow to finish after Encounter completion where the documented state model permits it, without modifying the Encounter or signed SOAP documentation.

Do not expose unpublished, withdrawn or restricted report content to unauthorized users.

Do not implement real PACS, DICOM transfer, imaging equipment connectivity, diagnostic image interpretation or actual radiology procedures.

Use fictional imaging study metadata and reports only. Do not import real patient images.

## Database and Safety

Maintain the existing Django 5.2 modular-monolith architecture.

Use additive migrations and protected relationships.

Never modify, reset, reseed or migrate the original db.sqlite3.

Never overwrite existing Phase 3B, 4A, 4B, 5 or 6 preview databases.

Create newly named isolated development previews and test databases.

Preserve all existing patients, appointments, signed clinical notes, laboratory reports, pharmacy events, MAR records, portal data and billing data.

Do not introduce a dependency on unmerged Phase 5 or Phase 6 code.

Keep Patient Portal imaging integration outside this independent Phase 7 increment.

## Automated Testing

Implement regression and Chromium tests covering:

- Imaging catalog management
- Physician-order permissions
- Draft editing and signing
- Order cancellation
- Radiology assignment
- Examination status transitions
- Draft and final reports
- Report correction and withdrawal
- Physician acknowledgement
- Role-based isolation
- Unauthorized direct URLs
- Duplicate command protection
- Stale versions and concurrency
- Audit rollback
- Encounter completion boundaries
- Preservation of existing clinical workflows

Run Django system checks, migration consistency checks, the full regression suite, relevant Chromium workflows and GitHub Actions CI.

Report exact test counts and CI links.

Do not claim manual UAT was performed.

## GitHub Workflow

For each increment:

1. Create an English GitHub Issue.
2. Create the approved branch.
3. Implement the actual working functionality.
4. Add tests and additive migrations.
5. Update English documentation and iteration records.
6. Commit and push.
7. Open a PR.
8. Verify GitHub Actions.

Keep all Phase 5, Phase 6 and Phase 7 PRs OPEN and UNMERGED.

Do not force-push or rewrite existing history.

Do not start surgery, inpatient, emergency or AI development.

Do not deploy.

## Final Deliverables

After Phase 7A and 7B are complete, provide:

- GitHub Issues and PRs
- Branch names and exact commit SHAs
- Implemented features and working URLs
- New models and migrations
- Regression test results
- Chromium workflow results
- GitHub Actions CI links
- Database preservation evidence
- Known limitations
- Safe preview startup instructions
- Consolidated Phase 7 manual UAT checklist

The user wants to postpone manual UAT until after this development stage.

Do not request intermediate manual testing.

Do not automatically merge any PR.

Stop after both Phase 7 increments are implemented, published and automatically verified.