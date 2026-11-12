import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

from careflow.clinical.access import can_write
from careflow.clinical.models import Encounter
from careflow.medications.services import MedicationConflict, check_version, command_identity, command_transaction
from careflow.patients.access import roles_for
from careflow.patients.models import AuditEvent
from careflow.scheduling.services import _lock_providers

from .models import ImagingCatalog, ImagingEvent, ImagingExam, ImagingOrder


def active_catalog():
    latest = ImagingCatalog.objects.filter(code=OuterRef("code")).order_by("-revision")
    return ImagingCatalog.objects.filter(pk=Subquery(latest.values("pk")[:1]), active=True)


def text_value(value, limit, label):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValidationError(f"Enter {label} of 1 to {limit} characters.")
    return value.strip()


def receipt(actor, key, action, *payload):
    identity = command_identity(key, action, *payload)
    event = ImagingEvent.objects.filter(actor=actor, key=identity[0]).first()
    if event and event.digest != identity[1]:
        raise ValidationError("This submission was already used for different input.")
    return identity, event


def record(actor, action, identity, *, order=None, catalog=None, **details):
    audit = AuditEvent.objects.create(actor=actor, patient_id=order.encounter.patient_id if order else None,
                                      action=action)
    ImagingEvent.objects.create(audit=audit, actor=actor, key=identity[0], digest=identity[1],
                                order=order, catalog=catalog, details=details)


@command_transaction
def catalog_revision(actor, data, version, key):
    if "Administrator" not in roles_for(actor):
        raise PermissionDenied
    _lock_providers([actor.pk])
    identity, previous = receipt(actor, key, "imaging_catalog_revision", data, version)
    if previous:
        return previous.catalog
    code = data["code"].strip().upper()
    if not re.fullmatch(r"SYN-[A-Z0-9-]{1,28}", code):
        raise ValidationError("Use a fictional code beginning with SYN-.")
    current = ImagingCatalog.objects.filter(code=code).first()
    try:
        check_version(version, current.revision if current else 0)
    except MedicationConflict:
        latest = (f"Latest revision is {current.revision}." if current else
                  "No revision exists yet. Use revision 0 to create this code.")
        raise MedicationConflict(
            f"The submitted revision for {code} is stale. {latest} "
            "Reload the catalog, review the latest entry, and reapply your changes before saving."
        ) from None
    item = ImagingCatalog(**{**data, "code": code}, revision=version + 1)
    item.full_clean()
    item.save()
    record(actor, "imaging_catalog_revision", identity, catalog=item, revision=item.revision, active=item.active)
    return item


def physician_encounter(actor, encounter_id, patient_id):
    if not can_write(actor, actor.pk):
        raise PermissionDenied
    _lock_providers([actor.pk])
    encounter = Encounter.objects.filter(
        pk=encounter_id, patient_id=patient_id, physician=actor,
    ).filter(patient_id=F("appointment__patient_id"), physician_id=F("appointment__physician_id")).first()
    if encounter is None:
        raise PermissionDenied
    return encounter


def order_snapshot(order):
    return {"status": order.status, "version": order.version, "catalog": order.catalog_id,
            "priority": order.priority, "indication": order.indication}


def can_cancel(order):
    return order.status in ("draft", "signed") and not (
        hasattr(order, "workflow") and order.workflow.status != "assigned"
    )


@command_transaction
def order_command(actor, patient_id, encounter_id, action, version, key, confirmed, *, order_id=None,
                  catalog_id=None, priority="", indication="", reason="", scheduled_at=None):
    encounter = physician_encounter(actor, encounter_id, patient_id)
    identity, previous = receipt(actor, key, action, patient_id, encounter_id, version, confirmed, order_id,
                                 catalog_id, priority, indication, reason, scheduled_at)
    if previous:
        return previous.order
    if confirmed is not True:
        raise ValidationError("Confirm this fictional imaging action.")
    order = ImagingOrder.objects.filter(pk=order_id, encounter=encounter).first() if order_id else None
    if order_id and order is None:
        raise PermissionDenied
    check_version(version, order.version if order else 0)
    before = order_snapshot(order) if order else None
    if action == "imaging_draft":
        if encounter.status != "in_progress" or (order and order.status != "draft"):
            raise ValidationError("Drafts require an active encounter.")
        catalog = active_catalog().filter(pk=catalog_id).first()
        if catalog is None or priority not in dict(ImagingOrder.PRIORITIES):
            raise ValidationError("Choose an active fictional examination and a priority.")
        order = order or ImagingOrder(encounter=encounter, version=0)
        order.catalog, order.priority = catalog, priority
        order.indication = text_value(indication, 500, "a fictional indication")
    elif not order:
        raise ValidationError("Create a draft first.")
    elif action == "imaging_sign" and order.status == "draft" and encounter.status == "in_progress":
        if not active_catalog().filter(pk=order.catalog_id).exists():
            raise ValidationError("Refresh the draft with an active catalog revision before signing.")
        order.status, order.signed_at, order.signed_by = "signed", timezone.now(), actor
    elif action == "imaging_cancel" and can_cancel(order):
        order.status, order.cancellation_reason = "cancelled", text_value(reason, 240, "a cancellation reason")
    elif action == "imaging_schedule" and order.status == "signed":
        schedule(order, scheduled_at)
    else:
        raise ValidationError("This action is unavailable in the current workflow state.")
    order.version += 1
    order.save()
    record(actor, action, identity, order=order, before=before, after=order_snapshot(order),
           reason=order.cancellation_reason, scheduled_at=scheduled_at.isoformat() if scheduled_at else None)
    return order


def schedule(order, scheduled_at):
    if hasattr(order, "workflow") and order.workflow.status != "assigned":
        raise ValidationError("An examination that has started cannot be rescheduled.")
    if scheduled_at is None or timezone.is_naive(scheduled_at) or scheduled_at <= timezone.now():
        raise ValidationError("Enter a future clinic-local examination time.")
    exam, created = ImagingExam.objects.get_or_create(order=order, defaults={"scheduled_at": scheduled_at})
    if not created:
        exam.scheduled_at = scheduled_at
        exam.version += 1
        exam.save(update_fields=["scheduled_at", "version"])
