from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from careflow.clinical.services import start_encounter
from .forms import MedicalHistoryForm
from .models import AllergyState, EncounterDiagnosis, HistoryEvent, MedicalHistory, PRIMARY_DIAGNOSIS_MESSAGE
from . import tests as history_tests


class UATValidationTests(TestCase):
    setUpTestData = classmethod(history_tests.HistoryTests.setUpTestData.__func__)
    setUp = history_tests.HistoryTests.setUp
    data = history_tests.HistoryTests.data
    payload = history_tests.HistoryTests.payload
    save = history_tests.HistoryTests.save
    url = history_tests.HistoryTests.url

    def test_date_year_validation_preserves_historical_dates(self):
        for value in ['12020-04-15', '020-04-15', '2020-13-15', 'malformed']:
            response = self.client.post(self.url('create', 'medical'), self.payload('medical', version=0, start_date=value))
            self.assertContains(response, 'four-digit year', status_code=400)
        self.assertFalse(MedicalHistory.objects.exists())
        for value in ['0001-04-15', '1899-04-15', '2020-04-15']:
            response = self.client.post(self.url('create', 'medical'), self.payload('medical', version=0, start_date=value))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(MedicalHistory.objects.filter(start_date=date.fromisoformat(value)).exists())
        field = MedicalHistoryForm().fields['start_date']
        self.assertEqual(field.widget.attrs['min'], '0001-01-01')

    def test_allergy_conflict_is_readable_and_retains_submitted_input(self):
        self.save('allergies')
        state = AllergyState.objects.get(patient=self.patient)
        response = self.client.post(reverse('allergy_state_review', args=[self.patient.pk]),
                                    {'version': state.version, 'status': 'no_known', 'synthetic_confirmed': 'on'})
        self.assertContains(response, 'The allergy assessment conflicts', status_code=400)
        self.assertNotContains(response, '__all__', status_code=400)
        self.assertContains(response, 'value="no_known" selected', status_code=400)
        self.assertTrue(response.context['form'].data['synthetic_confirmed'])
        state.refresh_from_db()
        self.assertEqual(state.status, 'documented')

    def test_primary_message_and_resolved_link_preserve_records_and_constraint(self):
        encounter = start_encounter(self.physician, self.appointment.pk, self.appointment.version)
        problem = self.save('problems', status='resolved', resolution_date=date(2020, 4, 15))
        primary = self.save('diagnoses', encounter=encounter, rank='primary')
        secondary = self.save('diagnoses', encounter=encounter, problem=problem)
        response = self.client.post(reverse('diagnosis_create', args=[self.patient.pk, encounter.pk]),
                                    self.payload('diagnoses', version=0, rank='primary'))
        self.assertContains(response, PRIMARY_DIAGNOSIS_MESSAGE, status_code=400)
        self.assertNotContains(response, 'one_primary_diagnosis_per_encounter', status_code=400)
        self.assertEqual(EncounterDiagnosis.objects.count(), 2)
        detail = self.client.get(reverse('diagnosis_detail', args=[self.patient.pk, encounter.pk, secondary.pk]))
        self.assertContains(detail, f'{problem.label} (Resolved)')
        problem.refresh_from_db()
        self.assertEqual(problem.status, 'resolved')
        with self.assertRaises(IntegrityError), transaction.atomic():
            EncounterDiagnosis.objects.filter(pk=secondary.pk).update(rank='primary')
        primary.refresh_from_db()
        self.assertEqual(primary.rank, 'primary')

    def test_review_replay_rejected_but_fresh_review_is_preserved(self):
        record = self.save('medical')
        url = self.url('review', 'medical', record)
        payload = {'version': 1, 'synthetic_confirmed': 'on'}
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        self.assertEqual(self.client.post(url, payload).status_code, 409)
        events = HistoryEvent.objects.filter(kind='medical', record_id=record.pk, audit__action='history_medical_review')
        self.assertEqual(events.count(), 1)
        response = self.client.get(self.url('detail', 'medical', record))
        self.assertContains(response, 'Review again')
        self.assertEqual(self.client.post(url, {**payload, 'version': 2}).status_code, 302)
        self.assertEqual(events.count(), 2)
        record.refresh_from_db()
        self.assertEqual(record.version, 3)
        self.assertEqual(record.author, self.physician)
        self.assertEqual(record.reviewed_by, self.physician)
        self.assertEqual(events.first().before['version'], 2)
        self.assertEqual(events.first().after['version'], 3)
