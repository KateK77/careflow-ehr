from django import forms
from django.core import signing
from django.db.models import Q
from django.utils import timezone

from careflow.patients.models import Patient
from .access import physicians_for


class PatientChoice(forms.ModelChoiceField):
    def label_from_instance(self, patient):
        return f"{patient.mrn} · {patient}"


class PhysicianChoice(forms.ModelChoiceField):
    def label_from_instance(self, user):
        return f"{user.get_full_name() or user.username} ({user.username})"


class AppointmentForm(forms.Form):
    patient = PatientChoice(queryset=Patient.objects.all())
    physician = PhysicianChoice(queryset=None)
    start_at = forms.DateTimeField(
        label="Appointment start (clinic local time)",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )
    duration = forms.IntegerField(min_value=5, max_value=240, initial=30, widget=forms.NumberInput(attrs={"step": 5}))
    appointment_type = forms.CharField(max_length=80, initial="Outpatient visit")
    reason = forms.CharField(
        label="Synthetic visit reason (optional)", max_length=240, required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    version = forms.IntegerField(min_value=1, initial=1, widget=forms.HiddenInput)

    def __init__(self, user, *args, appointment=None, patient_query="", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["physician"].queryset = physicians_for(user)
        if appointment:
            self.fields["patient"].disabled = True
        elif patient_query and not self.is_bound:
            match = Q(mrn__icontains=patient_query) | Q(first_name__icontains=patient_query) | Q(last_name__icontains=patient_query)
            parts = patient_query.split()
            if len(parts) == 2:
                match |= Q(first_name__icontains=parts[0], last_name__icontains=parts[1])
            self.fields["patient"].queryset = Patient.objects.filter(match)

    def clean_duration(self):
        minutes = self.cleaned_data["duration"]
        if minutes % 5:
            raise forms.ValidationError("Use five-minute increments.")
        return minutes

    def clean_start_at(self):
        value = self.cleaned_data["start_at"]
        if value <= timezone.now():
            raise forms.ValidationError("Choose a future appointment start.")
        return value

    def confirmation_payload(self, user, appointment_id):
        data = self.cleaned_data
        return {
            "actor": user.pk, "appointment": appointment_id,
            "patient": data["patient"].pk, "physician": data["physician"].pk,
            "start": data["start_at"].isoformat(), "duration": data["duration"],
            "type": data["appointment_type"], "reason": data["reason"], "version": data["version"],
        }

    def review_token(self, user, appointment_id):
        return signing.dumps(self.confirmation_payload(user, appointment_id), salt="appointment-review")

    def reviewed(self, token, user, appointment_id):
        try:
            payload = signing.loads(token, salt="appointment-review", max_age=600)
        except signing.BadSignature:
            return False
        return payload == self.confirmation_payload(user, appointment_id)


class ScheduleFilterForm(forms.Form):
    date = forms.DateField(
        required=True, initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}),
    )
    physician = PhysicianChoice(queryset=None, required=False, empty_label="All permitted physicians")
    view = forms.ChoiceField(choices=[("day", "Day"), ("week", "Week")], initial="day")
    q = forms.CharField(label="Patient name or MRN", required=False, max_length=120)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["physician"].queryset = physicians_for(user)

    def clean_date(self):
        value = self.cleaned_data["date"]
        if not 1900 <= value.year <= 2100:
            raise forms.ValidationError("Choose a date between 1900 and 2100.")
        return value


class TransitionForm(forms.Form):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    action = forms.ChoiceField(choices=[("arrive", "Check in"), ("cancel", "Cancel"), ("no_show", "No show")])
    reason = forms.CharField(max_length=240, required=False)
