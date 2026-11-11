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
