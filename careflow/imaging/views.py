import uuid

from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import can_write, charts_for
from careflow.clinical.models import Encounter
from careflow.patients.access import roles_for

from .access import orders_for
from .models import ImagingCatalog, ImagingOrder
from .services import active_catalog, can_cancel, catalog_revision, order_command


LABELS = {
    "imaging_catalog_revision": "Catalog revision created", "imaging_draft": "Draft saved",
    "imaging_sign": "Order signed", "imaging_schedule": "Examination scheduled", "imaging_cancel": "Order cancelled",
}
ACTIONS = {"imaging_draft": "Save draft", "imaging_sign": "Sign order",
           "imaging_schedule": "Schedule or reschedule examination", "imaging_cancel": "Cancel order"}


class CommandForm(forms.Form):
    key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)


class CatalogForm(CommandForm):
    version = forms.IntegerField(min_value=0, initial=0, label="Current revision")
    code = forms.CharField(max_length=32, help_text="Use a fictional SYN- code.")
    name = forms.CharField(max_length=120)
    modality = forms.ChoiceField(choices=ImagingCatalog.MODALITIES)
    active = forms.BooleanField(required=False, label="Active for ordering")


class OrderForm(CommandForm):
    action = forms.ChoiceField(choices=ACTIONS.items())
    catalog = forms.ModelChoiceField(queryset=ImagingCatalog.objects.none(), required=False)
    priority = forms.ChoiceField(choices=ImagingOrder.PRIORITIES, required=False)
    indication = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    reason = forms.CharField(max_length=240, required=False, label="Cancellation reason")
    scheduled_at = forms.DateTimeField(required=False, label="Clinic-local examination time",
                                      widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    confirmed = forms.BooleanField(label="Confirm fictional imaging action")

    def __init__(self, *args, order, encounter, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["catalog"].queryset = ImagingCatalog.objects.all() if self.is_bound else active_catalog()
        if not self.is_bound:
            allowed = []
            if not order or order.status == "draft":
                if encounter.status == "in_progress":
                    allowed = ["imaging_draft"] if not order else ["imaging_draft", "imaging_sign"]
                if order:
                    allowed.append("imaging_cancel")
            elif order.status == "signed":
                allowed = ["imaging_schedule", "imaging_cancel"] if can_cancel(order) else []
            self.fields["action"].choices = [(key, ACTIONS[key]) for key in allowed]


def submit(form, action):
    if form.is_valid():
        try:
            return action(dict(form.cleaned_data))
        except ValidationError as error:
            form.add_error(None, error.messages)
    return None


@never_cache
@require_http_methods(["GET", "POST"])
def catalog(request):
    if "Administrator" not in roles_for(request.user):
        raise PermissionDenied
    form = CatalogForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        def save(data):
            version, key = data.pop("version"), data.pop("key")
            return catalog_revision(request.user, data, version, key)
        if submit(form, save):
            return redirect("imaging_catalog")
    return render(request, "imaging/catalog.html", {"form": form, "items": ImagingCatalog.objects.all()},
                  status=400 if form.errors else 200)


def order_history(order):
    from .workspace_views import WORKFLOW_ACTIONS
    labels = {**LABELS, **WORKFLOW_ACTIONS}
    return [(labels.get(event.audit.action, "Imaging activity"), event.actor, event.audit.occurred_at,
             event.details.get("reason"), event.details.get("scheduled_at"))
            for event in order.events.select_related("audit", "actor")]


@never_cache
@require_http_methods(["GET", "POST"])
def order_detail(request, order_id):
    order = get_object_or_404(orders_for(request.user), pk=order_id)
    return _order_page(request, order.encounter, order)


@never_cache
@require_http_methods(["GET", "POST"])
def order_new(request, patient_id, encounter_id):
    if not can_write(request.user, request.user.pk):
        raise PermissionDenied
    visits = Encounter.objects.select_related("patient").filter(
        patient_id=F("appointment__patient_id"), physician_id=F("appointment__physician_id"),
    )
    encounter = get_object_or_404(visits, pk=encounter_id, patient_id=patient_id,
                                  physician=request.user, status="in_progress")
    return _order_page(request, encounter)


def _order_page(request, encounter, order=None):
    writer = can_write(request.user, encounter.physician_id)
    form = None
    if writer:
        form = OrderForm(request.POST if request.method == "POST" else None, order=order, encounter=encounter, initial={
            "version": order.version if order else 0, "catalog": order.catalog_id if order else None,
            "priority": order.priority if order else "routine", "indication": order.indication if order else "",
        })
    if request.method == "POST":
        if not writer:
            raise PermissionDenied

        def save(data):
            item = data.pop("catalog")
            return order_command(request.user, encounter.patient_id, encounter.pk, order_id=order.pk if order else None,
                                 catalog_id=item.pk if item else None, **data)
        saved = submit(form, save)
        if saved:
            return redirect("imaging_order", saved.pk)
    return render(request, "imaging/order.html", {"visit": encounter, "order": order, "form": form,
                  "history": order_history(order) if order else []}, status=400 if form and form.errors else 200)


@never_cache
@require_safe
def patient_orders(request, patient_id):
    if not set(roles_for(request.user)) & {"Administrator", "Physician", "Nurse"}:
        raise PermissionDenied
    patient = get_object_or_404(charts_for(request.user), pk=patient_id)
    return render(request, "imaging/orders.html", {
        "patient": patient, "orders": orders_for(request.user).filter(encounter__patient=patient),
    })
