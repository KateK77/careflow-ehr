from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Historical(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Imaging history cannot be edited.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Imaging history cannot be deleted.")


class ImagingCatalog(Historical):
    MODALITIES = [("XR", "X-ray"), ("CT", "CT"), ("MRI", "MRI"), ("US", "Ultrasound")]
    code = models.CharField(max_length=32)
    revision = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    modality = models.CharField(max_length=3, choices=MODALITIES)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ["code", "-revision"]
        constraints = [models.UniqueConstraint(fields=["code", "revision"], name="imaging_catalog_revision")]

    def __str__(self):
        return f"{self.code} · {self.name} · revision {self.revision}"


class ImagingOrder(models.Model):
    PRIORITIES = [("routine", "Routine"), ("urgent", "Urgent")]
    STATUS = [("draft", "Draft"), ("signed", "Signed"), ("cancelled", "Cancelled")]
    encounter = models.ForeignKey("clinical.Encounter", on_delete=models.PROTECT)
    catalog = models.ForeignKey(ImagingCatalog, on_delete=models.PROTECT)
    priority = models.CharField(max_length=10, choices=PRIORITIES)
    indication = models.CharField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS, default="draft")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(null=True)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    cancellation_reason = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-pk"]
        constraints = [
            models.CheckConstraint(condition=(
                Q(status="draft", signed_at__isnull=True, signed_by__isnull=True, cancellation_reason="")
                | Q(status="signed", signed_at__isnull=False, signed_by__isnull=False, cancellation_reason="")
                | (Q(status="cancelled") & ~Q(cancellation_reason="") & (
                    Q(signed_at__isnull=True, signed_by__isnull=True) | Q(signed_at__isnull=False, signed_by__isnull=False)
                ))
            ), name="imaging_order_state"),
        ]


class ImagingExam(models.Model):
    order = models.OneToOneField(ImagingOrder, on_delete=models.PROTECT, related_name="exam")
    scheduled_at = models.DateTimeField()
    version = models.PositiveIntegerField(default=1)


class ImagingEvent(Historical):
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    digest = models.CharField(max_length=64)
    catalog = models.ForeignKey(ImagingCatalog, null=True, on_delete=models.PROTECT)
    order = models.ForeignKey(ImagingOrder, null=True, on_delete=models.PROTECT, related_name="events")
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["actor", "key"], name="imaging_event_command"),
            models.CheckConstraint(condition=(
                Q(catalog__isnull=False, order__isnull=True) | Q(catalog__isnull=True, order__isnull=False)
            ), name="imaging_event_subject"),
        ]
