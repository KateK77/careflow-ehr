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
def record(actor, receipt_id, patient_id, encounter_id, *, version, key, confirmed, quantity, occurred_at, notes=""):
    if not nursing_writer(actor):
        raise PermissionDenied
    provider = PharmacyDispenseEvent.objects.values_list("review__order__author_id", flat=True).get(pk=receipt_id)
    return apply(actor, receipt_id, provider, patient_id, encounter_id, version, key, confirmed,
                 quantity, occurred_at, notes)


@command_transaction
def apply(actor, receipt_id, provider, patient_id, encounter_id, version, key, confirmed, quantity, occurred_at, notes):
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
    key, digest = command_identity(key, "mar_administer", receipt_id, patient_id, encounter_id,
                                   version, quantity, occurred_at, notes)
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
    if current:
        raise MedicationConflict("This fictional task already has an administration event.")
    if type(quantity) is not int or quantity != receipt.quantity:
        raise ValidationError("Enter the full quantity from the simulated dispensing receipt.")
    if (not isinstance(occurred_at, datetime) or timezone.is_naive(occurred_at)
            or not max(encounter.started_at, receipt.event.audit.occurred_at) <= occurred_at <= timezone.now()):
        raise ValidationError("Use a time from dispensing through the current time in this Encounter.")
    if not isinstance(notes, str) or len(notes) > 1000:
        raise ValidationError("Use at most 1,000 characters for fictional notes.")
    audit = AuditEvent.objects.create(actor=actor, patient_id=patient_id, action="mar_administer",
                                      changed_fields=["status", "quantity", "occurred_at", "notes"])
    return MedicationAdministrationEvent.objects.create(
        receipt=receipt, revision=1, status="administered", quantity=quantity, occurred_at=occurred_at,
        notes=notes, actor=actor, audit=audit, command_key=key, digest=digest,
    )
