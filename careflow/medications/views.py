from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import can_write, charts_for, clinical_access, encounters_for
from careflow.history.models import AllergyState
from careflow.patients.access import roles_for
from .access import orders_for
from .forms import CatalogForm, CommandForm, DraftForm, ReasonForm, SignForm
from .models import SyntheticMedicationCatalog
from .services import (
    MedicationConflict, create_catalog, require_admin, review_token, save_draft, set_active, transition_order,
)


def action_page(request, form, title, button, command, destination, **context):
    status = 200
    if request.method == "POST":
        status = 400
        if form.is_valid():
            try:
                record = command(form.cleaned_data)
            except ValidationError as exc:
                for message in exc.messages:
                    form.add_error(None, message)
                if isinstance(exc, MedicationConflict):
                    status = 409
            else:
                return destination(record)
    return render(request, "medications/action.html", {
        "form": form, "title": title, "button": button, **context,
    }, status=status)


@require_safe
@clinical_access
def catalog(request):
    roles = roles_for(request.user)
    admin = "Administrator" in roles
    if not admin and "Physician" not in roles:
        raise PermissionDenied
    rows = SyntheticMedicationCatalog.objects.all()
    if not admin:
        rows = rows.filter(active=True)
    return render(request, "medications/catalog.html", {
        "rows": Paginator(rows, 30).get_page(request.GET.get("page")), "manage": admin,
    })


@require_http_methods(["GET", "POST"])
@clinical_access
def catalog_create(request):
    require_admin(request.user)
    form = CatalogForm(request.POST if request.method == "POST" else None, initial={"version": 0})
    return action_page(request, form, "Create synthetic catalog revision", "Save revision",
                       lambda data: create_catalog(request.user, data, data["key"], data["confirmed"]),
                       lambda record: redirect("med_catalog"))


@require_http_methods(["GET", "POST"])
@clinical_access
def catalog_activation(request, catalog_id, active):
    require_admin(request.user)
    revision = get_object_or_404(SyntheticMedicationCatalog, pk=catalog_id)
    form = CommandForm(request.POST if request.method == "POST" else None, initial={"version": revision.version})
    label = "Activate revision" if active else "Retire revision"
    return action_page(request, form, label, label,
                       lambda data: set_active(request.user, catalog_id, active, **data),
                       lambda record: redirect("med_catalog"), revision=revision)


@require_http_methods(["GET", "POST"])
@clinical_access
def compose(request, patient_id, encounter_id, order_id=None):
    encounter = get_object_or_404(encounters_for(request.user), pk=encounter_id, patient_id=patient_id)
    if not can_write(request.user, encounter.physician_id):
        raise PermissionDenied
    order = None
    if order_id:
        order = get_object_or_404(orders_for(request.user), public_id=order_id, encounter=encounter, author=request.user)
    if request.method == "GET" and (encounter.status != "in_progress" or (order and order.status != "draft")):
        raise PermissionDenied
    form = DraftForm(request.POST if request.method == "POST" else None, instance=order,
                     initial={"version": order.version if order else 0})
    def execute(data):
        return save_draft(request.user, encounter_id, patient_id, {**data, "catalog_id": data["catalog"].pk},
                          data["version"], data["key"], data["confirmed"], order_id)
    return action_page(request, form, "Edit medication draft" if order else "Create medication order", "Save draft",
                       execute, lambda record: redirect("med_detail", record.public_id),
                       patient=encounter.patient, encounter=encounter)


@require_safe
@clinical_access
def history(request, patient_id, encounter_id=None):
    patient = get_object_or_404(charts_for(request.user), pk=patient_id)
    orders = orders_for(request.user).filter(encounter__patient=patient)
    encounter = None
    if encounter_id is not None:
        encounter = get_object_or_404(encounters_for(request.user), pk=encounter_id, patient=patient)
        orders = orders.filter(encounter=encounter)
    return render(request, "medications/history.html", {
        "patient": patient, "encounter": encounter, "rows": Paginator(orders, 30).get_page(request.GET.get("page")),
    })


@require_safe
@clinical_access
def detail(request, order_id):
    order = get_object_or_404(orders_for(request.user), public_id=order_id)
    owns = can_write(request.user, order.author_id)
    open_encounter = order.encounter.status == "in_progress"
    return render(request, "medications/detail.html", {
        "order": order, "patient": order.encounter.patient, "encounter": order.encounter,
        "editable": owns and open_encounter and order.status == "draft",
        "cancellable": owns and (order.status == "signed" or (open_encounter and order.status == "draft")),
        "events": order.events.select_related("actor", "audit"),
    })


@require_http_methods(["GET", "POST"])
@clinical_access
def transition(request, order_id, action):
    order = get_object_or_404(orders_for(request.user), public_id=order_id)
    if not can_write(request.user, order.author_id):
        raise PermissionDenied
    if request.method == "GET":
        if action == "sign" and (order.status != "draft" or order.encounter.status != "in_progress"):
            raise PermissionDenied
        if action == "cancel" and order.status == "cancelled":
            raise PermissionDenied
    signing = action == "sign"
    initial = {"version": order.version}
    if signing:
        initial["token"] = review_token(request.user, order)
    form_class = SignForm if signing else ReasonForm
    form = form_class(request.POST if request.method == "POST" else None, initial=initial)
    return action_page(
        request, form, "Review and sign medication order" if signing else "Cancel medication order",
        "Sign synthetic order" if signing else "Confirm cancellation",
        lambda data: transition_order(request.user, order_id, action, **data),
        lambda record: redirect("med_detail", record.public_id),
        order=order, patient=order.encounter.patient, encounter=order.encounter,
        allergy_state=AllergyState.objects.filter(patient=order.encounter.patient).first() if signing else None,
        show_allergy_context=signing,
    )
