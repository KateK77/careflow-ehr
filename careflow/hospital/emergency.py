import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from careflow.medications.services import check_version, command_transaction
from careflow.patients.access import roles_for
from careflow.patients.models import Patient

from .access import is_operator, require_operator
from .models import AdmissionRequest, EmergencyVisit, InpatientStay, Room
from .services import begin, decide_admission, physicians, record, request_admission, selected, value


ACTIVE_ED = ("waiting", "triage", "roomed", "provider", "observation")
ACTIONS = {
    "ed_triage": "Record fictional triage", "ed_room": "Room and assign clinician",
    "ed_provider": "Begin provider review", "ed_observation": "Move to observation",
    "ed_discharge": "Discharge from ED", "ed_admit": "Admit to inpatient care",
}


def ed_reader(actor):
    return is_operator(actor) or bool(set(roles_for(actor)) & {"Physician", "Nurse"})


def visits_for(actor):
    query = EmergencyVisit.objects.select_related("patient", "room__ward__department", "clinician", "inpatient_stay")
    if is_operator(actor) or "Nurse" in roles_for(actor):
        return query
    if "Physician" in roles_for(actor):
        return query.filter(clinician=actor)
    return query.none()


def free_ed_rooms():
    return Room.objects.filter(ward__kind="ed", emergencyvisit__isnull=True)


def allowed_role(actor, action, visit):
    roles = set(roles_for(actor))
    if action == "ed_triage":
        return "Nurse" in roles
    if action == "ed_room":
        return is_operator(actor) or "Nurse" in roles
    if action == "ed_admit":
        return is_operator(actor)
    return ("Physician" in roles and actor.pk == visit.clinician_id
            and action in ("ed_provider", "ed_observation", "ed_discharge"))


@command_transaction
def register_ed(actor, patient_id, arrival_method, complaint, key, confirmed):
    require_operator(actor)
    identity, prior = begin(actor, key, "ed_register", patient_id, arrival_method, complaint, confirmed)
    if prior:
        return prior.visit
    if confirmed is not True or arrival_method not in dict(EmergencyVisit.ARRIVAL_METHODS):
        raise ValidationError("Confirm a fictional arrival and choose its method.")
    patient = selected(Patient.objects, pk=patient_id)
    if (EmergencyVisit.objects.filter(patient=patient, status__in=ACTIVE_ED).exists()
            or InpatientStay.objects.filter(request__patient=patient, status="active").exists()
            or AdmissionRequest.objects.filter(patient=patient, status="pending").exists()):
        raise ValidationError("This patient already has an active ED visit, inpatient stay or pending admission.")
    item = EmergencyVisit.objects.create(patient=patient, arrival_method=arrival_method,
                                         complaint=value(complaint, 240, "a fictional chief complaint"))
    record(actor, "ed_register", identity, patient_id=patient_id, visit=item, details={"after": item.status})
    return item


@command_transaction
def advance_ed(actor, patient_id, visit_id, action, version, key, confirmed, *,
               category="", room_id=None, clinician_id=None, bed_id=None, note=""):
    identity, prior = begin(actor, key, action, patient_id, visit_id, version, confirmed,
                            category, room_id, clinician_id, bed_id, note)
    item = visits_for(actor).filter(pk=visit_id, patient_id=patient_id).first()
    if item is None or not allowed_role(actor, action, item):
        raise PermissionDenied
    if prior:
        return item
    check_version(version, item.version)
    if confirmed is not True or item.status not in ACTIVE_ED:
        raise ValidationError("Confirm an action on an active ED visit.")
    before = item.status
    details = {"before": before}
    if action == "ed_triage" and before in ("waiting", "triage"):
        if category not in dict(EmergencyVisit.TRIAGE):
            raise ValidationError("Select a fictional triage label.")
        note = value(note, 500, "a fictional triage observation")
        details.update(previous_category=item.triage_category, category=category, note=note)
        item.triage_category, item.status = category, "triage"
    elif action == "ed_room" and before == "triage":
        room = selected(free_ed_rooms(), pk=room_id)
        clinician = selected(physicians(), pk=clinician_id)
        item.room, item.clinician, item.status = room, clinician, "roomed"
        details.update(room=str(room), clinician=clinician.get_username())
    elif action == "ed_provider" and before == "roomed":
        item.status, item.provider_at = "provider", timezone.now()
    elif action == "ed_observation" and before == "provider":
        item.status = "observation"
    elif action in ("ed_discharge", "ed_admit") and before in ("provider", "observation"):
        note = value(note, 240, "a fictional disposition summary")
        details.update(note=note, released_room=str(item.room))
        if action == "ed_admit":
            _admit_from_ed(actor, item, bed_id, note, identity[0])
        else:
            item.status = "discharged"
        item.room, item.disposition_note, item.disposed_at = None, note, timezone.now()
    else:
        raise ValidationError("This action is unavailable in the current ED state.")
    item.version += 1
    item.save()
    record(actor, action, identity, patient_id=patient_id, visit=item,
           details={**details, "after": item.status, "version": item.version})
    return item


def _admit_from_ed(actor, visit, bed_id, note, key):
    request = request_admission(actor, visit.patient_id, note, uuid.uuid5(key, "ed-admission-request"),
                                ed_visit_id=visit.pk)
    stay = decide_admission(actor, request.pk, request.version, uuid.uuid5(key, "ed-admission-approval"),
                            "hospital_admit", True, bed_id=bed_id, attending_id=visit.clinician_id)
    visit.inpatient_stay, visit.status = stay, "admitted"


def wait_minutes(visit):
    end = visit.provider_at or visit.disposed_at or timezone.now()
    return max(0, int((end - visit.arrived_at).total_seconds() // 60))
