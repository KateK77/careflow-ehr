from django import forms

from .models import Patient


PATIENT_FIELDS = (
    "mrn", "first_name", "last_name", "dob", "sex", "gender_identity",
    "phone", "email", "address", "emergency_contact",
)


class PatientForm(forms.ModelForm):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput, initial=1)
    confirm_duplicate = forms.BooleanField(
        required=False, label="I reviewed the potential duplicate and confirm this is a separate synthetic patient."
    )
    synthetic_only = forms.BooleanField(label="I confirm this record contains synthetic data only.")

    class Meta:
        model = Patient
        fields = PATIENT_FIELDS
        widgets = {"dob": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.duplicates = Patient.objects.none()
        if self.instance.pk:
            self.fields["version"].initial = self.instance.version

    def clean_mrn(self):
        mrn = self.cleaned_data["mrn"].upper()
        if Patient.objects.filter(mrn__iexact=mrn).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A patient with this MRN already exists.")
        return mrn

    def clean(self):
        data = super().clean()
        if all(data.get(field) for field in ("first_name", "last_name", "dob")):
            self.duplicates = Patient.objects.filter(
                first_name__iexact=data["first_name"],
                last_name__iexact=data["last_name"],
                dob=data["dob"],
            ).exclude(pk=self.instance.pk)
            if self.duplicates.exists() and not data.get("confirm_duplicate"):
                self.add_error(None, "Potential duplicate found. Review the matching records and confirm before saving.")
        return data
