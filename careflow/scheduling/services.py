from datetime import UTC, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError, connection, transaction
from django.db.models import F
from django.utils import timezone

from careflow.patients.access import WRITE_ROLES, roles_for
from careflow.patients.models import AuditEvent
from .access import physicians_for
from .models import Appointment, AppointmentEvent, ProviderScheduleLock


class AppointmentConflict(ValidationError):
    pass


def _require_writer(actor):
    if not any(role in WRITE_ROLES for role in roles_for(actor)):
        raise PermissionDenied


def _lock_providers(ids):
    # The first SQL operation in the transaction is a write, including when no row exists.
    # SQLite serializes writers; PostgreSQL locks each provider row in a stable order.
    for physician_id in sorted(set(ids)):
        changed = ProviderScheduleLock.objects.filter(physician_id=physician_id).update(revision=F("revision") + 1)
        if not changed:
            lock, _ = ProviderScheduleLock.objects.get_or_create(physician_id=physician_id)
            ProviderScheduleLock.objects.filter(pk=lock.pk).update(revision=F("revision") + 1)


def _event(appointment, actor, action, previous="", reason="", details=None, fields=None):
    audit = AuditEvent.objects.create(
        actor=actor, patient=appointment.patient, action=action, changed_fields=fields or [],
    )
    AppointmentEvent.objects.create(
        appointment=appointment, audit=audit, previous_status=previous,
        next_status=appointment.status, reason=reason, details=details or {},
    )


def save_appointment(actor, data, appointment_id=None):
    _require_writer(actor)
    original = Appointment.objects.get(pk=appointment_id) if appointment_id else None
    provider_ids = [data["physician"].pk]
    if original:
        provider_ids.append(original.physician_id)
    try:
        with transaction.atomic():
            _lock_providers(provider_ids)
            current = Appointment.objects.select_for_update().get(pk=appointment_id) if original else Appointment()
            if original and (current.version != data["version"] or current.status != Appointment.Status.SCHEDULED):
                raise AppointmentConflict("This appointment changed or can no longer be rescheduled. Reload before retrying.")
            if original and current.patient_id != data["patient"].pk:
                raise ValidationError("Rescheduling must preserve the patient.")
            if not physicians_for(actor).filter(pk=data["physician"].pk).exists():
                raise ValidationError("Choose an active physician.")
            if timezone.is_naive(data["start_at"]):
                raise ValidationError("Appointment start must include a time zone.")
            start = data["start_at"].astimezone(UTC)
            if start <= timezone.now():
                raise ValidationError("Choose a future appointment start.")
            end = start + timedelta(minutes=data["duration"])
            conflicts = Appointment.objects.filter(
                physician=data["physician"], status__in=["scheduled", "arrived"],
                start_at__lt=end, end_at__gt=start,
            ).exclude(pk=current.pk)
            if conflicts.exists():
                raise AppointmentConflict("The physician is unavailable during this interval. Choose another time.")
            previous = {
                "start": current.start_at.isoformat(), "end": current.end_at.isoformat(),
                "physician": current.physician_id,
            } if original else {}
            changed_fields = [
                name for name, value in {
                    "patient": data["patient"], "physician": data["physician"],
                    "start_at": start, "end_at": end,
                    "appointment_type": data["appointment_type"], "reason": data["reason"],
                }.items()
                if not original or getattr(current, name) != value
            ]
            current.patient = data["patient"]
            current.physician = data["physician"]
            current.start_at = start
            current.end_at = end
            current.appointment_type = data["appointment_type"]
            current.reason = data["reason"]
            if original:
                current.version += 1
            current.full_clean()
            current.save()
            _event(
                current, actor, "appointment_reschedule" if original else "appointment_create",
                previous="scheduled" if original else "",
                details={"before": previous, "after": {
                    "start": current.start_at.isoformat(), "end": current.end_at.isoformat(),
                    "physician": current.physician_id,
                }},
                fields=changed_fields,
            )
            return current
    except IntegrityError as error:
        raise AppointmentConflict("The slot changed during booking. Reload the schedule and retry.") from error
    except OperationalError as error:
        if connection.vendor == "sqlite" and "locked" in str(error).lower():
            raise AppointmentConflict("Scheduling is busy. Retry after refreshing the schedule.") from error
        raise


def transition_appointment(actor, appointment_id, action, version, reason=""):
    _require_writer(actor)
    original = Appointment.objects.get(pk=appointment_id)
    try:
        with transaction.atomic():
            _lock_providers([original.physician_id])
            appointment = Appointment.objects.select_for_update().get(pk=appointment_id)
            # Clinical start uses the same provider lock; preserve started encounter context.
            if hasattr(appointment, "encounter"):
                raise AppointmentConflict("An encounter has started. Appointment transitions are no longer available.")
            if appointment.version != version:
                raise AppointmentConflict("This appointment changed. Reload before retrying.")
            permitted = {
                ("scheduled", "arrive"): "arrived",
                ("scheduled", "cancel"): "cancelled",
                ("scheduled", "no_show"): "no_show",
                ("arrived", "cancel"): "cancelled",
            }
            target = permitted.get((appointment.status, action))
            if not target:
                raise AppointmentConflict("This status transition is not allowed.")
            if action in ("cancel", "no_show") and not reason.strip():
                raise ValidationError("Provide a reason for cancellation or no-show.")
            if len(reason) > 240:
                raise ValidationError("Use a reason of at most 240 characters.")
            if action == "arrive" and timezone.localdate(appointment.start_at) != timezone.localdate():
                raise ValidationError("Check-in is available on the appointment's clinic-local date.")
            if action == "no_show" and appointment.start_at > timezone.now():
                raise ValidationError("Do not mark a future appointment as no-show.")
            previous = appointment.status
            appointment.status = target
            appointment.version += 1
            if action == "arrive":
                appointment.checked_in_at = timezone.now()
                appointment.checked_in_by = actor
            appointment.save()
            _event(
                appointment, actor, "appointment_" + action, previous=previous,
                reason=reason.strip(),
                fields=["status", "checked_in_at", "checked_in_by"] if action == "arrive" else ["status"],
            )
            return appointment
    except OperationalError as error:
        if connection.vendor == "sqlite" and "locked" in str(error).lower():
            raise AppointmentConflict("Scheduling is busy. Refresh and retry the action.") from error
        raise
