from django.core.exceptions import PermissionDenied

from careflow.patients.access import roles_for
from careflow.portal.models import PatientPortalAccount
from .models import InpatientStay


def is_operator(actor):
    return (actor.is_authenticated and actor.is_active
            and actor.groups.filter(name__in=["Administrator", "HospitalOperations"]).exists()
            and not PatientPortalAccount.objects.filter(user=actor).exists())


def require_operator(actor):
    if not is_operator(actor):
        raise PermissionDenied


def stays_for(actor):
    query = InpatientStay.objects.select_related("request__patient", "attending", "bed__room__ward__department")
    if is_operator(actor) or "Nurse" in roles_for(actor):
        return query
    if "Physician" in roles_for(actor):
        return query.filter(attending=actor)
    return query.none()


def hospital_context(request):
    return {"show_hospital": is_operator(request.user) or bool(set(roles_for(request.user)) & {"Physician", "Nurse"}),
            "hospital_operator": is_operator(request.user),
            "has_hospital_role": request.user.is_authenticated and request.user.is_active
            and request.user.groups.filter(name="HospitalOperations").exists()}
