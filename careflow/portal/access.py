from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.cache import add_never_cache_headers

from .models import PatientPortalAccount


def patient_for(user):
    if not user.is_authenticated or not user.is_active or user.is_staff or user.is_superuser or user.groups.exists():
        return None
    link = PatientPortalAccount.objects.select_related("patient").filter(user=user).first()
    return link.patient if link else None


def patient_only(view):
    @wraps(view)
    def checked(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), "portal_login")
        patient = patient_for(request.user)
        if patient is None:
            raise PermissionDenied
        return view(request, patient, *args, **kwargs)
    return checked


class PortalBoundary:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        portal = request.path_info.startswith("/portal/")
        staff = request.path_info.startswith("/app/")
        if staff and request.user.is_authenticated and PatientPortalAccount.objects.filter(user=request.user).exists():
            response = render(request, "portal/error.html", {"message": "Staff access is required."}, status=403)
            add_never_cache_headers(response)
            return response
        response = self.get_response(request)
        if portal or request.path_info.startswith("/app/portal/"):
            if response.status_code in (403, 404):
                response = render(request, "portal/error.html", {"message": "This page is unavailable."}, status=response.status_code)
            add_never_cache_headers(response)
        return response

    def process_exception(self, request, exception):
        from django.http import Http404
        if request.path_info.startswith(("/portal/", "/app/portal/")) and not isinstance(exception, (PermissionDenied, Http404)):
            return render(request, "portal/error.html", {"message": "The portal could not complete this request."}, status=500)
        return None
