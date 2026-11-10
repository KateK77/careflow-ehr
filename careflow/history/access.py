from django.db.models import Q

from careflow.clinical.access import charts_for
from careflow.patients.access import roles_for
from careflow.patients.models import Patient


def can_maintain(user, patient_id):
    if "Physician" not in roles_for(user):
        return False
    return Patient.objects.filter(pk=patient_id).filter(
        Q(appointment__physician=user, appointment__status__in=["scheduled", "arrived"],
          appointment__encounter__isnull=True)
        | Q(encounter__physician=user, encounter__status="in_progress")
    ).exists()


def patients_for(user):
    return charts_for(user)
