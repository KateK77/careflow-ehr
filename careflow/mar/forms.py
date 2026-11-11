from django import forms

from careflow.medications.forms import CommandForm
from .models import MedicationAdministrationEvent


class FilterForm(forms.Form):
    patient = forms.IntegerField(required=False, min_value=1, label="Patient ID")
    encounter = forms.IntegerField(required=False, min_value=1, label="Encounter ID")
    medication = forms.CharField(required=False, max_length=100)
    status = forms.ChoiceField(required=False, choices=[
        ("", "All states"), ("pending", "Pending"), *MedicationAdministrationEvent._meta.get_field("status").choices,
    ])


class AdministrationForm(CommandForm):
    quantity = forms.IntegerField(min_value=1, label="Simulated quantity")
    occurred_at = forms.DateTimeField(
        label="Actual simulated event time",
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M:%S", attrs={"type": "datetime-local", "step": "1"}),
        help_text="Use clinic-local time. The event must fall between simulated dispensing and now.",
    )
    notes = forms.CharField(required=False, max_length=1000, label="Fictional notes",
                            widget=forms.Textarea(attrs={"rows": 3}))


class ExceptionForm(AdministrationForm):
    quantity = None
    status = forms.ChoiceField(label="Outcome", choices=MedicationAdministrationEvent.Status.choices[1:])
    reason = forms.CharField(max_length=1000, label="Fictional exception reason",
                             widget=forms.Textarea(attrs={"rows": 3}))


class CorrectionForm(AdministrationForm):
    status = forms.ChoiceField(label="Corrected outcome", choices=MedicationAdministrationEvent.Status.choices)
    quantity = forms.IntegerField(required=False, min_value=1, label="Simulated quantity",
                                  help_text="Use the full receipt quantity for Administered. Leave blank for exceptions.")
    reason = forms.CharField(required=False, max_length=1000, label="Fictional exception reason",
                             help_text="Required for held, refused or omitted outcomes.")
    correction_reason = forms.CharField(max_length=1000, label="Reason for correction",
                                        widget=forms.Textarea(attrs={"rows": 3}))
