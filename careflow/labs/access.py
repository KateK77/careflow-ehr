from careflow.clinical.access import can_write
from careflow.patients.access import roles_for
from .models import LabOrder


def orders_for(user):
    records = LabOrder.objects.select_related("patient", "encounter", "ordering_physician", "catalog", "cancelled_by")
    roles = roles_for(user)
    if "Administrator" in roles:
        return records
    if "Nurse" in roles:
        # A multi-role Nurse/Physician can also read their own unsubmitted drafts.
        from django.db.models import Q
        scope = Q(submitted_at__isnull=False)
        if "Physician" in roles:
            scope |= Q(ordering_physician=user)
        return records.filter(scope)
    return records.filter(ordering_physician=user) if "Physician" in roles else records.none()


def may_write(user, order):
    return can_write(user, order.ordering_physician_id)
