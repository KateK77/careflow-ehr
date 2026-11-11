from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.utils import timezone

from careflow.medications.services import check_version, command_identity, command_transaction
from careflow.patients.access import roles_for
from careflow.patients.models import AuditEvent, Patient
from .access import require_operator
from .models import AdmissionRequest, Bed, Department, EmergencyVisit, HospitalEvent, InpatientStay, OperationLock, Room, Ward


def lock_operations():
    if not OperationLock.objects.filter(pk=1).update(revision=F("revision") + 1):
        OperationLock.objects.get_or_create(pk=1)
        OperationLock.objects.filter(pk=1).update(revision=F("revision") + 1)


def begin(actor, key, action, *payload):
    lock_operations()
    identity = command_identity(key, action, *payload)
    prior = HospitalEvent.objects.filter(actor=actor, key=identity[0]).first()
    if prior and prior.digest != identity[1]:
        raise ValidationError("This submission was already used for different input.")
    return identity, prior


def record(actor, action, identity, *, patient_id=None, **data):
    audit = AuditEvent.objects.create(actor=actor, patient_id=patient_id, action=action)
    return HospitalEvent.objects.create(audit=audit, actor=actor, key=identity[0], digest=identity[1], **data)


def value(text, limit, label):
    if not isinstance(text, str) or not text.strip() or len(text.strip()) > limit:
        raise ValidationError(f"Enter {label} of 1 to {limit} characters.")
    return text.strip()


def selected(query, **criteria):
    item = query.filter(**criteria).first()
    if item is None:
        raise ValidationError("The selected record is unavailable.")
    return item


def physicians():
    return get_user_model().objects.filter(is_active=True, groups__name="Physician")


def available_beds():
    return Bed.objects.filter(room__ward__kind="inpatient").exclude(stays__status="active")


FACILITIES = {"department": Department, "ward": Ward, "room": Room, "bed": Bed}


@command_transaction
def add_facility(actor, kind, name, parent_id, ward_kind, key):
    require_operator(actor)
    identity, prior = begin(actor, key, "hospital_facility_add", kind, name, parent_id, ward_kind)
    model = FACILITIES.get(kind)
    if model is None:
        raise ValidationError("Choose a facility type.")
    if prior:
        return model.objects.get(pk=prior.details["facility"])
    name = value(name, 80, "a fictional name")
    if kind == "department":
        item = Department(name=name)
    elif kind == "ward":
        item = Ward(name=name, department=selected(Department.objects, pk=parent_id), kind=ward_kind)
    elif kind == "room":
        item = Room(name=name, ward=selected(Ward.objects, pk=parent_id))
    else:
        item = Bed(name=name, room=selected(Room.objects, pk=parent_id, ward__kind="inpatient"))
    item.full_clean()
    item.save()
    record(actor, "hospital_facility_add", identity, details={"type": kind, "facility": item.pk})
    return item


@command_transaction
def request_admission(actor, patient_id, reason, key, *, ed_visit_id=None):
    require_operator(actor)
    context = () if ed_visit_id is None else (ed_visit_id,)
    identity, prior = begin(actor, key, "hospital_admission_request", patient_id, reason, *context)
    if prior:
        return prior.request
    patient = selected(Patient.objects, pk=patient_id)
    ed_visit = EmergencyVisit.objects.filter(patient=patient, disposed_at__isnull=True).first()
    if ed_visit and ed_visit.pk != ed_visit_id:
        raise ValidationError("Use the ED disposition to admit a patient with an active ED visit.")
    if ed_visit_id is not None and (not ed_visit or ed_visit.status not in ("provider", "observation")):
        raise ValidationError("The ED visit is unavailable for admission.")
    if (InpatientStay.objects.filter(request__patient=patient, status="active").exists()
            or AdmissionRequest.objects.filter(patient=patient, status="pending").exists()):
        raise ValidationError("This patient already has an active stay or pending request.")
    item = AdmissionRequest.objects.create(patient=patient, reason=value(reason, 240, "a fictional admission reason"))
    record(actor, "hospital_admission_request", identity, patient_id=patient.pk, request=item)
    return item


@command_transaction
def decide_admission(actor, request_id, version, key, action, confirmed, *, bed_id=None, attending_id=None, reason=""):
    require_operator(actor)
    identity, prior = begin(actor, key, action, request_id, version, confirmed, bed_id, attending_id, reason)
    if prior:
        return prior.stay or prior.request
    item = selected(AdmissionRequest.objects, pk=request_id)
    check_version(version, item.version)
    if confirmed is not True or item.status != "pending":
        raise ValidationError("Confirm an available admission decision.")
    stay = None
    bed = None
    details = {}
    if action == "hospital_admit":
        if InpatientStay.objects.filter(request__patient_id=item.patient_id, status="active").exists():
            raise ValidationError("This patient already has an active stay.")
        bed = selected(available_beds(), pk=bed_id)
        attending = selected(physicians(), pk=attending_id)
        stay = InpatientStay.objects.create(request=item, bed=bed, attending=attending)
        item.status = "admitted"
    elif action == "hospital_admission_cancel":
        item.status = "cancelled"
        details["reason"] = value(reason, 240, "a cancellation reason")
    else:
        raise ValidationError("Choose an available admission decision.")
    item.version += 1
    item.save(update_fields=["version", "status"])
    record(actor, action, identity, patient_id=item.patient_id, request=item, stay=stay, next_bed=bed, details=details)
    return stay or item


@command_transaction
def change_stay(actor, patient_id, stay_id, version, key, action, confirmed, *, bed_id=None, note=""):
    if action == "hospital_discharge_plan":
        if "Physician" not in roles_for(actor):
            raise PermissionDenied
    else:
        require_operator(actor)
    identity, prior = begin(actor, key, action, patient_id, stay_id, version, confirmed, bed_id, note)
    stay = InpatientStay.objects.filter(pk=stay_id, request__patient_id=patient_id).select_related("request").first()
    if stay is None or (action == "hospital_discharge_plan" and stay.attending_id != actor.pk):
        raise PermissionDenied
    if prior:
        return stay
    check_version(version, stay.version)
    if confirmed is not True or stay.status != "active":
        raise ValidationError("Confirm an action on an active stay.")
    previous = next_bed = None
    if action == "hospital_transfer":
        note = value(note, 240, "a transfer reason")
        previous = stay.bed
        next_bed = selected(available_beds(), pk=bed_id)
        stay.bed = next_bed
    elif action == "hospital_discharge_plan":
        stay.discharge_plan = note = value(note, 2000, "a fictional discharge plan")
    elif action == "hospital_discharge":
        if not stay.discharge_plan:
            raise ValidationError("The attending physician must document a discharge plan first.")
        stay.discharge_summary = note = value(note, 2000, "a fictional discharge summary")
        stay.discharged_at, stay.discharged_by, stay.status = timezone.now(), actor, "discharged"
        previous, stay.bed = stay.bed, None
    else:
        raise ValidationError("Choose an available stay action.")
    stay.version += 1
    stay.save()
    record(actor, action, identity, patient_id=patient_id, request=stay.request, stay=stay,
           previous_bed=previous, next_bed=next_bed, details={"note": note, "version": stay.version})
    return stay
