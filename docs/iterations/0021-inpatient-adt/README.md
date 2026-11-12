# Phase 8A — Inpatient Admission, Discharge, Transfer & Bed Management

[Issue #43](https://github.com/KateK77/careflow-ehr/issues/43) · [Approved prompt](../0020-phase5-7-integration/prompt.md) · [Verification](verification.md)

This increment builds on the two-parent integration commit `ecd0b440b9a75879129c01a75e11168639dc3c26`. It implements the admission, transfer and discharge portion of W04 and S18.

Administrator and HospitalOperations manage synthetic departments, wards, rooms and inpatient beds. They create and cancel admission requests, admit to an available bed, transfer with a reason, and confirm discharge with synthetic documentation. The attending Physician writes the discharge plan and sees their own stays. Nurses have read access to stay records. Patient chart links follow existing clinical access and do not broaden access to previous clinical encounters or notes.

An AdmissionRequest moves from Pending to Admitted or Cancelled. The resulting stay moves from Admitted to Discharged after an attending plan, explicit confirmation and documentation. A transfer replaces the current bed and records both beds in immutable history. Discharge releases the bed and retains its history, date, actor and summary. InpatientStay derives its patient from the protected admission request and has no outpatient encounter FK. No clinical orders, notes, vitals or MAR events are created by admission or discharge.

The shared hospital write lock, pending request uniqueness, active-bed uniqueness, command keys and versions protect allocation and replay. The audit row and operation commit atomically. `hospital.0001_initial` adds Department, Ward, Room, Bed, AdmissionRequest, InpatientStay, HospitalEvent and OperationLock.

## Staff routes

- Inpatient Dashboard at `/app/inpatient/`.
- Bed Capacity Board and Ward and Room Management under `/app/inpatient/`.
- Admission Worklist at `/app/inpatient/admissions/`, with patient-bound links to admit and manage a stay.
- Patient Chart includes scoped inpatient stay history.

Manual UAT is pending for the consolidated Phase 5–8 round.
