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
    from django.db.models import Q
    scope=(Q(ordering_physician=user)|Q(current_review_assignment__physician=user)) if "Physician" in roles else Q(pk__in=[])
    if is_lab(user): scope |= Q(assigned_lab_staff=user,submitted_at__isnull=False)
    return records.filter(scope)


def may_write(user, order):
    return can_write(user, order.ordering_physician_id)


def is_lab(user):
    from django.contrib.auth import get_user_model
    return bool(user.is_authenticated and get_user_model().objects.filter(pk=user.pk,is_active=True,groups__name="Lab Staff").exists())


def lab_roles(user):
    from django.contrib.auth import get_user_model
    if not user.is_authenticated: return []
    return list(get_user_model().objects.filter(pk=user.pk,is_active=True).values_list("groups__name",flat=True))


def lab_context(request):
    return {"show_lab_workspace":bool(set(lab_roles(request.user)) & {"Administrator","Physician","Nurse","Lab Staff"}),"show_lab_review":bool(set(lab_roles(request.user)) & {"Administrator","Physician"}),"lab_staff_role":is_lab(request.user)}


def publications_for(user):
    from django.db.models import Q
    from careflow.clinical.access import charts_for
    records=LabOrder.objects.filter(current_publication__isnull=False).select_related('patient','encounter','current_publication','current_review_assignment__physician','assigned_lab_staff')
    roles=lab_roles(user)
    if 'Administrator' in roles or 'Nurse' in roles: return records
    scope=Q(pk__in=[])
    if 'Physician' in roles:
        scope|=Q(patient__in=charts_for(user))|Q(current_review_assignment__physician=user)
    if is_lab(user): scope|=Q(assigned_lab_staff=user)
    return records.filter(scope)
