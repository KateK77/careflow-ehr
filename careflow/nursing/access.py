from careflow.clinical.access import clinical_appointments_for
from careflow.patients.access import roles_for
from careflow.clinical.models import Encounter


def appointments_for(user):
    return clinical_appointments_for(user)


def nursing_writer(user):
    return "Nurse" in roles_for(user)


def can_document(user, appointment):
    return (nursing_writer(user) and appointment.status == "arrived"
            and not Encounter.objects.filter(appointment=appointment, status="completed").exists())


def nursing_context(request):
    return {"show_nursing_workspace": bool(set(roles_for(request.user)) & {"Nurse", "Administrator"})}
