import uuid

from django import forms

from .models import FORMS, FREQUENCIES, ROUTES, MedicationOrder, SyntheticMedicationCatalog


class CommandForm(forms.Form):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)
    confirmed = forms.BooleanField(label="I confirm this action uses fictional medication data")


class CatalogForm(CommandForm):
    code = forms.CharField(max_length=40)
    revision = forms.IntegerField(min_value=1)
    name = forms.CharField(max_length=100)
    dosage_form = forms.ChoiceField(choices=FORMS)
    strength = forms.CharField(max_length=40)
    route = forms.ChoiceField(choices=ROUTES)
    frequency = forms.ChoiceField(choices=FREQUENCIES)


class DraftForm(forms.ModelForm, CommandForm):
    class Meta:
        model = MedicationOrder
        fields = ("catalog", "dose", "route", "frequency", "duration", "quantity", "instructions")
        labels = {"duration": "Duration in days", "quantity": "Quantity of simulated units",
                  "instructions": "Fictional instructions"}
        widgets = {"instructions": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        catalog = SyntheticMedicationCatalog.objects.all() if self.is_bound else SyntheticMedicationCatalog.objects.filter(active=True)
        # Preserve replay of a prior command if the catalog was retired after that command.
        self.fields["catalog"].queryset = catalog
        self.fields["catalog"].help_text = "Select the route and frequency shown in the catalog for this revision."


class SignForm(CommandForm):
    token = forms.CharField(widget=forms.HiddenInput)


class ReasonForm(CommandForm):
    reason = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 3}))
