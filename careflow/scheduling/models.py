from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class ProviderScheduleLock(models.Model):
    physician = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField(default=0)


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ARRIVED = "arrived", "Arrived"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No show"

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    appointment_type = models.CharField(max_length=80)
    reason = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    version = models.PositiveIntegerField(default=1)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="appointment_checkins",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "pk"]
        indexes = [models.Index(fields=["physician", "start_at", "end_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(end_at__gt=F("start_at")), name="appointment_positive_interval"),
            models.CheckConstraint(
                condition=Q(status__in=["scheduled", "arrived", "cancelled", "no_show"]),
                name="appointment_known_status",
            ),
            models.UniqueConstraint(
                fields=["physician", "start_at"],
                condition=Q(status__in=["scheduled", "arrived"]),
                name="appointment_reserved_start",
            ),
        ]

    def clean(self):
        super().clean()
        if self.start_at and self.end_at:
            if timezone.is_naive(self.start_at) or timezone.is_naive(self.end_at):
                raise ValidationError("Appointment times must include a time zone.")
            minutes = (self.end_at - self.start_at).total_seconds() / 60
            if not 5 <= minutes <= 240 or minutes % 5:
                raise ValidationError("Use a duration of 5–240 minutes in five-minute increments.")

    @property
    def duration(self):
        return int((self.end_at - self.start_at) / timedelta(minutes=1))


class AppointmentEvent(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, related_name="events")
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    previous_status = models.CharField(max_length=12, blank=True)
    next_status = models.CharField(max_length=12)
    reason = models.CharField(max_length=240, blank=True)
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
