from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Exists, OuterRef
from django.utils import timezone

from careflow.medications.services import check_version, command_identity, command_transaction
from careflow.patients.access import WRITE_ROLES, roles_for
from careflow.patients.models import AuditEvent
from careflow.scheduling.models import Appointment
from careflow.scheduling.services import _lock_providers, save_appointment, transition_appointment

from .access import patient_for
from .models import PatientAppointmentRequest, PatientMessage, PatientMessageThread, PatientPortalEvent


def physicians():
    return get_user_model().objects.filter(is_active=True, groups__name="Physician").order_by("username")


def care_team(patient):
    appointments = Appointment.objects.filter(patient=patient).exclude(status__in=["cancelled", "no_show"])
    return physicians().filter(pk__in=appointments.values("physician_id"))


def scheduling_writer(actor):
    return bool(set(roles_for(actor)).intersection(WRITE_ROLES))


def conversations(actor, patient=None):
    query = PatientMessageThread.objects.select_related("patient", "physician")
    if patient is not None:
        if patient != patient_for(actor):
            raise PermissionDenied
        return query.filter(patient=patient)
    if "Physician" in roles_for(actor):
        return query.filter(physician=actor)
    raise PermissionDenied


def with_unread(query, from_patient):
    cursor = "physician_seen" if from_patient else "patient_seen"
    unread = PatientMessage.objects.filter(thread=OuterRef("pk"), from_patient=from_patient,
                                            sequence__gt=OuterRef(cursor))
    return query.annotate(unread=Exists(unread))


def _patient(actor):
    patient = patient_for(actor)
    if patient is None:
        raise PermissionDenied
    return patient


def _text(value, maximum, label):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValidationError(f"Enter {label} of 1–{maximum} characters.")
    return value.strip()


def _replay(actor, identity):
    key, digest = identity
    event = PatientPortalEvent.objects.filter(actor=actor, command_key=key).first()
    if event is not None and event.digest != digest:
        raise ValidationError("This submission was already used for different input. Reload the form.")
    return event


def _event(actor, patient, action, identity, **subject):
    audit = AuditEvent.objects.create(actor=actor, patient=patient, action=action)
    PatientPortalEvent.objects.create(audit=audit, actor=actor, command_key=identity[0], digest=identity[1], **subject)


@command_transaction
def start_thread(actor, physician_id, subject, body, key):
    _lock_providers([physician_id])
    patient = _patient(actor)
    if not care_team(patient).filter(pk=physician_id).exists():
        raise ValidationError("Select an available clinician from your care team.")
    subject = _text(subject, 120, "a subject")
    body = _text(body, 2000, "a message")
    identity = command_identity(key, "start_thread", patient.pk, physician_id, subject, body)
    prior = _replay(actor, identity)
    if prior:
        return prior.thread
    thread = PatientMessageThread.objects.create(patient=patient, physician_id=physician_id,
                                                 subject=subject, patient_seen=1)
    PatientMessage.objects.create(thread=thread, sender=actor, sequence=1, from_patient=True, body=body)
    _event(actor, patient, "portal_message_send", identity, thread=thread)
    return thread


def _locked_thread(actor, thread_id, physician_id, as_patient):
    _lock_providers([physician_id])
    patient = _patient(actor) if as_patient else None
    thread = conversations(actor, patient).filter(pk=thread_id, physician_id=physician_id).first()
    if thread is None:
        raise PermissionDenied
    return thread


@command_transaction
def reply(actor, thread_id, physician_id, as_patient, body, version, key):
    thread = _locked_thread(actor, thread_id, physician_id, as_patient)
    body = _text(body, 2000, "a message")
    identity = command_identity(key, "reply", thread_id, as_patient, body, version)
    if _replay(actor, identity):
        return thread
    check_version(version, thread.version)
    thread.version += 1
    thread.save(update_fields=["version", "updated_at"])
    PatientMessage.objects.create(thread=thread, sender=actor, sequence=thread.version, from_patient=as_patient, body=body)
    _event(actor, thread.patient, "portal_message_send" if as_patient else "portal_message_reply", identity, thread=thread)
    return thread


@command_transaction
def mark_read(actor, thread_id, physician_id, as_patient, version, key):
    thread = _locked_thread(actor, thread_id, physician_id, as_patient)
    identity = command_identity(key, "mark_read", thread_id, as_patient, version)
    if _replay(actor, identity):
        return thread
    check_version(version, thread.version)
    cursor = "patient_seen" if as_patient else "physician_seen"
    if thread.messages.filter(from_patient=not as_patient, sequence__gt=getattr(thread, cursor)).exists():
        setattr(thread, cursor, version)
        thread.save(update_fields=[cursor])
        _event(actor, thread.patient, "portal_message_read", identity, thread=thread)
    return thread


def changeable_appointments(patient):
    return Appointment.objects.filter(patient=patient, status="scheduled", encounter__isnull=True)


@command_transaction
def submit_request(actor, kind, physician_id, target_id, start, duration, explanation, key):
    _lock_providers([physician_id])
    patient = _patient(actor)
    kind_choices = PatientAppointmentRequest.Kind
    if kind not in kind_choices.values:
        raise ValidationError("Select a request type.")
    target = None
    if kind == kind_choices.NEW:
        if target_id is not None or not physicians().filter(pk=physician_id).exists():
            raise ValidationError("Select an available clinician.")
    else:
        target = Appointment.objects.filter(pk=target_id, patient=patient, physician_id=physician_id).first()
        if target is None:
            raise ValidationError("Select an eligible appointment.")
    explanation = _text(explanation, 240, "a reason")
    if kind == kind_choices.CANCEL:
        start, duration = None, None
    identity = command_identity(key, "request_submit", patient.pk, kind, physician_id, target_id,
                                start, duration, explanation)
    prior = _replay(actor, identity)
    if prior:
        return prior.appointment_request
    if target and (target.status != "scheduled" or hasattr(target, "encounter")):
        raise ValidationError("Select an eligible appointment.")
    if kind != kind_choices.CANCEL and (
        start is None or timezone.is_naive(start) or start <= timezone.now()
        or type(duration) is not int or not 5 <= duration <= 240 or duration % 5
    ):
        raise ValidationError("Enter a future clinic-local time and a duration of 5–240 minutes in five-minute increments.")
    item = PatientAppointmentRequest.objects.create(
        patient=patient, physician_id=physician_id, requested_by=actor, target=target,
        target_version=target.version if target else None, kind=kind, proposed_start=start,
        duration=duration, explanation=explanation,
    )
    _event(actor, patient, "portal_request_submit", identity, appointment_request=item)
    return item


@command_transaction
def review_request(actor, request_id, physician_id, decision, version, response, key, confirmed):
    _lock_providers([physician_id])
    if not scheduling_writer(actor):
        raise PermissionDenied
    if decision not in ("approved", "rejected") or confirmed is not True:
        raise ValidationError("Confirm the selected review decision.")
    response = _text(response, 240, "a response")
    item = PatientAppointmentRequest.objects.select_related("target", "patient", "physician").filter(
        pk=request_id, physician_id=physician_id,
    ).first()
    if item is None:
        raise PermissionDenied
    identity = command_identity(key, "request_review", request_id, decision, version, response)
    if _replay(actor, identity):
        return item
    check_version(version, item.version)
    if item.status != "pending":
        raise ValidationError("This request has already been reviewed.")
    if decision == "approved":
        item.resulting_appointment = _apply_request(actor, item, response)
    item.status = decision
    item.response = response
    item.reviewer = actor
    item.reviewed_at = timezone.now()
    item.version += 1
    item.save(update_fields=["status", "response", "reviewer", "reviewed_at", "version", "resulting_appointment"])
    _event(actor, item.patient, "portal_request_" + decision, identity, appointment_request=item)
    return item


def _apply_request(actor, item, response):
    target = item.target
    if target and (target.patient_id != item.patient_id or target.physician_id != item.physician_id
                   or target.version != item.target_version or target.status != "scheduled"
                   or hasattr(target, "encounter")):
        raise ValidationError("The appointment changed or a visit started. Reject this request or ask for a new one.")
    if item.kind == "cancel":
        return transition_appointment(actor, target.pk, "cancel", item.target_version, response)
    return save_appointment(actor, {
        "patient": item.patient, "physician": item.physician, "start_at": item.proposed_start,
        "duration": item.duration, "appointment_type": target.appointment_type if target else "Portal request",
        "reason": target.reason if target else item.explanation, "version": item.target_version,
    }, target.pk if target else None)
