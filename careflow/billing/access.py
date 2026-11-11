from django.core.exceptions import PermissionDenied

from careflow.portal.models import PatientPortalAccount


def is_billing(user):
    return (user.is_authenticated and user.is_active and user.groups.filter(name="BillingStaff").exists()
            and not PatientPortalAccount.objects.filter(user=user).exists())


def require_billing(user):
    if not is_billing(user):
        raise PermissionDenied


def billing_context(request):
    return {"show_billing_workspace": is_billing(request.user)}
