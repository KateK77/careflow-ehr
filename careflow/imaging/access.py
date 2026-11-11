from django.db.models import F, OuterRef, Q, Subquery

from careflow.patients.access import roles_for
from .models import ImagingOrder, ImagingReport


def orders_in_context():
    return ImagingOrder.objects.filter(
        encounter__patient_id=F("encounter__appointment__patient_id"),
        encounter__physician_id=F("encounter__appointment__physician_id"),
    ).select_related("catalog", "encounter__patient", "encounter__physician", "exam", "workflow")


def orders_for(actor):
    roles = set(roles_for(actor))
    query = orders_in_context()
    allowed = Q(pk__in=[])
    if "Physician" in roles:
        allowed |= Q(encounter__physician=actor)
    if roles & {"Administrator", "Nurse"}:
        allowed |= Q(signed_at__isnull=False)
    publication = ImagingReport.objects.filter(order_id=OuterRef("pk")).exclude(status="draft")
    return query.filter(allowed).annotate(
        publication_status=Subquery(publication.values("status")[:1]),
        publication_review=Subquery(publication.values("review__pk")[:1]),
    )


def is_radiology(actor):
    return actor.is_authenticated and actor.is_active and actor.groups.filter(name="RadiologyStaff").exists()


def radiology_context(request):
    return {"show_radiology_workspace": is_radiology(request.user)}
