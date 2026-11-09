from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Encounter(models.Model):
    appointment = models.OneToOneField("scheduling.Appointment", on_delete=models.PROTECT)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, default="in_progress", choices=[
        ("in_progress", "In progress"), ("completed", "Completed"),
    ])
    started_at = models.DateTimeField(default=timezone.now, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True, editable=False)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-started_at", "-pk"]
        constraints = [models.CheckConstraint(
            condition=(Q(status="in_progress", completed_at__isnull=True)
                       | Q(status="completed", completed_at__isnull=False)),
            name="encounter_status_timestamp",
        )]

    def clean(self):
        if self.appointment_id:
            if self.patient_id != self.appointment.patient_id or self.physician_id != self.appointment.physician_id:
                raise ValidationError("Encounter context must match its appointment.")


class Note(models.Model):
    encounter = models.OneToOneField(Encounter, on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subjective = models.TextField(blank=True, max_length=20000, validators=[MaxLengthValidator(20000)])
    objective = models.TextField(blank=True, max_length=20000, validators=[MaxLengthValidator(20000)])
    assessment = models.TextField(blank=True, max_length=20000, validators=[MaxLengthValidator(20000)])
    plan = models.TextField(blank=True, max_length=20000, validators=[MaxLengthValidator(20000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signed_at = models.DateTimeField(null=True, blank=True, editable=False)
    version = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk, signed_at__isnull=False).exists():
            raise ValidationError("Signed notes cannot be modified.")
        return super().save(*args, **kwargs)

    def clean(self):
        if self.encounter_id and self.author_id != self.encounter.physician_id:
            raise ValidationError("Note author must be the encounter physician.")

    @property
    def patient(self):
        return self.encounter.patient


class ClinicalEvent(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.PROTECT, related_name="events")
    note = models.ForeignKey(Note, null=True, blank=True, on_delete=models.PROTECT)
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
