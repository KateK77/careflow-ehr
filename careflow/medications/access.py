from django.db.models import Q

from careflow.patients.access import roles_for
from .models import MedicationOrder
from .pharmacy_access import is_pharmacist


def orders_for(actor):
    records = MedicationOrder.objects.select_related(
        "encounter__patient", "author", "signed_by", "catalog", "pharmacy_review__dispense",
    )
    roles = set(roles_for(actor))
    scope = Q(pk__in=[])
    if roles & {"Administrator", "Nurse"}:
        scope |= Q(signed_at__isnull=False)
    if "Physician" in roles:
        scope |= Q(author=actor)
    return records.filter(scope)


def medication_context(request):
    return {
        "can_browse_medications": bool(set(roles_for(request.user)) & {"Administrator", "Physician"}),
        "show_pharmacy_workspace": is_pharmacist(request.user),
    }
