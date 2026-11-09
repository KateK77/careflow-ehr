from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from careflow.patients.models import AuditEvent
from careflow.scheduling.models import AppointmentEvent
from .access import (can_write, charts_for, clinical_access, clinical_appointments_for, encounters_for)
from .forms import NoteForm, SignForm, VersionForm
from .models import ClinicalEvent, Note
from .services import (ClinicalConflict, complete_encounter, save_note, sign_note, start_encounter)
from careflow.history.models import AllergyState, HistoryEvent, MedicalHistory, MedicationStatement, Problem


@require_safe
@clinical_access
def workspace(request):
    selected = timezone.localdate()
    error = ""
    if request.GET.get("date"):
        try:
            selected = date.fromisoformat(request.GET["date"])
            if not 1900 <= selected.year <= 2100:
                raise ValueError
        except ValueError:
            selected = timezone.localdate()
            error = "Enter a valid date between 1900 and 2100 (YYYY-MM-DD)."
    start = timezone.make_aware(datetime.combine(selected, time.min))
    end = timezone.make_aware(datetime.combine(selected + timedelta(days=1), time.min))
    appointments = clinical_appointments_for(request.user).filter(start_at__lt=end, end_at__gt=start)
    return render(request, "clinical/workspace.html", {
        "appointments": appointments, "selected": selected, "filter_error": error,
        "encounters": Paginator(encounters_for(request.user), 25).get_page(request.GET.get("page")),
    })


@require_safe
@clinical_access
def chart(request, patient_id):
    patient = get_object_or_404(charts_for(request.user), pk=patient_id)
    encounters = encounters_for(request.user).filter(patient=patient)
    appointments = clinical_appointments_for(request.user).filter(patient=patient)
    events = ClinicalEvent.objects.filter(encounter__in=encounters).select_related("audit__actor", "encounter")
    timeline = [{"at": e.audit.occurred_at, "label": e.audit.action,
                 "actor": e.audit.actor, "encounter": e.encounter} for e in events[:100]]
    appointment_events = AppointmentEvent.objects.filter(appointment__in=appointments).select_related("audit__actor", "appointment")
    for event in appointment_events[:100]:
        timeline.append({"at": event.audit.occurred_at, "label": event.audit.action,
                         "actor": event.audit.actor, "appointment": event.appointment})
    for appointment in appointments.order_by("-start_at")[:20]:
        timeline.append({"at": appointment.start_at, "label": "Appointment · " + appointment.get_status_display(),
                         "actor": appointment.physician, "appointment": appointment})
    timeline.sort(key=lambda item: item["at"], reverse=True)
    history_events = HistoryEvent.objects.filter(patient=patient).filter(
        Q(encounter__isnull=True) | Q(encounter__in=encounters)
    ).select_related("audit__actor")
    for event in history_events[:100]:
        if event.kind == "allergy_state":
            target = reverse("history_list", args=[patient.pk, "allergies"])
        elif event.encounter_id:
            target = reverse("diagnosis_detail", args=[patient.pk, event.encounter_id, event.record_id])
        else:
            target = reverse("history_detail", args=[patient.pk, event.kind, event.record_id])
        timeline.append({"at": event.audit.occurred_at, "label": event.audit.action,
                         "actor": event.audit.actor, "history_url": target})
    timeline.sort(key=lambda item: item["at"], reverse=True)
    AuditEvent.objects.create(actor=request.user, patient=patient, action="chart_view")
    return render(request, "clinical/chart.html", {
        "patient": patient, "encounters": encounters[:50], "appointments": appointments.order_by("-start_at")[:10],
        "notes": Note.objects.filter(encounter__in=encounters).select_related("encounter", "author").order_by("-created_at")[:50],
        "timeline": timeline[:100],
        "allergy_state": AllergyState.objects.filter(patient=patient).first(),
        "history_count": MedicalHistory.objects.filter(patient=patient).count(),
        "active_problems": Problem.objects.filter(patient=patient, status="active").count(),
        "active_medications": MedicationStatement.objects.filter(patient=patient, status="active").count(),
    })


def _encounter(request, patient_id, encounter_id):
    return get_object_or_404(encounters_for(request.user), pk=encounter_id, patient_id=patient_id)


@require_http_methods(["GET", "POST"])
@clinical_access
def encounter_start(request, appointment_id):
    appointment = get_object_or_404(clinical_appointments_for(request.user), pk=appointment_id)
    if not can_write(request.user, appointment.physician_id):
        raise PermissionDenied
    form = VersionForm(request.POST or None, initial={"version": appointment.version})
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                encounter = start_encounter(request.user, appointment.pk, form.cleaned_data["version"])
                messages.success(request, "Encounter started. Check-in provenance is unchanged.")
                return redirect("encounter_detail", encounter.patient_id, encounter.pk)
            except ValidationError as error:
                form.add_error(None, error)
                status = 409 if isinstance(error, ClinicalConflict) else 400
        else:
            status = 400
    return render(request, "clinical/start.html", {"appointment": appointment, "form": form}, status=status)


@require_safe
@clinical_access
def encounter_detail(request, patient_id, encounter_id):
    encounter = _encounter(request, patient_id, encounter_id)
    AuditEvent.objects.create(actor=request.user, patient=encounter.patient, action="encounter_view")
    return render(request, "clinical/encounter.html", {
        "patient": encounter.patient, "encounter": encounter,
        "note": Note.objects.filter(encounter=encounter).first(),
        "editable": can_write(request.user, encounter.physician_id) and encounter.status == "in_progress",
        "events": encounter.events.select_related("audit__actor"),
    })


@require_POST
@clinical_access
def encounter_complete(request, patient_id, encounter_id):
    encounter = _encounter(request, patient_id, encounter_id)
    if not can_write(request.user, encounter.physician_id):
        raise PermissionDenied
    form = VersionForm(request.POST)
    if form.is_valid():
        try:
            complete_encounter(request.user, encounter.pk, form.cleaned_data["version"])
            messages.success(request, "Encounter completed.")
            return redirect("encounter_detail", patient_id, encounter_id)
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, "clinical/action_error.html", {"patient": encounter.patient, "encounter": encounter, "form": form}, status=409)


@require_http_methods(["GET", "POST"])
@clinical_access
def note_edit(request, patient_id, encounter_id):
    encounter = _encounter(request, patient_id, encounter_id)
    if not can_write(request.user, encounter.physician_id):
        raise PermissionDenied
    note = Note.objects.filter(encounter=encounter).first()
    if encounter.status != "in_progress" or (note and note.signed_at):
        return render(request, "clinical/action_error.html", {"patient": encounter.patient, "encounter": encounter,
                      "error": "Signed notes and completed encounters cannot be edited."}, status=409)
    form = NoteForm(request.POST) if request.method == "POST" else NoteForm.for_note(note)
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                save_note(request.user, encounter.pk, form.cleaned_data, form.cleaned_data["version"])
                messages.success(request, "SOAP draft saved.")
                return redirect("encounter_detail", patient_id, encounter_id)
            except ValidationError as error:
                form.add_error(None, error)
                status = 409 if isinstance(error, ClinicalConflict) else 400
        else:
            status = 400
    return render(request, "clinical/note_form.html", {"patient": encounter.patient, "encounter": encounter, "form": form}, status=status)


@require_http_methods(["GET", "POST"])
@clinical_access
def note_sign(request, patient_id, encounter_id, note_id):
    encounter = _encounter(request, patient_id, encounter_id)
    note = get_object_or_404(Note, pk=note_id, encounter=encounter)
    if not can_write(request.user, encounter.physician_id) or note.author_id != request.user.pk:
        raise PermissionDenied
    if request.method == "GET" and (note.signed_at or encounter.status != "in_progress"):
        return redirect("encounter_detail", patient_id, encounter_id)
    form = SignForm(request.POST or None, initial={"version": note.version})
    status = 200
    if request.method == "POST":
        if form.is_valid():
            try:
                sign_note(request.user, note.pk, form.cleaned_data["version"], form.cleaned_data["confirmed"])
                messages.success(request, "SOAP note signed. Its content is now read-only.")
                return redirect("encounter_detail", patient_id, encounter_id)
            except ValidationError as error:
                form.add_error(None, error)
                status = 409 if isinstance(error, ClinicalConflict) else 400
        else:
            status = 400
    return render(request, "clinical/sign.html", {"patient": encounter.patient, "encounter": encounter, "note": note, "form": form}, status=status)
