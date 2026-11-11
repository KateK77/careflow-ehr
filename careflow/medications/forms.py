import uuid

from django import forms

from .models import CATALOG_CONTENT, MedicationOrder, SyntheticMedicationCatalog


class CommandForm(forms.Form):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)
    confirmed = forms.BooleanField(label="I confirm this action uses fictional medication data")


class CatalogForm(forms.ModelForm, CommandForm):
    class Meta:
        model = SyntheticMedicationCatalog
        fields = CATALOG_CONTENT


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
