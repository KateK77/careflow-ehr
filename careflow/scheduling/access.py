from django.contrib.auth import get_user_model

from careflow.patients.access import WRITE_ROLES, roles_for
from .models import Appointment


def own_schedule_only(user):
    roles = roles_for(user)
    return "Physician" in roles and not any(role in (*WRITE_ROLES, "Nurse") for role in roles)


def appointments_for(user):
    records = Appointment.objects.select_related("patient", "physician", "checked_in_by")
    return records.filter(physician=user) if own_schedule_only(user) else records


def physicians_for(user):
    records = get_user_model().objects.filter(is_active=True, groups__name="Physician").distinct()
    if own_schedule_only(user):
        records = records.filter(pk=user.pk)
    return records.order_by("last_name", "first_name", "username")
