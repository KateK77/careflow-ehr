from datetime import UTC, datetime, time, timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from careflow.patients.access import patient_access
from careflow.patients.models import AuditEvent
from .access import appointments_for, physicians_for
from .forms import AppointmentForm, ScheduleFilterForm, TransitionForm
from .models import Appointment
from .services import AppointmentConflict, save_appointment, transition_appointment


def _calendar(records, days, physicians, mode):
    columns = [{"key": day, "label": day.strftime("%a %d %b")} for day in days]
    if mode == "day":
        providers = {user.pk: user for user in physicians}
        providers.update({item.physician_id: item.physician for item in records})
        columns = [{"key": user.pk, "label": user.get_full_name() or user.username} for user in providers.values()]
    entries = {}
    hours = [8, 18]
    for item in records:
        for day in days:
            start = max(item.start_at, timezone.make_aware(datetime.combine(day, time.min)).astimezone(UTC))
            end = min(item.end_at, timezone.make_aware(datetime.combine(day + timedelta(days=1), time.min)).astimezone(UTC))
            if start >= end:
                continue
            key = day if mode == "week" else item.physician_id
            entries.setdefault((timezone.localtime(start).hour, key), []).append(item)
            hours.extend([timezone.localtime(start).hour, timezone.localtime(end - timedelta(microseconds=1)).hour])
    rows = [
        {"label": f"{hour:02d}:00", "cells": [
            {"appointments": entries.get((hour, column["key"]), [])} for column in columns
        ]}
        for hour in range(min(hours), max(hours) + 1)
    ]
    return columns, rows


@require_safe
@patient_access()
def schedule(request, checkin=False):
    data = {"date": timezone.localdate().isoformat(), "view": "day", **request.GET.dict()}
    form = ScheduleFilterForm(request.user, data)
    valid = form.is_valid()
    selected = form.cleaned_data.get("date", timezone.localdate())
    mode = "day" if checkin else form.cleaned_data.get("view", "day")
    first = selected - timedelta(days=selected.weekday()) if mode == "week" else selected
    days = [first + timedelta(days=index) for index in range(7 if mode == "week" else 1)]
    start = timezone.make_aware(datetime.combine(first, time.min))
    end = timezone.make_aware(datetime.combine(days[-1] + timedelta(days=1), time.min))
    records = appointments_for(request.user).filter(start_at__lt=end, end_at__gt=start)
    physician = form.cleaned_data.get("physician")
    if physician:
        records = records.filter(physician=physician)
    query = form.cleaned_data.get("q", "")
    if query:
        match = Q(patient__mrn__icontains=query) | Q(patient__first_name__icontains=query) | Q(patient__last_name__icontains=query)
        parts = query.split()
        if len(parts) == 2:
            match |= Q(patient__first_name__icontains=parts[0], patient__last_name__icontains=parts[1])
        records = records.filter(match)
    if not valid:
        records = records.none()
    records = list(records)
    physicians = physicians_for(request.user)
    if physician:
        physicians = physicians.filter(pk=physician.pk)
    columns, rows = _calendar(records, days, physicians, mode)
    return render(request, "scheduling/schedule.html", {
        "filter_form": form, "appointments": records, "columns": columns, "rows": rows,
        "selected_date": selected, "mode": mode, "checkin": checkin,
        "previous_date": first - timedelta(days=len(days)),
        "next_date": first + timedelta(days=len(days)), "physician_filter": physician,
        "query": query, "clinic_zone": timezone.get_current_timezone_name(),
    }, status=200 if valid else 400)


@require_safe
@patient_access()
def checkin_worklist(request):
    return schedule(request, checkin=True)


def _visible_appointment(request, pk):
    appointment = appointments_for(request.user).filter(pk=pk).first()
    if appointment is None:
        AuditEvent.objects.create(actor=request.user, action="appointment_denied", outcome="denied")
        raise Http404
    return appointment


def _detail_context(appointment, transition_form=None):
    return {
        "appointment": appointment,
        "events": appointment.events.select_related("audit__actor"),
        "transition_form": transition_form,
        "can_checkin_today": timezone.localdate(appointment.start_at) == timezone.localdate(),
        "has_started": appointment.start_at <= timezone.now(),
        "clinic_zone": timezone.get_current_timezone_name(),
    }


@require_safe
@patient_access()
def appointment_detail(request, pk):
    appointment = _visible_appointment(request, pk)
    return render(request, "scheduling/detail.html", _detail_context(appointment))


@require_http_methods(["GET", "POST"])
@patient_access(write=True)
def appointment_edit(request, pk=None):
    appointment = get_object_or_404(Appointment, pk=pk) if pk else None
    initial = {
        "patient": request.GET.get("patient"), "physician": request.GET.get("physician"),
    }
    if appointment:
        initial = {
            "patient": appointment.patient_id, "physician": appointment.physician_id,
            "start_at": timezone.localtime(appointment.start_at), "duration": appointment.duration,
            "appointment_type": appointment.appointment_type, "reason": appointment.reason,
            "version": appointment.version,
        }
    query = request.GET.get("q", "").strip()[:120]
    form = AppointmentForm(
        request.user, request.POST if request.method == "POST" else None,
        appointment=appointment, initial=initial, patient_query=query,
    )
    status = 200
    if request.method == "POST":
        status = 400
        if form.is_valid():
            action = request.POST.get("action")
            if action == "review":
                return render(request, "scheduling/review.html", {
                    "form": form, "appointment": appointment, "data": form.cleaned_data,
                    "review_token": form.review_token(request.user, pk),
                    "clinic_zone": timezone.get_current_timezone_name(),
                })
            if action == "edit":
                return render(request, "scheduling/form.html", {
                    "form": form, "appointment": appointment, "patient_query": query,
                    "clinic_zone": timezone.get_current_timezone_name(),
                })
            if action != "confirm" or not form.reviewed(request.POST.get("review_token", ""), request.user, pk):
                form.add_error(None, "Review this appointment again before confirming. The review may have expired.")
            else:
                try:
                    saved = save_appointment(request.user, form.cleaned_data, pk)
                except AppointmentConflict as error:
                    form.add_error(None, error)
                    status = 409
                except ValidationError as error:
                    form.add_error(None, error)
                else:
                    messages.success(request, "Appointment saved.")
                    return redirect("appointment_detail", pk=saved.pk)
    return render(request, "scheduling/form.html", {
        "form": form, "appointment": appointment, "patient_query": query,
        "clinic_zone": timezone.get_current_timezone_name(),
    }, status=status)


@require_POST
@patient_access(write=True)
def appointment_transition(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    form = TransitionForm(request.POST)
    status = 400
    if form.is_valid():
        try:
            saved = transition_appointment(request.user, pk, **form.cleaned_data)
        except AppointmentConflict as error:
            form.add_error(None, error)
            status = 409
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, f"Appointment marked {saved.get_status_display()}.")
            return redirect("appointment_detail", pk=pk)
    appointment.refresh_from_db()
    return render(request, "scheduling/detail.html", _detail_context(appointment, form), status=status)
