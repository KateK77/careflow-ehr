from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import charts_for, clinical_access
from careflow.history.models import AllergyState
from careflow.medications.views import action_page
from careflow.nursing.access import can_document, nursing_writer
from .access import receipts_for
from .forms import AdministrationForm, FilterForm
from .services import record


@require_safe
@clinical_access
def worklist(request, patient_id=None):
    patient = get_object_or_404(charts_for(request.user), pk=patient_id) if patient_id else None
    records = receipts_for(request.user)
    if patient:
        records = records.filter(review__order__encounter__patient=patient)
    form = FilterForm(request.GET)
    if form.is_valid():
        for name, lookup in (
            ("patient", "review__order__encounter__patient_id"),
            ("encounter", "review__order__encounter_id"),
            ("medication", "review__order__catalog_snapshot__name__icontains"),
        ):
            if value := form.cleaned_data[name]:
                records = records.filter(**{lookup: value})
        state = form.cleaned_data["status"]
        if state == "pending":
            records = records.filter(effective_status__isnull=True)
        elif state:
            records = records.filter(effective_status=state)
    else:
        records = records.none()
    page = Paginator(records.order_by("-pk"), 30).get_page(request.GET.get("page"))
    parameters = request.GET.copy()
    parameters.pop("page", None)
    return render(request, "mar/worklist.html", {
        "rows": page, "filter_form": form, "patient": patient, "query": parameters.urlencode(),
    })


@require_safe
@clinical_access
def detail(request, receipt_id):
    receipt = get_object_or_404(receipts_for(request.user), pk=receipt_id)
    order = receipt.review.order
    encounter = order.encounter
    events = list(receipt.administration_events.select_related("actor", "audit"))
    return render(request, "mar/detail.html", {
        "receipt": receipt, "order": order, "patient": encounter.patient, "encounter": encounter,
        "current": events[0] if events else None, "events": events,
        "writable": encounter.status == "in_progress" and can_document(request.user, encounter.appointment),
        "allergy_state": AllergyState.objects.filter(patient=encounter.patient).first(),
    })


@require_http_methods(["GET", "POST"])
@clinical_access
def administer(request, patient_id, encounter_id, receipt_id):
    if not nursing_writer(request.user):
        raise PermissionDenied
    receipt = get_object_or_404(receipts_for(request.user), pk=receipt_id,
                                review__order__encounter_id=encounter_id,
                                review__order__encounter__patient_id=patient_id)
    order = receipt.review.order
    encounter = order.encounter
    if request.method == "GET" and (receipt.effective_status or encounter.status != "in_progress"
                                    or not can_document(request.user, encounter.appointment)):
        raise PermissionDenied
    form = AdministrationForm(request.POST if request.method == "POST" else None,
                              initial={"version": 0, "quantity": receipt.quantity,
                                       "occurred_at": timezone.localtime()})
    return action_page(
        request, form, "Record simulated administration", "Record administration",
        lambda data: record(request.user, receipt_id, patient_id, encounter_id, **data),
        lambda event: redirect("mar_detail", receipt_id=receipt_id),
        order=order, patient=encounter.patient, encounter=encounter,
    )
