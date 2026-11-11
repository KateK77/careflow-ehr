from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import MedicationOrder


def is_pharmacist(actor):
    return bool(actor.is_authenticated and actor.is_active and actor.groups.filter(name="Pharmacist").exists())


def require_pharmacist(actor):
    if not is_pharmacist(actor):
        raise PermissionDenied


def pharmacy_access(view):
    @wraps(view)
    def checked(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        require_pharmacist(request.user)
        return view(request, *args, **kwargs)
    return checked


def signed_queue():
    return MedicationOrder.objects.filter(status="signed", signed_at__isnull=False)
