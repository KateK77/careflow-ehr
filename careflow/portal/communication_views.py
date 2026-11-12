import uuid

from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from careflow.medications.services import MedicationConflict
from careflow.scheduling.models import Appointment
from careflow.scheduling.services import AppointmentConflict

from .access import patient_only
from .communication import (
    care_team, changeable_appointments, conversations, mark_read, physicians, reply, review_request,
    scheduling_writer, start_thread, submit_request, with_unread,
)
from .models import PatientAppointmentRequest


class CommandForm(forms.Form):
    key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)


class ReplyForm(CommandForm):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    body = forms.CharField(label="Message", max_length=2000, widget=forms.Textarea(attrs={"rows": 5}))


class NewMessageForm(CommandForm):
    clinician = forms.ModelChoiceField(queryset=None)
    subject = forms.CharField(max_length=120)
    body = forms.CharField(label="Message", max_length=2000, widget=forms.Textarea(attrs={"rows": 5}))

    def __init__(self, *args, patient, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["clinician"].queryset = care_team(patient)


class ReadForm(CommandForm):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class RequestForm(CommandForm):
    clinician = forms.ModelChoiceField(queryset=None)
    appointment = forms.ModelChoiceField(queryset=None)
    start = forms.DateTimeField(label="Proposed clinic-local start",
                                widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    duration = forms.IntegerField(label="Duration in minutes", min_value=5, max_value=240,
                                  widget=forms.NumberInput(attrs={"step": 5}))
    explanation = forms.CharField(label="Synthetic reason", max_length=240, widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, patient, kind, **kwargs):
        super().__init__(*args, **kwargs)
        if kind == "new":
            self.fields["clinician"].queryset = physicians()
            del self.fields["appointment"]
        else:
            del self.fields["clinician"]
            self.fields["appointment"].queryset = (
                Appointment.objects.filter(patient=patient) if self.is_bound else changeable_appointments(patient)
            ).select_related("physician")
            self.fields["appointment"].label_from_instance = (
                lambda item: f"{timezone.localtime(item.start_at).strftime('%Y-%m-%d %H:%M %Z')} · {item.physician} · {item.appointment_type}"
            )
        if kind == "cancel":
            del self.fields["start"]
            del self.fields["duration"]


class ReviewForm(CommandForm):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    decision = forms.ChoiceField(choices=[("approved", "Approve"), ("rejected", "Reject")])
    response = forms.CharField(label="Response to patient", max_length=240, widget=forms.Textarea(attrs={"rows": 4}))
    confirmed = forms.BooleanField(label="Confirm this decision")


def _execute(form, callback):
    if form.is_valid():
        try:
            return callback(form.cleaned_data), 200
        except (AppointmentConflict, MedicationConflict) as exc:
            form.add_error(None, exc)
            return None, 409
        except ValidationError as exc:
            form.add_error(None, exc)
    return None, 400


def _render(request, page, patient, context, status=200):
    base = "portal/base.html" if patient is not None else "core/base.html"
    return render(request, f"portal/{page}.html", {**context, "patient": patient, "layout": base}, status=status)


def _messages(request, patient=None):
    threads = with_unread(conversations(request.user, patient), from_patient=patient is None)
    return _render(request, "messages", patient, {"threads": threads})


@require_safe
@patient_only
def messages(request, patient):
    return _messages(request, patient)


@require_safe
def staff_messages(request):
    return _messages(request)


@require_http_methods(["GET", "POST"])
@patient_only
def new_message(request, patient):
    form = NewMessageForm(request.POST if request.method == "POST" else None, patient=patient)
    status = 200
    if request.method == "POST":
        thread, status = _execute(form, lambda data: start_thread(
            request.user, data["clinician"].pk, data["subject"], data["body"], data["key"],
        ))
        if thread:
            return redirect("portal_thread", thread.pk)
    return _render(request, "message_new", patient, {"form": form}, status)


def _thread(request, thread_id, patient=None):
    as_patient = patient is not None
    query = with_unread(conversations(request.user, patient), from_patient=not as_patient)
    thread = get_object_or_404(query, pk=thread_id)
    initial = {"version": thread.version}
    form = ReplyForm(initial=initial)
    read_form = ReadForm(initial=initial)
    status = 200
    if request.method == "POST":
        data = request.POST
        if data.get("action") == "read":
            read_form = ReadForm(data)
            saved, status = _execute(read_form, lambda values: mark_read(
                request.user, thread.pk, thread.physician_id, as_patient, values["version"], values["key"],
            ))
        else:
            form = ReplyForm(data)
            saved, status = _execute(form, lambda values: reply(
                request.user, thread.pk, thread.physician_id, as_patient,
                values["body"], values["version"], values["key"],
            ))
        if saved:
            return redirect("portal_thread" if as_patient else "staff_portal_thread", thread.pk)
    return _render(request, "thread", patient, {
        "thread": thread, "items": thread.messages.select_related("sender"), "form": form, "read_form": read_form,
    }, status)


@require_http_methods(["GET", "POST"])
@patient_only
def thread(request, patient, thread_id):
    return _thread(request, thread_id, patient)


@require_http_methods(["GET", "POST"])
def staff_thread(request, thread_id):
    return _thread(request, thread_id)


def _request_query():
    return PatientAppointmentRequest.objects.select_related("patient", "physician", "target", "resulting_appointment")


@require_safe
@patient_only
def requests(request, patient):
    return _render(request, "requests", patient, {"items": _request_query().filter(patient=patient)})


@require_safe
def staff_requests(request):
    if not scheduling_writer(request.user):
        raise PermissionDenied
    return _render(request, "requests", None, {"items": _request_query()})


@require_http_methods(["GET", "POST"])
@patient_only
def new_request(request, patient, kind):
    if kind not in PatientAppointmentRequest.Kind.values:
        raise Http404
    form = RequestForm(request.POST if request.method == "POST" else None, patient=patient, kind=kind)
    status = 200
    if request.method == "POST":
        def submit(data):
            target = data.get("appointment")
            physician_id = target.physician_id if target else data["clinician"].pk
            return submit_request(request.user, kind, physician_id, target.pk if target else None,
                                  data.get("start"), data.get("duration"), data["explanation"], data["key"])

        item, status = _execute(form, submit)
        if item:
            return redirect("portal_request", item.pk)
    return _render(request, "request_new", patient, {
        "form": form, "kind": PatientAppointmentRequest.Kind(kind).label,
    }, status)


def _request_detail(request, request_id, patient=None):
    query = _request_query()
    if patient is not None:
        query = query.filter(patient=patient)
    elif not scheduling_writer(request.user):
        raise PermissionDenied
    item = get_object_or_404(query, pk=request_id)
    form = ReviewForm(initial={"version": item.version})
    status = 200
    if request.method == "POST":
        form = ReviewForm(request.POST)
        saved, status = _execute(form, lambda data: review_request(
            request.user, item.pk, item.physician_id, data["decision"], data["version"],
            data["response"], data["key"], data["confirmed"],
        ))
        if saved:
            return redirect("staff_portal_request", item.pk)
    return _render(request, "request_detail", patient, {
        "item": item, "form": form, "events": item.events.select_related("audit__actor").order_by("audit__occurred_at"),
    }, status)


@require_safe
@patient_only
def request_detail(request, patient, request_id):
    return _request_detail(request, request_id, patient)


@require_http_methods(["GET", "POST"])
def staff_request_detail(request, request_id):
    return _request_detail(request, request_id)
