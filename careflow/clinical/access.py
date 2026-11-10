from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django.shortcuts import render

from careflow.patients.access import roles_for
from careflow.patients.models import AuditEvent, Patient
from careflow.scheduling.models import Appointment
from .models import Encounter


def clinical_access(view):
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not set(roles_for(request.user)) & {"Administrator", "Physician", "Nurse"}:
            AuditEvent.objects.create(actor=request.user if request.user.is_authenticated else None,
                                      action="clinical_access_denied", outcome="denied")
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            return render(request, "core/403.html", status=403)
        return view(request, *args, **kwargs)
    return guarded


def clinic_reader(user):
    return bool(set(roles_for(user)) & {"Administrator", "Nurse"})


def encounters_for(user):
    records = Encounter.objects.select_related("patient", "physician", "appointment")
    return records if clinic_reader(user) else records.filter(physician=user)


def clinical_appointments_for(user):
    records = Appointment.objects.select_related("patient", "physician")
    return records if clinic_reader(user) else records.filter(physician=user)


def charts_for(user):
    if clinic_reader(user):
        return Patient.objects.all()
    return Patient.objects.filter(Q(appointment__physician=user) | Q(encounter__physician=user)).distinct()


def can_write(user, physician_id):
    return "Physician" in roles_for(user) and user.pk == physician_id


def clinical_context(request):
    return {"can_read_clinical": bool(set(roles_for(request.user)) & {"Administrator", "Physician", "Nurse"})}
