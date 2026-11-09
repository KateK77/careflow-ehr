from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

from .models import AuditEvent


READ_ROLES = ("Administrator", "Physician", "Nurse", "FrontDesk")
WRITE_ROLES = ("Administrator", "FrontDesk")


def roles_for(user):
    if not user.is_authenticated or not user.is_active:
        return []
    return list(user.groups.filter(name__in=READ_ROLES).values_list("name", flat=True))


def patient_access(write=False):
    def decorate(view):
        @wraps(view)
        def guarded(request, *args, **kwargs):
            roles = roles_for(request.user)
            allowed_roles = WRITE_ROLES if write else READ_ROLES
            if not any(role in allowed_roles for role in roles):
                actor = request.user if request.user.is_authenticated else None
                AuditEvent.objects.create(actor=actor, action="access_denied", outcome="denied")
                if not request.user.is_authenticated:
                    return redirect_to_login(request.get_full_path())
                return render(request, "core/403.html", status=403)
            return view(request, *args, **kwargs)
        return guarded
    return decorate


def staff_context(request):
    roles = roles_for(request.user)
    return {
        "staff_roles": roles,
        "can_manage_patients": any(role in WRITE_ROLES for role in roles),
    }
