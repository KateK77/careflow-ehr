from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F

from careflow.clinical.access import can_write
from careflow.labs.models import LabOrder, LabResult
from careflow.medications.services import command_transaction
from careflow.patients.models import AuditEvent
from careflow.scheduling.services import _lock_providers
from .models import PatientVisibleResultRelease


def eligible_results():
    return LabResult.objects.filter(
        order__status="fulfilled", order__current_publication_id=F("pk"),
        order__patient_id=F("order__encounter__patient_id"), specimen__order_id=F("order_id"),
        status__in=["final", "corrected"], publication_kind="report", published_at__isnull=False,
        schema_version=1, reason_code="",
    )


def patient_results(patient):
    return eligible_results().filter(order__patient=patient, portal_release__isnull=False).select_related("order").order_by("-published_at")


def display_result(result):
    components = []
    for item in result.payload["components"]:
        components.append({
            "code": item["code"], "value": item.get("value") if item["value_kind"] != "absent" else "Not performed",
            "unit": item.get("unit", ""),
        })
    return {"id": result.pk, "name": result.order.catalog_snapshot["display_name"],
            "published_at": result.published_at, "status": result.get_status_display(), "components": components}


@command_transaction
def release_result(actor, result_id, provider_id):
    if not can_write(actor, provider_id):
        raise PermissionDenied
    _lock_providers([provider_id])
    result = eligible_results().filter(pk=result_id, order__ordering_physician=actor).select_related("order").first()
    if result is None:
        raise ValidationError("This revision is no longer eligible for portal release.")
    existing = PatientVisibleResultRelease.objects.filter(result=result).first()
    if existing:
        return existing
    audit = AuditEvent.objects.create(actor=actor, patient_id=result.order.patient_id, action="portal_result_release",
                                      changed_fields=["patient_visible_release"])
    return PatientVisibleResultRelease.objects.create(result=result, audit=audit)
