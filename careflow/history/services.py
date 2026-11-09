from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import F
from django.utils import timezone

from careflow.clinical.access import can_write
from careflow.clinical.models import Encounter
from careflow.patients.models import AuditEvent
from careflow.scheduling.services import _lock_providers
from .access import can_maintain
from .forms import REGISTRY
from .models import Allergy, AllergyState, HistoryEvent, PatientHistoryLock


class HistoryConflict(ValidationError):
    pass


def _lock_patient(patient_id):
    changed = PatientHistoryLock.objects.filter(patient_id=patient_id).update(revision=F("revision") + 1)
    if not changed:
        row, _ = PatientHistoryLock.objects.get_or_create(patient_id=patient_id)
        PatientHistoryLock.objects.filter(pk=row.pk).update(revision=F("revision") + 1)


def snapshot(record):
    result = {}
    for field in record._meta.fields:
        value = field.value_from_object(record)
        result[field.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return result


def _event(patient_id, actor, kind, record, action, before, encounter=None):
    after = snapshot(record)
    changed = [key for key, value in after.items() if before.get(key) != value]
    audit = AuditEvent.objects.create(actor=actor, patient_id=patient_id,
        action=f"history_{kind}_{action}", changed_fields=changed)
    HistoryEvent.objects.create(patient_id=patient_id, encounter=encounter,
        kind=kind, record_id=record.pk, audit=audit, before=before, after=after)


def _require_treating(actor, patient_id):
    if not can_maintain(actor, patient_id):
        raise PermissionDenied


def _busy(error):
    if isinstance(error, IntegrityError) or "locked" in str(error).lower():
        raise HistoryConflict("The record changed, a primary diagnosis already exists, or the database is busy. Reload and retry.") from error
    raise error


def _sync_allergy_state(patient_id, actor):
    active = Allergy.objects.filter(patient_id=patient_id, status="active").exists()
    state = AllergyState.objects.filter(patient_id=patient_id).first()
    before = snapshot(state) if state else {}
    state = state or AllergyState(patient_id=patient_id)
    if active:
        state.status = "documented"
    elif state.status == "documented":
        state.status = "not_reviewed"
    state.reviewed_by = None
    state.reviewed_at = None
    if state.pk:
        state.version += 1
    state.save()
    _event(patient_id, actor, "allergy_state", state, "sync", before)


def save_record(actor, patient_id, kind, data, version, record_id=None, encounter_id=None, review=False):
    model, form_class, _ = REGISTRY[kind]
    try:
        if kind == "diagnoses":
            original = Encounter.objects.get(pk=encounter_id, patient_id=patient_id)
            if not can_write(actor, original.physician_id):
                raise PermissionDenied
        else:
            _require_treating(actor, patient_id)
        with transaction.atomic():
            if kind == "diagnoses":
                _lock_providers([original.physician_id])
            _lock_patient(patient_id)
            encounter = None
            if kind == "diagnoses":
                encounter = Encounter.objects.get(pk=encounter_id, patient_id=patient_id)
                if not can_write(actor, encounter.physician_id):
                    raise PermissionDenied
                if encounter.status != "in_progress":
                    raise HistoryConflict("Completed encounter diagnoses cannot be changed.")
            else:
                _require_treating(actor, patient_id)
            query = model.objects.filter(patient_id=patient_id)
            if encounter:
                query = query.filter(encounter=encounter)
            record = query.get(pk=record_id) if record_id else model(patient_id=patient_id)
            if (record.pk and record.version != version) or (not record.pk and (version != 0 or review)):
                raise HistoryConflict("This record changed. Reload before retrying.")
            if not data.get("synthetic_confirmed"):
                raise ValidationError("Confirm synthetic information only.")
            before = snapshot(record) if record.pk else {}
            creating = not record.pk
            if review:
                record.reviewed_by = actor
                record.reviewed_at = timezone.now()
            else:
                for name in form_class._meta.fields:
                    value = data[name]
                    setattr(record, name, value.strip() if isinstance(value, str) else value)
                record.reviewed_by = None
                record.reviewed_at = None
            if encounter:
                record.encounter = encounter
            if creating:
                record.author = actor
            else:
                record.version += 1
            record.updated_by = actor
            record.full_clean()
            record.save()
            _event(patient_id, actor, kind, record, "review" if review else "create" if creating else "edit", before, encounter)
            if kind == "allergies" and not review:
                _sync_allergy_state(patient_id, actor)
            return record
    except (IntegrityError, OperationalError) as error:
        _busy(error)


def review_allergy_state(actor, patient_id, status, version, confirmed):
    try:
        _require_treating(actor, patient_id)
        with transaction.atomic():
            _lock_patient(patient_id)
            _require_treating(actor, patient_id)
            state = AllergyState.objects.filter(patient_id=patient_id).first()
            if (state and state.version != version) or (not state and version != 0):
                raise HistoryConflict("The allergy assessment changed. Reload before retrying.")
            if not confirmed:
                raise ValidationError("Explicit synthetic review confirmation is required.")
            active = Allergy.objects.filter(patient_id=patient_id, status="active").exists()
            if (active and status != "documented") or (not active and status == "documented"):
                raise ValidationError("The allergy assessment must agree with the active allergy entries.")
            before = snapshot(state) if state else {}
            state = state or AllergyState(patient_id=patient_id)
            state.status = status
            state.reviewed_by = actor if status != "not_reviewed" else None
            state.reviewed_at = timezone.now() if status != "not_reviewed" else None
            if state.pk:
                state.version += 1
            state.full_clean()
            state.save()
            _event(patient_id, actor, "allergy_state", state, "review", before)
            return state
    except (IntegrityError, OperationalError) as error:
        _busy(error)
