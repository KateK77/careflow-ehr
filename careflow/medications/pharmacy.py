from django.core.exceptions import PermissionDenied, ValidationError

from careflow.clinical.access import can_write
from careflow.scheduling.services import _lock_providers
from .models import MedicationOrder, MedicationOrderEvent, PharmacyDispenseEvent, PharmacyReview
from .pharmacy_access import require_pharmacist
from .services import (
    MedicationConflict, check_version, command_conflicts, command_identity, command_transaction,
    record_event, replay, require_confirmation, snapshot,
)


REVIEW_TRANSITIONS = {
    "approve": ("pending", "approved"),
    "clarify": ("pending", "clarification"),
    "reject": ("pending", "rejected"),
    "respond": ("clarification", "pending"),
}
REASON_ACTIONS = {"clarify", "reject", "respond"}


@command_conflicts
def pharmacy_command(actor, order_id, action, version, key, confirmed, reason="", quantity=None):
    if action != "respond":
        require_pharmacist(actor)
    provider = MedicationOrder.objects.values_list("author_id", flat=True).get(public_id=order_id)
    if action == "respond" and not can_write(actor, provider):
        raise PermissionDenied
    return apply_command(actor, order_id, provider, action, version, key, confirmed, reason, quantity)


def require_signed_context(order):
    encounter = order.encounter
    encounter.clean()
    if order.author_id != encounter.physician_id or order.status != "signed" or not order.signed_at:
        raise MedicationConflict("Pharmacy processing requires a signed order in its original Encounter.")
    if encounter.status == "completed" and order.signed_at >= encounter.completed_at:
        raise MedicationConflict("The order must have been signed before Encounter completion.")


def review_snapshot(review):
    return {**snapshot(review), "status_label": review.get_status_display()}


@command_transaction
def apply_command(actor, order_id, provider, action, version, key, confirmed, reason, quantity):
    _lock_providers([provider])
    order = MedicationOrder.objects.select_for_update().select_related("encounter__appointment").get(public_id=order_id)
    if order.author_id != provider:
        raise MedicationConflict("The order context changed.")
    require_signed_context(order)
    require_confirmation(confirmed)

    review = PharmacyReview.objects.select_for_update().filter(order=order).first()
    if action == "respond":
        if not can_write(actor, order.author_id):
            raise PermissionDenied
    else:
        require_pharmacist(actor)
        if action != "claim" and (not review or review.assignee_id != actor.pk):
            raise PermissionDenied
    if not isinstance(reason, str) or len(reason) > 1000:
        raise ValidationError("Enter a reason of up to 1,000 characters.")
    reason = reason.strip()
    if action in REASON_ACTIONS and not reason:
        raise ValidationError("Enter a reason or clarification response.")
    event_action = "pharmacy_" + action
    key, digest = command_identity(key, event_action, order_id, version, reason, quantity)
    if prior := replay(actor, key, digest):
        return prior
    if action == "claim":
        check_version(version, order.version)
        if review:
            raise MedicationConflict("A Pharmacist has already claimed this order.")
        review = PharmacyReview.objects.create(order=order, assignee=actor)
        return record_event(actor, key, digest, event_action, order, {}, after=review_snapshot(review))

    if not review:
        raise MedicationConflict("This order has not been claimed.")
    check_version(version, review.version)
    before = review_snapshot(review)
    if action == "dispense":
        if review.status != "approved" or PharmacyDispenseEvent.objects.filter(review=review).exists():
            raise MedicationConflict("Simulated dispensing requires approval and can occur once.")
        if type(quantity) is not int or quantity != order.quantity:
            raise ValidationError("Enter the full ordered quantity of simulated units.")
    else:
        transition = REVIEW_TRANSITIONS.get(action)
        if not transition or review.status != transition[0]:
            raise MedicationConflict("This action is unavailable in the current review state.")
        review.status = transition[1]
        review.reason = reason if review.status in {"clarification", "rejected"} else ""
    review.version += 1
    review.full_clean()
    review.save()
    after = review_snapshot(review)
    if action == "dispense":
        after["dispensed_quantity"] = quantity
    record_event(actor, key, digest, event_action, order, before, reason=reason, after=after)
    if action == "dispense":
        event = MedicationOrderEvent.objects.get(actor=actor, command_key=key)
        PharmacyDispenseEvent.objects.create(review=review, event=event, quantity=quantity)
    return order
