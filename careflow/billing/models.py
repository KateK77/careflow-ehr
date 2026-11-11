from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class Immutable(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("This historical record cannot be edited.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("This historical record cannot be deleted.")


class BillingLock(models.Model):
    revision = models.PositiveBigIntegerField(default=0)


class ChargeCatalog(Immutable):
    code = models.CharField(max_length=32)
    revision = models.PositiveIntegerField()
    description = models.CharField(max_length=120)
    unit_cents = models.PositiveIntegerField()

    class Meta:
        ordering = ["code", "-revision"]
        constraints = [
            models.UniqueConstraint(fields=["code", "revision"], name="billing_catalog_revision"),
            models.CheckConstraint(condition=Q(unit_cents__gte=1, unit_cents__lte=10000000), name="billing_catalog_price"),
        ]

    def __str__(self):
        return f"{self.code} revision {self.revision} · {self.description}"


class PatientCoverage(Immutable):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    policy = models.CharField(max_length=40)
    revision = models.PositiveIntegerField()
    payer = models.CharField(max_length=80)
    coverage_type = models.CharField(max_length=20, choices=[
        ("individual", "Individual"), ("group", "Group"), ("other", "Other"),
    ])
    status = models.CharField(max_length=12, choices=[
        ("active", "Active"), ("inactive", "Inactive"), ("historical", "Historical"),
    ])
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["policy", "-revision"]
        constraints = [
            models.UniqueConstraint(fields=["policy", "revision"], name="billing_coverage_revision"),
            models.CheckConstraint(condition=Q(effective_to__isnull=True) | Q(effective_to__gte=F("effective_from")),
                                   name="billing_coverage_dates"),
        ]

    def __str__(self):
        return f"{self.payer} · {self.policy} revision {self.revision}"


class PatientStatement(models.Model):
    encounter = models.OneToOneField("clinical.Encounter", on_delete=models.PROTECT)
    status = models.CharField(max_length=12, default="draft", choices=[
        ("draft", "Draft"), ("finalized", "Finalized"), ("released", "Released"), ("void", "Voided draft"),
    ])
    version = models.PositiveIntegerField(default=1)
    total_cents = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finalized_at = models.DateTimeField(null=True)
    released_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=(
                Q(status__in=["draft", "void"], finalized_at__isnull=True, released_at__isnull=True, total_cents=0)
                | Q(status="finalized", finalized_at__isnull=False, released_at__isnull=True, total_cents__gt=0)
                | Q(status="released", finalized_at__isnull=False, released_at__isnull=False, total_cents__gt=0)
            ), name="billing_statement_state"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status != "draft" and (
                original.status != "finalized" or self.status != "released"
                or self.encounter_id != original.encounter_id or self.total_cents != original.total_cents
                or self.finalized_at != original.finalized_at
            ):
                raise ValidationError("A closed statement cannot be edited.")
        super().save(*args, **kwargs)


class EncounterCharge(models.Model):
    statement = models.ForeignKey(PatientStatement, on_delete=models.PROTECT, related_name="charges")
    catalog = models.ForeignKey(ChargeCatalog, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()
    void = models.BooleanField(default=False)

    class Meta:
        ordering = ["pk"]
        constraints = [models.CheckConstraint(condition=Q(quantity__gte=1, quantity__lte=100),
                                             name="billing_charge_quantity")]

    @property
    def subtotal_cents(self):
        return self.catalog.unit_cents * self.quantity

    def save(self, *args, **kwargs):
        if not PatientStatement.objects.filter(pk=self.statement_id, status="draft").exists():
            raise ValidationError("Only draft charges can be changed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Use a draft charge void to retain history.")


class StatementLine(Immutable):
    statement = models.ForeignKey(PatientStatement, on_delete=models.PROTECT, related_name="lines")
    charge = models.OneToOneField(EncounterCharge, on_delete=models.PROTECT)
    code = models.CharField(max_length=32)
    revision = models.PositiveIntegerField()
    description = models.CharField(max_length=120)
    unit_cents = models.PositiveIntegerField()
    quantity = models.PositiveSmallIntegerField()

    @property
    def subtotal_cents(self):
        return self.unit_cents * self.quantity


class BillingEvent(Immutable):
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    actor = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    key = models.UUIDField()
    digest = models.CharField(max_length=64)
    subject = models.CharField(max_length=24)
    subject_id = models.PositiveBigIntegerField()
    version = models.PositiveIntegerField()
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["actor", "key"], name="billing_command_unique")]
