from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class NursingRecord(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    encounter = models.ForeignKey("clinical.Encounter", null=True, blank=True, on_delete=models.PROTECT)
    observed_at = models.DateTimeField("Observation / assessment time", default=timezone.now)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True
        ordering = ["-observed_at", "-pk"]

    def clean(self):
        super().clean()
        errors = {}
        if self.appointment_id and self.appointment.patient_id != self.patient_id:
            errors["__all__"] = "Patient must match the appointment."
        if self.encounter_id:
            if self.encounter.patient_id != self.patient_id or self.encounter.appointment_id != self.appointment_id:
                errors["encounter"] = "Encounter must match this patient and appointment."
        if isinstance(self.observed_at, datetime):
            if timezone.is_naive(self.observed_at):
                errors["observed_at"] = "Observation time must include a time zone."
            elif self.observed_at > timezone.now():
                errors["observed_at"] = "Observation time cannot be in the future."
            elif self.patient_id and timezone.localdate(self.observed_at) < self.patient.dob:
                errors["observed_at"] = "Observation time cannot precede date of birth."
        if errors:
            raise ValidationError(errors)


def integer_measurement(label, low, high):
    return models.PositiveSmallIntegerField(label, null=True, blank=True,
        validators=[MinValueValidator(low), MaxValueValidator(high)])


def decimal_measurement(label, low, high):
    return models.DecimalField(label, max_digits=7, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal(str(low))), MaxValueValidator(Decimal(str(high)))])


class RoomingAssessment(NursingRecord):
    appointment = models.OneToOneField("scheduling.Appointment", on_delete=models.PROTECT, related_name="rooming")
    chief_complaint = models.CharField(max_length=240)
    pain_score = integer_measurement("Assessment pain score (0–10)", 0, 10)
    observations = models.TextField("General nursing observations", blank=True, validators=[MaxLengthValidator(4000)])
    ready_for_provider = models.BooleanField(default=False)


class VitalObservation(NursingRecord):
    appointment = models.ForeignKey("scheduling.Appointment", on_delete=models.PROTECT, related_name="vitals")
    systolic = integer_measurement("Systolic blood pressure (mmHg)", 20, 350)
    diastolic = integer_measurement("Diastolic blood pressure (mmHg)", 10, 250)
    heart_rate = integer_measurement("Heart rate (beats/min)", 10, 350)
    respiratory_rate = integer_measurement("Respiratory rate (breaths/min)", 1, 100)
    temperature = decimal_measurement("Body temperature", 25, 113)
    temperature_unit = models.CharField(max_length=2, blank=True, choices=[("C", "°C"), ("F", "°F")])
    oxygen_saturation = decimal_measurement("Oxygen saturation (%)", 0, 100)
    height = decimal_measurement("Height", 0.2, 300)
    height_unit = models.CharField(max_length=2, blank=True, choices=[("cm", "cm"), ("m", "m"), ("in", "in")])
    weight = decimal_measurement("Weight", 0.1, 1544)
    weight_unit = models.CharField(max_length=2, blank=True, choices=[("kg", "kg"), ("lb", "lb")])
    pain_score = integer_measurement("Vital observation pain score (0–10)", 0, 10)
    source = models.CharField(max_length=20, choices=[("measured", "Measured"), ("patient_reported", "Patient reported")])
    source_detail = models.CharField("Source detail / equipment context", max_length=160, blank=True)

    def clean(self):
        super().clean()
        errors = {}
        if (self.systolic is None) != (self.diastolic is None):
            errors["systolic"] = "Enter both blood-pressure values or neither."
        if isinstance(self.systolic, int) and isinstance(self.diastolic, int) and self.systolic <= self.diastolic:
            errors["diastolic"] = "Diastolic must be lower than systolic."
        unit_bounds = {
            "temperature": {"C": (25, 45), "F": (77, 113)},
            "height": {"cm": (20, 300), "m": (0.2, 3), "in": (8, 120)},
            "weight": {"kg": (0.1, 700), "lb": (0.2, 1544)},
        }
        for name, bounds in unit_bounds.items():
            value, unit = getattr(self, name), getattr(self, name + "_unit")
            if value is None and unit:
                errors[name] = "A unit requires a measurement value."
            elif value is not None and not unit:
                errors[name + "_unit"] = "Choose the measurement unit."
            elif isinstance(value, Decimal) and value.is_finite() and unit in bounds:
                low, high = map(lambda n: Decimal(str(n)), bounds[unit])
                if not low <= value <= high:
                    errors[name] = "Value is outside the documented demo input bounds for this unit."
        if all(getattr(self, field) is None for field in MEASUREMENTS):
            errors["__all__"] = "Record at least one vital-sign measurement."
        if errors:
            raise ValidationError(errors)


MEASUREMENTS = ("systolic", "diastolic", "heart_rate", "respiratory_rate", "temperature",
                "oxygen_saturation", "height", "weight", "pain_score")


class NursingEvent(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    appointment = models.ForeignKey("scheduling.Appointment", on_delete=models.PROTECT)
    assessment = models.ForeignKey(RoomingAssessment, null=True, blank=True, on_delete=models.PROTECT)
    observation = models.ForeignKey(VitalObservation, null=True, blank=True, on_delete=models.PROTECT)
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
        constraints = [models.CheckConstraint(
            condition=(Q(assessment__isnull=False, observation__isnull=True)
                       | Q(assessment__isnull=True, observation__isnull=False)),
            name="nursing_event_one_record",
        )]
