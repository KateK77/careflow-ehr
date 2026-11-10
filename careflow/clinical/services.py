from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone

from careflow.patients.models import AuditEvent
from careflow.scheduling.models import Appointment
from careflow.scheduling.services import _lock_providers
from .access import can_write
from .models import ClinicalEvent, Encounter, Note

SECTIONS = ("subjective", "objective", "assessment", "plan")


class ClinicalConflict(ValidationError):
    pass


def _require_owner(actor, physician_id):
    if not can_write(actor, physician_id):
        raise PermissionDenied


def _event(encounter, actor, action, fields, note=None):
    audit = AuditEvent.objects.create(actor=actor, patient=encounter.patient,
                                      action=action, changed_fields=fields)
    ClinicalEvent.objects.create(encounter=encounter, note=note, audit=audit)


def _busy(error):
    if isinstance(error, IntegrityError) or "locked" in str(error).lower():
        raise ClinicalConflict("The record changed or is busy. Reload and retry.") from error
    raise error


def start_encounter(actor, appointment_id, version):
    original = Appointment.objects.get(pk=appointment_id)
    _require_owner(actor, original.physician_id)
    try:
        with transaction.atomic():
            _lock_providers([original.physician_id])
            appointment = Appointment.objects.select_for_update().get(pk=appointment_id)
            if appointment.version != version or appointment.status != "arrived":
                raise ClinicalConflict("Start requires the current version of an arrived appointment.")
            if Encounter.objects.filter(appointment=appointment).exists():
                raise ClinicalConflict("An encounter already exists for this appointment.")
            encounter = Encounter(appointment=appointment, patient=appointment.patient,
                                  physician=appointment.physician)
            encounter.full_clean()
            encounter.save()
            _event(encounter, actor, "encounter_start", ["status", "started_at"])
            return encounter
    except (IntegrityError, OperationalError) as error:
        _busy(error)


def save_note(actor, encounter_id, data, version):
    original = Encounter.objects.get(pk=encounter_id)
    _require_owner(actor, original.physician_id)
    try:
        with transaction.atomic():
            _lock_providers([original.physician_id])
            encounter = Encounter.objects.select_for_update().get(pk=encounter_id)
            if encounter.status != "in_progress":
                raise ClinicalConflict("Completed encounters cannot be edited.")
            note = Note.objects.filter(encounter=encounter).first()
            if (note and (note.version != version or note.signed_at)) or (not note and version != 0):
                raise ClinicalConflict("The note changed or is signed. Reload before retrying.")
            if note and note.author_id != actor.pk:
                raise PermissionDenied
            if not data.get("synthetic_confirmed"):
                raise ValidationError("Confirm that the note contains synthetic information only.")
            creating = note is None
            note = note or Note(encounter=encounter, author=actor)
            changed = [key for key in SECTIONS if getattr(note, key) != data[key]]
            for key in SECTIONS:
                setattr(note, key, data[key])
            if not creating:
                note.version += 1
            note.full_clean()
            note.save()
            _event(encounter, actor, "note_create" if creating else "note_edit", changed, note)
            return note
    except (IntegrityError, OperationalError) as error:
        _busy(error)


def sign_note(actor, note_id, version, confirmed):
    original = Note.objects.select_related("encounter").get(pk=note_id)
    _require_owner(actor, original.encounter.physician_id)
    if original.author_id != actor.pk:
        raise PermissionDenied
    try:
        with transaction.atomic():
            _lock_providers([original.encounter.physician_id])
            note = Note.objects.select_related("encounter").get(pk=note_id)
            if note.signed_at or note.version != version or note.encounter.status != "in_progress":
                raise ClinicalConflict("The note changed, is signed, or its encounter is completed.")
            if not confirmed or not all(getattr(note, key).strip() for key in SECTIONS):
                raise ValidationError("Signing requires confirmation and all four SOAP sections.")
            note.signed_at = timezone.now()
            note.version += 1
            note.save()
            _event(note.encounter, actor, "note_sign", ["signed_at"], note)
            return note
    except OperationalError as error:
        _busy(error)


def complete_encounter(actor, encounter_id, version):
    original = Encounter.objects.get(pk=encounter_id)
    _require_owner(actor, original.physician_id)
    try:
        with transaction.atomic():
            _lock_providers([original.physician_id])
            encounter = Encounter.objects.get(pk=encounter_id)
            if encounter.version != version or encounter.status != "in_progress":
                raise ClinicalConflict("The encounter changed or is already completed.")
            if not Note.objects.filter(encounter=encounter, signed_at__isnull=False).exists():
                raise ValidationError("Sign the SOAP note before completing the encounter.")
            encounter.status = "completed"
            encounter.completed_at = timezone.now()
            encounter.version += 1
            encounter.save()
            _event(encounter, actor, "encounter_complete", ["status", "completed_at"])
            return encounter
    except OperationalError as error:
        _busy(error)
