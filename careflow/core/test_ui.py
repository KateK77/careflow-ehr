from datetime import date

from django import forms
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from .forms import configure_date_field
from .templatetags.clinical_ui import event_label


class ClinicalPresentationTests(SimpleTestCase):
    def test_date_years_are_clear_and_historical_dates_remain_supported(self):
        field = configure_date_field(forms.DateField())
        for value in ['0001-01-01', '1899-04-15', '2020-04-15']:
            self.assertEqual(field.clean(value), date.fromisoformat(value))
        for value in ['12020-04-15', '2020-02-31', 'not-a-date']:
            with self.assertRaisesMessage(forms.ValidationError, 'four-digit year'):
                field.clean(value)

    def test_non_field_error_summary_has_no_internal_key_and_escapes_text(self):
        form = forms.Form(data={})
        form.is_valid()
        form.add_error(None, 'Please review <script>synthetic</script>')
        content = render_to_string('core/form_errors.html', {'form': form})
        self.assertNotIn('__all__', content)
        self.assertIn('&lt;script&gt;', content)
        self.assertNotIn('<script>', content)

    def test_audit_event_and_field_labels_preserve_human_context(self):
        self.assertEqual(event_label('note_sign'), 'SOAP note signed')
        self.assertEqual(event_label('history_medical_review'), 'Medical history review recorded')
        self.assertEqual(event_label('nursing_vitals_edit'), 'Vital observation corrected')
        text = Template('{% load clinical_ui %}{{ fields|field_labels|join:", " }}').render(Context({'fields': ['mrn', 'signed_at']}))
        self.assertEqual(text, 'MRN, Signing time')
