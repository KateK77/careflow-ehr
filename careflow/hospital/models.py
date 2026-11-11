from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Department(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class Ward(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=12, choices=[("inpatient", "Inpatient"), ("ed", "Emergency")])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["department", "name"], name="hospital_ward_name")]

    def __str__(self):
        return f"{self.department} / {self.name}"


class Room(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["ward", "name"], name="hospital_room_name")]

    def __str__(self):
        return f"{self.ward} / {self.name}"


class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    name = models.CharField(max_length=80)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["room", "name"], name="hospital_bed_name")]

    def __str__(self):
        return f"{self.room} / {self.name}"


class AdmissionRequest(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    reason = models.CharField(max_length=240)
    status = models.CharField(max_length=12, default="pending", choices=[
        ("pending", "Pending"), ("admitted", "Admitted"), ("cancelled", "Cancelled"),
    ])
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["patient"], condition=Q(status="pending"),
                                               name="hospital_one_pending_admission")]


class InpatientStay(models.Model):
    request = models.OneToOneField(AdmissionRequest, on_delete=models.PROTECT, related_name="stay")
    attending = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    bed = models.ForeignKey(Bed, null=True, on_delete=models.PROTECT, related_name="stays")
    status = models.CharField(max_length=12, default="active", choices=[("active", "Admitted"), ("discharged", "Discharged")])
    version = models.PositiveIntegerField(default=1)
    admitted_at = models.DateTimeField(auto_now_add=True)
    discharge_plan = models.TextField(max_length=2000, blank=True)
    discharged_at = models.DateTimeField(null=True)
    discharged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="+")
    discharge_summary = models.TextField(max_length=2000, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["bed"], condition=Q(status="active"), name="hospital_active_bed"),
            models.CheckConstraint(condition=(
                Q(status="active", bed__isnull=False, discharged_at__isnull=True, discharged_by__isnull=True, discharge_summary="")
                | (Q(status="discharged", bed__isnull=True, discharged_at__isnull=False, discharged_by__isnull=False)
                   & ~Q(discharge_summary="") & ~Q(discharge_plan=""))
            ), name="hospital_stay_state"),
        ]


class OperationLock(models.Model):
    revision = models.PositiveBigIntegerField(default=0)


class HospitalEvent(models.Model):
    audit = models.OneToOneField("patients.AuditEvent", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    digest = models.CharField(max_length=64)
    request = models.ForeignKey(AdmissionRequest, null=True, on_delete=models.PROTECT, related_name="events")
    stay = models.ForeignKey(InpatientStay, null=True, on_delete=models.PROTECT, related_name="events")
    previous_bed = models.ForeignKey(Bed, null=True, on_delete=models.PROTECT, related_name="+")
    next_bed = models.ForeignKey(Bed, null=True, on_delete=models.PROTECT, related_name="+")
    details = models.JSONField(default=dict)
    visit = models.ForeignKey("EmergencyVisit", null=True, on_delete=models.PROTECT, related_name="events")

    class Meta:
        ordering = ["audit__occurred_at", "pk"]
        constraints = [models.UniqueConstraint(fields=["actor", "key"], name="hospital_command_receipt")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Hospital events are append-only.")
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Hospital events are append-only.")


class EmergencyVisit(models.Model):
    ARRIVAL_METHODS = [("walk_in", "Walk-in"), ("demo_transport", "Synthetic transport"), ("other", "Other fictional method")]
    TRIAGE = [("demo_a", "Demo A"), ("demo_b", "Demo B"), ("demo_c", "Demo C")]
    STATES = [("waiting", "Waiting"), ("triage", "Triage"), ("roomed", "Roomed"),
              ("provider", "Provider"), ("observation", "Observation"), ("discharged", "Discharged"), ("admitted", "Admitted")]
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT)
    arrived_at = models.DateTimeField(auto_now_add=True)
    arrival_method = models.CharField(max_length=20, choices=ARRIVAL_METHODS)
    complaint = models.CharField(max_length=240)
    triage_category = models.CharField(max_length=12, choices=TRIAGE, blank=True)
    status = models.CharField(max_length=12, choices=STATES, default="waiting")
    room = models.ForeignKey(Room, null=True, on_delete=models.PROTECT)
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    provider_at = models.DateTimeField(null=True)
    disposed_at = models.DateTimeField(null=True)
    disposition_note = models.CharField(max_length=240, blank=True)
    inpatient_stay = models.OneToOneField(InpatientStay, null=True, on_delete=models.PROTECT, related_name="ed_origin")
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["patient"], condition=Q(status__in=[
                "waiting", "triage", "roomed", "provider", "observation",
            ]), name="hospital_one_active_ed_visit"),
            models.UniqueConstraint(fields=["room"], condition=Q(room__isnull=False), name="hospital_ed_room_occupied"),
            models.CheckConstraint(condition=(
                Q(status__in=["waiting", "triage"], room__isnull=True, clinician__isnull=True, provider_at__isnull=True,
                  disposed_at__isnull=True, disposition_note="", inpatient_stay__isnull=True)
                | Q(status="roomed", room__isnull=False, clinician__isnull=False, provider_at__isnull=True,
                    disposed_at__isnull=True, disposition_note="", inpatient_stay__isnull=True)
                | Q(status__in=["provider", "observation"], room__isnull=False, clinician__isnull=False, provider_at__isnull=False,
                    disposed_at__isnull=True, disposition_note="", inpatient_stay__isnull=True)
                | ((Q(status="discharged", inpatient_stay__isnull=True) | Q(status="admitted", inpatient_stay__isnull=False))
                   & Q(room__isnull=True, clinician__isnull=False, provider_at__isnull=False, disposed_at__isnull=False)
                   & ~Q(disposition_note=""))
            ), name="hospital_ed_workflow_state"),
            models.CheckConstraint(condition=Q(status="waiting", triage_category="") | (
                ~Q(status="waiting") & Q(triage_category__in=["demo_a", "demo_b", "demo_c"])
            ), name="hospital_ed_triage_state"),
        ]
