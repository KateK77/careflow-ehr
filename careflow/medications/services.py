import hashlib
import json
import uuid
from functools import wraps

from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import F
from django.utils import timezone

from careflow.clinical.access import can_write
from careflow.clinical.models import Encounter
from careflow.patients.access import roles_for
from careflow.patients.models import AuditEvent
from careflow.scheduling.services import _lock_providers
from .models import CATALOG_CONTENT, MedicationOrder, MedicationOrderEvent, PharmacyReview, SyntheticMedicationCatalog


class MedicationConflict(ValidationError):
    pass


ORDER_FIELDS = ("catalog_id", "dose", "route", "frequency", "duration", "quantity", "instructions")


def command_conflicts(function):
    @wraps(function)
    def execute(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except IntegrityError as exc:
            raise MedicationConflict("This change conflicts with another record. Reload and try again.") from exc
        except OperationalError as exc:
            if "locked" in str(exc).lower():
                raise MedicationConflict("Another action is in progress. Reload and try again.") from exc
            raise
    return execute


def command_transaction(function):
    return command_conflicts(transaction.atomic(function))


def command_identity(key, action, *payload):
    try:
        key = uuid.UUID(str(key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("A valid command identifier is required.") from None
    digest = hashlib.sha256(json.dumps([action, *payload], sort_keys=True, default=str).encode()).hexdigest()
    return key, digest


def replay(actor, key, digest):
    prior = MedicationOrderEvent.objects.filter(actor=actor, command_key=key).first()
    if prior:
        if prior.digest != digest:
            raise MedicationConflict("This submission was already used for different input. Reload the form.")
        return prior.order or prior.catalog
    return None


def check_version(version, current):
    if type(version) is not int or version != current:
        raise MedicationConflict("This record changed. Reload before trying again.")


def snapshot(instance):
    values = {field.name: field.value_from_object(instance) for field in instance._meta.fields}
    if isinstance(instance, MedicationOrder):
        values.update(route_label=instance.get_route_display(), frequency_label=instance.get_frequency_display())
    return json.loads(json.dumps(values, default=str))


def record_event(actor, key, digest, action, record, before, reason="", after=None):
    order = record if isinstance(record, MedicationOrder) else None
    after = snapshot(record) if after is None else after
    audit = AuditEvent.objects.create(
        actor=actor, patient=order.encounter.patient if order else None, action=action,
        changed_fields=[field for field in after if after[field] != before.get(field)],
    )
    MedicationOrderEvent.objects.create(
        order=order, catalog=None if order else record, actor=actor, audit=audit,
        command_key=key, digest=digest, before=before, after=after, reason=reason,
    )
    return record


def require_confirmation(confirmed):
    if confirmed is not True:
        raise ValidationError("Confirm that this action uses synthetic data.")


def require_admin(actor):
    if "Administrator" not in roles_for(actor):
        raise PermissionDenied


@command_transaction
def create_catalog(actor, data, key, confirmed):
    SyntheticMedicationCatalog.objects.filter(pk=0).update(version=F("version"))
    require_admin(actor)
    require_confirmation(confirmed)
    data = {field: data.get(field) for field in CATALOG_CONTENT}
    key, digest = command_identity(key, "med_catalog_create", data)
    if prior := replay(actor, key, digest):
        return prior
    revision = SyntheticMedicationCatalog(**data)
    revision.full_clean(validate_constraints=False)
    if SyntheticMedicationCatalog.objects.filter(code=revision.code, revision=revision.revision).exists():
        raise ValidationError("This code and revision already exist.")
    revision.save()
    return record_event(actor, key, digest, "med_catalog_create", revision, {})


@command_transaction
def set_active(actor, catalog_id, active, version, key, confirmed):
    SyntheticMedicationCatalog.objects.filter(pk=0).update(version=F("version"))
    require_admin(actor)
    require_confirmation(confirmed)
    if type(active) is not bool:
        raise ValidationError("Choose activation or retirement.")
    key, digest = command_identity(key, "med_catalog_active", catalog_id, active, version)
    if prior := replay(actor, key, digest):
        return prior
    revision = SyntheticMedicationCatalog.objects.select_for_update().get(pk=catalog_id)
    check_version(version, revision.version)
    if revision.active == active:
        raise ValidationError("The revision already has this status.")
    if active and SyntheticMedicationCatalog.objects.filter(code=revision.code, active=True).exists():
        raise ValidationError("Retire the current active revision before activating another.")
    before = snapshot(revision)
    revision.active = active
    revision.version += 1
    revision.save()
    return record_event(actor, key, digest, "med_catalog_activate" if active else "med_catalog_retire", revision, before)


def owned_encounter(actor, encounter_id, patient_id):
    encounter = Encounter.objects.select_related("patient", "appointment").get(pk=encounter_id)
    if encounter.patient_id != patient_id or not can_write(actor, encounter.physician_id):
        raise PermissionDenied
    encounter.clean()
    return encounter


def require_open(encounter):
    if encounter.status != "in_progress":
        raise MedicationConflict("This action requires an in-progress Encounter.")


@command_transaction
def save_draft(actor, encounter_id, patient_id, data, version, key, confirmed, order_id=None):
    _lock_providers([actor.pk])
    encounter = owned_encounter(actor, encounter_id, patient_id)
    require_confirmation(confirmed)
    data = {field: data.get(field) for field in ORDER_FIELDS}
    key, digest = command_identity(key, "med_order_save", encounter_id, patient_id, order_id, version, data)
    if prior := replay(actor, key, digest):
        return prior
    require_open(encounter)
    if order_id:
        order = MedicationOrder.objects.select_for_update().get(public_id=order_id)
        if order.encounter_id != encounter_id or order.author_id != actor.pk:
            raise PermissionDenied
        check_version(version, order.version)
        if order.status != "draft":
            raise MedicationConflict("Only a draft may be edited.")
        before = snapshot(order)
        order.version += 1
    else:
        check_version(version, 0)
        order = MedicationOrder(encounter=encounter, author=actor)
        before = {}
    catalog = SyntheticMedicationCatalog.objects.select_for_update().filter(pk=data["catalog_id"], active=True).first()
    if not catalog:
        raise ValidationError("Select an active fictional medication revision.")
    for field, value in data.items():
        setattr(order, field, value)
    order.catalog_snapshot = catalog.snapshot()
    order.full_clean()
    order.save()
    return record_event(actor, key, digest, "med_order_edit" if order_id else "med_order_create", order, before)


def review_token(actor, order):
    return signing.dumps([actor.pk, str(order.public_id), order.version], salt="medication-review")


@command_transaction
def transition_order(actor, order_id, action, version, key, confirmed, token="", reason=""):
    _lock_providers([actor.pk])
    order = MedicationOrder.objects.select_for_update().select_related("encounter").get(public_id=order_id)
    encounter = owned_encounter(actor, order.encounter_id, order.encounter.patient_id)
    if order.author_id != actor.pk:
        raise PermissionDenied
    require_confirmation(confirmed)
    key, digest = command_identity(key, "med_order_" + action, order_id, version, reason)
    if prior := replay(actor, key, digest):
        return prior
    check_version(version, order.version)
    before = snapshot(order)
    now = timezone.now()
    if action == "sign":
        require_open(encounter)
        if order.status != "draft":
            raise MedicationConflict("Only a draft may be signed.")
        catalog = SyntheticMedicationCatalog.objects.select_for_update().get(pk=order.catalog_id)
        if not catalog.active:
            raise ValidationError("Select an active revision before signing.")
        try:
            reviewed = signing.loads(token, salt="medication-review", max_age=900)
        except signing.BadSignature:
            raise ValidationError("Open Review and Sign again before confirming.") from None
        if reviewed != [actor.pk, str(order.public_id), order.version]:
            raise MedicationConflict("The draft changed since preview. Review it again.")
        order.status = "signed"
        order.signed_at = now
        order.signed_by = actor
    elif action == "cancel":
        if order.status not in {"draft", "signed"}:
            raise MedicationConflict("This order cannot be cancelled.")
        if order.status == "draft":
            require_open(encounter)
        if PharmacyReview.objects.filter(order=order).exists():
            raise MedicationConflict("A claimed order must remain available for pharmacy review.")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 1000:
            raise ValidationError("Enter a cancellation reason of up to 1,000 characters.")
        order.status = "cancelled"
        order.cancelled_at = now
        order.cancellation_reason = reason.strip()
    else:
        raise ValidationError("Unknown medication order action.")
    order.version += 1
    order.full_clean()
    order.save()
    return record_event(actor, key, digest, "med_order_" + action, order, before, reason=reason)
