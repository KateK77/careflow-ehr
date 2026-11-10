from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError, transaction

from decimal import Decimal

from careflow.history.services import snapshot as history_snapshot
from careflow.patients.models import AuditEvent
from careflow.scheduling.models import Appointment
from careflow.scheduling.services import _lock_providers
from .access import can_document, nursing_writer
from .forms import FORMS
from .models import NursingEvent


class NursingConflict(ValidationError):
    pass


def snapshot(record):
    return {key: str(value) if isinstance(value, Decimal) else value
            for key, value in history_snapshot(record).items()}


def _event(record, actor, kind, before, creating):
    after = snapshot(record)
    audit = AuditEvent.objects.create(actor=actor, patient_id=record.patient_id,
        action=f"nursing_{kind}_{'create' if creating else 'edit'}",
        changed_fields=[key for key, value in after.items() if before.get(key) != value])
    NursingEvent.objects.create(patient_id=record.patient_id, appointment=record.appointment,
        assessment=record if kind == "assessment" else None,
        observation=record if kind == "vitals" else None, audit=audit, before=before, after=after)


def save_documentation(actor, patient_id, appointment_id, kind, data, version, record_id=None):
    if not nursing_writer(actor):
        raise PermissionDenied
    form_class = FORMS[kind]
    model = form_class._meta.model
    try:
        original = Appointment.objects.get(pk=appointment_id, patient_id=patient_id)
        with transaction.atomic():
            _lock_providers([original.physician_id])
            appointment = Appointment.objects.select_for_update().get(pk=appointment_id, patient_id=patient_id)
            if not can_document(actor, appointment):
                raise NursingConflict("Nursing writes require an arrived appointment without a completed encounter. Reload the record.")
            if not data.get("synthetic_confirmed"):
                raise ValidationError("Confirm synthetic information only.")
            if kind == "assessment" and not record_id and model.objects.filter(appointment=appointment).exists():
                raise NursingConflict("Rooming assessment already exists. Open it for a versioned correction.")
            record = (model.objects.get(pk=record_id, patient_id=patient_id, appointment=appointment)
                      if record_id else model(patient_id=patient_id, appointment=appointment))
            if (record.pk and record.version != version) or (not record.pk and version != 0):
                raise NursingConflict("This documentation changed. Reload before retrying.")
            incoming_encounter = data.get("encounter")
            incoming_id = incoming_encounter.pk if incoming_encounter else None
            if record.pk and record.encounter_id != incoming_id:
                raise ValidationError({"encounter": "An existing record's encounter context cannot be changed."})
            before = snapshot(record) if record.pk else {}
            creating = record.pk is None
            for name in form_class._meta.fields:
                value = data[name]
                setattr(record, name, value.strip() if isinstance(value, str) else value)
            if creating:
                record.recorded_by = actor
            else:
                record.version += 1
            record.updated_by = actor
            record.full_clean()
            record.save()
            _event(record, actor, kind, before, creating)
            return record
    except (IntegrityError, OperationalError) as error:
        if isinstance(error, IntegrityError) or "locked" in str(error).lower():
            raise NursingConflict("Documentation changed or the database is busy. Reload and retry.") from error
        raise
