from django import forms
from django.utils import timezone

from careflow.clinical.models import Encounter
from careflow.scheduling.models import Appointment
from .models import RoomingAssessment, VitalObservation


class WorklistFilterForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    q = forms.CharField(label="Patient name or MRN", max_length=120, required=False)
    status = forms.ChoiceField(required=False, choices=[("", "All appointment statuses"), *Appointment.Status.choices])

    def clean_date(self):
        value = self.cleaned_data["date"]
        if not 1900 <= value.year <= 2100:
            raise forms.ValidationError("Use a date between 1900 and 2100.")
        return value


class NursingForm(forms.ModelForm):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    synthetic_confirmed = forms.BooleanField(label="I confirm this documentation contains synthetic information only.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["version"] = self.instance.version if self.instance.pk else 0
        self.fields["encounter"].queryset = Encounter.objects.filter(
            appointment_id=self.instance.appointment_id, patient_id=self.instance.patient_id)
        self.fields["encounter"].label_from_instance = lambda row: f"Encounter #{row.pk} · {row.get_status_display()}"
        self.fields["encounter"].help_text = "Optional; fixed after creation. Pre-encounter records stay linked to this appointment."
        if self.instance.pk:
            self.fields["encounter"].disabled = True
        else:
            self.initial["observed_at"] = timezone.localtime().replace(second=0, microsecond=0)
        self.fields["observed_at"].widget = forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"})
        self.fields["observed_at"].help_text = "Clinic-local time; ambiguous/nonexistent DST input is rejected."


class AssessmentForm(NursingForm):
    class Meta:
        model = RoomingAssessment
        fields = ["chief_complaint", "observed_at", "encounter", "pain_score", "observations", "ready_for_provider"]
        widgets = {"observations": forms.Textarea(attrs={"rows": 4})}


class VitalsForm(NursingForm):
    class Meta:
        model = VitalObservation
        fields = ["observed_at", "encounter", "source", "source_detail", "systolic", "diastolic",
                  "heart_rate", "respiratory_rate", "temperature", "temperature_unit", "oxygen_saturation",
                  "height", "height_unit", "weight", "weight_unit", "pain_score"]


FORMS = {"assessment": AssessmentForm, "vitals": VitalsForm}
