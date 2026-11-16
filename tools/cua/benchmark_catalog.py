"""CUA-100 v1.0: fixed task contracts; offline recipes are never native evidence."""
import json
TASKS=[]
def add(title,role,target,text="",level=1,status=200,**kw):
    TASKS.append(dict(id=f"CF-{len(TASKS)+1:03}",title=title,role=role,target=target,text=text,
        difficulty=level,status=status,final=kw.pop("final",target),steps=kw.pop("steps",[]),
        goal=kw.pop("goal","Open the requested route, observe its content and report whether access is allowed."),
        sql=kw.pop("sql",[]),post=kw.pop("post",[]),extra=kw.pop("extra",[]),
        variant=kw.pop("variant","base"),forbidden=kw.pop("forbidden",[]),invalid=kw.pop("invalid",None),**kw))
# Simple entry and authorized workspace checks.
for title,role,path,text in [
("Unified landing","Anonymous","/","Choose your portal"),
("Staff sign-in entry","Anonymous","/login/","Staff sign in"),
("Patient sign-in entry","Anonymous","/portal/login/","Sign in to the Patient Portal"),
("Patient signup fields","Anonymous","/accounts/register/patient/","Confirm password"),
("Staff application fields","Anonymous","/accounts/register/staff/","Requested staff role"),
("Administrator dashboard","Administrator","/app/dashboard/","Dashboard"),
("Physician worklist","Physician","/app/physician/","Physician worklist"),
("Nursing workspace","Nurse","/app/nursing/","Nursing workspace"),
("Laboratory worklist","Lab Staff","/app/lab/workspace/","Laboratory"),
("Pharmacy worklist","Pharmacist","/app/pharmacy/","Pharmacy Workspace"),
]:add(title,role,path,text)
for title,role,path,text in [
("Patient directory","FrontDesk","/app/patients/","LAB-01"),
("Patient demographics","FrontDesk","/app/patients/1/","LAB-01"),
("Appointment calendar","FrontDesk","/app/schedule/","Synthetic benchmark"),
("Check-in worklist","FrontDesk","/app/check-in/","Synthetic benchmark"),
("Appointment creation history","FrontDesk","/app/appointments/2/","Appointment booked"),
("Longitudinal patient chart","Physician","/app/patients/1/chart/","LAB-01"),
("In-progress encounter","Physician","/app/patients/1/encounters/1/","In progress"),
("Medical-history empty state","Physician","/app/patients/1/history/medical/","Medical history"),
("Longitudinal problems","Physician","/app/patients/1/history/problems/","Problems"),
("Allergy review status","Physician","/app/patients/1/history/allergies/","Not reviewed"),
("Medication history","Physician","/app/patients/1/history/medications/","Medication history"),
("Encounter diagnoses","Physician","/app/patients/1/encounters/1/diagnoses/","Encounter diagnoses"),
("Appointment nursing context","Nurse","/app/patients/1/nursing/appointments/1/","LAB-01"),
("Longitudinal flowsheet","Nurse","/app/patients/1/nursing/flowsheet/","LAB-01"),
("Lab catalog","Physician","/app/lab/catalog/","Demo chemistry"),
("Lab order history","Physician","/app/patients/1/lab-orders/","Demo chemistry"),
("Medication catalog","Physician","/app/medications/catalog/","Synthetic Amber"),
("Signed medication history","Physician","/app/patients/1/medication-orders/","Synthetic Amber"),
("Billing worklist","BillingStaff","/app/billing/","Billing"),
("Claims queue","BillingStaff","/app/billing/claims/","Claims"),
("Radiology worklist","RadiologyStaff","/app/radiology/","Radiology"),
("Imaging catalog","Administrator","/app/imaging/catalog/","Imaging"),
("Inpatient dashboard","HospitalOperations","/app/inpatient/","Inpatient"),
("Capacity dashboard","HospitalOperations","/app/inpatient/capacity/","Capacity"),
("Emergency tracking board","Nurse","/app/ed/","Emergency"),
]:add(title,role,path,text,2)
# Direct URL probes: a fixture launcher exposes only the explicitly approved URL.
for title,role,path,status in [
("Anonymous staff redirect","Anonymous","/app/patients/",302),
("Anonymous patient redirect","Anonymous","/portal/",302),
("Patient denied directory","Patient","/app/patients/",403),
("Patient denied staff approval","Patient","/app/accounts/applications/",403),
("Patient denied nursing","Patient","/app/nursing/",403),
("Patient denied pharmacy","Patient","/app/pharmacy/",403),
("Physician denied registration","Physician","/app/patients/new/",403),
("Physician denied demographics edit","Physician","/app/patients/1/edit/",403),
("Physician denied account approval","Physician","/app/accounts/applications/",403),
("FrontDesk denied chart","FrontDesk","/app/patients/1/chart/",403),
("FrontDesk denied SOAP","FrontDesk","/app/patients/1/encounters/1/",403),
("FrontDesk denied history","FrontDesk","/app/patients/1/history/medical/",403),
("Nurse denied SOAP authoring","Nurse","/app/patients/1/encounters/1/note/",403),
("Nurse denied patient creation","Nurse","/app/patients/new/",403),
("Lab denied demographics","Lab Staff","/app/patients/",403),
("Lab denied physician worklist","Lab Staff","/app/physician/",403),
("Pharmacist denied chart","Pharmacist","/app/patients/1/chart/",403),
("Pharmacist denied demographics edit","Pharmacist","/app/patients/1/edit/",403),
("Billing denied ED","BillingStaff","/app/ed/",403),
("Billing denied inpatient","BillingStaff","/app/inpatient/",403),
("Radiology denied SOAP","RadiologyStaff","/app/patients/1/encounters/1/",403),
("HospitalOperations denied approval","HospitalOperations","/app/accounts/applications/",403),
("Physician denied unrelated chart","Physician","/app/patients/2/chart/",404),
("Mismatched patient encounter denied","Physician","/app/patients/2/encounters/1/",404),
("Unclaimed pharmacy details denied","Pharmacist","/app/pharmacy/orders/{meduuid}/",404),
]:
    final=("/login/?next=/app/patients/" if path=="/app/patients/" else "/portal/login/?next=/portal/") if status==302 else path
    add(title,role,path,level=3,status=status,final=final,forbidden=["LAB-01","LAB-02","Synthetic protected"],
        goal="Click Open requested application route, observe the login or denial page and stop. Do not bypass access controls.")
for title,path,text in [
("Own patient dashboard","/portal/","Patient dashboard"),("Own appointments","/portal/appointments/","Appointments"),
("Own visits","/portal/visits/","Visits"),("Own medications","/portal/medications/","Medications"),
("Released-results empty state","/portal/results/","Results"),("Own messages","/portal/messages/","Messages"),
("Own appointment requests","/portal/requests/","requests"),("Own billing statements","/portal/billing/","Billing"),
]:add(title,"Patient",path,text,2)
add("Owner cannot see unreleased lab result","Patient","/portal/results/1/",level=3,status=404,forbidden=["demo-U","LAB-02"])
add("Other patient cannot see lab result","OtherPatient","/portal/results/1/",level=3,status=404,forbidden=["demo-U","LAB-01"])
def fill(s,v):return ["fill",s,v]
def button(s):return ["button",s]
def link(s):return ["link",s]
def check(s):return ["check",s]
def select(s,v):return ["select",s,v]
def q(s,v):return [s,v]
def write(title,role,path,goal,steps,text,**kw):
    add(title,role,path,text,kw.pop("level",4),steps=steps,goal=goal,**kw)
pf=[fill("#id_mrn","SYN-BENCH-NEW"),fill("#id_first_name","Synthetic"),fill("#id_last_name","Benchmark"),fill("#id_dob","1990-01-15"),check('input[name=sex][value=unknown]')]
write("Register synthetic patient","FrontDesk","/app/patients/new/",
"Register MRN SYN-BENCH-NEW, first name Synthetic, last name Benchmark, DOB 1990-01-15, sex Unknown. Explicitly confirm synthetic data and save.",
pf+[check("#id_synthetic_only"),button("Save patient")],"SYN-BENCH-NEW",final="/app/patients/3/",post=["/app/patients/new/"],extra=["/app/patients/3/"],
sql=[q("SELECT COUNT(*) FROM patients_patient WHERE mrn='SYN-BENCH-NEW'",1),q("SELECT COUNT(*) FROM patients_auditevent WHERE action='patient_create'",1)])
write("Required synthetic confirmation","FrontDesk","/app/patients/new/",
"Fill MRN SYN-BENCH-NEW, Synthetic Benchmark, DOB 1990-01-15, sex Unknown. Leave synthetic confirmation UNCHECKED, attempt Save patient and observe required-field blocking.",
pf+[button("Save patient")],"",invalid="synthetic_only",post=["/app/patients/new/"],sql=[q("SELECT COUNT(*) FROM patients_patient",2)])
write("Duplicate MRN rejection","FrontDesk","/app/patients/new/",
"Attempt MRN LAB-01, Synthetic Benchmark, DOB 1990-01-15, sex Unknown. Confirm synthetic data and submit once. Observe the duplicate MRN error.",
[fill("#id_mrn","LAB-01")]+pf[1:]+[check("#id_synthetic_only"),button("Save patient")],"already",post=["/app/patients/new/"],sql=[q("SELECT COUNT(*) FROM patients_patient",2)])
write("Edit demographics and audit","FrontDesk","/app/patients/1/edit/",
"Change the last name to Updated, confirm synthetic data and save.",
[fill("#id_last_name","Updated"),check("#id_synthetic_only"),button("Save patient")],"Updated",final="/app/patients/1/",post=["/app/patients/1/edit/"],extra=["/app/patients/1/"],
sql=[q("SELECT last_name FROM patients_patient WHERE id=1","Updated"),q("SELECT COUNT(*) FROM patients_auditevent WHERE action='patient_update'",1)])
appt=[select("#id_patient","1"),select("#id_physician","{physician}"),fill("#id_start_at","{start}"),button("Review appointment"),button("Confirm appointment")]
write("Schedule and confirm appointment","FrontDesk","/app/appointments/new/",
"Schedule Synthetic Lab (LAB-01) with its treating physician at {start}, default duration 30 minutes. Review then confirm.",
appt,"Scheduled",final="/app/appointments/4/",post=["/app/appointments/new/"],extra=["/app/appointments/4/"],
sql=[q("SELECT COUNT(*) FROM scheduling_appointment",4),q("SELECT patient_id FROM scheduling_appointment WHERE id=4",1),q("SELECT COUNT(*) FROM patients_auditevent WHERE action='appointment_create'",2)])
write("Check in and audit","FrontDesk","/app/appointments/2/","Mark this appointment Arrived. Verify check-in actor and Patient checked in history.",
[button("Mark Arrived")],"Arrived",post=["/app/appointments/2/transition/"],sql=[q("SELECT status FROM scheduling_appointment WHERE id=2","arrived"),q("SELECT COUNT(*) FROM patients_auditevent WHERE action='appointment_arrive'",1)])
write("Reschedule same patient","FrontDesk","/app/appointments/2/edit/","Change start time to {reschedule}, preserve patient and physician, review and confirm.",
[fill("#id_start_at","{reschedule}"),button("Review appointment"),button("Confirm appointment")],"Scheduled",final="/app/appointments/2/",extra=["/app/appointments/2/"],post=["/app/appointments/2/edit/"],
sql=[q("SELECT version FROM scheduling_appointment WHERE id=2",2),q("SELECT patient_id FROM scheduling_appointment WHERE id=2",1)])
write("Cancel with retained reason","FrontDesk","/app/appointments/2/","Cancel this appointment with reason Synthetic cancellation and verify Cancelled status.",
[fill('form:has(button:has-text("Cancel appointment")) input[name=reason]',"Synthetic cancellation"),button("Cancel appointment")],"Cancelled",post=["/app/appointments/2/transition/"],
sql=[q("SELECT status FROM scheduling_appointment WHERE id=2","cancelled"),q("SELECT COUNT(*) FROM patients_auditevent WHERE action='appointment_cancel'",1)])
soap=[fill("#id_"+x,"Synthetic benchmark "+x) for x in ("subjective","objective","assessment","plan")]
write("Create four-section SOAP","Physician","/app/patients/1/encounters/1/note/",
"Enter Synthetic benchmark plus each section name in Subjective, Objective, Assessment and Plan. Confirm synthetic data and save draft.",
soap+[check("#id_synthetic_confirmed"),button("Save draft")],"Synthetic benchmark",final="/app/patients/1/encounters/1/",extra=["/app/patients/1/encounters/1/"],post=["/app/patients/1/encounters/1/note/"],
sql=[q("SELECT COUNT(*) FROM clinical_note WHERE encounter_id=1 AND signed_at IS NULL",1)])
sign=[link("Review and sign"),check("#id_confirmed"),button("Confirm and sign note")]
write("Sign existing SOAP","Physician","/app/patients/1/encounters/1/","Review and sign this draft after explicitly confirming all four sections. Verify signed read-only state.",
sign,"Signed",variant="note_draft",extra=["/app/patients/1/encounters/1/notes/2/sign/"],post=["/app/patients/1/encounters/1/notes/2/sign/"],
sql=[q("SELECT COUNT(*) FROM clinical_note WHERE encounter_id=1 AND signed_at IS NOT NULL",1)])
write("Complete signed encounter","Physician","/app/patients/1/encounters/1/","Complete this encounter; preserve its already signed SOAP.",
[button("Complete encounter")],"Completed",variant="note_signed",post=["/app/patients/1/encounters/1/complete/"],sql=[q("SELECT status FROM clinical_encounter WHERE id=1","completed")])
for kind,title,fields,table,detail in [
("medical","Past medical history",[select("#id_category","medical")],"history_medicalhistory","category Past medical history"),
("problems","Active longitudinal problem",[],"history_problem","default Active status"),
("allergies","Document fictional allergy",[fill("#id_reaction","Synthetic rash"),select("#id_severity","mild")],"history_allergy","reaction Synthetic rash, severity Mild"),
("medications","Medication statement",[fill("#id_dose","1 demo unit"),fill("#id_route","oral"),fill("#id_frequency","daily")],"history_medicationstatement","dose 1 demo unit, route oral, frequency daily"),
]:
    path=f"/app/patients/1/history/{kind}/"
    write(title,"Physician",path+"new/","Create record labelled Synthetic benchmark, "+detail+". Select Source Documented, confirm synthetic data and save.",
    fields+[fill("#id_label","Synthetic benchmark"),select("#id_source","documented"),check("#id_synthetic_confirmed"),button("Save record")],"Synthetic benchmark",
    final=path+"1/",extra=[path,path+"1/"],post=[path+"new/"],sql=[q(f"SELECT COUNT(*) FROM {table} WHERE patient_id=1",1)])
for kind,title,steps,goal,text,query in [
("assessment","Nursing assessment",[fill("#id_chief_complaint","Synthetic benchmark"),fill("#id_pain_score","2"),check("#id_ready_for_provider")],
"Record complaint Synthetic benchmark, pain score 2, and ready for provider.","Synthetic benchmark","SELECT COUNT(*) FROM nursing_roomingassessment WHERE ready_for_provider=1"),
("vitals","Vital-sign panel",[fill("#id_systolic","120"),fill("#id_diastolic","80"),fill("#id_heart_rate","70"),fill("#id_temperature","37.2"),select("#id_temperature_unit","C"),select("#id_source","measured")],
"Record fictional systolic 120, diastolic 80, heart rate 70, temperature 37.2 C, source Measured.","120","SELECT COUNT(*) FROM nursing_vitalobservation WHERE systolic=120 AND diastolic=80"),
]:
    path=f"/app/patients/1/nursing/appointments/1/{kind}/"
    write(title,"Nurse",path+"new/",goal+" Explicitly confirm synthetic information and save.",steps+[check("#id_synthetic_confirmed"),button("Save nursing documentation")],text,
    final=path+"1/",extra=[path+"1/"],post=[path+"new/"],sql=[q(query,1)])
for decision,status in [("approve","approved"),("reject","rejected")]:
    steps=[select("#id_decision",decision)]+([select("#id_role","Nurse")] if decision=="approve" else [])+[fill("#id_reason","Synthetic benchmark review"),button("Save review decision")]
    write(decision.title()+" pending staff application","Administrator","/app/accounts/applications/{pending}/",
    decision.title()+" benchmark-pending "+("as Nurse " if decision=="approve" else "")+"with reason Synthetic benchmark review. Verify recorded decision.",
    steps,status,final="/app/accounts/applications/",extra=["/app/accounts/applications/"],post=["/app/accounts/applications/{pending}/"],
    sql=[q("SELECT status FROM accounts_enrollment WHERE user_id=(SELECT id FROM auth_user WHERE username='benchmark-pending')",status)])
write("Mismatched password confirmation","Anonymous","/accounts/register/patient/",
"Attempt username benchmark-new, Password QA_PASSWORD and Confirm password QA_WRONG_PASSWORD. Confirm synthetic data, submit once and observe mismatch rejection.",
[fill("#id_username","benchmark-new"),fill("#id_password1","QA_PASSWORD"),fill("#id_password2","QA_WRONG_PASSWORD"),check("#id_synthetic_only"),button("Create patient account")],
"passwords do not match",post=["/accounts/register/patient/"],sql=[q("SELECT COUNT(*) FROM auth_user WHERE username='benchmark-new'",0)])
# Advanced, isolated clinical transitions and multistep journeys.
for title,variant,action,label,fields,text,sqls in [
("Claim signed requisition","base","claim","Claim order",[],"Pharmacy Verification",[q("SELECT COUNT(*) FROM medications_pharmacyreview",1)]),
("Request clarification","pharmacy_claimed","clarify","Request clarification",[fill("#id_reason","Synthetic benchmark clarification")],"Clarification requested",[q("SELECT status FROM medications_pharmacyreview","clarification")]),
("Approve pharmacy verification","pharmacy_claimed","approve","Approve verification",[],"Approved",[q("SELECT status FROM medications_pharmacyreview","approved")]),
("Record simulated dispensing","pharmacy_approved","dispense","Record simulated dispensing",[fill("#id_quantity","2")],"Simulated dispensing recorded",[q("SELECT COUNT(*) FROM medications_pharmacydispenseevent",1)]),
]:
    detail="/app/pharmacy/orders/{meduuid}/"
    write(title,"Pharmacist","/app/pharmacy/" if action=="claim" else detail,
    label+" for the one synthetic order. "+("Use reason Synthetic benchmark "+("claim" if action=="claim" else "clarification")+". " if fields and action!="dispense" else "Use quantity 2. " if action=="dispense" else "")+"Explicitly confirm and verify the resulting workflow state.",
    [link(label)]+fields+[check("#id_confirmed"),button(label)],text,level=5,variant=variant,final=detail,extra=[detail,detail+action+"/"],post=[detail+action+"/"],sql=sqls)
for title,role,variant,action,label,steps,text,sqls in [
("Claim lab requisition","Lab Staff","base","claim","Claim requisition",[fill("#id_reason","Synthetic benchmark claim")],"Synthetic",[q("SELECT COUNT(*) FROM labs_laborder WHERE assigned_lab_staff_id IS NOT NULL",1)]),
("Collect specimen with identity","Nurse","base","collect","Collect specimen",[fill("#id_mrn","LAB-01"),fill("#id_dob","1980-01-01"),check("#id_identity_confirmed")],"Collected",[q("SELECT status FROM labs_labspecimen","collected")]),
("Publish prepared lab report","Lab Staff","lab_result","publish","Preview and finalize",[],"Fulfilled",[q("SELECT status FROM labs_labresult","final"),q("SELECT status FROM labs_laborder","fulfilled")]),
]:
    detail="/app/lab/processing/{labuuid}/"
    workflow=[link(label)]+steps+[check("#id_synthetic_confirmed")]+([button("Preview report"),button("Confirm publication")] if action=="publish" else [button("Confirm laboratory action")])
    write(title,role,"/app/lab/workspace/" if action=="claim" else detail,
    label+". "+("Use MRN LAB-01 and DOB 1980-01-01; explicitly confirm identity. " if action=="collect" else "Review the draft and explicitly confirm publication. ")+"Confirm synthetic data and verify final state.",
    workflow,text,level=5,variant=variant,final=detail,extra=[detail,detail+action+"/"],post=[detail+action+"/"],sql=sqls)
write("Acknowledge exact lab revision","Physician","/app/lab/reports/{labuuid}/","Review the current synthetic laboratory publication, explicitly confirm synthetic information and acknowledge it. Verify it is acknowledged.",
[link("Acknowledge current publication"),check("#id_synthetic_confirmed"),button("Confirm acknowledgement")],"acknowledged",level=5,variant="lab_published",
extra=["/app/lab/reports/{labuuid}/acknowledge/"],post=["/app/lab/reports/{labuuid}/acknowledge/"],sql=[q("SELECT COUNT(*) FROM labs_labresultreview",1)])
write("Compose and sign SOAP journey","Physician","/app/patients/1/encounters/1/note/",
"Fill all four SOAP sections with Synthetic benchmark plus section name, confirm synthetic data, save draft, review and explicitly sign.",
soap+[check("#id_synthetic_confirmed"),button("Save draft")]+sign,"Signed",level=5,final="/app/patients/1/encounters/1/",
extra=["/app/patients/1/encounters/1/","/app/patients/1/encounters/1/notes/2/sign/"],post=["/app/patients/1/encounters/1/note/","/app/patients/1/encounters/1/notes/2/sign/"],
sql=[q("SELECT COUNT(*) FROM clinical_note WHERE encounter_id=1 AND signed_at IS NOT NULL",1)])
write("Schedule and check-in journey","FrontDesk","/app/appointments/new/",
"Schedule Synthetic Lab (LAB-01) with its treating physician at {start}, review and confirm, then mark the new appointment Arrived. Verify matching patient and booking then check-in history.",
appt+[button("Mark Arrived")],"Arrived",level=5,final="/app/appointments/4/",extra=["/app/appointments/4/"],post=["/app/appointments/new/","/app/appointments/4/transition/"],
sql=[q("SELECT status FROM scheduling_appointment WHERE id=4","arrived"),q("SELECT patient_id FROM scheduling_appointment WHERE id=4",1),q("SELECT COUNT(*) FROM scheduling_appointmentevent WHERE appointment_id=4",2)])
assert len(TASKS)==100,len(TASKS)
def render():
    heading="# CareFlow CUA-100 v1.0\n\n100 independent tasks. Difficulty 1-5; fresh synthetic database per task. A separate signed SOAP record must remain unchanged in every case. Deterministic offline recipes are NOT native CUA results.\n\n"
    return heading+"\n".join(f"## {t['id']}: {t['title']}\n\n- Role: {t['role']}; difficulty: {t['difficulty']}/5; fixture: {t['variant']}.\n- Target: `{t['target']}`; expected HTTP {t['status']}; final: `{t['final']}`.\n- Task: {t['goal']}\n- Visible result: {t['text'] or 'specified denial or validation state'}.\n- Database assertions: `{json.dumps(t['sql'])}`; read-only tasks preserve all business tables.\n- Forbidden denied-page text: {', '.join(t['forbidden']) or 'not applicable'}.\n" for t in TASKS)
if __name__=="__main__":print(json.dumps(TASKS,indent=2))
