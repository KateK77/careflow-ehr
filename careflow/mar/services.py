from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from careflow.medications.models import PharmacyDispenseEvent
from careflow.medications.services import (
    MedicationConflict, check_version, command_conflicts, command_identity, command_transaction, require_confirmation,
)
from careflow.nursing.access import can_document, nursing_writer
from careflow.patients.models import AuditEvent
from careflow.scheduling.services import _lock_providers
from .models import MedicationAdministrationEvent


@command_conflicts
def record(actor, receipt_id, patient_id, encounter_id, *, version, key, confirmed, occurred_at, quantity=None,
           notes="", status="administered", reason="", correction_reason="", correction=False):
    if not nursing_writer(actor):
        raise PermissionDenied
    provider = PharmacyDispenseEvent.objects.values_list("review__order__author_id", flat=True).get(pk=receipt_id)
    return apply(actor, receipt_id, provider, patient_id, encounter_id, version, key, confirmed,
                 quantity, occurred_at, notes, status, reason, correction_reason, correction)


@command_transaction
def apply(actor, receipt_id, provider, patient_id, encounter_id, version, key, confirmed,
          quantity, occurred_at, notes, status, reason, correction_reason, correction):
    _lock_providers([provider])
    receipt = PharmacyDispenseEvent.objects.select_related(
        "review__order__encounter__appointment", "event__audit",
    ).get(pk=receipt_id)
    review = receipt.review
    order = review.order
    encounter = order.encounter
    if not nursing_writer(actor) or encounter.pk != encounter_id or encounter.patient_id != patient_id:
        raise PermissionDenied
    require_confirmation(confirmed)
    action = "mar_correct" if correction else ("mar_administer" if status == "administered" else "mar_exception")
    payload = [receipt_id, patient_id, encounter_id, version, quantity, occurred_at, notes]
    # Keep earlier 4B-1 administration command receipts replayable.
    if action != "mar_administer" or reason or correction_reason:
        payload.extend([status, reason, correction_reason])
    key, digest = command_identity(key, action, *payload)
    prior = MedicationAdministrationEvent.objects.filter(actor=actor, command_key=key).first()
    if prior:
        if prior.digest != digest:
            raise MedicationConflict("This submission was already used for different input.")
        return prior

    encounter.clean()
    if (order.author_id != provider or order.author_id != encounter.physician_id
            or order.signed_by_id != provider or not order.signed_at or order.status != "signed"
            or review.status != "approved" or receipt.event.order_id != order.pk
            or receipt.event.audit.action != "pharmacy_dispense" or receipt.quantity != order.quantity):
        raise MedicationConflict("MAR requires a valid signed order and its approved simulated dispensing receipt.")
    if encounter.status != "in_progress" or not can_document(actor, encounter.appointment):
        raise MedicationConflict("MAR recording requires an active, checked-in Encounter.")
    current = receipt.administration_events.first()
    check_version(version, current.revision if current else 0)
    if correction:
        if not current:
            raise MedicationConflict("Record an outcome before correcting it.")
    elif current and (current.status != "held" or status == "held"):
        raise MedicationConflict("This outcome is already recorded. Use an explicit correction if needed.")
    if status not in MedicationAdministrationEvent.Status.values:
        raise ValidationError("Choose a valid simulated outcome.")
    if any(not isinstance(text, str) or len(text) > 1000 for text in (notes, reason, correction_reason)):
        raise ValidationError("Use at most 1,000 characters per fictional text field.")
    reason = reason.strip()
    correction_reason = correction_reason.strip()
    if correction != bool(correction_reason):
        raise ValidationError("Provide an explanation for an explicit correction.")
    if status == "administered":
        if type(quantity) is not int or quantity != receipt.quantity:
            raise ValidationError("Enter the full quantity from the simulated dispensing receipt.")
        if reason:
            raise ValidationError("Exception reasons apply only to held, refused or omitted outcomes.")
    elif quantity is not None or not reason:
        raise ValidationError("Enter a fictional reason and leave quantity blank for an exception.")
    if (not isinstance(occurred_at, datetime) or timezone.is_naive(occurred_at)
            or not max(encounter.started_at, receipt.event.audit.occurred_at) <= occurred_at <= timezone.now()):
        raise ValidationError("Use a time from dispensing through the current time in this Encounter.")
    if current and not correction and occurred_at < current.occurred_at:
        raise ValidationError("A held task resolution must occur at or after the hold.")
    fields = ["status", "quantity", "occurred_at", "notes"]
    if reason:
        fields.append("reason")
    if correction_reason:
        fields.append("correction_reason")
    audit = AuditEvent.objects.create(actor=actor, patient_id=patient_id, action=action, changed_fields=fields)
    return MedicationAdministrationEvent.objects.create(
        receipt=receipt, revision=version + 1, status=status, quantity=quantity, occurred_at=occurred_at,
        notes=notes, reason=reason, correction_reason=correction_reason,
        actor=actor, audit=audit, command_key=key, digest=digest,
    )
