# Phase 4B-1 — Nurse MAR Workspace

[Issue #27](https://github.com/KateK77/careflow-ehr/issues/27). Approved base `91b3a11806fe102bac0328348da594c9f4813ab5`. See the English baseline §1.8, S18 and W03.

An approved pharmacy review with a valid simulated dispensing receipt supplies one fictional MAR task. The receipt ID identifies the task. No schedules are inferred from the order. A task with no event is pending. A Nurse may record one simulated administration during the active Encounter for the receipt's full quantity. The receipt and signed order remain independent of MAR. The event time must fall between dispensing and documentation, within the Encounter.

The existing Nurse group supplies clinic-wide nursing scope. A Nurse can filter by patient and Encounter. Assigned Physicians and existing clinical readers can read within their established scope. Only Nurse membership authorizes a write. A provider lock serializes recording with Encounter completion. Version and actor-scoped command receipt checks prevent stale and duplicate writes. Audit and event persist atomically.

Consolidated manual UAT follows both increments.
