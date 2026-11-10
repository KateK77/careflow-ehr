import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from .catalog import SPECIMEN_TYPES, validate_components


class LabTestCatalog(models.Model):
    code = models.CharField(max_length=40, validators=[RegexValidator(r"^SYN-[A-Z0-9-]{1,32}$", "Use an uppercase fictional SYN- code.")])
    revision = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    display_name = models.CharField(max_length=160)
    specimen_type = models.CharField(max_length=20, choices=SPECIMEN_TYPES)
    components = models.JSONField(validators=[validate_components])
    schema_version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False)
    edit_version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code", "-revision"]
        constraints = [models.UniqueConstraint(fields=["code", "revision"], name="lab_catalog_revision_unique"),
                       models.UniqueConstraint(fields=["code"], condition=Q(is_active=True), name="lab_catalog_one_active"),
                       models.CheckConstraint(condition=Q(revision__gte=1, schema_version=1, edit_version__gte=1), name="lab_catalog_versions_valid")]

    def clean(self):
        super().clean()
        if self.schema_version != 1:
            raise ValidationError("Unsupported catalog schema version.")
        others = type(self).objects.exclude(pk=self.pk)
        if others.filter(code=self.code, revision=self.revision).exists():
            raise ValidationError({"code": "This catalog code and revision already exist. Create a new revision."})
        if self.is_active and others.filter(code=self.code, is_active=True).exists():
            raise ValidationError({"code": "Deactivate the current active revision of this code first."})
        if not self.display_name.strip():
            raise ValidationError({"display_name": "Enter a fictional panel name."})

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(old, n) != getattr(self, n) for n in ["code", "revision", "display_name", "specimen_type", "components", "schema_version", "created_by_id", "created_at"]):
                raise ValidationError("Catalog content is immutable. Create a new revision.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} r{self.revision} · {self.display_name}"


class LabOrder(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creation_key = models.UUIDField(unique=True, editable=False)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    encounter = models.ForeignKey("clinical.Encounter", on_delete=models.PROTECT)
    ordering_physician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    catalog = models.ForeignKey(LabTestCatalog, on_delete=models.PROTECT)
    catalog_snapshot = models.JSONField(default=dict)
    identity_snapshot = models.JSONField(default=dict, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    priority = models.CharField(max_length=12, default="routine", choices=[("routine", "Routine (demo)")])
    status = models.CharField(max_length=12, default="draft", choices=[("draft", "Draft"), ("submitted", "Submitted"), ("cancelled", "Cancelled")])
    version = models.PositiveIntegerField(default=1)
    repeat_reason = models.CharField(max_length=1000, blank=True)
    cancellation_reason = models.CharField(max_length=1000, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True, editable=False)
    cancelled_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["ordering_physician", "status"]), models.Index(fields=["patient", "created_at"])]
        constraints = [models.CheckConstraint(condition=(Q(status="draft", submitted_at__isnull=True, cancelled_at__isnull=True, cancelled_by__isnull=True)
                    | Q(status="submitted", submitted_at__isnull=False, cancelled_at__isnull=True, cancelled_by__isnull=True)
                    | Q(status="cancelled", cancelled_at__isnull=False, cancelled_by__isnull=False)), name="lab_order_state_times"),
                    models.CheckConstraint(condition=Q(version__gte=1, priority="routine"), name="lab_order_version_priority")]

    def clean(self):
        super().clean()
        if self.encounter_id and (self.encounter.patient_id != self.patient_id or self.encounter.physician_id != self.ordering_physician_id):
            raise ValidationError("Order patient and physician must match the encounter.")
        if self.status == "cancelled" and not self.cancellation_reason.strip():
            raise ValidationError("A cancellation reason is required.")

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(old, n) != getattr(self, n) for n in ["public_id", "creation_key", "patient_id", "encounter_id", "ordering_physician_id"]):
                raise ValidationError("Order identity and clinical context cannot be changed.")
            if old.status == "cancelled" or (old.status == "submitted" and self.status not in {"submitted", "cancelled"}):
                raise ValidationError("Cancelled orders are terminal; submitted orders cannot return to draft.")
            if old.status != "draft" and any(getattr(old, n) != getattr(self, n) for n in ["catalog_id", "catalog_snapshot", "identity_snapshot", "reason", "priority", "repeat_reason", "submitted_at"]):
                raise ValidationError("Submitted order content cannot be changed.")
        return super().save(*args, **kwargs)


class LabSpecimen(models.Model):
    order = models.ForeignKey(LabOrder, on_delete=models.PROTECT, related_name="specimens")
    attempt = models.PositiveIntegerField(default=1)
    accession = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    specimen_type = models.CharField(max_length=20, choices=SPECIMEN_TYPES)
    status = models.CharField(max_length=12, default="pending", choices=[("pending", "Pending"), ("collected", "Collected"), ("received", "Received"), ("rejected", "Rejected")])
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    rejection_reason = models.CharField(max_length=1000, blank=True)
    comments = models.CharField(max_length=1000, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "attempt"], name="lab_specimen_attempt_unique"),
                       models.UniqueConstraint(fields=["order"], condition=Q(status__in=["pending", "collected", "received"]), name="lab_specimen_one_active"),
                       models.CheckConstraint(condition=Q(attempt__gte=1, version__gte=1, status__in=["pending", "collected", "received", "rejected"]), name="lab_specimen_versions_state")]

    def clean(self):
        super().clean()
        if self.status != "pending" or any([self.collected_at, self.collected_by_id, self.received_at, self.received_by_id, self.rejected_at, self.rejected_by_id, self.rejection_reason]):
            raise ValidationError("Collection, receipt and rejection are not available in Phase 3B-1.")
        if self.order_id and self.specimen_type != self.order.catalog_snapshot.get("specimen_type"):
            raise ValidationError("Pending specimen type must match the submitted panel.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class LabEvent(models.Model):
    order = models.ForeignKey(LabOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    catalog = models.ForeignKey(LabTestCatalog, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    specimen = models.ForeignKey(LabSpecimen, null=True, blank=True, on_delete=models.PROTECT)
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    command_actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    command_key = models.UUIDField()
    request_fingerprint = models.CharField(max_length=64)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["command_actor", "command_key"], name="lab_command_actor_key_unique"),
                       models.CheckConstraint(condition=(Q(order__isnull=False, catalog__isnull=True) | Q(order__isnull=True, catalog__isnull=False)), name="lab_event_one_scope")]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Laboratory command receipts are immutable.")
        if self.audit.actor_id != self.command_actor_id:
            raise ValidationError("Laboratory audit actor must match the command actor.")
        if self.order_id and self.audit.patient_id != self.order.patient_id:
            raise ValidationError("Laboratory audit patient must match the order.")
        if self.specimen_id and self.specimen.order_id != self.order_id:
            raise ValidationError("Laboratory specimen must match the event's order.")
        return super().save(*args, **kwargs)
