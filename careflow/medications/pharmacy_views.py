from django import forms
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import can_write, clinical_access
from careflow.history.models import AllergyState
from careflow.patients.models import AuditEvent
from .access import orders_for
from .forms import CommandForm, ReasonForm
from .pharmacy import pharmacy_command
from .pharmacy_access import pharmacy_access, signed_queue
from .views import action_page


ACTIONS = {
    "claim": "Claim order",
    "approve": "Approve verification",
    "clarify": "Request clarification",
    "reject": "Reject order",
    "dispense": "Record simulated dispensing",
}


class DispenseForm(CommandForm):
    quantity = forms.IntegerField(min_value=1, label="Quantity of simulated units")


@require_safe
@pharmacy_access
def worklist(request):
    queue = signed_queue().select_related("pharmacy_review__dispense")
    waiting = queue.filter(pharmacy_review__isnull=True)
    assigned = queue.filter(pharmacy_review__assignee=request.user).select_related("encounter__patient")
    return render(request, "medications/pharmacy_worklist.html", {
        "waiting": Paginator(waiting, 30).get_page(request.GET.get("waiting_page")),
        "assigned": Paginator(assigned, 30).get_page(request.GET.get("assigned_page")),
    })


def assigned_order(actor, order_id):
    return get_object_or_404(
        signed_queue().select_related("encounter__patient", "signed_by", "pharmacy_review__dispense__event__audit"),
        public_id=order_id, pharmacy_review__assignee=actor,
    )


@require_safe
@pharmacy_access
def pharmacy_detail(request, order_id):
    order = assigned_order(request.user, order_id)
    patient = order.encounter.patient
    AuditEvent.objects.create(actor=request.user, patient=patient, action="pharmacy_view")
    return render(request, "medications/pharmacy_detail.html", {
        "order": order, "patient": patient, "review": order.pharmacy_review,
        "events": order.events.select_related("actor", "audit").filter(audit__action__startswith="pharmacy_"),
        "allergy_state": AllergyState.objects.filter(patient=patient).first(),
    })


@require_http_methods(["GET", "POST"])
@pharmacy_access
def action(request, order_id, action):
    if action not in ACTIONS:
        raise PermissionDenied
    if action == "claim":
        order = get_object_or_404(
            signed_queue().filter(Q(pharmacy_review__isnull=True) | Q(pharmacy_review__assignee=request.user)),
            public_id=order_id,
        )
        if request.method == "GET" and hasattr(order, "pharmacy_review"):
            return redirect("pharmacy_detail", order.public_id)
        version = order.version
        context = {"requisition": order}
    else:
        order = assigned_order(request.user, order_id)
        review = order.pharmacy_review
        if request.method == "GET":
            allowed = (review.status == "approved" and not hasattr(review, "dispense")
                       if action == "dispense" else review.status == "pending")
            if not allowed:
                raise PermissionDenied
        version = review.version
        context = {"order": order, "patient": order.encounter.patient, "encounter": order.encounter}
    form_class = {"clarify": ReasonForm, "reject": ReasonForm, "dispense": DispenseForm}.get(action, CommandForm)
    form = form_class(request.POST if request.method == "POST" else None, initial={"version": version})
    return action_page(request, form, ACTIONS[action], ACTIONS[action],
                       lambda data: pharmacy_command(request.user, order_id, action, **data),
                       lambda record: redirect("pharmacy_detail", record.public_id),
                       pharmacy_action=True, **context)


@require_http_methods(["GET", "POST"])
@clinical_access
def respond(request, order_id):
    order = get_object_or_404(orders_for(request.user), public_id=order_id, author=request.user)
    if not can_write(request.user, order.author_id) or not hasattr(order, "pharmacy_review"):
        raise PermissionDenied
    review = order.pharmacy_review
    if request.method == "GET" and review.status != "clarification":
        raise PermissionDenied
    form = ReasonForm(request.POST if request.method == "POST" else None, initial={"version": review.version})
    form.fields["reason"].label = "Clarification response"
    return action_page(request, form, "Respond to pharmacy clarification", "Submit response",
                       lambda data: pharmacy_command(request.user, order_id, "respond", **data),
                       lambda record: redirect("med_detail", record.public_id),
                       order=order, patient=order.encounter.patient, encounter=order.encounter,
                       clarification=review.reason)
