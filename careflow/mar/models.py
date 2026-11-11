from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MedicationAdministrationEvent(models.Model):
    receipt = models.ForeignKey("medications.PharmacyDispenseEvent", on_delete=models.PROTECT,
                                related_name="administration_events")
    revision = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=[("administered", "Administered")])
    quantity = models.PositiveIntegerField(null=True, blank=True)
    occurred_at = models.DateTimeField()
    notes = models.CharField(max_length=1000, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    command_key = models.UUIDField()
    digest = models.CharField(max_length=64)

    class Meta:
        ordering = ("-revision",)
        constraints = [
            models.UniqueConstraint(fields=["receipt", "revision"], name="mar_receipt_revision_unique"),
            models.UniqueConstraint(fields=["actor", "command_key"], name="mar_actor_command_unique"),
            models.CheckConstraint(condition=models.Q(revision__gte=1), name="mar_positive_revision"),
            models.CheckConstraint(condition=models.Q(status="administered", quantity__isnull=False, quantity__gte=1),
                                   name="mar_status_quantity"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("MAR events are immutable.")
        kwargs['force_insert'] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("MAR events are immutable.")
