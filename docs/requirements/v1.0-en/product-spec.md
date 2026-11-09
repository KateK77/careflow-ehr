# CareFlow EHR — Complete Epic-inspired product specification v1.0

English translation revision 1.0.0, dated 2026-11-07. Source baseline v1.0, dated 2026-11-06. [Chinese source](../v1.0/product-spec.md) · [Translation registry](README.md).

This translation preserves the original requirements, section numbers, screen and workflow identifiers, literal API paths, and proposed architecture. Current implementation decisions, including retaining Django, are recorded separately in [ADR 0001](../../decisions/0001-retain-django.md) and [ADR 0002](../../decisions/0002-patient-management-access.md). Source inconsistencies remain visible and require an explicit decision before implementation.

> Purpose — Independently build an original educational and demonstration EHR inspired by common Epic workflows. The project is independent of Epic and carries no guarantee of interface compatibility.
>
> Data boundary — Use synthetic or fictional patients only. Every screen must show DEMO / NOT FOR CLINICAL USE. The system must not be used for actual care, prescribing, medication administration, billing, or processing patient private information.
>
> Reference basis — Epic's public product catalog and specialty, inpatient, patient-experience, scheduling, interoperability and AI materials, plus public institutional training overviews. Screens and enabled modules vary by hospital. These requirements describe development goals and provide no internal pixel-level or field-level Epic specification.

## 0. Overall objective and definition of success

Build an interactive browser-based full-stack EHR for outpatient and inpatient physicians, nurses, reception and scheduling staff, pharmacists, laboratory staff, radiology staff, billing staff, system administrators and patients. One patient record must connect appointment → registration → encounter → diagnosis → note → order → laboratory result → follow-up/discharge → patient portal. Each action must update the actual database, operational state and relevant staff task queues. Static pages and nonfunctional buttons do not satisfy acceptance.

### Principles

1. Clinical records are central. Organize the system around Patient, Encounter and a longitudinal timeline.
2. Give each role access to its authorized workspace, with frontend and backend authorization.
3. Track state, time and actor for orders, notes, tests, appointments and medication actions.
4. Preload synthetic patients, staff, encounters, tests, prescriptions, messages and bills. All critical paths must be interactive.
5. Use the CareFlow EHR name and original branding and layouts. Do not appropriate Epic or MyChart logos, trademarks, screenshots or CSS, or claim affiliation.
6. Complete workflows before expanding breadth. Begin with outpatient care and connect later modules to the same data model.
7. Restrict the project to demonstration use. Prohibit real electronic prescribing, insurance transactions, result interfaces and PHI. Label AI clinical suggestions as drafts requiring human confirmation.

## 1. System modules

### 1.1 P0 — Platform foundation

- Login, logout, demo accounts, role switching with administrator simulation, user profiles, organizations, facilities, departments and rooms.
- Administrator, Physician, Nurse, FrontDesk, Pharmacist, LabTech, Radiologist, BillingStaff and Patient roles. Users may hold multiple roles.
- Global patient search by name, MRN, date of birth or phone, patient creation, possible-duplicate warnings and operation auditing.
- Global search, notifications, task counts, quick actions, favorite patients and recently opened patients.

### 1.2 Outpatient care — EpicCare Ambulatory-style workflows

- Physician schedules with day/week views and physician/department filters. Appointment states include scheduled/arrived/roomed/in-progress/completed/cancelled/no-show.
- Registration/check-in with demographics, contact phone, emergency contacts, mock insurance, demonstration consent checkboxes, arrival and triage.
- Rooming with chief complaint, vitals, allergies, current medication, history, screening questionnaires and a ready-for-provider marker.
- Visit Navigator with stepwise history, problem/allergy/medication review, SOAP or H&P notes, linked diagnoses, orders, patient instructions and visit completion.
- Separate the longitudinal problem list from encounter diagnoses. Provide searchable mock ICD-10/SNOMED catalogs, status, start/end dates and comments.
- Clinical notes support creation, autosave, drafts, revision, signing and signed addenda, with HPI, ROS, Exam, Assessment and Plan templates.
- Independently implement dot phrases such as `.followup`, patient/latest-vitals interpolation, selectable content fragments and common order sets. Do not copy Epic proprietary configuration.
- After Visit Summary (AVS) includes diagnoses, medications, tests, follow-up and personalized instructions, with print preview and portal synchronization.

### 1.3 Longitudinal patient record / Chart Review

- Patient Snapshot with avatar placeholder/name, MRN, DOB/age, sex, current encounter, allergies, nursing alerts, problems, medication, history and recent vitals.
- Chart Review tabs include Overview, Timeline, Encounters, Notes, Problems, Allergies, Medications, Labs, Imaging, Procedures, Immunizations, Documents and Care Plans.
- Timeline filters by event type/date, groups by date and opens detail drawers. Each record shows author, time, encounter, source and signature state.
- Laboratory values support lists, trends, reference ranges and high/low flags, preserving units and specimen/collection times.
- Medication reconciliation distinguishes active, historical/discontinued and patient-reported use, recording reviewer, time and status. It does not dispense prescriptions.
- Allergy records include substance, reaction, severity, notes, recorder and review status. Distinguish unknown allergy status from an explicit statement of no known allergies.

### 1.4 Clinical orders

- Categories include Laboratory, Imaging, simulated Medication, Procedure, Referral, Nursing and Other.
- Composer flow is catalog search → selection → diagnosis association → priority/time/details → preview → submission.
- Order states follow draft → signed → queued → in-progress → completed, with cancelled/rejected/failed branches and visible history.
- Order sets propose several orders for a clinical context. Users must review and may edit/remove individual items before confirming submission.
- Simulated medication orders include drug, dosage form, strength, dose, route, frequency, duration, quantity, mock pharmacy and instructions. Include illustrative warnings and require physician signature.
- Track all orders with type, priority, status and patient filters, order details and linked results.
- Prohibit connections to real pharmacies and issuance of real prescriptions.

### 1.5 Laboratory — Beaker-style workflows

- Work queue follows ordered → awaiting collection → collected → received → processing → awaiting verification → released/cancelled.
- Track specimen type, simulated barcode, collection/receipt/processing times, collector and rejection reason.
- Enter analyte value, unit, reference interval, abnormal flag and comments. Support multi-analyte panels such as CBC, BMP and HbA1c.
- Simulated verification and release make results immediately visible in physician Chart Review/Inbox. Abnormal results enter the alert queue.
- Do not infer treatment advice. Critical values serve as visual-alert test cases only.

### 1.6 Radiology — Radiant-style workflows

- Imaging worklist follows unscheduled, scheduled, checked in, examination in progress, awaiting report and final report.
- Store modality (X-ray/CT/MRI/US), body site, contrast flag without dose recommendations, scheduled time and examination status.
- Reports include Findings, Impression, reporting physician and signature time. Use demonstration image placeholders, with no requirement for a real DICOM system.
- Physicians can review imaging reports, result history and status from the chart.

### 1.7 Inpatient care — EpicCare Inpatient-style workflows

- Admission/discharge/transfer supports admission requests, admission, ward/bed allocation, departmental or bed transfers, discharge and visual bed capacity.
- Lists can be sorted by department, ward and attending physician, showing length of stay (LOS), diagnoses, tasks and alerts.
- The inpatient summary includes days hospitalized, care team, vital trends, active orders, intake/output, care plan, progress notes and results.
- Rounding checklists cover daily tasks, unsigned orders, results, consultations and discharge planning.
- Discharge requires diagnoses, instructions, simulated medication list, follow-up and discharge summary. Close the encounter after required items are complete.

### 1.8 Nursing and MAR

- Nurse Worklist includes beds, daily tasks, vitals to collect, orders to acknowledge, medication plans and handoff tasks.
- Nursing assessments cover pain, fall risk, mental status, temperature, pulse, respiratory rate, blood pressure, oxygen saturation, height/weight, symptoms and notes.
- Flowsheets use metric rows and time columns with edits, comments and individual trends, preserving units and recorder.
- The simulated Medication Administration Record includes planned timelines and events with Scheduled/Given/Held/Refused/Missed states. Actions require actor, time, reason and immutable audit.
- Care plans include goals, interventions, owner and progress. Handoffs use SBAR (Situation/Background/Assessment/Recommendation).
- Clearly mark high-risk medication scenarios as simulations. Do not initiate actual administration or barcode administration.

### 1.9 Emergency care — ASAP-style workflows

- ED Tracking Board follows Waiting → Triage → Roomed → Provider → Observation → Discharged/Admitted, showing acuity, wait, bed and responsible physician.
- Triage records arrival mode, chief complaint, acuity, initial vitals, principal risk flags and follow-up actions.
- Support ED notes, test orders, result observation, discharge/admit/transfer disposition and transition history.
- Provide sorting, filtering, refresh and aggregate counts, without real emergency medical decision algorithms.

### 1.10 Pharmacy — Willow-style workflows

- Simulated medication verification queue includes awaiting review, verified, clarification needed, rejected and cancelled.
- Show drug, form, strength, route, quantity, proposed administration time, allergy alerts and ordering physician.
- Preserve review comments and synchronize state with physician orders and MAR, including simulated inventory/dispensing status.
- Demonstrate order workflows without connecting to actual prescribing, pharmacy inventory or controlled-substance networks.

### 1.11 In Basket / collaborative messages

- Task categories include Patient Message, Result Notification, simulated Refill Request, Referral, Staff Message, Cosign and Chart Completion.
- Inbox/Assigned/Sent/Completed/Archived folders support search, filters, priority, unread state and assignment.
- Threads include sender, linked patient/encounter, contextual summary, attachment placeholders, reply templates and task completion.
- Abnormal-result notifications link to the chart and support marking results reviewed.

### 1.12 Patient portal — original name required

- Patients access only their linked records, with login, profile and notification settings.
- Dashboard shows upcoming appointments, recent results, medications, unread messages, outstanding fees and questionnaires.
- Appointments show available slots and support booking, cancellation and rescheduling, instructions and simulated telehealth link placeholders.
- Results appear chronologically. Abnormal-value explanations must not substitute for professional interpretation.
- Patients may send demonstration nonurgent messages to the care team. Avoid presenting messaging as an emergency channel.
- Show current/historical medications and accept simulated refill requests.
- Show bills and simulated payment outcomes without a payment gateway.
- Include AVS/forms, with proxy access deferred.

### 1.13 Front desk, finance and revenue cycle — Cadence/Resolute-style workflows

- Registration covers demographics, simulated coverage, emergency contacts, guarantor and eligibility-check placeholders.
- Scheduling provides physician/room/date grids, creation/rescheduling/cancellation/waitlists and conflict detection.
- Patient flow covers awaiting check-in, checked in, triaged, in progress, complete and no-show.
- Billing covers encounter items, simulated charge codes, charge items, invoices, mock claim status and simulated payment transactions.
- Do not transmit claims to insurers or collect actual payments.

### 1.14 Population health / analytics — Healthy Planet/SlicerDicer-style workflows

- Cohort Builder filters anonymous synthetic populations by age range, date, diagnosis, medication, lab results and follow-up timeliness.
- Dashboards show patient counts, today's arrivals/no-shows, unfinished orders, abnormal results, discharges and module metrics.
- Care Gaps represents simulated incomplete screenings or appointments and may create outreach tasks. Demonstration rules must not be used as medical advice.
- Support synthetic-only CSV export, date filters, bar/line charts and role authorization.

### 1.15 Healthcare interoperability — FHIR-inspired

- Use a unified internal model with export mapping toward FHIR R4 Patient, Encounter, Observation, Condition, AllergyIntolerance, MedicationRequest, DiagnosticReport, Appointment, Practitioner and DocumentReference.
- Initially provide internal REST APIs. Later add read-only demonstration routes such as `/fhir/Patient/{id}`, mappings and JSON validation.
- Care Everywhere denotes cross-organization exchange. Do not claim actual Epic Care Everywhere connectivity or certification.

### 1.16 AI clinical assistance — independently implemented Epic Art-inspired categories

- AI Chart Summary produces patient-history/order/recent-result summaries with source links and no invented history.
- AI Note Draft uses explicitly supplied simulated visit text to draft SOAP for physician review, editing and signature.
- Inbox Reply Draft prepares replies and never sends them automatically.
- Clinical Timeline Q&A retrieves synthetic records, cites answers and states when evidence is missing.
- Explain Result explains test terminology without diagnosis or treatment advice.
- Label outputs AI-generated draft, show citations and request confirmation. Do not upload actual patient information to cloud services.

### 1.17 Later specialty extensions — excluded from first delivery

- Oncology covers staging and regimen/cycle tracking without actual chemotherapy-dose recommendations.
- Surgery/Anesthesia covers scheduling, preoperative checklists, intraoperative events and recovery notes.
- Cardiology covers ECG tests and structured echocardiography reports.
- Obstetrics covers prenatal visits, maternal/newborn associations and delivery events.
- Add Dermatology, Dentistry, Ophthalmology, Orthopedics, Nephrology, Endoscopy and Transplant as specialty workspaces through a plugin approach.

## 2. Detailed original interface design

### 2.1 Design system

- Desktop-first clinical UI targets 1440×900, supports 1280-pixel width and collapses the sidebar on tablets. The patient portal is mobile-first.
- Use light neutral backgrounds, clear grids, low-saturation blue/teal accents, gray table borders and consistent typography, with original icons and artwork.
- Global Header is approximately 56 pixels high with logo, organization, role, search, notifications, tasks, profile menu and DEMO badge.
- App Navigation is approximately 210–230 pixels wide, collapsible and role-dependent.
- Patient pages have a 250–280-pixel summary/storyboard, flexible workspace and expandable 320-pixel context drawer.
- Workspace headers show identity, MRN, age, allergy/safety flags, encounter, clinical state and tabs. Fixed bottom actions include Save Draft, Sign and Complete according to permissions.
- Controls include Table, DataGrid, Tabs, Search ComboBox, DatePicker, Status Tag, Inline Editor, Modal, Drawer, Toast, Validation Errors, Command Palette, Confirm Dialog, Skeleton and Empty State.
- State colors include gray draft, blue in-progress, green complete, amber warning and red critical result, with textual labels alongside color.
- Tables support sorting/filtering/pagination. Saving state must be clear and signing requires confirmation. Provide keyboard access, labels/ARIA, visible focus and browser-zoom support.
- Clinical workspaces keep patient context readily accessible.

### 2.2 Global layout illustration

Original conceptual layout reproduced from the source.

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ CareFlow EHR  [Organization] [Global Search]     [Alerts 3] [Inbox 8] [Dr. Demo] │
├──────────────┬─────────────────────────────────────────────────────────────────────┤
│ Home         │ Patient: Sarah Johnson | MRN D-1001 | Visit: In Progress           │
│ Schedule     ├───────────────────┬─────────────────────────────────────────────────┤
│ Patients     │ Story Panel       │ Workspace Tabs: Summary / Chart / Notes / ...   │
│ Inbox        │ Age / DOB / MRN   │ ┌─────────────────────────────────────────────┐ │
│ Orders       │ Allergies         │ │ Main lists, forms, trends, note editor     │ │
│ Lab          │ Active Problems   │ │                                             │ │
│ Radiology    │ Current Meds      │ │                                             │ │
│ ED           │ Latest Vitals     │ │                                             │ │
│ Inpatient    │ Alerts & CareTeam │ └─────────────────────────────────────────────┘ │
│ Analytics    │                   │ [Save Draft]   [Review]   [Sign]  [Close Visit]│
├──────────────┴───────────────────┴─────────────────────────────────────────────────┤
│ DEMO ONLY • Synthetic patient data • Not for clinical use                         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Screen elements and actions — S01–S27

#### S01 Login / role selection `/login`

- Left side shows product information and the demo statement. Right side provides Email, Password and Sign In, plus sample-account selection for development seeds only.
- Login opens the appropriate role workspace. Show generic errors and audit failures. Never display production credentials.

#### S02 Physician Dashboard `/app/dashboard`

- KPIs include Today's Appointments, Patients Waiting, Unsigned Notes, Unreviewed Results and Inbox Count.
- Today's Schedule table shows time, patient, age, visit type, status, room and Open Chart.
- Action Center includes simulated Urgent Results, Open Tasks, Recent Charts and Quick Create Note.
- Rows open the correct patient encounter, and KPIs open corresponding filtered pages.

#### S03 Patient search `/app/patients`

- Include name/MRN/DOB search, advanced filters, New Patient and a patient list.
- Columns include MRN, Name, DOB, Age, Sex, Last Encounter, Primary Doctor and Actions.
- Open patients in S06 and registration in S04. An exact duplicate MRN must produce an error.

#### S04 Patient registration/editing `/app/patients/new`, `/app/patients/:id/edit`

- Stepper includes Identity, Contact, Emergency Contact, mock Coverage and Review.
- Require name, DOB, sex/gender record, contact information according to an optional-field policy, and demonstration MRN, which may be generated.
- Reject future DOBs and warn about likely duplicates. Save opens the snapshot, and edits record actor/time.

#### S05 Schedule `/app/schedule`

- Provide Day/Week, date picker, provider, department and visit-type filters, plus New Appointment.
- The time grid spans 08:00–18:00 vertically and rooms/providers horizontally. Blocks show patient, state and time.
- Appointment dialogs collect patient, provider, slot, duration, type and reason. Block conflicts and support reschedule/cancel/check-in.

#### S06 Patient Snapshot `/app/patients/:id/summary`

- Identity header and story cards show allergies, conditions, medications, vitals, care team and warnings.
- Main cards include Recent Encounters, Clinical Timeline, Latest Labs, Active Orders, Care Gaps and Care Team.
- View All actions open corresponding tabs. Missing records show No data.

#### S07 Chart Review `/app/patients/:id/chart`

- Tabs include Overview, Encounters, Notes, Problems, Allergies, Medications, Results, Imaging, Documents and Immunizations.
- Filters include time range, type, provider and status. Show timeline/table in the center and a detail panel on row selection.
- Laboratory results add trends, reference interval, units and critical flags, with date-filtered simulated CSV export.

#### S08 Encounter / Visit Navigator `/app/encounters/:id`

- Steps include Rooming, Chief Complaint, History, Problems, Medication Reconciliation, Allergy Review, Vitals, Review of Systems, Physical Exam, Diagnoses, Orders, Notes, Instructions and Wrap-up.
- Each has Not Started/In Progress/Complete status and an editor. Actions include Next, Previous, Save Draft and Complete Encounter.
- Completion checks at least one diagnosis, required note signatures or an explicit incomplete warning, and unsigned-order warnings. Do not silently complete missing work.

#### S09 Rooming & Vitals `/app/encounters/:id/rooming`

- Show patient/appointment context and chief complaint, systolic/diastolic BP, pulse, respiratory rate, temperature, SpO2, height, weight, pain and time.
- Show prior vitals/trends and preserve the source of entries and amendments.
- Allergy/medication review records reviewer/time and updates completion state.

#### S10 Note Editor `/app/encounters/:id/notes/new`, `.../notes/:noteId`

- Header includes SOAP/H&P/Progress/Discharge type, author, draft status, save indicator and template picker.
- Fields include Chief Complaint, HPI, ROS, History, Exam, Assessment, Plan and Follow-up, with a free-text alternative.
- Support templates, dot-phrase autocomplete, latest-vitals insertion, preview, autosave, draft save and confirmed signing.
- Preserve signed text, addenda, signature time and version. Later AI drafts require sources and review.

#### S11 Diagnoses & Problem List `/app/patients/:id/problems`

- Separate Longitudinal Problems and Visit Diagnoses tabs with searchable mock ICD-10/SNOMED entries.
- Show code, description, onset, status, priority, linked encounter and author, with a resolved action.
- Adding a visit diagnosis must not automatically force a longitudinal problem or vice versa.

#### S12 Medications & Allergies `/app/patients/:id/medications`, `/allergies`

- Medication views separate Active, Historical and Patient-reported, showing name, sig, route, frequency, start/end, status and reconciliation.
- Allergies show substance, reaction, severity, recording time and verification, with explicit Unknown/None documented states.
- Support Add/Edit/Discontinue/Mark Reviewed without external pharmacy synchronization.

#### S13 Order Composer `/app/encounters/:id/orders/new`

- Provide category/catalog search at left, central results and an order-detail drawer on selection.
- Details include type, name/code, priority, requested date, indication and ordering provider. Medication adds route/dose/frequency/quantity/simulated pharmacy.
- Add to Draft Queue → Review Queue → Sign/Submit, with remove/edit/cancel. Validate patient and encounter association before signing.
- Show allergy context and demonstration duplicate-order warnings with expandable explanations.

#### S14 Active Orders `/app/patients/:id/orders`

- All/Labs/Medications/Imaging/Referrals tabs, with status/time/provider filters.
- Show order number, type, display, creation time, priority, status, owner and details. Open event history and permit authorized cancellation/acknowledgment.

#### S15 Lab Workbench `/app/lab`

- Left state counts, central worklist and right specimen details/result entry.
- Worklist fields include Specimen ID, Patient, Tests, Collection Time, Priority and Status.
- Results contain analyte, value, unit, range and flag. Draft, verify and release to Chart Review and Inbox.

#### S16 Results Review `/app/results`

- My Patients/Unreviewed/Abnormal/All queues show patient, order, time, value and flag.
- Show detail/trends with Mark Reviewed, Open Chart and Message Team, persisting reviewer/time.

#### S17 Radiology Worklist `/app/radiology`

- Show examination queue, scheduling, modality, patient and state. Details include examination metadata, demo image/file placeholders, Findings and Impression.
- Final signing publishes a draft report to the chart and physician Inbox.

#### S18 Inpatient Patient List `/app/inpatient`

- Ward filter and bed table/list with Bed, Patient, Admitted, LOS, Attending, Primary Diagnosis and Open Tasks.
- Admit, Assign/Move Bed, Transfer, Open Chart and Start Discharge. Selecting a bed shows occupancy.

#### S19 Nurse Worklist & Flowsheets `/app/nursing`

- Assigned Patients, Assessments, Flowsheets, Care Plans and Handoff tabs.
- Grid has measurement rows and time columns with editable values, added time points and recording details.
- Assessments include Vitals, Pain, Fall Risk, Neuro, Skin, I/O and Notes. Saving updates the longitudinal timeline.

#### S20 MAR `/app/mar`

- Filter by unit, patient and Due Now/Next 4 Hours/All. Rows represent medication, columns time.
- Cells represent simulated scheduled events with Scheduled/Recorded Given/Held/Refused/Missed states.
- Dialogs collect action, actual time, ordered dose shown read-only by default, reason and mock cosign. Preserve prior entries after saving.

#### S21 ED Tracking Board `/app/ed`

- Kanban/Table views show triage level, chief complaint, arrival, wait, room, assigned clinician and state.
- Group by state and support ED encounter creation, triage, room assignment and departure. Each transition updates history/counts.

#### S22 Pharmacy Verification Queue `/app/pharmacy`

- Show Patient, Medication, Dose, Route, Ordering Provider, Status and Allergy Alert, with simulation warnings/history in details.
- Verify/clarify/reject require actor/time/reason and synchronize order state. Exclude real dispensing.

#### S23 Inbox `/app/inbox`

- Three panes for folders/filters, message list and thread detail, with unread badge, priority and patient links.
- Open, mark read, draft reply, send internally, assign, complete and archive. Result notifications support Mark Reviewed.

#### S24 Patient Portal `/portal`

- Independent layout with Home, Appointments, Test Results, Messages, Medications, Bills and Visit Summaries.
- Home cards include Upcoming Appointment, Recent Results, Tasks and Messages. Never show another patient's records.
- Simulated bookings/messages must appear in staff Scheduling/Inbox.

#### S25 Billing & Registration `/app/billing`

- List Patient, Encounter, Charges, Amount, mock Insurance, Statement Status and Payment Status.
- Support itemized bills, simulated charges, statement generation, mock payments and demonstration receipts.

#### S26 Analytics `/app/analytics`

- KPIs, date filters, diagnosis/clinic cohorts, sortable results and trends use synthetic records only.
- Cards include Patients Served, Appointments, Pending Orders and Turnaround Time calculated from simulated events.

#### S27 Admin & Audit `/app/admin`

- Users/Roles, Clinic Setup, Catalog Setup, Note Templates, Audit Log and Demo Reset.
- Audit filters cover timestamp, actor, role, action, resource, resource ID, summary and outcome. Ordinary users cannot delete events.
- Include denied-access records and backend protection of administrator pages.

### 2.4 Shared interaction requirements

- Save validates and persists, shows success, updates updatedAt and survives refresh.
- Sign requires confirmation, author/time and preserved signed state, with later versions/addenda for changes.
- Search/filter uses server-side or controlled pagination, empty states and clear filters.
- Cancel requires an allowed state and reason, preserving audit.
- Clinical actions bind patientId and encounterId to prevent context mix-ups.
- Network failures offer Retry. Explain 403/404/409 as denied/not found/conflict and surface failures.
- Hide unauthorized UI operations and enforce authorization at every API.

## 3. Domain models, relationships and key fields

### 3.1 Identity and foundational resources

- `Organization(id,name)`, `Facility(id,organizationId,name)`, `Department(id,facilityId,name,type)`, `Room(id,departmentId,name)`, `Bed(id,roomId,label,status)`.
- `User(id,email,passwordHash,displayName,roles,status,departmentId)`, `Role(id,key)`, `UserRole(userId,roleId)`, `Practitioner(id,userId,credentials,specialty)`.
- `Patient(id,mrn,firstName,lastName,dob,sex,genderIdentity?,phone?,email?,address?,emergencyContact?,createdAt,updatedAt)`.
- `Coverage(id,patientId,payerNameMock,memberIdMock,status)`, always with fictional IDs.

### 3.2 Encounters and records

- `Appointment(id,patientId,practitionerId,departmentId,startAt,endAt,type,reason,status)`.
- `Encounter(id,patientId,appointmentId?,type,departmentId,practitionerId,startAt,endAt?,status,chiefComplaint)`.
- `Admission(id,encounterId,bedId,admitAt,dischargeAt?,state)`, `Transfer(id,admissionId,fromBedId,toBedId,at,reason)`.
- `ClinicalNote(id,patientId,encounterId,authorId,type,structuredSections,content,status,version,signedAt?,updatedAt)` and `NoteAddendum(id,noteId,authorId,text,signedAt)`.
- `Condition(id,patientId,encounterId?,codeSystem,code,display,clinicalStatus,onsetDate?,resolvedDate?)`.
- `Allergy(id,patientId,substance,reaction,severity,status,verifiedBy?,verifiedAt?)`.
- `MedicationStatement(id,patientId,name,doseText,route,frequency,startAt?,endAt?,status,source)`.
- `VitalObservation(id,patientId,encounterId,type,value,unit,observedAt,recordedBy)`. Blood-pressure systolic/diastolic values may be separate and grouped.
- `CarePlan(id,patientId,encounterId?,goal,interventions,status,ownerId)`, `CareTask(id,patientId,encounterId?,type,title,dueAt?,status,assigneeId)`.

### 3.3 Orders and results

- `Order(id,patientId,encounterId,category,catalogItemId,orderedBy,indication?,priority,status,detailsJson,signedAt?)`.
- `OrderEvent(id,orderId,previousStatus,nextStatus,actorId,occurredAt,reason?)`.
- `Specimen(id,labOrderId,accessionNumber,type,collectedAt?,receivedAt?,status)`.
- `LabResult(id,orderId,specimenId?,analyte,valueNumeric?,valueText?,unit?,refLow?,refHigh?,abnormalFlag?,status,resultedAt?,verifiedBy?)`.
- `ImagingStudy(id,orderId,modality,bodySite,scheduledAt?,status)`, `ImagingReport(id,studyId,findings,impression,authorId,status,signedAt?)`.
- `MedicationRequest(id,orderId,name,strength,dose,route,frequency,duration?,quantity?,simulatedPharmacy?,verificationStatus)`.
- `MedicationAdministration(id,medRequestId,patientId,encounterId,scheduledAt,administeredAt?,status,recordedBy?,reason?)`.

### 3.4 Communication, billing and governance

- `InboxThread(id,patientId?,encounterId?,category,subject,priority,status,createdBy,assignedTo?)`, `InboxMessage(id,threadId,senderId,body,createdAt,isRead)`.
- `Invoice(id,patientId,encounterId,amountCents,status)`, `ChargeItem(id,invoiceId,description,amountCents,codeMock)`, `MockPayment(id,invoiceId,amountCents,at,status)`.
- `AuditEvent(id,actorId,action,resourceType,resourceId,patientId?,occurredAt,detailsJson,outcome)`.
- `NoteTemplate(id,name,shortcut,body,ownerId?,isShared)`, `OrderCatalogItem(id,type,name,code?,description?,fieldsSchema)`.
- `AiDraft(id,patientId,encounterId?,kind,content,sourceRefsJson,modelLabel?,status,reviewedBy?)`.

### 3.5 State-machine constraints

- Appointment follows `scheduled → arrived → roomed → in_progress → completed`, with `cancelled` and `no_show` branches. Completed appointments cannot be cancelled.
- Encounter follows `planned → in_progress → completed → closed` and requires a patient.
- Note follows `draft → signed`, with signed changes captured through addenda/versions.
- Order follows `draft → signed → queued → in_progress → completed`, recording reasons for `cancelled/rejected`.
- Lab follows `ordered → collected → received → processing → verified → released`. Do not mark complete before release.
- Invoice follows `draft → issued → partially_paid/paid/void`. Mock payments do not collect real funds.
- Store changes in UTC and display the configured hospital-local time zone. Test appointments across calendar-day boundaries.

## 4. Initial role-permission policy

| Action | Physician | Nurse | FrontDesk | Pharmacist | LabTech | Billing | Patient | Admin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Patient search/chart | R/W-limited | R/W-limited | Demographics | Relevant chart R | Relevant orders R | Financial subset | Self only | Configuration + audited |
| Create/sign notes | Own W/Sign | Nursing note W | — | — | — | — | — | — |
| Place/sign orders | W/Sign | Scoped acknowledgment | — | Verify medication | Process labs | — | — | — |
| Vitals and MAR | View | W | — | Review | — | — | Own results R | — |
| Appointment check-in | Read | Rooming | W | — | — | — | Self scheduling | Configure |
| Messages | W | W | Scheduling | Pharmacy | Results | Billing | Self only | Audit |
| Billing | Limited view | — | Registration | — | — | W | Own view/mock payment | Configure |
| Users/permissions | — | — | — | — | — | — | — | W |

A production EHR would additionally require finer access controls, break-glass workflows, partitioning and security certification. This table is the demonstration baseline.
## 5. Required end-to-end workflows

**W01 Typical outpatient loop** — FrontDesk registers a fictional patient → schedules → checks in → Nurse records vitals and medication/allergy review → Physician opens the encounter, reviews history, adds diagnosis and SOAP note → creates HbA1c laboratory order → signs order/note → generates AVS → completes encounter → Patient views AVS in the portal. Verify database persistence and correct authorship at every step.

**W02 Laboratory-result loop** — Physician places lab order → laboratory queue receives it → collect/receive/process → enter illustrative HbA1c 7.1% → verify/release → physician Inbox gains Result Notification → Chart Review shows result → physician marks reviewed → task closes.

**W03 Simulated medication workflow** — Physician creates order → known-allergy warning → confirm/change simulated prescription → submit for pharmacy review → pharmacist approves or clarifies → state synchronizes → nurse MAR shows scheduled items → record simulated administration/hold reason → audit is available.

**W04 Inpatient workflow** — Create inpatient encounter → assign bed → nursing assessment/daily note → tests/results → simulated bed transfer → discharge summary/AVS → release bed → portal shows discharge summary.

**W05 Portal messaging** — Patient sends nonurgent message → physician Inbox receives it → physician replies → patient portal shows reply → both retain thread.

**W06 Appointment conflict** — A second appointment for the same physician and time returns 409 with a clear error. Rescheduling allows recovery.

**W07 Medical-record access isolation** — Patient A cannot access Patient B by route or API. FrontDesk cannot sign clinical notes. Audit every denial.

**W08 Immutable clinical signatures** — Signed notes cannot be silently changed. Addenda record their own signer/time. Ordinary users cannot delete audit events.

**W09 ED flow** — arriving → triage → roomed → provider → discharged/admitted, with synchronized board counts.

**W10 Billing loop** — Complete visit → billing staff adds mock charges → generate statement → patient views it → simulated payment → Paid state, without a real gateway.

**W11 Analytics** — Adding synthetic patients, completing appointments or releasing results updates database-driven KPIs.

**W12 AI provenance** — Summaries cite only currently authorized patient data. Citations open source records. AI cannot automatically sign or place orders.

## 6. Proposed technical architecture

### 6.1 Recommended technology stack

The following recommendations belong to the historical source. The approved Django decisions linked in this translation's introduction govern current implementation.

- Frontend uses React, TypeScript, Next.js, Tailwind CSS, shadcn/ui or equivalent accessible components, React Query, Zod, React Hook Form and Recharts.
- Backend uses FastAPI, Pydantic, SQLAlchemy and Alembic with generated OpenAPI documentation.
- PostgreSQL runs locally with Docker Compose. SQLite is a development fallback when Docker is unavailable, with later migration to PostgreSQL.
- Authentication uses secure sessions or an HttpOnly-cookie/short-lived JWT approach, Argon2 password hashing, backend RBAC and development-only seeded accounts.
- Tests include Pytest API integration, Vitest UI, Playwright E2E, linting, formatting and type checks.
- Separate frontend/backend type contracts use OpenAPI generation or shared schemas.
- Provide `.env.example`, keep actual secrets outside Git and leave external AI API keys absent by default.

### 6.2 Proposed initial directory convention

Inspect the existing workspace first and preserve unrelated projects.

```text
careflow-ehr/
  README.md
  AGENTS.md
  docs/
    product-spec.md
    architecture.md
    screens.md
    api.md
  apps/
    web/                 # Next.js / TypeScript UI
    api/                 # FastAPI / Python REST API
  packages/              # optional shared schemas
  scripts/
    seed_demo_data.py
  tests/
  docker-compose.yml
  .env.example
```

### 6.3 Suggested internal API resources

These examples do not require implementation in one increment.

- `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`.
- `GET /patients`, `POST /patients`, `GET /patients/{id}`, `PATCH /patients/{id}`.
- `GET /appointments`, `POST /appointments`, `PATCH /appointments/{id}`.
- `GET /encounters`, `POST /encounters`, `GET /encounters/{id}`, `PATCH /encounters/{id}`.
- `GET /patients/{id}/timeline`, `GET/POST /patients/{id}/conditions`, `/allergies`, `/medications`, `/observations`.
- `GET/POST /encounters/{id}/notes`, `POST /notes/{id}/sign`, `POST /notes/{id}/addenda`.
- `GET/POST /encounters/{id}/orders`, `POST /orders/{id}/sign`, `POST /orders/{id}/cancel`.
- `GET /lab/worklist`, `POST /lab/orders/{id}/specimens`, `POST /lab/orders/{id}/results`, `POST /lab/results/{id}/release`.
- `GET /inbox`, `POST /inbox/threads`, `POST /inbox/threads/{id}/messages`, `POST /inbox/threads/{id}/complete`.
- `GET /portal/me`, `GET /portal/appointments`, `GET /portal/results`, `GET /portal/messages`.
- `GET /admin/audit`, `GET /analytics/overview`, and future read-only `/fhir/*`.

Use consistent resource IDs, ISO8601 dates and pagination. Validate requests and return 400/403/404/409/422 as appropriate. Do not directly log sensitive fields.

## 7. Synthetic demonstration data

### 7.1 Recommended seed volume

- One Organization, two Departments, 12 Users across roles and 30 fictional Patients.
- 60 historical/current/future Appointments, 40 Encounters, 20 Notes, approximately 120 Observations, 70 Orders, 40 Lab Results, 10 Imaging Reports, 20 Inbox Threads and 10 mock bills.
- At least three complete scenarios. Patient A is a 42-year-old chronic-disease outpatient follow-up with HbA1c result, physician review and portal AVS. Patient B proceeds from emergency triage through admission/discharge. Patient C has inpatient nursing vitals, simulated MAR, bed transfer and discharge summary.
- Construct fictional diagnoses, drugs, tests, history and names in code. Do not reuse real identities appearing in public training screenshots.

### 7.2 Data consistency

- Each relevant record has a valid patientId and encounterId where required. Prevent records linking different patients.
- Keep appointment dates and encounter associations consistent and persist all state changes. Support repeatable seed/reset of test databases.
- Use fixed random seeds for reproducible demonstration data suitable for recording and automation.

## 8. Development stages, priorities and completion

| Phase | Working deliverable | Completion criterion |
| --- | --- | --- |
| 0 | Monorepo, run instructions, schema, Auth/RBAC, demo seed, basic shell | Frontend/backend start, demo login works, audit data is correct |
| 1 | Patient search/registration, schedule, check-in, snapshot | Patient/appointment/check-in data survives refresh, search/filter works |
| 2 | Encounter Navigator, vitals, problems, allergies, medications, notes | Physician sees nursing data and notes save/sign |
| 3 | Order Composer, lab queue, results, Inbox, AVS | W01 and W02 work with functional controls |
| 4 | Inpatient, nursing, flowsheets, MAR, ED, pharmacy, radiology | Cross-role state synchronization and permission tests pass |
| 5 | Patient portal, billing, analytics, FHIR-shaped export | Portal isolates patient data and reports query the database |
| 6 | AI summaries/drafts/RAG evidence, test hardening, demo deployment | Sources are traceable, unreviewed text cannot auto-sign, workflow can be recorded |

Implement one small vertical slice at a time, from database to API, UI and tests, and obtain human acceptance before continuing. Avoid generating many apparently complete screens without functioning workflows. This is the source roadmap. Approved iteration records define the actual delivery sequence.

## 9. Quality and acceptance

### Functional behavior

- Major buttons invoke APIs/state transitions or are explicitly disabled with explanations.
- Data survives refresh/restart, state history is complete and queue counts are accurate.
- Only authorized roles write, portal access is self-only and cross-patient queries are isolated.

### Code quality

- Use clear components and modules, avoid 2,000-line pages and separate API services from UI.
- Run lint, type checks and unit/integration/E2E tests before commits and report passing/failing counts.
- Preserve existing projects. Destructive migrations, file deletion and cloud deployment require user confirmation.

### Security and compliance boundaries

- Use synthetic data without real patient or account information.
- Keep clear demonstration statements. Do not claim HIPAA compliance, ONC certification or clinical usability without independent required assessments.
- Apply access auditing, least privilege, input validation, parameterized SQL, XSS/CSRF protection and sanitized errors.
- Default AI providers to mock/disabled. Define data flow, privacy and cost boundaries before real LLM integration.

## 10. Terminology and source references

These references are carried over from the source document. Their inclusion does not establish that they were independently revalidated for this translation.

1. [Epic software catalog](https://www.epic.com/software/)
2. [Epic specialties](https://www.epic.com/software/specialties/)
3. [Epic acute and inpatient care](https://www.epic.com/software/acute-and-inpatient-care/)
4. [Epic patient experience / MyChart](https://www.epic.com/software/patient-experience/)
5. [Epic appointment scheduling](https://www.epic.com/software/appointment-scheduling/)
6. [Epic interoperability](https://www.epic.com/software/interoperability/)
7. [Epic population health](https://www.epic.com/software/population-health/)
8. [Epic healthcare intelligence](https://www.epic.com/software/healthcare-intelligence/)
9. [Epic Art clinical AI](https://www.epic.com/software/art/)
10. [open.epic FHIR technical specifications](https://open.epic.com/TechnicalSpecifications)
11. [UI Health Care Hyperspace basics](https://epicsupport.sites.uiowa.edu/epic-resources/hyperspace-epic-basics)
12. [UI Health Care SmartTools](https://epicsupport.sites.uiowa.edu/epic-resources/smarttools)
13. [Vanderbilt public Epic introduction](https://www.vumc.org/vclic/intro-epic-and-build-capabilities)
14. [Storyboard terminology](https://ehealth.connect-care.ca/epic-systems/epic-modules/storyboard)

This document is a development requirements specification for an independent project. It contains no proprietary Epic internal manual, official Epic screen prototype or certification specification for a complete commercial EHR.
