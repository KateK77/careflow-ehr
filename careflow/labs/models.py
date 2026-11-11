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
    status = models.CharField(max_length=12, default="draft", choices=[("draft", "Draft"), ("submitted", "Submitted"), ("cancelled", "Cancelled"), ("fulfilled", "Fulfilled"), ("withdrawn", "Withdrawn")])
    assigned_lab_staff = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    current_publication = models.ForeignKey("LabResult", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    current_review_assignment = models.ForeignKey("LabReviewAssignment", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
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
                    | Q(status__in=["submitted", "fulfilled", "withdrawn"], submitted_at__isnull=False, cancelled_at__isnull=True, cancelled_by__isnull=True)
                    | Q(status="cancelled", cancelled_at__isnull=False, cancelled_by__isnull=False)), name="lab_order_state_times"),
                    models.CheckConstraint(condition=Q(version__gte=1, priority="routine"), name="lab_order_version_priority"),
                    models.CheckConstraint(condition=(Q(status__in=["draft","submitted","cancelled"],current_publication__isnull=True,fulfilled_at__isnull=True)|Q(status__in=["fulfilled","withdrawn"],current_publication__isnull=False,fulfilled_at__isnull=False)),name="lab_order_publication_state"),
                    models.CheckConstraint(condition=(Q(status__in=["draft","cancelled"])|Q(current_review_assignment__isnull=False)),name="lab_order_review_responsibility")]

    def clean(self):
        super().clean()
        if self.encounter_id and (self.encounter.patient_id != self.patient_id or self.encounter.physician_id != self.ordering_physician_id):
            raise ValidationError("Order patient and physician must match the encounter.")
        if (self.status in {"fulfilled","withdrawn"}) != bool(self.current_publication_id and self.fulfilled_at):
            raise ValidationError("Fulfilled orders require a current publication and fulfillment timestamp.")
        if self.current_publication_id and (self.current_publication.order_id != self.pk or self.current_publication.status not in ({"withdrawn"} if self.status=="withdrawn" else {"final","corrected"})):
            raise ValidationError("The publication must be the final report for this order.")
        if self.current_review_assignment_id and self.current_review_assignment.order_id != self.pk:
            raise ValidationError("Review assignment must belong to this order.")
        if self.status in {"submitted","fulfilled","withdrawn"} and not self.current_review_assignment_id:
            raise ValidationError("Submitted orders require explicit review responsibility.")
        if self.status == "cancelled" and not self.cancellation_reason.strip():
            raise ValidationError("A cancellation reason is required.")

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(old, n) != getattr(self, n) for n in ["public_id", "creation_key", "patient_id", "encounter_id", "ordering_physician_id"]):
                raise ValidationError("Order identity and clinical context cannot be changed.")
            if old.status == "fulfilled" and self.status not in {"fulfilled","withdrawn"}:
                raise ValidationError("Published orders cannot return to draft/submitted/cancelled.")
            if old.status == "cancelled" or (old.status == "withdrawn" and self.status != "withdrawn") or (old.status == "submitted" and self.status not in {"submitted", "cancelled", "fulfilled"}):
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
    status = models.CharField(max_length=12, default="draft", choices=[("draft","Draft"),("final","Final"),("abandoned","Abandoned"),("corrected","Corrected"),("withdrawn","Withdrawn")])
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
        permissions = [("reassign_review_responsibility","Explicitly reassign an ineligible laboratory reviewer"),("view_quarantined_report","Inspect quarantined laboratory report payloads")]
        constraints = [models.UniqueConstraint(fields=["order","revision"], name="lab_result_revision_unique"),
            models.UniqueConstraint(fields=["order"],condition=Q(status="draft"),name="lab_result_one_draft"),
            models.UniqueConstraint(fields=["order"],condition=Q(status="final"),name="lab_result_one_original"),
            models.CheckConstraint(condition=Q(revision__gte=1,edit_version__gte=1,schema_version=1),name="lab_result_versions"),
            models.CheckConstraint(condition=(Q(status__in=["draft","abandoned"],published_at__isnull=True,finalized_by__isnull=True)|Q(status__in=["final","corrected","withdrawn"],published_at__isnull=False,finalized_by__isnull=False)),name="lab_result_state_times"),
            models.UniqueConstraint(fields=["supersedes"],condition=Q(status__in=["final","corrected","withdrawn"],supersedes__isnull=False),name="lab_result_linear_successor"),
            models.CheckConstraint(condition=(Q(publication_kind="report",status__in=["draft","final","corrected","abandoned"])|Q(publication_kind="withdrawal",status="withdrawn",supersedes__isnull=False,performed_at__isnull=True,reason_code__in=["report_error","context_error"])),name="lab_result_kind_status"),
            models.CheckConstraint(condition=(Q(status="final",supersedes__isnull=True)|Q(status__in=["corrected","withdrawn"],supersedes__isnull=False)|Q(status__in=["draft","abandoned"])),name="lab_result_predecessor")]


    def delete(self,*args,**kwargs):
        raise ValidationError("Laboratory history cannot be deleted through supported application paths.")

    def clean(self):
        from .payloads import validate_payload
        if self.specimen_id and self.specimen.order_id != self.order_id:
            raise ValidationError("Result specimen and order do not match.")
        if self.publication_kind=="withdrawal":
            from .payloads import validate_withdrawal
            validate_withdrawal(self)
        elif self.publication_kind=="report":
            validate_payload(self.order,self.specimen,self.payload,complete=self.status in {"final","corrected"})
            if self.schema_version != 1: raise ValidationError("Unsupported report schema.")
        else: raise ValidationError("Unsupported publication kind.")
        if self.publication_kind=="report":
            from django.utils import timezone
            performed=any(c["value_kind"]!="absent" for c in self.payload["components"])
            if performed and (not self.performed_at or not self.specimen.received_at or self.performed_at<self.specimen.received_at or self.performed_at>timezone.now()):
                raise ValidationError("Performed values require a non-future time at or after specimen receipt.")
            if not performed and self.performed_at:
                raise ValidationError("All-not-performed reports have no performed timestamp.")
        if self.supersedes_id and (self.supersedes.order_id!=self.order_id or self.supersedes.specimen_id!=self.specimen_id or self.supersedes.revision>=self.revision or self.supersedes.status not in {"final","corrected"}):
            raise ValidationError("Publication predecessor must be an earlier report from the same order and specimen.")
        if self.status in {"corrected","withdrawn"} and not self.reason.strip():
            raise ValidationError("Publication changes require a reason.")

    def save(self,*args,**kwargs):
        if self.pk:
            old=type(self).objects.get(pk=self.pk)
            if old.status != "draft":
                raise ValidationError("Published and abandoned results are immutable.")
            if any(getattr(old,n)!=getattr(self,n) for n in ["order_id","specimen_id","revision","entered_by_id","entered_at","supersedes_id"]):
                raise ValidationError("Result context and original entry provenance are immutable.")
        self.clean()
        return super().save(*args,**kwargs)


class LabReviewAssignment(models.Model):
    order = models.ForeignKey(LabOrder,on_delete=models.PROTECT,related_name="review_assignments")
    sequence = models.PositiveIntegerField()
    physician = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="+")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name="+")
    assigned_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=1000)
    source = models.CharField(max_length=24,choices=[("initial_submission","Initial submission"),("manual_reassignment","Manual reassignment"),("migration_backfill","Migration backfill")])
    supersedes = models.OneToOneField("self",null=True,blank=True,on_delete=models.PROTECT,related_name="+")

    class Meta:
        constraints=[models.UniqueConstraint(fields=["order","sequence"],name="lab_assignment_sequence"),models.CheckConstraint(condition=Q(sequence__gte=1),name="lab_assignment_positive"),
            models.CheckConstraint(condition=(Q(source="migration_backfill",sequence=1,assigned_by__isnull=True,supersedes__isnull=True)|Q(source="initial_submission",sequence=1,assigned_by__isnull=False,supersedes__isnull=True)|Q(source="manual_reassignment",sequence__gte=2,assigned_by__isnull=False,supersedes__isnull=False)),name="lab_assignment_provenance")]

    def delete(self,*args,**kwargs):
        raise ValidationError("Laboratory history cannot be deleted through supported application paths.")

    def save(self,*args,**kwargs):
        if self.pk: raise ValidationError("Review assignment history is immutable.")
        if self.supersedes_id and (self.supersedes.order_id!=self.order_id or self.sequence!=self.supersedes.sequence+1): raise ValidationError("Review assignment predecessor mismatch.")
        if not self.reason.strip() or (not self.assigned_by_id and self.source!="migration_backfill"): raise ValidationError("Assignment actor and reason required.")
        return super().save(*args,**kwargs)


class LabResultReview(models.Model):
    publication = models.ForeignKey(LabResult,on_delete=models.PROTECT,related_name="reviews")
    review_assignment = models.ForeignKey(LabReviewAssignment,on_delete=models.PROTECT)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="+")
    reviewed_at = models.DateTimeField(auto_now_add=True)
    review_kind = models.CharField(max_length=20,choices=[("result_review","Result review"),("withdrawal_notice","Withdrawal notice")])
    comment = models.CharField(max_length=1000,blank=True)

    class Meta:
        constraints=[models.UniqueConstraint(fields=["publication","review_assignment"],name="lab_review_current_pair"),models.CheckConstraint(condition=Q(review_kind__in=["result_review","withdrawal_notice"]),name="lab_review_kind_valid")]

    def delete(self,*args,**kwargs):
        raise ValidationError("Laboratory history cannot be deleted through supported application paths.")

    def save(self,*args,**kwargs):
        if self.pk: raise ValidationError("Acknowledgements are immutable.")
        if self.publication.order_id!=self.review_assignment.order_id or self.reviewer_id!=self.review_assignment.physician_id or self.publication.status not in {"final","corrected","withdrawn"}: raise ValidationError("Review publication and responsibility do not match.")
        expected="withdrawal_notice" if self.publication.status=="withdrawn" else "result_review"
        if self.review_kind!=expected: raise ValidationError("Incorrect acknowledgement kind.")
        return super().save(*args,**kwargs)


class LabEvent(models.Model):
    order = models.ForeignKey(LabOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    catalog = models.ForeignKey(LabTestCatalog, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    specimen = models.ForeignKey(LabSpecimen, null=True, blank=True, on_delete=models.PROTECT)
    review_assignment = models.ForeignKey(LabReviewAssignment, null=True, blank=True, on_delete=models.PROTECT)
    review = models.ForeignKey(LabResultReview, null=True, blank=True, on_delete=models.PROTECT)
    result = models.ForeignKey(LabResult, null=True, blank=True, on_delete=models.PROTECT)
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    command_actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    command_key = models.UUIDField(null=True, blank=True)
    system_source = models.CharField(max_length=24, blank=True)
    request_fingerprint = models.CharField(max_length=64)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        ordering = ["-audit__occurred_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["command_actor", "command_key"], name="lab_command_actor_key_unique"),
                       models.CheckConstraint(condition=(Q(order__isnull=False, catalog__isnull=True) | Q(order__isnull=True, catalog__isnull=False)), name="lab_event_one_scope"),models.CheckConstraint(condition=(Q(system_source="",command_actor__isnull=False,command_key__isnull=False)|Q(system_source="migration_backfill",command_actor__isnull=True,command_key__isnull=True)),name="lab_event_receipt_provenance")]

    def delete(self,*args,**kwargs):
        raise ValidationError("Laboratory history cannot be deleted through supported application paths.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Laboratory command receipts are immutable.")
        if (self.command_actor_id is None or self.command_key is None) and self.system_source!="migration_backfill":
            raise ValidationError("Only explicit migration provenance may omit the command actor and UUID.")
        if self.review_assignment_id and self.review_assignment.order_id!=self.order_id:
            raise ValidationError("Event review assignment mismatch.")
        if self.review_id and self.review.publication.order_id!=self.order_id:
            raise ValidationError("Event acknowledgement mismatch.")
        if self.audit.actor_id != self.command_actor_id:
            raise ValidationError("Laboratory audit actor must match the command actor.")
        if self.order_id and self.audit.patient_id != self.order.patient_id:
            raise ValidationError("Laboratory audit patient must match the order.")
        if self.result_id and self.result.order_id != self.order_id:
            raise ValidationError("Laboratory result must match the event order.")
        if self.specimen_id and self.specimen.order_id != self.order_id:
            raise ValidationError("Laboratory specimen must match the event's order.")
        return super().save(*args, **kwargs)
