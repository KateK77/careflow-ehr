import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.test import TestCase,TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from .tests import LabFixture
from .models import LabOrder,LabResult,LabEvent,LabSpecimen
from .processing import process,publication_token
from .payloads import envelope,validate_payload
from .services import LabConflict,cancel_order


class ProcessingFixture(LabFixture):
    def setup_processing(self):
        self.make_fixture(); self.order=self.submit(self.draft()).record
        self.lab=self.staff['Lab Staff']; self.nurse=self.staff['Nurse']

    def command(self,action,actor=None,**data):
        self.order.refresh_from_db()
        return process(actor or self.lab,self.order.public_id,self.order.version,uuid.uuid4(),action,data,True)

    def collect(self):
        s=self.order.specimens.get(); return self.command('collect',self.nurse,specimen_id=s.pk,specimen_version=s.version,mrn=self.patient.mrn,dob=self.patient.dob.isoformat(),identity_confirmed=True,collected_at=timezone.now().isoformat())

    def receive(self):
        self.command('claim',reason='Synthetic processing'); self.collect(); s=self.order.specimens.get()
        self.command('receive',specimen_id=s.pk,specimen_version=s.version,accession=str(s.accession))

    def result_draft(self):
        self.receive(); s=self.order.specimens.get(); self.command('result_create',specimen_id=s.pk,specimen_version=s.version)
        r=self.order.results.get(); self.command('result_save',result_id=r.pk,result_version=r.edit_version,components=[{'code':'SYN-A','value_kind':'numeric','value':'2.25','unit':'demo-U'}],performed_at=timezone.now().isoformat())
        return self.order.results.get()

    def publish(self):
        r=self.result_draft(); self.order.refresh_from_db()
        self.command('publish',result_id=r.pk,result_version=r.edit_version,preview_token=publication_token(self.lab,self.order,r))
        return self.order.results.get()


class ProcessingTests(ProcessingFixture,TestCase):
    def setUp(self): self.setup_processing()

    def test_complete_lifecycle_and_same_person_provenance(self):
        r=self.publish(); self.order.refresh_from_db()
        self.assertEqual(self.order.status,'fulfilled'); self.assertEqual(self.order.current_publication,r)
        self.assertEqual(r.entered_by,self.lab); self.assertEqual(r.finalized_by,self.lab)
        self.assertEqual(self.order.specimens.count(),1)
        self.assertTrue(LabEvent.objects.filter(result=r,audit__action='lab_publish').exists())

    def test_post_encounter_completion_publication_preserves_signed_note(self):
        self.finish_encounter()
        from careflow.clinical.models import Note
        before=list(Note.objects.values()); r=self.publish()
        self.encounter.refresh_from_db(); self.assertEqual(self.encounter.status,'completed')
        self.assertEqual(before,list(Note.objects.values())); self.assertEqual(r.status,'final')

    def test_collection_identity_and_future_time_validation(self):
        s=self.order.specimens.get()
        for changes in [{'mrn':self.foreign.mrn},{'identity_confirmed':False},{'dob':self.foreign.dob.isoformat()},{'collected_at':'nonsense'}]:
            d=dict(specimen_id=s.pk,specimen_version=s.version,mrn=self.patient.mrn,dob=self.patient.dob.isoformat(),identity_confirmed=True,collected_at=timezone.now().isoformat()); d.update(changes)
            with self.assertRaises(ValidationError): self.command('collect',self.nurse,**d)
        s.refresh_from_db(); self.assertEqual(s.status,'pending')

    def test_collection_correction_before_receipt_and_rejection_recollection(self):
        self.collect(); s=self.order.specimens.get()
        self.command('correct_collection',self.nurse,specimen_id=s.pk,specimen_version=s.version,mrn=self.patient.mrn,dob=self.patient.dob.isoformat(),identity_confirmed=True,collected_at=timezone.now().isoformat(),reason='Corrected synthetic time')
        s.refresh_from_db(); self.command('reject',self.nurse,specimen_id=s.pk,specimen_version=s.version,reason='Synthetic specimen rejected')
        self.command('recollect',self.nurse,reason='New synthetic attempt'); self.assertEqual(self.order.specimens.count(),2)
        self.assertEqual(self.order.specimens.get(attempt=1).status,'rejected'); self.assertEqual(self.order.specimens.get(attempt=2).status,'pending')
        with self.assertRaises(ValidationError): s.save()

    def test_receipt_ever_blocks_cancellation_even_after_rejection(self):
        self.receive(); s=self.order.specimens.get(); self.command('reject',specimen_id=s.pk,specimen_version=s.version,reason='Synthetic quality issue')
        self.order.refresh_from_db()
        with self.assertRaises(ValidationError): cancel_order(self.physician,self.order.public_id,self.order.version,'Stop',uuid.uuid4(),True)
        self.assertIsNotNone(self.order.specimens.get().received_at)
        self.command('recollect',self.nurse,reason='Collect again')

    def test_assigned_lab_and_role_isolation(self):
        self.command('claim',reason='Synthetic claim')
        for actor in [self.admin,self.physician,self.nurse,self.staff['FrontDesk'],self.other]:
            with self.assertRaises(PermissionDenied): self.command('result_create',actor)
        stranger=get_user_model().objects.create_user('unassigned.lab'); stranger.groups.add(self.lab.groups.get(name='Lab Staff'))
        with self.assertRaises(PermissionDenied): self.command('claim',stranger,reason='Not mine')
        self.client.force_login(stranger); self.assertEqual(self.client.get(reverse('lab_processing_detail',args=[self.order.public_id])).status_code,404)
        self.client.force_login(self.lab)
        for url in ['/app/patients/','/app/physician/','/app/nursing/']:
            self.assertNotEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.get(reverse('lab_worklist')).status_code,200)

    def test_wrong_specimen_and_result_are_rejected(self):
        self.receive()
        with self.assertRaises(ValidationError): self.command('result_create',specimen_id=99999,specimen_version=1)
        with self.assertRaises(ValidationError): self.command('result_save',result_id=99999,result_version=1,components=[])

    def test_strict_json_invalid_values_units_context_and_keys(self):
        self.receive(); s=self.order.specimens.get()
        good=envelope(self.order,s,[{'code':'SYN-A','value_kind':'numeric','value':'2','unit':'demo-U'}]); validate_payload(self.order,s,good,True)
        for value in [2,True,'NaN','Infinity','1e2','1,2','1.12345','-1','10000']:
            bad=copy.deepcopy(good); bad['components'][0]['value']=value
            with self.assertRaises(ValidationError): validate_payload(self.order,s,bad,True)
        for change in [{'unit':'mg/dL'},{'unknown':'ignored'}]:
            bad=copy.deepcopy(good); bad['components'][0].update(change)
            with self.assertRaises(ValidationError): validate_payload(self.order,s,bad,True)
        for change in [{'context':{'order_id':'other','specimen_id':str(s.accession)}},{'schema_version':True},{'components':good['components']*2},{'components':[]}]:
            bad={**good,**change}
            with self.assertRaises(ValidationError): validate_payload(self.order,s,bad,True)

    def test_absent_values_no_fabricated_performed_time(self):
        self.receive(); s=self.order.specimens.get(); self.command('result_create',specimen_id=s.pk,specimen_version=s.version)
        r=self.order.results.get(); self.command('result_save',result_id=r.pk,result_version=r.edit_version,components=[{'code':'SYN-A','value_kind':'absent','absence_reason':'not_performed','absence_explanation':'Synthetic unavailable'}])
        r.refresh_from_db(); self.order.refresh_from_db(); self.command('publish',result_id=r.pk,result_version=r.edit_version,preview_token=publication_token(self.lab,self.order,r))
        r.refresh_from_db(); self.assertIsNone(r.performed_at)

    def test_preview_required_immutable_publication_and_no_rejection(self):
        r=self.result_draft()
        with self.assertRaises(ValidationError): self.command('publish',result_id=r.pk,result_version=r.edit_version)
        self.order.refresh_from_db(); self.command('publish',result_id=r.pk,result_version=r.edit_version,preview_token=publication_token(self.lab,self.order,r))
        r.refresh_from_db(); r.payload['components'][0]['value']='3'
        with self.assertRaises(ValidationError): r.save()
        s=self.order.specimens.get()
        with self.assertRaises(ValidationError): self.command('reject',specimen_id=s.pk,specimen_version=s.version,reason='Too late')

    def test_abandon_before_reject_and_original_entry_preserved(self):
        r=self.result_draft(); s=self.order.specimens.get()
        with self.assertRaises(ValidationError): self.command('reject',specimen_id=s.pk,specimen_version=s.version,reason='Blocked')
        self.command('abandon',result_id=r.pk,result_version=r.edit_version,reason='Explicitly abandoned')
        self.command('reject',specimen_id=s.pk,specimen_version=s.version,reason='Quality issue')
        r.refresh_from_db(); self.assertEqual(r.status,'abandoned'); self.assertEqual(r.entered_by,self.lab)

    def test_command_replay_stale_and_rollback(self):
        key=uuid.uuid4(); version=self.order.version; data={'reason':'Synthetic claim'}
        first=process(self.lab,self.order.public_id,version,key,'claim',data,True)
        self.assertFalse(first.replayed); self.assertTrue(process(self.lab,self.order.public_id,version,key,'claim',data,True).replayed)
        with self.assertRaises(LabConflict): process(self.lab,self.order.public_id,version,key,'claim',{'reason':'Different'},True)
        with self.assertRaises(LabConflict): process(self.lab,self.order.public_id,version,uuid.uuid4(),'claim',data,True)
        self.collect(); s=self.order.specimens.get(); before=LabEvent.objects.count()
        with patch('careflow.labs.services.AuditEvent.objects.create',side_effect=RuntimeError('Injected audit failure')):
            with self.assertRaises(RuntimeError): self.command('receive',specimen_id=s.pk,specimen_version=s.version,accession=str(s.accession))
        s.refresh_from_db(); self.assertEqual(s.status,'collected'); self.assertEqual(before,LabEvent.objects.count())

    def test_admin_can_reassign_lab_staff_and_revoke_prior_access(self):
        self.command('claim',reason='Initial assignment')
        target=get_user_model().objects.create_user('new.lab'); target.groups.add(self.lab.groups.get(name='Lab Staff'))
        self.command('assign',self.admin,assignee_id=target.pk,reason='Explicit laboratory coverage')
        with self.assertRaises(PermissionDenied): self.command('result_create',self.lab)
        self.order.refresh_from_db(); self.assertEqual(self.order.assigned_lab_staff,target)

    def test_receipt_requires_correct_accession(self):
        self.command('claim',reason='Synthetic processing'); self.collect(); s=self.order.specimens.get()
        with self.assertRaises(ValidationError): self.command('receive',specimen_id=s.pk,specimen_version=s.version,accession=str(uuid.uuid4()))
        s.refresh_from_db(); self.assertEqual(s.status,'collected')

    def test_result_edit_form_post(self):
        import json
        r=self.result_draft(); self.order.refresh_from_db(); self.client.force_login(self.lab)
        response=self.client.post(reverse('lab_command',args=[self.order.public_id,'result_save']),{'command_key':str(uuid.uuid4()),'version':self.order.version,'result_id':r.pk,'result_version':r.edit_version,'components':json.dumps(r.payload['components']),'performed_at':timezone.now().isoformat(),'synthetic_confirmed':'on'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get(response.url).status_code,200)

    def test_views_and_csrf_and_request_method(self):
        from django.test import Client
        self.client.force_login(self.nurse)
        self.assertEqual(self.client.get(reverse('lab_processing_detail',args=[self.order.public_id])).status_code,200)
        self.client.force_login(self.staff['FrontDesk']); self.assertEqual(self.client.get(reverse('lab_worklist')).status_code,403)
        c=Client(enforce_csrf_checks=True); c.force_login(self.nurse)
        self.assertEqual(c.post(reverse('lab_command',args=[self.order.public_id,'collect']),{}).status_code,403)
        self.client.force_login(self.lab); self.assertEqual(self.client.get(reverse('lab_command',args=[self.order.public_id,'claim'])).status_code,200)
        self.order.refresh_from_db(); self.assertIsNone(self.order.assigned_lab_staff_id)


class ProcessingConcurrencyTests(ProcessingFixture,TransactionTestCase):
    def test_two_claims_only_one_wins(self):
        self.setup_processing(); other=get_user_model().objects.create_user('lab.second'); other.groups.add(self.lab.groups.get(name='Lab Staff'))
        barrier=Barrier(2); version=self.order.version; order_id=self.order.public_id
        def race(pk):
            close_old_connections(); actor=get_user_model().objects.get(pk=pk); barrier.wait()
            try: process(actor,order_id,version,uuid.uuid4(),'claim',{'reason':'Concurrent claim'},True); return 'ok'
            except (ValidationError,PermissionDenied): return 'conflict'
            finally: close_old_connections()
        with ThreadPoolExecutor(2) as pool: outcomes=list(pool.map(race,[self.lab.pk,other.pk]))
        self.assertEqual(outcomes.count('ok'),1); self.assertEqual(LabEvent.objects.filter(audit__action='lab_claim').count(),1)

    def test_receipt_cancellation_race(self):
        self.setup_processing(); self.command('claim',reason='Race'); self.collect()
        s=self.order.specimens.get(); self.order.refresh_from_db(); version=self.order.version; order_id=self.order.public_id; barrier=Barrier(2)
        def race(action):
            close_old_connections(); barrier.wait()
            try:
                if action=='receive': process(get_user_model().objects.get(pk=self.lab.pk),order_id,version,uuid.uuid4(),'receive',{'specimen_id':s.pk,'specimen_version':s.version,'accession':str(s.accession)},True)
                else: cancel_order(get_user_model().objects.get(pk=self.physician.pk),order_id,version,'Race cancel',uuid.uuid4(),True)
                return 'ok'
            except ValidationError: return 'conflict'
            finally: close_old_connections()
        with ThreadPoolExecutor(2) as pool: outcomes=list(pool.map(race,['receive','cancel']))
        self.assertEqual(outcomes.count('ok'),1)
        s.refresh_from_db(); self.order.refresh_from_db(); self.assertFalse(self.order.status=='cancelled' and s.received_at)

    def test_two_publications_one_receipt(self):
        self.setup_processing(); r=self.result_draft(); self.order.refresh_from_db(); version=self.order.version; barrier=Barrier(2)
        data={'result_id':r.pk,'result_version':r.edit_version,'preview_token':publication_token(self.lab,self.order,r)}
        def race(_):
            close_old_connections(); actor=get_user_model().objects.get(pk=self.lab.pk); barrier.wait()
            try: process(actor,self.order.public_id,version,uuid.uuid4(),'publish',data,True); return 'ok'
            except ValidationError: return 'conflict'
            finally: close_old_connections()
        with ThreadPoolExecutor(2) as pool: outcomes=list(pool.map(race,[1,2]))
        self.assertEqual(outcomes.count('ok'),1); self.assertEqual(LabResult.objects.filter(status='final').count(),1)
        self.assertEqual(LabEvent.objects.filter(audit__action='lab_publish').count(),1)
