import uuid

from django import forms
from django.db.models import Q
from .catalog import DEMO_COMPONENTS, SPECIMEN_TYPES, validate_components
from .models import LabTestCatalog


class CommandForm(forms.Form):
    command_key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    synthetic_confirmed = forms.BooleanField(label="I confirm this action uses synthetic information only.")

    def clean(self):
        data = super().clean()
        forbidden = {"patient", "patient_id", "encounter", "encounter_id", "ordering_physician", "ordering_physician_id", "author", "status", "catalog_snapshot", "identity_snapshot", "priority"}
        if forbidden.intersection(self.data):
            raise forms.ValidationError("Patient, encounter, author and workflow context are fixed by the server and cannot be changed.")
        return data


class CatalogForm(CommandForm):
    code = forms.RegexField(r"^SYN-[A-Z0-9-]{1,32}$", max_length=40, initial="SYN-CHEM-01", help_text="Fictional uppercase SYN- code only.")
    revision = forms.IntegerField(min_value=1, initial=1)
    display_name = forms.CharField(max_length=160, initial="Demo chemistry")
    specimen_type = forms.ChoiceField(choices=SPECIMEN_TYPES)
    components = forms.JSONField(initial=lambda: DEMO_COMPONENTS, widget=forms.Textarea(attrs={"rows": 12}), validators=[validate_components],
                                 help_text="Immutable synthetic definitions: numeric mock units start demo-; coded components use allowed_codes. No real test terminology or clinical reference ranges.")


class DraftForm(CommandForm):
    catalog = forms.ModelChoiceField(queryset=LabTestCatalog.objects.filter(is_active=True), label="Active synthetic panel")
    reason = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Synthetic order reason (optional)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A formerly active selected revision remains parseable for an exact durable replay.
        # New commands still recheck activation inside the service transaction.
        if self.is_bound:
            selected = str(self.data.get('catalog', ''))
            if selected.isascii() and selected.isdecimal() and 0 < len(selected) < 19:
                self.fields['catalog'].queryset = LabTestCatalog.objects.filter(Q(is_active=True) | Q(pk=int(selected)))


class SubmitForm(CommandForm):
    repeat_confirmed = forms.BooleanField(required=False, label="This is intentional repeat testing for the same encounter and panel.")
    repeat_reason = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Repeat-test reason")
    review_token = forms.CharField(required=False, widget=forms.HiddenInput)


class CancelForm(CommandForm):
    reason = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={"rows": 3}), label="Cancellation reason")
