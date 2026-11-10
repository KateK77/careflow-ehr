from django import forms
from django.utils import timezone
from careflow.core.forms import configure_date_field

from .models import Allergy, AllergyState, EncounterDiagnosis, MedicalHistory, MedicationStatement, Problem

COMMON_FIELDS = ["label", "comments", "source", "source_detail"]


class RecordForm(forms.ModelForm):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    synthetic_confirmed = forms.BooleanField(label="I confirm this record contains synthetic information only.")

    class Meta:
        fields = COMMON_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["version"] = self.instance.version if self.instance.pk else 0
        for name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                configure_date_field(field, maximum=timezone.localdate().isoformat())
        self.fields["comments"].widget = forms.Textarea(attrs={"rows": 3})


class MedicalHistoryForm(RecordForm):
    class Meta(RecordForm.Meta):
        model = MedicalHistory
        fields = ["category", *COMMON_FIELDS, "start_date", "end_date"]


class ProblemForm(RecordForm):
    class Meta(RecordForm.Meta):
        model = Problem
        fields = [*COMMON_FIELDS, "status", "onset_date", "resolution_date", "code"]


class AllergyForm(RecordForm):
    class Meta(RecordForm.Meta):
        model = Allergy
        fields = [*COMMON_FIELDS, "reaction", "severity", "status", "verification", "onset_date"]
        labels = {"label": "Allergen"}


class MedicationForm(RecordForm):
    class Meta(RecordForm.Meta):
        model = MedicationStatement
        fields = [*COMMON_FIELDS, "dose", "route", "frequency", "status", "start_date", "end_date"]
        labels = {"label": "Medication name"}


class DiagnosisForm(RecordForm):
    class Meta(RecordForm.Meta):
        model = EncounterDiagnosis
        fields = [*COMMON_FIELDS, "rank", "code", "problem"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["problem"].queryset = Problem.objects.filter(patient_id=self.instance.patient_id)
        self.fields["problem"].label_from_instance = lambda item: f"{item.label} ({item.get_status_display()})"


class ReviewForm(forms.Form):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    synthetic_confirmed = forms.BooleanField(label="I reviewed this synthetic record and its provenance.")


class AllergyStateForm(ReviewForm):
    status = forms.ChoiceField(choices=AllergyState._meta.get_field("status").choices)


REGISTRY = {
    "medical": (MedicalHistory, MedicalHistoryForm, "Medical history"),
    "problems": (Problem, ProblemForm, "Problems"),
    "allergies": (Allergy, AllergyForm, "Allergies"),
    "medications": (MedicationStatement, MedicationForm, "Medication history"),
    "diagnoses": (EncounterDiagnosis, DiagnosisForm, "Encounter diagnoses"),
}
