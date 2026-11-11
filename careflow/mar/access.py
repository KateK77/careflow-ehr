from django.db.models import OuterRef, Subquery, Q

from careflow.clinical.access import encounters_for
from careflow.medications.models import PharmacyDispenseEvent
from careflow.patients.access import roles_for
from .models import MedicationAdministrationEvent


def receipts_for(actor):
    order = "review__order"
    events = MedicationAdministrationEvent.objects.filter(receipt=OuterRef("pk")).order_by("-revision")
    records = PharmacyDispenseEvent.objects.select_related(
        "review__order__encounter__patient", "review__order__author", "event__audit",
    ).annotate(
        effective_status=Subquery(events.values("status")[:1]),
        effective_revision=Subquery(events.values("revision")[:1]),
        effective_time=Subquery(events.values("occurred_at")[:1]),
        effective_actor=Subquery(events.values("actor__username")[:1]),
    )
    if not set(roles_for(actor)) & {"Administrator", "Physician", "Nurse"}:
        return records.none()
    return records.filter(**{f"{order}__encounter__in": encounters_for(actor)}).filter(
        Q(effective_status__isnull=False) | Q(
            review__status="approved", review__order__status="signed",
            review__order__signed_at__isnull=False, review__order__encounter__status="in_progress",
            review__order__encounter__appointment__status="arrived",
        )
    )
