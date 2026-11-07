from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Upper
from django.utils import timezone


class Patient(models.Model):
    class Sex(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        OTHER = "other", "Other"
        UNKNOWN = "unknown", "Unknown"

    mrn = models.CharField(
        "MRN", max_length=32, unique=True,
        validators=[RegexValidator(r"^[A-Z0-9-]+$", "Use letters, numbers and hyphens.")],
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    dob = models.DateField("Date of birth")
    sex = models.CharField(max_length=10, choices=Sex.choices)
    gender_identity = models.CharField(max_length=80, blank=True)
    phone = models.CharField(
        max_length=30, blank=True,
        validators=[RegexValidator(r"^[0-9+() .-]*$", "Enter a valid phone number.")],
    )
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)
    emergency_contact = models.CharField(max_length=160, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "pk"]
        constraints = [
            models.UniqueConstraint(Upper("mrn"), name="patient_mrn_case_insensitive"),
        ]

    def clean(self):
        super().clean()
        if self.dob and self.dob > timezone.localdate():
            raise ValidationError({"dob": "Date of birth cannot be in the future."})

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = timezone.localdate()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    patient = models.ForeignKey(Patient, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=40)
    outcome = models.CharField(max_length=12, default="success")
    occurred_at = models.DateTimeField(default=timezone.now, editable=False)
    changed_fields = models.JSONField(default=list)

    class Meta:
        ordering = ["-occurred_at", "-pk"]
