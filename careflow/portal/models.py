from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PatientPortalAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    patient = models.OneToOneField("patients.Patient", on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Patient ownership cannot be reassigned.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)


class PatientVisibleResultRelease(models.Model):
    result = models.OneToOneField("labs.LabResult", on_delete=models.PROTECT, related_name="portal_release")
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Release history is immutable.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

class PatientMessageThread(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subject = models.CharField(max_length=120)
    version = models.PositiveIntegerField(default=1)
    patient_seen = models.PositiveIntegerField(default=0)
    physician_seen = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-pk"]


class AppendOnly(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("This portal history record cannot be edited.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("This portal history record cannot be deleted.")


class PatientMessage(AppendOnly):
    thread = models.ForeignKey(PatientMessageThread, on_delete=models.PROTECT, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    sequence = models.PositiveIntegerField()
    from_patient = models.BooleanField()
    body = models.TextField(max_length=2000)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["thread", "sequence"], name="portal_message_sequence"),
        ]


class PatientAppointmentRequest(models.Model):
    class Kind(models.TextChoices):
        NEW = "new", "New appointment"
        RESCHEDULE = "reschedule", "Reschedule"
        CANCEL = "cancel", "Cancellation"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    target = models.ForeignKey("scheduling.Appointment", null=True, on_delete=models.PROTECT, related_name="+")
    target_version = models.PositiveIntegerField(null=True)
    resulting_appointment = models.ForeignKey("scheduling.Appointment", null=True, on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    proposed_start = models.DateTimeField(null=True)
    duration = models.PositiveSmallIntegerField(null=True)
    explanation = models.CharField(max_length=240)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    response = models.CharField(max_length=240, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="+")
    reviewed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["target"], condition=models.Q(status="pending", target__isnull=False),
                                    name="portal_pending_target"),
            models.UniqueConstraint(fields=["patient", "physician", "proposed_start"],
                                    condition=models.Q(status="pending", kind="new"), name="portal_pending_slot"),
            models.CheckConstraint(condition=(
                models.Q(kind="new", target__isnull=True, target_version__isnull=True,
                         proposed_start__isnull=False, duration__isnull=False)
                | models.Q(kind="reschedule", target__isnull=False, target_version__isnull=False,
                           proposed_start__isnull=False, duration__isnull=False)
                | models.Q(kind="cancel", target__isnull=False, target_version__isnull=False,
                           proposed_start__isnull=True, duration__isnull=True)
            ), name="portal_request_context"),
            models.CheckConstraint(condition=(
                models.Q(status="pending", reviewer__isnull=True, reviewed_at__isnull=True, resulting_appointment__isnull=True)
                | models.Q(status="rejected", reviewer__isnull=False, reviewed_at__isnull=False, resulting_appointment__isnull=True)
                | models.Q(status="approved", reviewer__isnull=False, reviewed_at__isnull=False, resulting_appointment__isnull=False)
            ), name="portal_request_review_state"),
        ]


class PatientPortalEvent(AppendOnly):
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    command_key = models.UUIDField()
    digest = models.CharField(max_length=64)
    thread = models.ForeignKey(PatientMessageThread, null=True, on_delete=models.PROTECT, related_name="events")
    appointment_request = models.ForeignKey(PatientAppointmentRequest, null=True, on_delete=models.PROTECT, related_name="events")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["actor", "command_key"], name="portal_unique_command"),
            models.CheckConstraint(condition=(
                models.Q(thread__isnull=False, appointment_request__isnull=True)
                | models.Q(thread__isnull=True, appointment_request__isnull=False)
            ), name="portal_event_subject"),
        ]
