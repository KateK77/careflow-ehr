"""Create a brand-new synthetic benchmark database and serve only loopback."""
import json, os, secrets, sys
from pathlib import Path
from datetime import timedelta, date
from wsgiref.simple_server import make_server, WSGIRequestHandler

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
class Quiet(WSGIRequestHandler):
    def log_message(self,*args): pass

def main():
    folder=Path(sys.argv[1]).resolve(strict=True)
    db=folder/"benchmark.sqlite3"
    db.touch(exist_ok=False)
    os.environ["CAREFLOW_DB_PATH"]=str(db)
    os.environ["DJANGO_SETTINGS_MODULE"]="careflow.settings"
    import django
    django.setup()
    from django.conf import settings
    settings.ALLOWED_HOSTS=["127.0.0.1"]
    # Keep same-day synthetic check-in comfortably inside a clinic day.
    settings.TIME_ZONE="UTC" if __import__("datetime").datetime.now(__import__("datetime").UTC).hour<12 else "Etc/GMT+12"
    from django.core.management import call_command
    call_command("migrate",verbosity=0,interactive=False)
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.utils import timezone
    from careflow.medications.test_pharmacy import PharmacyFixture
    from careflow.labs.test_processing import ProcessingFixture
    from careflow.portal.models import PatientPortalAccount
    from careflow.scheduling.services import save_appointment
    from careflow.scheduling.models import Appointment
    from careflow.clinical.models import Encounter, Note
    from careflow.clinical.services import save_note, sign_note, complete_encounter
    from careflow.accounts.models import Enrollment

    class Fixture(PharmacyFixture,ProcessingFixture): pass
    f=Fixture();f.setup_pharmacy()
    f.lab=f.staff["Lab Staff"];f.nurse=f.staff["Nurse"]
    f.order=f.submit(f.draft()).record
    variant=sys.argv[2]
    if variant in {"lab_received","lab_result","lab_published"}:
        if variant=="lab_received": f.receive()
        elif variant=="lab_result": f.result_draft()
        else: f.publish()
    staff={**f.staff,"Pharmacist":f.pharmacist}
    for role in ("BillingStaff","RadiologyStaff","HospitalOperations"):
        u=get_user_model().objects.create_user("benchmark-"+role.lower())
        u.groups.add(Group.objects.get_or_create(name=role)[0]);staff[role]=u
    password=secrets.token_urlsafe(24)
    from django.contrib.auth.hashers import make_password
    encoded=make_password(password)
    accounts={}
    for role,u in staff.items():
        u.password=encoded;u.save()
        accounts[role]=u.username
    for role,patient in (("Patient",f.patient),("OtherPatient",f.foreign)):
        u=get_user_model().objects.create_user("benchmark-"+role.lower())
        u.password=encoded;u.save()
        PatientPortalAccount.objects.create(user=u,patient=patient);accounts[role]=u.username
    pending=get_user_model().objects.create_user("benchmark-pending",is_active=False)
    pending.password=encoded;pending.save()
    Enrollment.objects.create(user=pending,kind="staff",status="pending",requested_role="Nurse")
    future=timezone.localtime(timezone.now()+timedelta(hours=1)).replace(second=0,microsecond=0)
    a=save_appointment(staff["FrontDesk"],dict(patient=f.patient,physician=f.physician,start_at=future,duration=30,appointment_type="Synthetic benchmark",reason="Fictional fixture"))
    # A separate signed/completed record is preserved in EVERY task.
    protected_app=Appointment.objects.create(patient=f.patient,physician=f.physician,start_at=timezone.now()-timedelta(days=1),end_at=timezone.now()-timedelta(days=1)+timedelta(minutes=30),status="arrived",checked_in_at=timezone.now()-timedelta(days=1),checked_in_by=staff["FrontDesk"])
    protected=Encounter.objects.create(patient=f.patient,physician=f.physician,appointment=protected_app)
    sections=dict(subjective="Synthetic protected S",objective="Synthetic protected O",assessment="Synthetic protected A",plan="Synthetic protected P",synthetic_confirmed=True)
    protected_note=save_note(f.physician,protected.pk,sections,0)
    sign_note(f.physician,protected_note.pk,protected_note.version,True)
    complete_encounter(f.physician,protected.pk,1)
    if variant in {"note_draft","note_signed"}:
        note=save_note(f.physician,f.encounter.pk,sections,0)
        if variant=="note_signed": sign_note(f.physician,note.pk,note.version,True)
    if variant in {"pharmacy_claimed","pharmacy_approved"}:
        f.pharmacy_action("claim",f.signed.version)
        if variant=="pharmacy_approved":f.pharmacy_action("approve",1)
    fixture={"password":password,"accounts":accounts,"patient":f.patient.pk,"foreign":f.foreign.pk,"physician":f.physician.pk,
        "appointment":a.pk,"encounter":f.encounter.pk,"protected_note":protected_note.pk,"pending":Enrollment.objects.get(user=pending).pk,
        "labuuid":str(f.order.public_id),"meduuid":str(f.signed.public_id),"start":(future+timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
        "reschedule":(future+timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M"),"observed":timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
        "mrn":f.patient.mrn,"dob":f.patient.dob.isoformat(),"accession":str(f.order.specimens.get().accession)}
    (folder/"fixture.json").write_text(json.dumps(fixture),encoding="utf-8")
    from django.core.wsgi import get_wsgi_application
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    app=StaticFilesHandler(get_wsgi_application())
    def application(environ,start_response):
        if environ["PATH_INFO"]=="/__benchmark__/":
            import html
            target=(folder/"target.txt").read_text(encoding="utf-8")
            body=('<!doctype html><html lang="en"><meta charset="utf-8"><title>Isolated route probe</title><body style="font:22px sans-serif;padding:60px"><h1>CareFlow isolated route probe</h1><p>DEMO â€” NOT FOR CLINICAL USE</p><p>This is a test launcher, not an application feature.</p><a data-target href="'+html.escape(target,quote=True)+'">Open requested application route</a></body></html>').encode()
            start_response("200 OK",[("Content-Type","text/html; charset=utf-8"),("Content-Length",str(len(body)))])
            return [body]
        return app(environ,start_response)
    with make_server("127.0.0.1",0,application,handler_class=Quiet) as server:
        (folder/"server-port.tmp").write_text(str(server.server_port),encoding="ascii")
        (folder/"server-port.tmp").replace(folder/"server-port")
        server.timeout=0.25
        while not (folder/"STOP").exists():server.handle_request()
if __name__=="__main__":main()
