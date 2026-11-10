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
    status = models.CharField(max_length=12, default="draft", choices=[("draft", "Draft"), ("submitted", "Submitted"), ("cancelled", "Cancelled"), ("fulfilled", "Fulfilled")])
    assigned_lab_staff = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    current_publication = models.ForeignKey("LabResult", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    fulfilled_at = models.DateTimeField(null=True, blank=True)
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
                    | Q(status__in=["submitted", "fulfilled"], submitted_at__isnull=False, cancelled_at__isnull=True, cancelled_by__isnull=True)
                    | Q(status="cancelled", cancelled_at__isnull=False, cancelled_by__isnull=False)), name="lab_order_state_times"),
                    models.CheckConstraint(condition=Q(version__gte=1, priority="routine"), name="lab_order_version_priority")]

    def clean(self):
        super().clean()
        if self.encounter_id and (self.encounter.patient_id != self.patient_id or self.encounter.physician_id != self.ordering_physician_id):
            raise ValidationError("Order patient and physician must match the encounter.")
        if (self.status == "fulfilled") != bool(self.current_publication_id and self.fulfilled_at):
            raise ValidationError("Fulfilled orders require a current publication and fulfillment timestamp.")
        if self.current_publication_id and (self.current_publication.order_id != self.pk or self.current_publication.status != "final"):
            raise ValidationError("The publication must be the final report for this order.")
        if self.status == "cancelled" and not self.cancellation_reason.strip():
            raise ValidationError("A cancellation reason is required.")

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(old, n) != getattr(self, n) for n in ["public_id", "creation_key", "patient_id", "encounter_id", "ordering_physician_id"]):
                raise ValidationError("Order identity and clinical context cannot be changed.")
            if old.status == "cancelled" or (old.status == "submitted" and self.status not in {"submitted", "cancelled", "fulfilled"}):
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
        if self.order_id and self.specimen_type != self.order.catalog_snapshot.get("specimen_type"):
            raise ValidationError("Specimen type must match the submitted panel.")
        if self.status in {"collected", "received", "rejected"} and not (self.collected_at and self.collected_by_id):
            raise ValidationError("Collection identity and timestamp are required.")
        if bool(self.received_at) != bool(self.received_by_id) or (self.status == "received" and not self.received_at):
            raise ValidationError("Receipt identity and timestamp are required.")
        if self.status == "pending" and any([self.collected_at, self.collected_by_id, self.received_at, self.rejected_at]):
            raise ValidationError("Pending attempts cannot contain collection or receipt metadata.")
        if self.status == "rejected" and not (self.rejected_at and self.rejected_by_id and self.rejection_reason.strip()):
            raise ValidationError("Rejection requires an actor, timestamp and reason.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            fixed = ["order_id", "attempt", "accession", "specimen_type", "created_by_id", "created_at"]
            if any(getattr(old, n) != getattr(self, n) for n in fixed):
                raise ValidationError("Specimen identity is immutable.")
            if old.status == "rejected" or (old.received_at and any(getattr(old,n) != getattr(self,n) for n in ["received_at","received_by_id","collected_at","collected_by_id"])):
                raise ValidationError("Rejected attempts and received provenance are immutable.")
        return super().save(*args, **kwargs)


class LabResult(models.Model):
    order = models.ForeignKey(LabOrder, on_delete=models.PROTECT, related_name="results")
    specimen = models.ForeignKey(LabSpecimen, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    edit_version = models.PositiveIntegerField(default=1)
    schema_version = models.PositiveIntegerField(default=1)
    publication_kind = models.CharField(max_length=12, default="report")
    status = models.CharField(max_length=12, default="draft", choices=[("draft","Draft"),("final","Final"),("abandoned","Abandoned")])
    payload = models.JSONField(default=dict)
    supersedes = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    entered_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    published_at = models.DateTimeField(null=True, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=1000, blank=True)
    reason_code = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["revision"]
        constraints = [models.UniqueConstraint(fields=["order","revision"], name="lab_result_revision_unique"),
            models.UniqueConstraint(fields=["order"],condition=Q(status="draft"),name="lab_result_one_draft"),
            models.UniqueConstraint(fields=["order"],condition=Q(status="final"),name="lab_result_one_original"),
            models.CheckConstraint(condition=Q(revision__gte=1,edit_version__gte=1,schema_version=1),name="lab_result_versions"),
            models.CheckConstraint(condition=(Q(status__in=["draft","abandoned"],published_at__isnull=True,finalized_by__isnull=True)|Q(status="final",published_at__isnull=False,finalized_by__isnull=False)),name="lab_result_state_times")]

    def clean(self):
        from .payloads import validate_payload
        if self.specimen_id and self.specimen.order_id != self.order_id:
            raise ValidationError("Result specimen and order do not match.")
        validate_payload(self.order,self.specimen,self.payload,complete=self.status=="final")
        if self.schema_version != 1 or self.publication_kind != "report":
            raise ValidationError("Unsupported publication schema or kind.")

    def save(self,*args,**kwargs):
        if self.pk:
            old=type(self).objects.get(pk=self.pk)
            if old.status != "draft":
                raise ValidationError("Published and abandoned results are immutable.")
            if any(getattr(old,n)!=getattr(self,n) for n in ["order_id","specimen_id","revision","entered_by_id","entered_at","supersedes_id"]):
                raise ValidationError("Result context and original entry provenance are immutable.")
        self.clean()
        return super().save(*args,**kwargs)


class LabEvent(models.Model):
    order = models.ForeignKey(LabOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    catalog = models.ForeignKey(LabTestCatalog, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    specimen = models.ForeignKey(LabSpecimen, null=True, blank=True, on_delete=models.PROTECT)
    result = models.ForeignKey(LabResult, null=True, blank=True, on_delete=models.PROTECT)
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
        if self.result_id and self.result.order_id != self.order_id:
            raise ValidationError("Laboratory result must match the event order.")
        if self.specimen_id and self.specimen.order_id != self.order_id:
            raise ValidationError("Laboratory specimen must match the event's order.")
        return super().save(*args, **kwargs)
