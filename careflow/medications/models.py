import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q


ROUTES = [("oral", "Oral (simulated)"), ("topical", "Topical (simulated)")]
FREQUENCIES = [("daily", "Daily"), ("twice_daily", "Twice daily"), ("once", "Once")]
FORMS = [("demo_tablet", "Demo tablet"), ("demo_gel", "Demo gel")]
CATALOG_CONTENT = ("code", "revision", "name", "dosage_form", "strength", "route", "frequency")
ORDER_CONTENT = ("encounter_id", "author_id", "public_id", "catalog_id", "catalog_snapshot",
                 "dose", "route", "frequency", "duration", "quantity", "instructions")


class SyntheticMedicationCatalog(models.Model):
    code = models.CharField(max_length=40, validators=[RegexValidator(
        r"\ASYN-[A-Z0-9]+(?:-[A-Z0-9]+)*\Z", "Use a fictional SYN- code with uppercase letters and digits."
    )])
    revision = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    name = models.CharField(max_length=100, validators=[RegexValidator(
        r"\ASynthetic ", "Start the fictional display name with Synthetic."
    )])
    dosage_form = models.CharField(max_length=20, choices=FORMS)
    strength = models.CharField(max_length=40, validators=[RegexValidator(
        r"\A[1-9][0-9]{0,3} demo units\Z", "Use a fictional strength such as 10 demo units."
    )])
    route = models.CharField(max_length=20, choices=ROUTES)
    frequency = models.CharField(max_length=20, choices=FREQUENCIES)
    active = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("code", "-revision")
        constraints = [
            models.UniqueConstraint(fields=["code", "revision"], name="med_catalog_revision_unique"),
            models.UniqueConstraint(fields=["code"], condition=Q(active=True), name="med_catalog_active_unique"),
            models.CheckConstraint(condition=Q(revision__gte=1, version__gte=1), name="med_catalog_positive"),
        ]

    def __str__(self):
        return f"{self.name} · {self.code} r{self.revision}"

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(old, field) != getattr(self, field) for field in CATALOG_CONTENT):
                raise ValidationError("Create a new catalog revision to change its content.")
        super().save(*args, **kwargs)

    def snapshot(self):
        return {
            "code": self.code, "revision": self.revision, "name": self.name,
            "dosage_form": self.get_dosage_form_display(), "strength": self.strength,
        }


class MedicationOrder(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    encounter = models.ForeignKey("clinical.Encounter", on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    catalog = models.ForeignKey(SyntheticMedicationCatalog, on_delete=models.PROTECT)
    catalog_snapshot = models.JSONField()
    dose = models.CharField(max_length=80, validators=[RegexValidator(
        r"\A[1-9][0-9]{0,3} demo units\Z", "Use fictional dose units, such as 1 demo units."
    )])
    route = models.CharField(max_length=20, choices=ROUTES)
    frequency = models.CharField(max_length=20, choices=FREQUENCIES)
    duration = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    instructions = models.CharField(max_length=1000)
    status = models.CharField(max_length=12, default="draft", choices=[
        ("draft", "Draft"), ("signed", "Signed"), ("cancelled", "Cancelled"),
    ])
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=1000, blank=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        constraints = [
            models.CheckConstraint(condition=Q(duration__gte=1, quantity__gte=1, version__gte=1), name="med_order_positive"),
            models.CheckConstraint(condition=(
                Q(status="draft", signed_at__isnull=True, signed_by__isnull=True, cancelled_at__isnull=True)
                | Q(status="signed", signed_at__isnull=False, signed_by__isnull=False, cancelled_at__isnull=True)
                | (Q(status="cancelled", cancelled_at__isnull=False) & ~Q(cancellation_reason="")
                   & (Q(signed_at__isnull=True, signed_by__isnull=True) | Q(signed_at__isnull=False, signed_by__isnull=False)))
            ), name="med_order_state_metadata"),
        ]

    def clean(self):
        if self.encounter_id and self.author_id != self.encounter.physician_id:
            raise ValidationError("The order author must be the Encounter physician.")
        if self.signed_by_id and self.signed_by_id != self.author_id:
            raise ValidationError("Only the original author may sign the order.")
        if self.catalog_id and (self.route != self.catalog.route or self.frequency != self.catalog.frequency):
            raise ValidationError("Choose the route and frequency configured for the selected synthetic revision.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if (old.encounter_id, old.author_id, old.public_id) != (self.encounter_id, self.author_id, self.public_id):
                raise ValidationError("Order identity is immutable.")
            if old.status == "cancelled":
                raise ValidationError("Cancelled orders are immutable.")
            if old.signed_at:
                protected = (*ORDER_CONTENT, "signed_at", "signed_by_id", "created_at")
                if self.status not in {"signed", "cancelled"} or any(
                    getattr(old, field) != getattr(self, field) for field in protected
                ):
                    raise ValidationError("Signed order content and signature are immutable.")
        super().save(*args, **kwargs)


class PharmacyReview(models.Model):
    order = models.OneToOneField(MedicationOrder, on_delete=models.PROTECT, related_name="pharmacy_review")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    claimed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, default="pending", choices=[
        ("pending", "Awaiting verification"),
        ("clarification", "Clarification requested"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ])
    reason = models.CharField(max_length=1000, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gte=1), name="pharmacy_review_positive_version"),
            models.CheckConstraint(condition=(
                (Q(status__in=["pending", "approved"]) & Q(reason=""))
                | (Q(status__in=["clarification", "rejected"]) & ~Q(reason=""))
            ), name="pharmacy_review_reason_state"),
        ]


    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if (old.order_id, old.assignee_id, old.claimed_at) != (self.order_id, self.assignee_id, self.claimed_at):
                raise ValidationError("The pharmacy claim and its provenance are immutable.")
        super().save(*args, **kwargs)


class PharmacyDispenseEvent(models.Model):
    review = models.OneToOneField(PharmacyReview, on_delete=models.PROTECT, related_name="dispense")
    event = models.OneToOneField("MedicationOrderEvent", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gte=1), name="pharmacy_dispense_positive")]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Simulated dispensing records are immutable.")
        if (self.event.order_id != self.review.order_id or self.event.actor_id != self.review.assignee_id
                or self.event.audit.action != "pharmacy_dispense" or self.review.status != "approved"
                or self.quantity != self.review.order.quantity):
            raise ValidationError("The dispensing receipt must match the approved order and pharmacy event.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Simulated dispensing records are immutable.")


class MedicationOrderEvent(models.Model):
    order = models.ForeignKey(MedicationOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    catalog = models.ForeignKey(SyntheticMedicationCatalog, null=True, blank=True, on_delete=models.PROTECT, related_name="events")
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    command_key = models.UUIDField()
    digest = models.CharField(max_length=64)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.CharField(max_length=1000, blank=True)

    class Meta:
        ordering = ("pk",)
        constraints = [
            models.UniqueConstraint(fields=["actor", "command_key"], name="med_event_command_unique"),
            models.CheckConstraint(condition=Q(order__isnull=False, catalog__isnull=True) |
                                   Q(order__isnull=True, catalog__isnull=False), name="med_event_one_subject"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Medication events are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Medication events are append-only.")
