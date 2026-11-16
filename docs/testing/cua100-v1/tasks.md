# CareFlow CUA-100 v1.0

100 independent tasks. Difficulty 1â€“5; fresh synthetic database per task. A separate signed SOAP record must remain unchanged in every case. Deterministic offline recipes are NOT native CUA results.

## CF-001 â€” Unified landing

- Role: Anonymous; difficulty: 1/5; fixture: base.
- Target: `/`; expected HTTP 200; final: `/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Choose your portal.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-002 â€” Staff sign-in entry

- Role: Anonymous; difficulty: 1/5; fixture: base.
- Target: `/login/`; expected HTTP 200; final: `/login/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Staff sign in.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-003 â€” Patient sign-in entry

- Role: Anonymous; difficulty: 1/5; fixture: base.
- Target: `/portal/login/`; expected HTTP 200; final: `/portal/login/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Sign in to the Patient Portal.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-004 â€” Patient signup fields

- Role: Anonymous; difficulty: 1/5; fixture: base.
- Target: `/accounts/register/patient/`; expected HTTP 200; final: `/accounts/register/patient/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Confirm password.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-005 â€” Staff application fields

- Role: Anonymous; difficulty: 1/5; fixture: base.
- Target: `/accounts/register/staff/`; expected HTTP 200; final: `/accounts/register/staff/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Requested staff role.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-006 â€” Administrator dashboard

- Role: Administrator; difficulty: 1/5; fixture: base.
- Target: `/app/dashboard/`; expected HTTP 200; final: `/app/dashboard/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Dashboard.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-007 â€” Physician worklist

- Role: Physician; difficulty: 1/5; fixture: base.
- Target: `/app/physician/`; expected HTTP 200; final: `/app/physician/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Physician worklist.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-008 â€” Nursing workspace

- Role: Nurse; difficulty: 1/5; fixture: base.
- Target: `/app/nursing/`; expected HTTP 200; final: `/app/nursing/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Nursing workspace.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-009 â€” Laboratory worklist

- Role: Lab Staff; difficulty: 1/5; fixture: base.
- Target: `/app/lab/workspace/`; expected HTTP 200; final: `/app/lab/workspace/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Laboratory.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-010 â€” Pharmacy worklist

- Role: Pharmacist; difficulty: 1/5; fixture: base.
- Target: `/app/pharmacy/`; expected HTTP 200; final: `/app/pharmacy/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Pharmacy Workspace.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-011 â€” Patient directory

- Role: FrontDesk; difficulty: 2/5; fixture: base.
- Target: `/app/patients/`; expected HTTP 200; final: `/app/patients/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: LAB-01.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-012 â€” Patient demographics

- Role: FrontDesk; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/`; expected HTTP 200; final: `/app/patients/1/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: LAB-01.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-013 â€” Appointment calendar

- Role: FrontDesk; difficulty: 2/5; fixture: base.
- Target: `/app/schedule/`; expected HTTP 200; final: `/app/schedule/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Synthetic benchmark.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-014 â€” Check-in worklist

- Role: FrontDesk; difficulty: 2/5; fixture: base.
- Target: `/app/check-in/`; expected HTTP 200; final: `/app/check-in/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Synthetic benchmark.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-015 â€” Appointment creation history

- Role: FrontDesk; difficulty: 2/5; fixture: base.
- Target: `/app/appointments/2/`; expected HTTP 200; final: `/app/appointments/2/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Appointment booked.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-016 â€” Longitudinal patient chart

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/chart/`; expected HTTP 200; final: `/app/patients/1/chart/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: LAB-01.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-017 â€” In-progress encounter

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/encounters/1/`; expected HTTP 200; final: `/app/patients/1/encounters/1/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: In progress.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-018 â€” Medical-history empty state

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/history/medical/`; expected HTTP 200; final: `/app/patients/1/history/medical/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Medical history.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-019 â€” Longitudinal problems

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/history/problems/`; expected HTTP 200; final: `/app/patients/1/history/problems/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Problems.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-020 â€” Allergy review status

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/history/allergies/`; expected HTTP 200; final: `/app/patients/1/history/allergies/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Not reviewed.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-021 â€” Medication history

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/history/medications/`; expected HTTP 200; final: `/app/patients/1/history/medications/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Medication history.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-022 â€” Encounter diagnoses

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/encounters/1/diagnoses/`; expected HTTP 200; final: `/app/patients/1/encounters/1/diagnoses/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Encounter diagnoses.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-023 â€” Appointment nursing context

- Role: Nurse; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/nursing/appointments/1/`; expected HTTP 200; final: `/app/patients/1/nursing/appointments/1/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: LAB-01.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-024 â€” Longitudinal flowsheet

- Role: Nurse; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/nursing/flowsheet/`; expected HTTP 200; final: `/app/patients/1/nursing/flowsheet/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: LAB-01.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-025 â€” Lab catalog

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/lab/catalog/`; expected HTTP 200; final: `/app/lab/catalog/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Demo chemistry.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-026 â€” Lab order history

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/lab-orders/`; expected HTTP 200; final: `/app/patients/1/lab-orders/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Demo chemistry.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-027 â€” Medication catalog

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/medications/catalog/`; expected HTTP 200; final: `/app/medications/catalog/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Synthetic Amber.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-028 â€” Signed medication history

- Role: Physician; difficulty: 2/5; fixture: base.
- Target: `/app/patients/1/medication-orders/`; expected HTTP 200; final: `/app/patients/1/medication-orders/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Synthetic Amber.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-029 â€” Billing worklist

- Role: BillingStaff; difficulty: 2/5; fixture: base.
- Target: `/app/billing/`; expected HTTP 200; final: `/app/billing/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Billing.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-030 â€” Claims queue

- Role: BillingStaff; difficulty: 2/5; fixture: base.
- Target: `/app/billing/claims/`; expected HTTP 200; final: `/app/billing/claims/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Claims.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-031 â€” Radiology worklist

- Role: RadiologyStaff; difficulty: 2/5; fixture: base.
- Target: `/app/radiology/`; expected HTTP 200; final: `/app/radiology/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Radiology.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-032 â€” Imaging catalog

- Role: Administrator; difficulty: 2/5; fixture: base.
- Target: `/app/imaging/catalog/`; expected HTTP 200; final: `/app/imaging/catalog/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Imaging.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-033 â€” Inpatient dashboard

- Role: HospitalOperations; difficulty: 2/5; fixture: base.
- Target: `/app/inpatient/`; expected HTTP 200; final: `/app/inpatient/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Inpatient.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-034 â€” Capacity dashboard

- Role: HospitalOperations; difficulty: 2/5; fixture: base.
- Target: `/app/inpatient/capacity/`; expected HTTP 200; final: `/app/inpatient/capacity/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Capacity.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-035 â€” Emergency tracking board

- Role: Nurse; difficulty: 2/5; fixture: base.
- Target: `/app/ed/`; expected HTTP 200; final: `/app/ed/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Emergency.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-036 â€” Anonymous staff redirect

- Role: Anonymous; difficulty: 3/5; fixture: base.
- Target: `/app/patients/`; expected HTTP 302; final: `/login/?next=/app/patients/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-037 â€” Anonymous patient redirect

- Role: Anonymous; difficulty: 3/5; fixture: base.
- Target: `/portal/`; expected HTTP 302; final: `/portal/login/?next=/portal/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-038 â€” Patient denied directory

- Role: Patient; difficulty: 3/5; fixture: base.
- Target: `/app/patients/`; expected HTTP 403; final: `/app/patients/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-039 â€” Patient denied staff approval

- Role: Patient; difficulty: 3/5; fixture: base.
- Target: `/app/accounts/applications/`; expected HTTP 403; final: `/app/accounts/applications/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-040 â€” Patient denied nursing

- Role: Patient; difficulty: 3/5; fixture: base.
- Target: `/app/nursing/`; expected HTTP 403; final: `/app/nursing/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-041 â€” Patient denied pharmacy

- Role: Patient; difficulty: 3/5; fixture: base.
- Target: `/app/pharmacy/`; expected HTTP 403; final: `/app/pharmacy/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-042 â€” Physician denied registration

- Role: Physician; difficulty: 3/5; fixture: base.
- Target: `/app/patients/new/`; expected HTTP 403; final: `/app/patients/new/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-043 â€” Physician denied demographics edit

- Role: Physician; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/edit/`; expected HTTP 403; final: `/app/patients/1/edit/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-044 â€” Physician denied account approval

- Role: Physician; difficulty: 3/5; fixture: base.
- Target: `/app/accounts/applications/`; expected HTTP 403; final: `/app/accounts/applications/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-045 â€” FrontDesk denied chart

- Role: FrontDesk; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/chart/`; expected HTTP 403; final: `/app/patients/1/chart/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-046 â€” FrontDesk denied SOAP

- Role: FrontDesk; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/encounters/1/`; expected HTTP 403; final: `/app/patients/1/encounters/1/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-047 â€” FrontDesk denied history

- Role: FrontDesk; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/history/medical/`; expected HTTP 403; final: `/app/patients/1/history/medical/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-048 â€” Nurse denied SOAP authoring

- Role: Nurse; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/encounters/1/note/`; expected HTTP 403; final: `/app/patients/1/encounters/1/note/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-049 â€” Nurse denied patient creation

- Role: Nurse; difficulty: 3/5; fixture: base.
- Target: `/app/patients/new/`; expected HTTP 403; final: `/app/patients/new/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-050 â€” Lab denied demographics

- Role: Lab Staff; difficulty: 3/5; fixture: base.
- Target: `/app/patients/`; expected HTTP 403; final: `/app/patients/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-051 â€” Lab denied physician worklist

- Role: Lab Staff; difficulty: 3/5; fixture: base.
- Target: `/app/physician/`; expected HTTP 403; final: `/app/physician/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-052 â€” Pharmacist denied chart

- Role: Pharmacist; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/chart/`; expected HTTP 403; final: `/app/patients/1/chart/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-053 â€” Pharmacist denied demographics edit

- Role: Pharmacist; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/edit/`; expected HTTP 403; final: `/app/patients/1/edit/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-054 â€” Billing denied ED

- Role: BillingStaff; difficulty: 3/5; fixture: base.
- Target: `/app/ed/`; expected HTTP 403; final: `/app/ed/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-055 â€” Billing denied inpatient

- Role: BillingStaff; difficulty: 3/5; fixture: base.
- Target: `/app/inpatient/`; expected HTTP 403; final: `/app/inpatient/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-056 â€” Radiology denied SOAP

- Role: RadiologyStaff; difficulty: 3/5; fixture: base.
- Target: `/app/patients/1/encounters/1/`; expected HTTP 403; final: `/app/patients/1/encounters/1/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-057 â€” HospitalOperations denied approval

- Role: HospitalOperations; difficulty: 3/5; fixture: base.
- Target: `/app/accounts/applications/`; expected HTTP 403; final: `/app/accounts/applications/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-058 â€” Physician denied unrelated chart

- Role: Physician; difficulty: 3/5; fixture: base.
- Target: `/app/patients/2/chart/`; expected HTTP 404; final: `/app/patients/2/chart/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-059 â€” Mismatched patient encounter denied

- Role: Physician; difficulty: 3/5; fixture: base.
- Target: `/app/patients/2/encounters/1/`; expected HTTP 404; final: `/app/patients/2/encounters/1/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-060 â€” Unclaimed pharmacy details denied

- Role: Pharmacist; difficulty: 3/5; fixture: base.
- Target: `/app/pharmacy/orders/{meduuid}/`; expected HTTP 404; final: `/app/pharmacy/orders/{meduuid}/`.
- Task: Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: LAB-01, LAB-02, Synthetic protected.

## CF-061 â€” Own patient dashboard

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/`; expected HTTP 200; final: `/portal/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Patient dashboard.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-062 â€” Own appointments

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/appointments/`; expected HTTP 200; final: `/portal/appointments/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Appointments.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-063 â€” Own visits

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/visits/`; expected HTTP 200; final: `/portal/visits/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Visits.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-064 â€” Own medications

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/medications/`; expected HTTP 200; final: `/portal/medications/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Medications.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-065 â€” Released-results empty state

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/results/`; expected HTTP 200; final: `/portal/results/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Results.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-066 â€” Own messages

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/messages/`; expected HTTP 200; final: `/portal/messages/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Messages.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-067 â€” Own appointment requests

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/requests/`; expected HTTP 200; final: `/portal/requests/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: requests.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-068 â€” Own billing statements

- Role: Patient; difficulty: 2/5; fixture: base.
- Target: `/portal/billing/`; expected HTTP 200; final: `/portal/billing/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: Billing.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-069 â€” Owner cannot see unreleased lab result

- Role: Patient; difficulty: 3/5; fixture: base.
- Target: `/portal/results/1/`; expected HTTP 404; final: `/portal/results/1/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: demo-U, LAB-02.

## CF-070 â€” Other patient cannot see lab result

- Role: OtherPatient; difficulty: 3/5; fixture: base.
- Target: `/portal/results/1/`; expected HTTP 404; final: `/portal/results/1/`.
- Task: Open the requested route, observe its content and report whether access is allowed.
- Visible result: specified denial or validation state.
- Database assertions: `[]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: demo-U, LAB-01.

## CF-071 â€” Register synthetic patient

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/patients/new/`; expected HTTP 200; final: `/app/patients/3/`.
- Task: Register MRN SYN-BENCH-NEW, first name Synthetic, last name Benchmark, DOB 1990-01-15, sex Unknown. Explicitly confirm synthetic data and save.
- Visible result: SYN-BENCH-NEW.
- Database assertions: `[["SELECT COUNT(*) FROM patients_patient WHERE mrn='SYN-BENCH-NEW'", 1], ["SELECT COUNT(*) FROM patients_auditevent WHERE action='patient_create'", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-072 â€” Required synthetic confirmation

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/patients/new/`; expected HTTP 200; final: `/app/patients/new/`.
- Task: Fill MRN SYN-BENCH-NEW, Synthetic Benchmark, DOB 1990-01-15, sex Unknown. Leave synthetic confirmation UNCHECKED, attempt Save patient and observe required-field blocking.
- Visible result: specified denial or validation state.
- Database assertions: `[["SELECT COUNT(*) FROM patients_patient", 2]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-073 â€” Duplicate MRN rejection

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/patients/new/`; expected HTTP 200; final: `/app/patients/new/`.
- Task: Attempt MRN LAB-01, Synthetic Benchmark, DOB 1990-01-15, sex Unknown. Confirm synthetic data and submit once. Observe the duplicate MRN error.
- Visible result: already.
- Database assertions: `[["SELECT COUNT(*) FROM patients_patient", 2]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-074 â€” Edit demographics and audit

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/edit/`; expected HTTP 200; final: `/app/patients/1/`.
- Task: Change the last name to Updated, confirm synthetic data and save.
- Visible result: Updated.
- Database assertions: `[["SELECT last_name FROM patients_patient WHERE id=1", "Updated"], ["SELECT COUNT(*) FROM patients_auditevent WHERE action='patient_update'", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-075 â€” Schedule and confirm appointment

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/appointments/new/`; expected HTTP 200; final: `/app/appointments/4/`.
- Task: Schedule Synthetic Lab (LAB-01) with its treating physician at {start}, default duration 30 minutes. Review then confirm.
- Visible result: Scheduled.
- Database assertions: `[["SELECT COUNT(*) FROM scheduling_appointment", 4], ["SELECT patient_id FROM scheduling_appointment WHERE id=4", 1], ["SELECT COUNT(*) FROM patients_auditevent WHERE action='appointment_create'", 2]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-076 â€” Check in and audit

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/appointments/2/`; expected HTTP 200; final: `/app/appointments/2/`.
- Task: Mark this appointment Arrived. Verify check-in actor and Patient checked in history.
- Visible result: Arrived.
- Database assertions: `[["SELECT status FROM scheduling_appointment WHERE id=2", "arrived"], ["SELECT COUNT(*) FROM patients_auditevent WHERE action='appointment_arrive'", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-077 â€” Reschedule same patient

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/appointments/2/edit/`; expected HTTP 200; final: `/app/appointments/2/`.
- Task: Change start time to {reschedule}, preserve patient and physician, review and confirm.
- Visible result: Scheduled.
- Database assertions: `[["SELECT version FROM scheduling_appointment WHERE id=2", 2], ["SELECT patient_id FROM scheduling_appointment WHERE id=2", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-078 â€” Cancel with retained reason

- Role: FrontDesk; difficulty: 4/5; fixture: base.
- Target: `/app/appointments/2/`; expected HTTP 200; final: `/app/appointments/2/`.
- Task: Cancel this appointment with reason Synthetic cancellation and verify Cancelled status.
- Visible result: Cancelled.
- Database assertions: `[["SELECT status FROM scheduling_appointment WHERE id=2", "cancelled"], ["SELECT COUNT(*) FROM patients_auditevent WHERE action='appointment_cancel'", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-079 â€” Create four-section SOAP

- Role: Physician; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/encounters/1/note/`; expected HTTP 200; final: `/app/patients/1/encounters/1/`.
- Task: Enter Synthetic benchmark plus each section name in Subjective, Objective, Assessment and Plan. Confirm synthetic data and save draft.
- Visible result: Synthetic benchmark.
- Database assertions: `[["SELECT COUNT(*) FROM clinical_note WHERE encounter_id=1 AND signed_at IS NULL", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-080 â€” Sign existing SOAP

- Role: Physician; difficulty: 4/5; fixture: note_draft.
- Target: `/app/patients/1/encounters/1/`; expected HTTP 200; final: `/app/patients/1/encounters/1/`.
- Task: Review and sign this draft after explicitly confirming all four sections. Verify signed read-only state.
- Visible result: Signed.
- Database assertions: `[["SELECT COUNT(*) FROM clinical_note WHERE encounter_id=1 AND signed_at IS NOT NULL", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-081 â€” Complete signed encounter

- Role: Physician; difficulty: 4/5; fixture: note_signed.
- Target: `/app/patients/1/encounters/1/`; expected HTTP 200; final: `/app/patients/1/encounters/1/`.
- Task: Complete this encounter; preserve its already signed SOAP.
- Visible result: Completed.
- Database assertions: `[["SELECT status FROM clinical_encounter WHERE id=1", "completed"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-082 â€” Past medical history

- Role: Physician; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/history/medical/new/`; expected HTTP 200; final: `/app/patients/1/history/medical/1/`.
- Task: Create record labelled Synthetic benchmark, category Past medical history. Select Source Documented, confirm synthetic data and save.
- Visible result: Synthetic benchmark.
- Database assertions: `[["SELECT COUNT(*) FROM history_medicalhistory WHERE patient_id=1", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-083 â€” Active longitudinal problem

- Role: Physician; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/history/problems/new/`; expected HTTP 200; final: `/app/patients/1/history/problems/1/`.
- Task: Create record labelled Synthetic benchmark, default Active status. Select Source Documented, confirm synthetic data and save.
- Visible result: Synthetic benchmark.
- Database assertions: `[["SELECT COUNT(*) FROM history_problem WHERE patient_id=1", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-084 â€” Document fictional allergy

- Role: Physician; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/history/allergies/new/`; expected HTTP 200; final: `/app/patients/1/history/allergies/1/`.
- Task: Create record labelled Synthetic benchmark, reaction Synthetic rash, severity Mild. Select Source Documented, confirm synthetic data and save.
- Visible result: Synthetic benchmark.
- Database assertions: `[["SELECT COUNT(*) FROM history_allergy WHERE patient_id=1", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-085 â€” Medication statement

- Role: Physician; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/history/medications/new/`; expected HTTP 200; final: `/app/patients/1/history/medications/1/`.
- Task: Create record labelled Synthetic benchmark, dose 1 demo unit, route oral, frequency daily. Select Source Documented, confirm synthetic data and save.
- Visible result: Synthetic benchmark.
- Database assertions: `[["SELECT COUNT(*) FROM history_medicationstatement WHERE patient_id=1", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-086 â€” Nursing assessment

- Role: Nurse; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/nursing/appointments/1/assessment/new/`; expected HTTP 200; final: `/app/patients/1/nursing/appointments/1/assessment/1/`.
- Task: Record complaint Synthetic benchmark, pain score 2, and ready for provider. Explicitly confirm synthetic information and save.
- Visible result: Synthetic benchmark.
- Database assertions: `[["SELECT COUNT(*) FROM nursing_roomingassessment WHERE ready_for_provider=1", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-087 â€” Vital-sign panel

- Role: Nurse; difficulty: 4/5; fixture: base.
- Target: `/app/patients/1/nursing/appointments/1/vitals/new/`; expected HTTP 200; final: `/app/patients/1/nursing/appointments/1/vitals/1/`.
- Task: Record fictional systolic 120, diastolic 80, heart rate 70, temperature 37.2 C, source Measured. Explicitly confirm synthetic information and save.
- Visible result: 120.
- Database assertions: `[["SELECT COUNT(*) FROM nursing_vitalobservation WHERE systolic=120 AND diastolic=80", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-088 â€” Approve pending staff application

- Role: Administrator; difficulty: 4/5; fixture: base.
- Target: `/app/accounts/applications/{pending}/`; expected HTTP 200; final: `/app/accounts/applications/`.
- Task: Approve benchmark-pending as Nurse with reason Synthetic benchmark review. Verify recorded decision.
- Visible result: approved.
- Database assertions: `[["SELECT status FROM accounts_enrollment WHERE user_id=(SELECT id FROM auth_user WHERE username='benchmark-pending')", "approved"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-089 â€” Reject pending staff application

- Role: Administrator; difficulty: 4/5; fixture: base.
- Target: `/app/accounts/applications/{pending}/`; expected HTTP 200; final: `/app/accounts/applications/`.
- Task: Reject benchmark-pending with reason Synthetic benchmark review. Verify recorded decision.
- Visible result: rejected.
- Database assertions: `[["SELECT status FROM accounts_enrollment WHERE user_id=(SELECT id FROM auth_user WHERE username='benchmark-pending')", "rejected"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-090 â€” Mismatched password confirmation

- Role: Anonymous; difficulty: 4/5; fixture: base.
- Target: `/accounts/register/patient/`; expected HTTP 200; final: `/accounts/register/patient/`.
- Task: Attempt username benchmark-new, Password QA_PASSWORD and Confirm password QA_WRONG_PASSWORD. Confirm synthetic data, submit once and observe mismatch rejection.
- Visible result: passwords do not match.
- Database assertions: `[["SELECT COUNT(*) FROM auth_user WHERE username='benchmark-new'", 0]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-091 â€” Claim signed requisition

- Role: Pharmacist; difficulty: 5/5; fixture: base.
- Target: `/app/pharmacy/`; expected HTTP 200; final: `/app/pharmacy/orders/{meduuid}/`.
- Task: Claim order for the one synthetic order. Use reason Synthetic benchmark claim. Explicitly confirm and verify the resulting workflow state.
- Visible result: Pharmacy Verification.
- Database assertions: `[["SELECT COUNT(*) FROM medications_pharmacyreview", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-092 â€” Request clarification

- Role: Pharmacist; difficulty: 5/5; fixture: pharmacy_claimed.
- Target: `/app/pharmacy/orders/{meduuid}/`; expected HTTP 200; final: `/app/pharmacy/orders/{meduuid}/`.
- Task: Request clarification for the one synthetic order. Use reason Synthetic benchmark clarification. Explicitly confirm and verify the resulting workflow state.
- Visible result: Clarification requested.
- Database assertions: `[["SELECT status FROM medications_pharmacyreview", "clarification"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-093 â€” Approve pharmacy verification

- Role: Pharmacist; difficulty: 5/5; fixture: pharmacy_claimed.
- Target: `/app/pharmacy/orders/{meduuid}/`; expected HTTP 200; final: `/app/pharmacy/orders/{meduuid}/`.
- Task: Approve verification for the one synthetic order. Explicitly confirm and verify the resulting workflow state.
- Visible result: Approved.
- Database assertions: `[["SELECT status FROM medications_pharmacyreview", "approved"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-094 â€” Record simulated dispensing

- Role: Pharmacist; difficulty: 5/5; fixture: pharmacy_approved.
- Target: `/app/pharmacy/orders/{meduuid}/`; expected HTTP 200; final: `/app/pharmacy/orders/{meduuid}/`.
- Task: Record simulated dispensing for the one synthetic order. Use quantity 2. Explicitly confirm and verify the resulting workflow state.
- Visible result: Simulated dispensing recorded.
- Database assertions: `[["SELECT COUNT(*) FROM medications_pharmacydispenseevent", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-095 â€” Claim lab requisition

- Role: Lab Staff; difficulty: 5/5; fixture: base.
- Target: `/app/lab/workspace/`; expected HTTP 200; final: `/app/lab/processing/{labuuid}/`.
- Task: Claim requisition. Use reason Synthetic benchmark claim. Confirm synthetic data and verify final state.
- Visible result: Synthetic.
- Database assertions: `[["SELECT COUNT(*) FROM labs_laborder WHERE assigned_lab_id IS NOT NULL", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-096 â€” Collect specimen with identity

- Role: Nurse; difficulty: 5/5; fixture: base.
- Target: `/app/lab/processing/{labuuid}/`; expected HTTP 200; final: `/app/lab/processing/{labuuid}/`.
- Task: Collect specimen. Use MRN LAB-01 and DOB 1980-01-01; explicitly confirm identity. Confirm synthetic data and verify final state.
- Visible result: Collected.
- Database assertions: `[["SELECT status FROM labs_labspecimen", "collected"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-097 â€” Publish prepared lab report

- Role: Lab Staff; difficulty: 5/5; fixture: lab_result.
- Target: `/app/lab/processing/{labuuid}/`; expected HTTP 200; final: `/app/lab/processing/{labuuid}/`.
- Task: Preview and finalize. Review the draft and explicitly confirm publication. Confirm synthetic data and verify final state.
- Visible result: Fulfilled.
- Database assertions: `[["SELECT status FROM labs_labresult", "final"], ["SELECT status FROM labs_laborder", "fulfilled"]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-098 â€” Acknowledge exact lab revision

- Role: Physician; difficulty: 5/5; fixture: lab_published.
- Target: `/app/lab/reports/{labuuid}/`; expected HTTP 200; final: `/app/lab/reports/{labuuid}/`.
- Task: Review and acknowledge the current synthetic laboratory publication. Verify it is acknowledged.
- Visible result: acknowledged.
- Database assertions: `[["SELECT COUNT(*) FROM labs_labresultreview", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-099 â€” Compose and sign SOAP journey

- Role: Physician; difficulty: 5/5; fixture: base.
- Target: `/app/patients/1/encounters/1/note/`; expected HTTP 200; final: `/app/patients/1/encounters/1/`.
- Task: Fill all four SOAP sections with Synthetic benchmark plus section name, confirm synthetic data, save draft, review and explicitly sign.
- Visible result: Signed.
- Database assertions: `[["SELECT COUNT(*) FROM clinical_note WHERE encounter_id=1 AND signed_at IS NOT NULL", 1]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.

## CF-100 â€” Schedule and check-in journey

- Role: FrontDesk; difficulty: 5/5; fixture: base.
- Target: `/app/appointments/new/`; expected HTTP 200; final: `/app/appointments/4/`.
- Task: Schedule Synthetic Lab (LAB-01) with its treating physician at {start}, review and confirm, then mark the new appointment Arrived. Verify matching patient and booking then check-in history.
- Visible result: Arrived.
- Database assertions: `[["SELECT status FROM scheduling_appointment WHERE id=4", "arrived"], ["SELECT patient_id FROM scheduling_appointment WHERE id=4", 1], ["SELECT COUNT(*) FROM scheduling_appointmentevent WHERE appointment_id=4", 2]]`; read-only tasks preserve all business tables.
- Forbidden denied-page text: not applicable.
