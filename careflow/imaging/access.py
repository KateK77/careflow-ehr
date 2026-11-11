from django.db.models import F, Q

from careflow.patients.access import roles_for
from .models import ImagingOrder


def orders_in_context():
    return ImagingOrder.objects.filter(
        encounter__patient_id=F("encounter__appointment__patient_id"),
        encounter__physician_id=F("encounter__appointment__physician_id"),
    ).select_related("catalog", "encounter__patient", "encounter__physician", "exam")


def orders_for(actor):
    roles = set(roles_for(actor))
    query = orders_in_context()
    allowed = Q(pk__in=[])
    if "Physician" in roles:
        allowed |= Q(encounter__physician=actor)
    if roles & {"Administrator", "Nurse"}:
        allowed |= Q(signed_at__isnull=False)
    return query.filter(allowed)
