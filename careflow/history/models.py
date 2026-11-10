from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class PatientHistoryLock(models.Model):
    patient = models.OneToOneField("patients.Patient", on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField(default=0)


class ClinicalRecord(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    label = models.CharField(max_length=160)
    comments = models.TextField(blank=True, validators=[MaxLengthValidator(4000)])
    source = models.CharField(max_length=20, choices=[
        ("patient_reported", "Patient reported"), ("documented", "Documented"),
        ("family_reported", "Family reported"),
    ])
    source_detail = models.CharField(max_length=160, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.PROTECT, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True
        ordering = ["-updated_at", "-pk"]

    def clean(self):
        super().clean()
        errors = {}
        for field in self._meta.fields:
            if isinstance(field, models.DateField) and not isinstance(field, models.DateTimeField):
                value = getattr(self, field.name)
                if value and value > timezone.localdate():
                    errors[field.name] = "Clinical history dates cannot be in the future."
        for first, last in [("start_date", "end_date"), ("onset_date", "resolution_date")]:
            start, end = getattr(self, first, None), getattr(self, last, None)
            if start and end and end < start:
                errors[last] = "End/resolution date cannot precede onset/start date."
        if errors:
            raise ValidationError(errors)

    @property
    def review_status(self):
        return "Reviewed" if self.reviewed_at else "Not reviewed"

    def __str__(self):
        return self.label


class MedicalHistory(ClinicalRecord):
    category = models.CharField(max_length=16, choices=[
        ("medical", "Past medical"), ("surgical", "Past surgical"),
        ("family", "Family"), ("social", "Social"),
    ])
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class Problem(ClinicalRecord):
    status = models.CharField(max_length=12, choices=[
        ("active", "Active"), ("resolved", "Resolved"), ("inactive", "Inactive"),
    ], default="active")
    onset_date = models.DateField(null=True, blank=True)
    resolution_date = models.DateField(null=True, blank=True)
    code = models.CharField("Mock terminology code", max_length=40, blank=True)

    def clean(self):
        super().clean()
        if self.status == "resolved" and not self.resolution_date:
            raise ValidationError({"resolution_date": "Provide a resolution date for a resolved problem."})
        if self.status != "resolved" and self.resolution_date:
            raise ValidationError({"resolution_date": "Only resolved problems have a resolution date."})


class Allergy(ClinicalRecord):
    reaction = models.CharField(max_length=240)
    severity = models.CharField(max_length=12, choices=[
        ("unknown", "Unknown"), ("mild", "Mild"), ("moderate", "Moderate"), ("severe", "Severe"),
    ])
    status = models.CharField("Clinical status", max_length=12, default="active", choices=[
        ("active", "Active"), ("inactive", "Inactive"), ("resolved", "Resolved"),
    ])
    verification = models.CharField("Verification status", max_length=20, choices=[
        ("unconfirmed", "Unconfirmed"), ("confirmed", "Confirmed"),
        ("refuted", "Refuted"), ("entered_in_error", "Entered in error"),
    ], default="unconfirmed")
    onset_date = models.DateField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.status == "active" and self.verification in {"refuted", "entered_in_error"}:
            raise ValidationError({"status": "A refuted/entered-in-error allergy cannot be active."})


class MedicationStatement(ClinicalRecord):
    dose = models.CharField("Dose description", max_length=160)
    route = models.CharField(max_length=80)
    frequency = models.CharField(max_length=80)
    status = models.CharField(max_length=12, default="active", choices=[
        ("active", "Active"), ("stopped", "Stopped"), ("historical", "Historical"),
    ])
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.status == "active" and self.end_date:
            raise ValidationError({"end_date": "An active medication statement cannot have an end date."})
        if self.status == "stopped" and not self.end_date:
            raise ValidationError({"end_date": "Provide an end date for a stopped medication."})


PRIMARY_DIAGNOSIS_MESSAGE = ("This encounter already has a primary diagnosis. Change the existing primary "
                             "diagnosis to secondary before assigning another.")


class EncounterDiagnosis(ClinicalRecord):
    encounter = models.ForeignKey("clinical.Encounter", on_delete=models.PROTECT, related_name="diagnoses")
    problem = models.ForeignKey(Problem, null=True, blank=True, on_delete=models.PROTECT)
    rank = models.CharField(max_length=12, default="secondary", choices=[
        ("primary", "Primary"), ("secondary", "Secondary"),
    ])
    code = models.CharField("Mock terminology code", max_length=40, blank=True)

    class Meta(ClinicalRecord.Meta):
        abstract = False
        constraints = [models.UniqueConstraint(fields=["encounter"], condition=Q(rank="primary"),
                                                name="one_primary_diagnosis_per_encounter")]

    def clean(self):
        super().clean()
        if self.encounter_id and self.encounter.patient_id != self.patient_id:
            raise ValidationError("Diagnosis patient must match the encounter.")
        if (self.rank == "primary" and self.encounter_id and
                EncounterDiagnosis.objects.filter(encounter_id=self.encounter_id, rank="primary").exclude(pk=self.pk).exists()):
            raise ValidationError({"rank": PRIMARY_DIAGNOSIS_MESSAGE})
        if self.problem_id and self.problem.patient_id != self.patient_id:
            raise ValidationError({"problem": "Choose a longitudinal problem for this patient."})


class AllergyState(models.Model):
    patient = models.OneToOneField("patients.Patient", on_delete=models.PROTECT)
    status = models.CharField(max_length=16, default="not_reviewed", choices=[
        ("not_reviewed", "Not reviewed"), ("unknown", "Unknown"),
        ("no_known", "No known allergies"), ("documented", "Documented allergies"),
    ])
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)


class HistoryEvent(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    encounter = models.ForeignKey("clinical.Encounter", null=True, blank=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20)
    record_id = models.PositiveBigIntegerField()
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
