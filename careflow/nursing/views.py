from datetime import datetime, time, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import charts_for, clinical_access
from careflow.patients.models import AuditEvent
from careflow.mar.access import receipts_for as mar_receipts_for
from .access import appointments_for, can_document
from .forms import FORMS, WorklistFilterForm
from .models import NursingEvent, RoomingAssessment, VitalObservation
from .presentation import LABELS, value_with_unit, values
from .services import NursingConflict, save_documentation


@require_safe
@clinical_access
def workspace(request):
    data = {"date": timezone.localdate().isoformat(), **request.GET.dict()}
    form = WorklistFilterForm(data)
    valid = form.is_valid()
    selected = form.cleaned_data.get("date", timezone.localdate())
    start = timezone.make_aware(datetime.combine(selected, time.min))
    end = timezone.make_aware(datetime.combine(selected + timedelta(days=1), time.min))
    records = appointments_for(request.user).filter(start_at__lt=end, end_at__gt=start)
    if not valid:
        records = records.none()
    else:
        query = form.cleaned_data.get("q", "")
        if query:
            match = Q(patient__mrn__icontains=query) | Q(patient__first_name__icontains=query) | Q(patient__last_name__icontains=query)
            parts = query.split()
            if len(parts) == 2:
                match |= Q(patient__first_name__icontains=parts[0], patient__last_name__icontains=parts[1])
            records = records.filter(match)
        if form.cleaned_data.get("status"):
            records = records.filter(status=form.cleaned_data["status"])
    records = records.select_related("rooming").annotate(vital_count=Count("vitals")).order_by("start_at", "pk")
    page = Paginator(records, 25).get_page(request.GET.get("page"))
    rows = [{"appointment": item, "writable": can_document(request.user, item)} for item in page]
    query_data = request.GET.copy()
    query_data.pop("page", None)
    return render(request, "nursing/workspace.html", {"form": form, "rows": rows, "page": page,
                  "filter_query": query_data.urlencode(),
                  "mar_summary": mar_receipts_for(request.user).filter(effective_status__isnull=False).order_by("-effective_time", "-pk")[:5]})


def _appointment(request, patient_id, appointment_id):
    return get_object_or_404(appointments_for(request.user), pk=appointment_id, patient_id=patient_id)


@require_safe
@clinical_access
def appointment_documentation(request, patient_id, appointment_id):
    appointment = _appointment(request, patient_id, appointment_id)
    assessment = RoomingAssessment.objects.filter(appointment=appointment).select_related("recorded_by", "updated_by").first()
    vitals = VitalObservation.objects.filter(appointment=appointment).select_related("recorded_by")[:20]
    AuditEvent.objects.create(actor=request.user, patient_id=patient_id, action="nursing_view")
    return render(request, "nursing/appointment.html", {"patient": appointment.patient, "appointment": appointment,
                  "assessment": assessment, "observations": vitals, "writable": can_document(request.user, appointment)})


@require_http_methods(["GET", "POST"])
@clinical_access
def record_edit(request, patient_id, appointment_id, kind, record_id=None):
    if kind not in FORMS:
        raise Http404
    appointment = _appointment(request, patient_id, appointment_id)
    if not can_document(request.user, appointment):
        raise PermissionDenied
    form_class = FORMS[kind]
    model = form_class._meta.model
    record = get_object_or_404(model, pk=record_id, patient_id=patient_id, appointment=appointment) if record_id else model(patient=appointment.patient, appointment=appointment)
    form = form_class(request.POST if request.method == "POST" else None, instance=record)
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                saved = save_documentation(request.user, patient_id, appointment_id, kind, form.cleaned_data,
                                           form.cleaned_data["version"], record_id)
                messages.success(request, "Nursing documentation saved with versioned audit history.")
                return redirect("nursing_record", patient_id, appointment_id, kind, saved.pk)
            except ValidationError as error:
                if hasattr(error, "error_dict"):
                    for name, errors in error.error_dict.items():
                        for item in errors:
                            form.add_error(name if name in form.fields else None, item)
                else:
                    form.add_error(None, error)
                status = 409 if isinstance(error, NursingConflict) else 400
        else:
            status = 400
    return render(request, "nursing/form.html", {"patient": appointment.patient, "appointment": appointment,
                  "encounter": record.encounter, "form": form, "kind": kind, "record": record}, status=status)


@require_safe
@clinical_access
def record_detail(request, patient_id, appointment_id, kind, record_id):
    if kind not in FORMS:
        raise Http404
    appointment = _appointment(request, patient_id, appointment_id)
    model = FORMS[kind]._meta.model
    record = get_object_or_404(model.objects.select_related("recorded_by", "updated_by", "encounter"),
                             pk=record_id, patient_id=patient_id, appointment=appointment)
    events = NursingEvent.objects.filter(appointment=appointment, **{
        "assessment_id" if kind == "assessment" else "observation_id": record.pk,
    }).select_related("audit__actor")[:100]
    history = [{"event": event, "changes": [(key, event.before.get(key, "Not recorded"), value)
               for key, value in event.after.items() if event.before.get(key) != value]} for event in events]
    AuditEvent.objects.create(actor=request.user, patient_id=patient_id, action="nursing_record_view")
    return render(request, "nursing/detail.html", {"patient": appointment.patient, "appointment": appointment,
                  "encounter": record.encounter,
                  "record": record, "kind": kind, "measurements": values(record) if kind == "vitals" else [],
                  "events": history, "writable": can_document(request.user, appointment)})


@require_safe
@clinical_access
def flowsheet(request, patient_id):
    patient = get_object_or_404(charts_for(request.user), pk=patient_id)
    appointments = appointments_for(request.user).filter(patient=patient)
    selected_id = request.GET.get("appointment")
    selected = None
    if selected_id:
        if len(selected_id) > 19 or not selected_id.isascii() or not selected_id.isdecimal() or not 1 <= int(selected_id) <= 2**63 - 1:
            raise Http404
        selected = get_object_or_404(appointments, pk=selected_id)
        appointments = appointments.filter(pk=selected.pk)
    records = VitalObservation.objects.filter(appointment__in=appointments).select_related("recorded_by", "updated_by", "appointment")
    page = Paginator(records, 12).get_page(request.GET.get("page"))
    columns = sorted(page.object_list, key=lambda item: (item.observed_at, item.pk))
    rows = [{"label": label, "cells": [value_with_unit(item, name) for item in columns]} for name, label in LABELS.items()]
    AuditEvent.objects.create(actor=request.user, patient=patient, action="nursing_flowsheet_view")
    return render(request, "nursing/flowsheet.html", {"patient": patient, "columns": columns, "rows": rows,
                  "page": page, "selected_appointment": selected, "filter_query": f"appointment={selected.pk}&" if selected else ""})
