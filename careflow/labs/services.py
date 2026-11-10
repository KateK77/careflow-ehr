import hashlib
import json
import uuid
from functools import wraps
from typing import NamedTuple

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
from .models import LabEvent, LabOrder, LabSpecimen, LabTestCatalog


class LabConflict(ValidationError):
    pass


class Outcome(NamedTuple):
    record: object
    replayed: bool


def busy(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (IntegrityError, OperationalError) as error:
            if isinstance(error, IntegrityError) or "locked" in str(error).lower():
                raise LabConflict("The laboratory record changed or is busy. Reload and retry; no partial change was saved.") from error
            raise
    return run


def _admin(actor):
    if "Administrator" not in roles_for(actor):
        raise PermissionDenied


def _owner(actor, encounter):
    if not can_write(actor, encounter.physician_id):
        raise PermissionDenied


def _current(version, expected):
    if type(version) is not int or version != expected:
        raise LabConflict("This laboratory record changed. Reload before retrying.")


def _key(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("A valid command identifier is required.") from None


def _fingerprint(action, **data):
    return hashlib.sha256(json.dumps({"action": action, **data}, sort_keys=True, default=str, allow_nan=False).encode()).hexdigest()


def _replay(actor, key, fingerprint):
    event = LabEvent.objects.filter(command_actor=actor, command_key=key).select_related("order", "catalog").first()
    if event:
        if event.request_fingerprint != fingerprint:
            raise LabConflict("This command identifier was already used with different input. Reload the form.")
        return Outcome(event.order if event.order_id else event.catalog, True)


def _snapshot(record):
    return json.loads(json.dumps({f.name: f.value_from_object(record) for f in record._meta.fields}, default=str))


def _event(actor, key, fingerprint, action, record, before, specimen=None, result=None, extra=None, review_assignment=None, review=None):
    is_order = isinstance(record, LabOrder)
    after = _snapshot(record)
    changed = [k for k, v in after.items() if before.get(k) != v]
    audit = AuditEvent.objects.create(actor=actor, patient_id=record.patient_id if is_order else None,
                                      action=action, changed_fields=changed + (["pending_specimen"] if specimen else []))
    LabEvent.objects.create(order=record if is_order else None, catalog=None if is_order else record,
        specimen=specimen, result=result, review_assignment=review_assignment, review=review, audit=audit, command_actor=actor, command_key=key, request_fingerprint=fingerprint,
        before=before, after={**after, **({"specimen": _snapshot(specimen)} if specimen else {}), **(extra or {})})
    return Outcome(record, False)


def panel_snapshot(panel):
    return {name: getattr(panel, name) for name in ["code", "revision", "display_name", "specimen_type", "components", "schema_version"]}


@busy
def create_catalog(actor, data, command_key, confirmed):
    _admin(actor)
    if confirmed is not True:
        raise ValidationError("Confirm synthetic catalog information only.")
    key = _key(command_key)
    panel = LabTestCatalog(**{k: data[k] for k in ["code", "revision", "display_name", "specimen_type", "components"]}, created_by=actor)
    # Field/schema validation precedes the replay lookup, without uniqueness queries.
    panel.clean_fields(exclude=["created_at"])
    fingerprint = _fingerprint("catalog_create", **panel_snapshot(panel))
    with transaction.atomic():
        LabTestCatalog.objects.filter(pk=0).update(edit_version=F("edit_version"))  # initial SQLite writer reservation
        _admin(actor)
        if replay := _replay(actor, key, fingerprint):
            return replay
        panel.full_clean()
        panel.save()
        return _event(actor, key, fingerprint, "lab_catalog_create", panel, {})


@busy
def set_catalog_active(actor, catalog_id, version, active, command_key, confirmed):
    _admin(actor)
    if type(active) is not bool or confirmed is not True:
        raise ValidationError("Confirm the synthetic catalog action.")
    key = _key(command_key)
    fingerprint = _fingerprint("catalog_active", catalog=catalog_id, version=version, active=active)
    with transaction.atomic():
        LabTestCatalog.objects.filter(pk=0).update(edit_version=F("edit_version"))
        _admin(actor)
        if replay := _replay(actor, key, fingerprint):
            return replay
        panel = LabTestCatalog.objects.select_for_update().get(pk=catalog_id)
        _current(version, panel.edit_version)
        before = _snapshot(panel)
        panel.is_active = active
        panel.edit_version += 1
        panel.full_clean()
        panel.save()
        return _event(actor, key, fingerprint, "lab_catalog_activate" if active else "lab_catalog_deactivate", panel, before)


@busy
def save_draft(actor, encounter_id, catalog_id, reason, version, command_key, confirmed, order_id=None):
    encounter = Encounter.objects.get(pk=encounter_id)
    _owner(actor, encounter)
    if confirmed is not True or not isinstance(reason, str) or len(reason.strip()) > 1000:
        raise ValidationError("Confirm synthetic information and use a reason of at most 1000 characters.")
    reason = reason.strip()
    key = _key(command_key)
    fingerprint = _fingerprint("order_edit" if order_id else "order_create", encounter=encounter_id,
                                order=str(order_id) if order_id else None, catalog=catalog_id, reason=reason, version=version)
    with transaction.atomic():
        _lock_providers([encounter.physician_id])
        encounter = Encounter.objects.get(pk=encounter_id)
        _owner(actor, encounter)
        if order_id:
            order = LabOrder.objects.select_for_update().get(public_id=order_id, encounter=encounter, ordering_physician=actor)
        if replay := _replay(actor, key, fingerprint):
            return replay
        if encounter.status != "in_progress":
            raise LabConflict("New or edited drafts require an in-progress encounter.")
        panel = LabTestCatalog.objects.select_for_update().get(pk=catalog_id)
        if not panel.is_active:
            raise ValidationError("Select an active catalog revision.")
        if order_id:
            _current(version, order.version)
            if order.status != "draft":
                raise LabConflict("Only draft orders can be edited.")
            before = _snapshot(order)
            order.version += 1
        else:
            _current(version, 0)
            if LabOrder.objects.filter(creation_key=key).exists():
                raise LabConflict("This command identifier has already been used. Reload the form.")
            before = {}
            order = LabOrder(encounter=encounter, patient=encounter.patient, ordering_physician=actor, creation_key=key)
        order.catalog = panel
        order.catalog_snapshot = panel_snapshot(panel)
        order.reason = reason
        order.full_clean()
        order.save()
        return _event(actor, key, fingerprint, "lab_order_edit" if order_id else "lab_order_create", order, before)


def duplicate_orders(order):
    return LabOrder.objects.filter(encounter_id=order.encounter_id, catalog__code=order.catalog.code).exclude(pk=order.pk).exclude(status="cancelled")


def review_payload(actor, order, version, repeat_confirmed, repeat_reason):
    return {"actor": actor.pk, "order": str(order.public_id), "version": version,
            "repeat_confirmed": repeat_confirmed, "repeat_reason": repeat_reason.strip()}


def review_token(actor, order, version, repeat_confirmed, repeat_reason):
    return signing.dumps(review_payload(actor, order, version, repeat_confirmed, repeat_reason), salt="lab-order-review")


@busy
def submit_order(actor, order_id, version, command_key, confirmed, repeat_confirmed=False, repeat_reason="", token=""):
    order = LabOrder.objects.select_related("encounter").get(public_id=order_id)
    _owner(actor, order.encounter)
    if confirmed is not True or type(repeat_confirmed) is not bool or not isinstance(repeat_reason, str) or len(repeat_reason.strip()) > 1000:
        raise ValidationError("Confirm the synthetic order and provide a valid repeat-test reason if needed.")
    repeat_reason = repeat_reason.strip()
    key = _key(command_key)
    fingerprint = _fingerprint("order_submit", order=str(order_id), version=version, repeat_confirmed=repeat_confirmed, repeat_reason=repeat_reason)
    with transaction.atomic():
        _lock_providers([order.ordering_physician_id])
        order = LabOrder.objects.select_for_update().select_related("encounter", "catalog", "patient").get(public_id=order_id)
        _owner(actor, order.encounter)
        if replay := _replay(actor, key, fingerprint):
            return replay
        _current(version, order.version)
        if order.status != "draft" or order.encounter.status != "in_progress":
            raise LabConflict("Submission requires a current draft in an in-progress encounter.")
        panel = LabTestCatalog.objects.select_for_update().get(pk=order.catalog_id)
        if not panel.is_active:
            raise LabConflict("This panel revision is inactive. Edit the draft and explicitly select an active revision.")
        try:
            if signing.loads(token, salt="lab-order-review", max_age=600) != review_payload(actor, order, version, repeat_confirmed, repeat_reason):
                raise signing.BadSignature
        except signing.BadSignature:
            raise ValidationError("Review this order and confirm the same input within ten minutes.") from None
        if duplicate_orders(order).exists() and (not repeat_confirmed or not repeat_reason):
            raise ValidationError("A non-cancelled order for this panel already exists in the encounter. Confirm intentional repeat testing and enter a reason.")
        before = _snapshot(order)
        order.catalog_snapshot = panel_snapshot(panel)
        order.identity_snapshot = {"mrn": order.patient.mrn, "name": str(order.patient), "dob": order.patient.dob.isoformat()}
        from .review import initial_assignment
        order.current_review_assignment = initial_assignment(order, actor)
        order.status = "submitted"
        order.submitted_at = timezone.now()
        order.repeat_reason = repeat_reason if repeat_confirmed else ""
        order.version += 1
        order.full_clean()
        order.save()
        specimen = LabSpecimen(order=order, specimen_type=order.catalog_snapshot["specimen_type"], created_by=actor)
        specimen.full_clean()
        specimen.save()
        return _event(actor, key, fingerprint, "lab_order_submit", order, before, specimen)


@busy
def cancel_order(actor, order_id, version, reason, command_key, confirmed):
    order = LabOrder.objects.select_related("encounter").get(public_id=order_id)
    _owner(actor, order.encounter)
    if confirmed is not True or not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 1000:
        raise ValidationError("Confirm cancellation and enter a reason of 1–1000 characters.")
    reason = reason.strip()
    key = _key(command_key)
    fingerprint = _fingerprint("order_cancel", order=str(order_id), version=version, reason=reason)
    with transaction.atomic():
        _lock_providers([order.ordering_physician_id])
        order = LabOrder.objects.select_for_update().select_related("encounter").get(public_id=order_id)
        _owner(actor, order.encounter)
        if replay := _replay(actor, key, fingerprint):
            return replay
        _current(version, order.version)
        if order.status not in {"draft", "submitted"} or order.specimens.filter(received_at__isnull=False).exists():
            raise LabConflict("Cancellation requires a draft/submitted order with no specimen ever received.")
        before = _snapshot(order)
        order.status = "cancelled"
        order.cancelled_at = timezone.now()
        order.cancelled_by = actor
        order.cancellation_reason = reason
        order.version += 1
        order.full_clean()
        order.save()
        return _event(actor, key, fingerprint, "lab_order_cancel", order, before)
