import uuid

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from careflow.clinical.access import can_write, charts_for, clinical_access, encounters_for
from careflow.patients.access import roles_for
from careflow.patients.models import AuditEvent
from .access import may_write, orders_for
from .forms import CancelForm, CatalogForm, CommandForm, DraftForm, SubmitForm
from .models import LabTestCatalog
from .services import (LabConflict, cancel_order, create_catalog, duplicate_orders, review_token,
                       save_draft, set_catalog_active, submit_order)


def errors(form, error):
    if hasattr(error, "error_dict"):
        for name, items in error.error_dict.items():
            for item in items:
                form.add_error(name if name in form.fields else None, item)
    else:
        form.add_error(None, error)


def saved(request, outcome, label):
    messages.success(request, "Command already processed; showing the current record." if outcome.replayed else label)


@require_safe
@clinical_access
def catalog_list(request):
    admin = "Administrator" in roles_for(request.user)
    panels = LabTestCatalog.objects.all() if admin else LabTestCatalog.objects.filter(is_active=True)
    page = Paginator(panels, 25).get_page(request.GET.get("page"))
    AuditEvent.objects.create(actor=request.user, action="lab_catalog_view")
    return render(request, "labs/catalog.html", {"page": page, "admin": admin,
                  "rows": [{"panel": p, "command_key": str(uuid.uuid4())} for p in page]})


@require_http_methods(["GET", "POST"])
@clinical_access
def catalog_create(request):
    if "Administrator" not in roles_for(request.user):
        raise PermissionDenied
    form = CatalogForm(request.POST if request.method == "POST" else None, initial={"version": 0})
    status = 200
    if request.method == "POST":
        status = 400
        if form.is_valid():
            try:
                result = create_catalog(request.user, form.cleaned_data, form.cleaned_data["command_key"], form.cleaned_data["synthetic_confirmed"])
                saved(request, result, "Synthetic catalog revision created inactive. Activate it explicitly when ready.")
                return redirect("lab_catalog")
            except ValidationError as error:
                errors(form, error)
                status = 409 if isinstance(error, LabConflict) else 400
    return render(request, "labs/form.html", {"title": "Create immutable catalog revision", "form": form, "submit_label": "Create catalog revision"}, status=status)


@require_POST
@clinical_access
def catalog_toggle(request, catalog_id, active):
    if "Administrator" not in roles_for(request.user):
        raise PermissionDenied
    get_object_or_404(LabTestCatalog, pk=catalog_id)
    form = CommandForm(request.POST)
    status = 400
    if form.is_valid():
        try:
            result = set_catalog_active(request.user, catalog_id, form.cleaned_data["version"], bool(active), form.cleaned_data["command_key"], form.cleaned_data["synthetic_confirmed"])
            saved(request, result, "Catalog activation updated. Historical definitions were preserved.")
            return redirect("lab_catalog")
        except ValidationError as error:
            errors(form, error)
            status = 409 if isinstance(error, LabConflict) else 400
    return render(request, "labs/form.html", {"title": "Catalog action not completed", "form": form, "submit_label": "Retry catalog action"}, status=status)


@require_http_methods(["GET", "POST"])
@clinical_access
def draft_edit(request, patient_id=None, encounter_id=None, order_id=None):
    order = get_object_or_404(orders_for(request.user), public_id=order_id) if order_id else None
    encounter = (order.encounter if order else get_object_or_404(encounters_for(request.user), pk=encounter_id, patient_id=patient_id))
    if not can_write(request.user, encounter.physician_id):
        raise PermissionDenied
    # Reject writes through services too; replay of an earlier successful command is still allowed.
    writable = encounter.status == "in_progress" and (not order or order.status == "draft")
    if request.method == "GET" and not writable:
        raise PermissionDenied
    initial = {"version": order.version if order else 0, "catalog": order.catalog_id if order else None, "reason": order.reason if order else ""}
    form = DraftForm(request.POST if request.method == "POST" else None, initial=initial)
    status = 200
    if request.method == "POST":
        status = 400
        if form.is_valid():
            d = form.cleaned_data
            try:
                result = save_draft(request.user, encounter.pk, d["catalog"].pk, d["reason"], d["version"], d["command_key"], d["synthetic_confirmed"], order.public_id if order else None)
                saved(request, result, "Laboratory draft saved.")
                return redirect("lab_order_detail", order_id=result.record.public_id)
            except ValidationError as error:
                errors(form, error)
                status = 409 if isinstance(error, LabConflict) else 400
    return render(request, "labs/form.html", {"title": "Edit laboratory draft" if order else "Create laboratory order", "form": form,
                  "patient": encounter.patient, "encounter": encounter, "submit_label": "Save draft"}, status=status)


@require_safe
@clinical_access
def order_detail(request, order_id):
    order = get_object_or_404(orders_for(request.user), public_id=order_id)
    AuditEvent.objects.create(actor=request.user, patient=order.patient, action="lab_order_view")
    return render(request, "labs/detail.html", {"order": order, "patient": order.patient, "encounter": order.encounter,
        "editable": may_write(request.user, order) and order.status == "draft" and order.encounter.status == "in_progress",
        "cancellable": may_write(request.user, order) and order.status in {"draft", "submitted"} and not order.specimens.filter(received_at__isnull=False).exists(),
        "events": order.events.select_related("audit__actor")[:100], "specimens": order.specimens.select_related("created_by")})


@require_http_methods(["GET", "POST"])
@clinical_access
def order_submit(request, order_id):
    order = get_object_or_404(orders_for(request.user), public_id=order_id)
    if not may_write(request.user, order):
        raise PermissionDenied
    if request.method == "GET" and (order.status != "draft" or order.encounter.status != "in_progress"):
        raise PermissionDenied
    form = SubmitForm(request.POST if request.method == "POST" else None, initial={"version": order.version})
    preview, status = False, 200
    if request.method == "POST":
        status = 400
        if form.is_valid():
            d = form.cleaned_data
            if request.POST.get("action") == "review":
                if order.version != d["version"] or order.status != "draft" or order.encounter.status != "in_progress":
                    form.add_error(None, "The draft changed or its encounter is completed. Reload before review.")
                    status = 409
                elif duplicate_orders(order).exists() and (not d["repeat_confirmed"] or not d["repeat_reason"].strip()):
                    form.add_error(None, "Confirm intentional repeat testing and enter a reason for this existing panel order.")
                else:
                    form.cleaned_data["review_token"] = review_token(request.user, order, d["version"], d["repeat_confirmed"], d["repeat_reason"])
                    preview, status = True, 200
            elif request.POST.get("action") == "confirm":
                try:
                    result = submit_order(request.user, order.public_id, d["version"], d["command_key"], d["synthetic_confirmed"], d["repeat_confirmed"], d["repeat_reason"], d["review_token"])
                    saved(request, result, "Order submitted with one pending specimen. Collection and results are not available in this increment.")
                    return redirect("lab_order_detail", order_id=order.public_id)
                except ValidationError as error:
                    errors(form, error)
                    status = 409 if isinstance(error, LabConflict) else 400
            else:
                form.add_error(None, "Choose Review order before confirming submission.")
    return render(request, "labs/submit.html", {"order": order, "patient": order.patient, "encounter": order.encounter,
        "form": form, "preview": preview, "token": form.cleaned_data.get("review_token", "") if preview else "", "duplicate": duplicate_orders(order).exists()}, status=status)


@require_http_methods(["GET", "POST"])
@clinical_access
def order_cancel(request, order_id):
    order = get_object_or_404(orders_for(request.user), public_id=order_id)
    if not may_write(request.user, order):
        raise PermissionDenied
    form = CancelForm(request.POST if request.method == "POST" else None, initial={"version": order.version})
    status = 200
    if request.method == "POST":
        status = 400
        if form.is_valid():
            d = form.cleaned_data
            try:
                result = cancel_order(request.user, order.public_id, d["version"], d["reason"], d["command_key"], d["synthetic_confirmed"])
                saved(request, result, "Order cancelled. Draft/submission and specimen history were retained.")
                return redirect("lab_order_detail", order_id=order.public_id)
            except ValidationError as error:
                errors(form, error)
                status = 409 if isinstance(error, LabConflict) else 400
    return render(request, "labs/form.html", {"title": "Cancel laboratory order", "form": form, "patient": order.patient,
                  "encounter": order.encounter, "submit_label": "Confirm cancellation"}, status=status)


@require_safe
@clinical_access
def order_history(request, patient_id, encounter_id=None):
    patient = get_object_or_404(charts_for(request.user), pk=patient_id)
    encounter = get_object_or_404(encounters_for(request.user), pk=encounter_id, patient=patient) if encounter_id else None
    orders = orders_for(request.user).filter(patient=patient)
    if encounter:
        orders = orders.filter(encounter=encounter)
    page = Paginator(orders, 25).get_page(request.GET.get("page"))
    AuditEvent.objects.create(actor=request.user, patient=patient, action="lab_history_view")
    return render(request, "labs/history.html", {"patient": patient, "encounter": encounter, "page": page,
        "can_create": bool(encounter and can_write(request.user, encounter.physician_id) and encounter.status == "in_progress")})
