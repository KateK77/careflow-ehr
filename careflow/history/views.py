from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from careflow.clinical.access import can_write, clinical_access, encounters_for
from careflow.patients.models import AuditEvent
from .access import can_maintain, patients_for
from .forms import AllergyStateForm, REGISTRY, ReviewForm
from .models import AllergyState, HistoryEvent
from .services import HistoryConflict, review_allergy_state, save_record


def _scope(request, patient_id, kind, encounter_id=None):
    if kind not in REGISTRY or (kind == "diagnoses") != bool(encounter_id):
        raise Http404
    patient = get_object_or_404(patients_for(request.user), pk=patient_id)
    model, form_class, title = REGISTRY[kind]
    records = model.objects.filter(patient=patient).select_related("author", "updated_by", "reviewed_by")
    encounter = None
    if encounter_id:
        encounter = get_object_or_404(encounters_for(request.user), pk=encounter_id, patient=patient)
        records = records.filter(encounter=encounter)
    writable = (can_write(request.user, encounter.physician_id) and encounter.status == "in_progress"
                if encounter else can_maintain(request.user, patient.pk))

    def url(action, record_id=None):
        args = [patient.pk, encounter.pk] if encounter else [patient.pk, kind]
        if record_id is not None:
            args.append(record_id)
        return reverse(("diagnosis_" if encounter else "history_") + action, args=args)

    return patient, records, encounter, writable, form_class, title, url


def _values(record, form_class):
    result = []
    for name in form_class._meta.fields:
        field = record._meta.get_field(name)
        value = getattr(record, name)
        if name == "problem" and value is not None:
            value = f"{value.label} ({value.get_status_display()})"
        if field.choices:
            value = getattr(record, "get_" + name + "_display")()
        result.append((field.verbose_name.capitalize(), value if value not in (None, "") else "Not recorded"))
    return result


def _errors(form, error):
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            for item in errors:
                form.add_error(field if field in form.fields else None, item)
    else:
        form.add_error(None, error)


@require_safe
@clinical_access
def record_list(request, patient_id, kind, encounter_id=None):
    patient, records, encounter, writable, form_class, title, url = _scope(request, patient_id, kind, encounter_id)
    page = Paginator(records, 20).get_page(request.GET.get("page"))
    rows = [{"record": item, "detail_url": url("detail", item.pk),
             "edit_url": url("edit", item.pk)} for item in page]
    state = AllergyState.objects.filter(patient=patient).first() if kind == "allergies" else None
    AuditEvent.objects.create(actor=request.user, patient=patient, action="history_view")
    return render(request, "history/list.html", {
        "patient": patient, "encounter": encounter, "kind": kind, "title": title,
        "writable": writable, "rows": rows, "page": page, "create_url": url("create"),
        "allergy_state": state, "state_form": AllergyStateForm(initial={
            "version": state.version if state else 0, "status": state.status if state else "not_reviewed"}),
    })


@require_safe
@clinical_access
def record_detail(request, patient_id, kind, record_id, encounter_id=None):
    patient, records, encounter, writable, form_class, title, url = _scope(request, patient_id, kind, encounter_id)
    record = get_object_or_404(records, pk=record_id)
    history = HistoryEvent.objects.filter(patient=patient, kind=kind, record_id=record.pk).select_related("audit__actor")
    events = []
    for event in history[:100]:
        changed = [(key, event.before.get(key, "Not recorded"), value)
                   for key, value in event.after.items() if event.before.get(key) != value]
        events.append({"event": event, "changed": changed})
    AuditEvent.objects.create(actor=request.user, patient=patient, action="history_detail_view")
    return render(request, "history/detail.html", {
        "patient": patient, "encounter": encounter, "record": record, "title": title,
        "values": _values(record, form_class), "events": events, "writable": writable,
        "edit_url": url("edit", record.pk), "review_url": url("review", record.pk), "list_url": url("list"),
    })


@require_http_methods(["GET", "POST"])
@clinical_access
def record_edit(request, patient_id, kind, record_id=None, encounter_id=None):
    patient, records, encounter, writable, form_class, title, url = _scope(request, patient_id, kind, encounter_id)
    if not writable:
        raise PermissionDenied
    model = REGISTRY[kind][0]
    record = get_object_or_404(records, pk=record_id) if record_id else model(patient=patient)
    if encounter:
        record.encounter = encounter
    form = form_class(request.POST if request.method == "POST" else None, instance=record)
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                saved = save_record(request.user, patient.pk, kind, form.cleaned_data,
                    form.cleaned_data["version"], record_id, encounter.pk if encounter else None)
                messages.success(request, title + " saved. Previous records and signed notes were preserved.")
                return redirect(url("detail", saved.pk))
            except ValidationError as error:
                _errors(form, error)
                status = 409 if isinstance(error, HistoryConflict) else 400
        else:
            status = 400
    return render(request, "history/form.html", {"patient": patient, "encounter": encounter,
                  "title": title, "form": form, "list_url": url("list")}, status=status)


@require_POST
@clinical_access
def record_review(request, patient_id, kind, record_id, encounter_id=None):
    patient, records, encounter, writable, form_class, title, url = _scope(request, patient_id, kind, encounter_id)
    if not writable:
        raise PermissionDenied
    get_object_or_404(records, pk=record_id)
    form = ReviewForm(request.POST)
    status = 400
    if form.is_valid():
        try:
            save_record(request.user, patient.pk, kind, form.cleaned_data, form.cleaned_data["version"],
                        record_id, encounter.pk if encounter else None, review=True)
            messages.success(request, "Review recorded with your identity and timestamp.")
            return redirect(url("detail", record_id))
        except ValidationError as error:
            _errors(form, error)
            status = 409 if isinstance(error, HistoryConflict) else 400
    return render(request, "history/error.html", {"patient": patient, "encounter": encounter,
                  "form": form, "retry_url": request.path, "return_url": url("detail", record_id)}, status=status)


@require_POST
@clinical_access
def allergy_state_review(request, patient_id):
    patient = get_object_or_404(patients_for(request.user), pk=patient_id)
    if not can_maintain(request.user, patient.pk):
        raise PermissionDenied
    form = AllergyStateForm(request.POST)
    status = 400
    if form.is_valid():
        try:
            review_allergy_state(request.user, patient.pk, form.cleaned_data["status"],
                                form.cleaned_data["version"], form.cleaned_data["synthetic_confirmed"])
            messages.success(request, "Allergy assessment recorded.")
            return redirect("history_list", patient.pk, "allergies")
        except ValidationError as error:
            _errors(form, error)
            status = 409 if isinstance(error, HistoryConflict) else 400
    return render(request, "history/error.html", {"patient": patient, "form": form,
                  "retry_url": request.path, "return_url": reverse("history_list", args=[patient.pk, "allergies"])}, status=status)
