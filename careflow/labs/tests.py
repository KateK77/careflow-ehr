import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from careflow.clinical.models import Encounter, Note
from careflow.clinical.services import complete_encounter, save_note, sign_note
from careflow.patients.models import AuditEvent, Patient
from careflow.scheduling.models import Appointment
from .catalog import DEMO_COMPONENTS, validate_components
from .models import LabEvent, LabOrder, LabSpecimen, LabTestCatalog
from .services import (LabConflict, cancel_order, create_catalog, review_token, save_draft,
                       set_catalog_active, submit_order)


class LabFixture:
    def make_fixture(self):
        self.staff = {}
        for role in ['Administrator', 'Physician', 'Nurse', 'FrontDesk', 'Lab Staff']:
            actor = get_user_model().objects.create_user(username='lab-'+role.replace(' ', '-'))
            actor.groups.add(Group.objects.get_or_create(name=role)[0])
            self.staff[role] = actor
        self.admin, self.physician = self.staff['Administrator'], self.staff['Physician']
        self.other = get_user_model().objects.create_user(username='lab-other')
        self.other.groups.add(Group.objects.get(name='Physician'))
        self.patient = Patient.objects.create(mrn='LAB-01', first_name='Synthetic', last_name='Lab', dob=date(1980, 1, 1), sex='unknown')
        self.foreign = Patient.objects.create(mrn='LAB-02', first_name='Synthetic', last_name='Other', dob=date(1985, 1, 1), sex='unknown')
        now = timezone.now()
        self.appointment = Appointment.objects.create(patient=self.patient, physician=self.physician,
            start_at=now, end_at=now+timedelta(minutes=30), status='arrived', checked_in_at=now, checked_in_by=self.staff['FrontDesk'])
        self.encounter = Encounter.objects.create(patient=self.patient, physician=self.physician, appointment=self.appointment)
        self.panel = self.catalog()
        set_catalog_active(self.admin, self.panel.pk, 1, True, uuid.uuid4(), True)
        self.panel.refresh_from_db()

    def catalog(self, **changes):
        data={'code':'SYN-CHEM-01','revision':1,'display_name':'Demo chemistry','specimen_type':'mock_serum','components':copy.deepcopy(DEMO_COMPONENTS),**changes}
        return create_catalog(self.admin, data, uuid.uuid4(), True).record

    def draft(self, **changes):
        args={'actor':self.physician,'encounter_id':self.encounter.pk,'catalog_id':self.panel.pk,'reason':'Fictional test only','version':0,'command_key':uuid.uuid4(),'confirmed':True,**changes}
        return save_draft(**args).record

    def submit(self, order, **changes):
        args={'actor':self.physician,'order_id':order.public_id,'version':order.version,'command_key':uuid.uuid4(),
              'confirmed':True,'repeat_confirmed':False,'repeat_reason':'',**changes}
        args.setdefault('token',review_token(args['actor'],order,args['version'],args['repeat_confirmed'],args['repeat_reason']))
        return submit_order(**args)

    def finish_encounter(self):
        note=save_note(self.physician,self.encounter.pk,{'subjective':'Synthetic S','objective':'Synthetic O','assessment':'Synthetic A','plan':'Synthetic P','synthetic_confirmed':True},0)
        sign_note(self.physician,note.pk,note.version,True)
        complete_encounter(self.physician,self.encounter.pk,1)
        self.encounter.refresh_from_db()


class LaboratoryTests(LabFixture, TestCase):
    def setUp(self):
        self.make_fixture()
        self.client.force_login(self.physician)

    def test_catalog_and_dashboard_describe_available_workspaces(self):
        catalog = self.client.get(reverse("lab_catalog"))
        self.assertContains(catalog, "Select an active synthetic test")
        self.assertNotContains(catalog, "Phase 3B-1")
        self.assertNotContains(catalog, "Collection and results are not available")
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, "Open clinical workspace")
        self.assertContains(dashboard, "Browse laboratory catalog")
        self.assertNotContains(dashboard, "Clinical notes, orders and the patient portal are planned")
        self.client.force_login(self.staff["FrontDesk"])
        dashboard = self.client.get(reverse("dashboard"))
        self.assertNotContains(dashboard, "Browse laboratory catalog")

    def test_catalog_schema_versions_and_immutable_content(self):
        next_panel=self.catalog(revision=2,display_name='Demo revision two')
        with self.assertRaises(ValidationError): set_catalog_active(self.admin,next_panel.pk,1,True,uuid.uuid4(),True)
        set_catalog_active(self.admin,self.panel.pk,self.panel.edit_version,False,uuid.uuid4(),True)
        set_catalog_active(self.admin,next_panel.pk,1,True,uuid.uuid4(),True)
        self.panel.display_name='Changed'
        with self.assertRaises(ValidationError): self.panel.save()
        with self.assertRaises(ValidationError): self.catalog()
        self.assertEqual(LabTestCatalog.objects.count(),2)

    def test_catalog_invalid_definitions_and_units(self):
        invalid=[[],{},[{'code':'REAL'}],copy.deepcopy(DEMO_COMPONENTS)*2]
        for changes in [{'minimum':'NaN'},{'unit':'mg/dL'},{'precision':True},{'type':'expression'},{'extra':'bad'},{'maximum':'-1'}]:
            invalid.append([{**DEMO_COMPONENTS[0],**changes}])
        for value in invalid:
            with self.subTest(value=value),self.assertRaises(ValidationError): validate_components(value)
        validate_components([{'code':'SYN-D','label':'Demo screen','type':'coded','required':True,'allowed_codes':['detected','not_detected']}])

    def test_catalog_role_permissions(self):
        for role,actor in self.staff.items():
            self.client.force_login(actor)
            self.assertEqual(self.client.get(reverse('lab_catalog')).status_code,403 if role in ['FrontDesk','Lab Staff'] else 200)
            self.assertEqual(self.client.get(reverse('lab_catalog_create')).status_code,200 if role=='Administrator' else 403)
            if role!='Administrator':
                with self.assertRaises(PermissionDenied): set_catalog_active(actor,self.panel.pk,self.panel.edit_version,False,uuid.uuid4(),True)

    def test_catalog_activation_replay_stale_and_rollback(self):
        key=uuid.uuid4(); version=self.panel.edit_version
        result=set_catalog_active(self.admin,self.panel.pk,version,False,key,True)
        count=LabEvent.objects.count()
        self.assertTrue(set_catalog_active(self.admin,self.panel.pk,version,False,key,True).replayed)
        self.assertEqual(LabEvent.objects.count(),count)
        with self.assertRaises(LabConflict): set_catalog_active(self.admin,self.panel.pk,version,True,uuid.uuid4(),True)
        with self.assertRaises(LabConflict): set_catalog_active(self.admin,self.panel.pk,version,True,key,True)
        with patch('careflow.labs.services._event',side_effect=RuntimeError('test rollback')):
            with self.assertRaises(RuntimeError): set_catalog_active(self.admin,self.panel.pk,result.record.edit_version,True,uuid.uuid4(),True)
        self.panel.refresh_from_db(); self.assertFalse(self.panel.is_active)

    def test_draft_create_edit_and_persistence(self):
        order=self.draft()
        self.assertEqual((order.patient,order.encounter,order.ordering_physician),(self.patient,self.encounter,self.physician))
        self.assertFalse(LabSpecimen.objects.exists())
        outcome=save_draft(self.physician,self.encounter.pk,self.panel.pk,'Revised synthetic reason',1,uuid.uuid4(),True,order.public_id)
        order.refresh_from_db()
        self.assertEqual((order.reason,order.version),('Revised synthetic reason',2))
        self.assertEqual(order.events.count(),2)

    def test_draft_http_form_and_safe_context(self):
        url=reverse('lab_order_create',args=[self.patient.pk,self.encounter.pk])
        payload={'catalog':self.panel.pk,'reason':'Keep synthetic input','version':0,'command_key':uuid.uuid4(),'synthetic_confirmed':'on'}
        invalid=self.client.post(url,{**payload,'patient':self.foreign.pk})
        self.assertContains(invalid,'context',status_code=400)
        self.assertContains(invalid,'Keep synthetic input',status_code=400)
        self.assertFalse(LabOrder.objects.exists())
        self.assertEqual(self.client.post(url,payload).status_code,302)
        self.assertEqual(self.client.get(reverse('lab_order_create',args=[self.foreign.pk,self.encounter.pk])).status_code,404)

    def test_draft_invalid_input_stale_and_inactive_panel(self):
        order=self.draft()
        with self.assertRaises(LabConflict): save_draft(self.physician,self.encounter.pk,self.panel.pk,'bad',0,uuid.uuid4(),True,order.public_id)
        with self.assertRaises(ValidationError): self.draft(reason='x'*1001)
        with self.assertRaises(ValidationError): self.draft(confirmed=False)
        set_catalog_active(self.admin,self.panel.pk,self.panel.edit_version,False,uuid.uuid4(),True)
        with self.assertRaises(ValidationError): self.draft()

    def test_create_and_edit_idempotent_receipts(self):
        key=uuid.uuid4(); order=self.draft(command_key=key)
        count=LabEvent.objects.count()
        result=save_draft(self.physician,self.encounter.pk,self.panel.pk,'Fictional test only',0,key,True)
        self.assertTrue(result.replayed); self.assertEqual(result.record.pk,order.pk)
        self.assertEqual(LabEvent.objects.count(),count)
        with self.assertRaises(LabConflict): self.draft(command_key=key,reason='Different')
        editkey=uuid.uuid4()
        save_draft(self.physician,self.encounter.pk,self.panel.pk,'Edit',1,editkey,True,order.public_id)
        self.assertTrue(save_draft(self.physician,self.encounter.pk,self.panel.pk,'Edit',1,editkey,True,order.public_id).replayed)

    def test_submission_atomic_pending_specimen_provenance(self):
        order=self.draft(); self.submit(order); order.refresh_from_db()
        specimen=LabSpecimen.objects.get()
        self.assertEqual((order.status,order.version),('submitted',2))
        self.assertEqual((specimen.order,specimen.status,specimen.attempt,specimen.created_by),(order,'pending',1,self.physician))
        self.assertIsNone(specimen.collected_at); self.assertIsNone(specimen.received_at)
        event=order.events.first()
        self.assertEqual(event.specimen,specimen)
        self.assertEqual(event.audit.action,'lab_order_submit')
        self.assertEqual(event.audit.patient,self.patient)
        self.assertEqual(order.identity_snapshot['mrn'],self.patient.mrn)

    def test_submit_requires_review_confirmation_and_active_revision(self):
        order=self.draft()
        with self.assertRaises(ValidationError): self.submit(order,token='forged')
        with self.assertRaises(ValidationError): self.submit(order,confirmed=False)
        with self.assertRaises(ValidationError): self.submit(order,token=review_token(self.other,order,1,False,''))
        set_catalog_active(self.admin,self.panel.pk,self.panel.edit_version,False,uuid.uuid4(),True)
        with self.assertRaises(LabConflict): self.submit(order)
        self.assertFalse(LabSpecimen.objects.exists())

    def test_submission_replay_survives_expired_review_token(self):
        order=self.draft(); key=uuid.uuid4(); token=review_token(self.physician,order,1,False,'')
        self.submit(order,command_key=key,token=token)
        count=AuditEvent.objects.count()
        with patch('careflow.labs.services.signing.loads',side_effect=signing.SignatureExpired):
            self.assertTrue(self.submit(order,command_key=key,token=token).replayed)
        self.assertEqual(LabSpecimen.objects.count(),1); self.assertEqual(AuditEvent.objects.count(),count)
        with self.assertRaises(LabConflict): self.submit(order,command_key=key,repeat_confirmed=True,repeat_reason='Changed')

    def test_duplicate_order_requires_explicit_repeat_and_reason(self):
        first=self.draft(); self.submit(first)
        second=self.draft()
        with self.assertRaises(ValidationError): self.submit(second)
        with self.assertRaises(ValidationError): self.submit(second,repeat_confirmed=True)
        self.submit(second,repeat_confirmed=True,repeat_reason='Intentional synthetic repeat')
        self.assertEqual(LabSpecimen.objects.count(),2)
        second.refresh_from_db(); self.assertEqual(second.repeat_reason,'Intentional synthetic repeat')

    def test_submit_http_review_does_not_write_then_confirm(self):
        order=self.draft(); url=reverse('lab_order_submit',args=[order.public_id])
        payload={'version':1,'command_key':str(uuid.uuid4()),'synthetic_confirmed':'on','action':'review'}
        review=self.client.post(url,payload)
        self.assertEqual(review.status_code,200)
        self.assertFalse(LabSpecimen.objects.exists())
        self.assertEqual(self.client.post(url,{**payload,'action':'confirm','review_token':review.context['token']}).status_code,302)
        self.assertEqual(self.client.post(url,{**payload,'action':'confirm','review_token':review.context['token']}).status_code,302)
        self.assertEqual(LabSpecimen.objects.count(),1)

    def test_cancellation_draft_submitted_and_terminal_behavior(self):
        for submitted in [False,True]:
            order=self.draft()
            if submitted: self.submit(order); order.refresh_from_db()
            key=uuid.uuid4(); version=order.version
            cancel_order(self.physician,order.public_id,version,'Synthetic cancellation',key,True)
            self.assertTrue(cancel_order(self.physician,order.public_id,version,'Synthetic cancellation',key,True).replayed)
            order.refresh_from_db(); self.assertEqual(order.status,'cancelled')
            self.assertEqual(order.specimens.count(),1 if submitted else 0)
            with self.assertRaises(LabConflict): cancel_order(self.physician,order.public_id,order.version,'Again',uuid.uuid4(),True)
            with self.assertRaises(LabConflict): self.submit(order)

    def test_cancellation_reason_stale_and_future_received_guard(self):
        order=self.draft(); self.submit(order); order.refresh_from_db()
        with self.assertRaises(ValidationError): cancel_order(self.physician,order.public_id,2,'',uuid.uuid4(),True)
        with self.assertRaises(LabConflict): cancel_order(self.physician,order.public_id,1,'Reason',uuid.uuid4(),True)
        # Simulate future schema data, without implementing any receipt endpoint.
        order.specimens.update(status='rejected',received_at=timezone.now())
        with self.assertRaises(LabConflict): cancel_order(self.physician,order.public_id,2,'Reason',uuid.uuid4(),True)

    def test_completed_encounter_blocks_new_edits_and_submission(self):
        order=self.draft(); self.finish_encounter()
        with self.assertRaises(LabConflict): self.draft()
        with self.assertRaises(LabConflict): save_draft(self.physician,self.encounter.pk,self.panel.pk,'Edit',1,uuid.uuid4(),True,order.public_id)
        with self.assertRaises(LabConflict): self.submit(order)
        self.assertEqual(self.client.get(reverse('lab_order_edit',args=[order.public_id])).status_code,403)
        cancel_order(self.physician,order.public_id,1,'Closed encounter draft',uuid.uuid4(),True)

    def test_late_access_cancel_preserves_signed_soap_and_provenance(self):
        order=self.draft(); self.submit(order); order.refresh_from_db(); self.finish_encounter()
        before=(Note.objects.values().get(),Encounter.objects.values().get(pk=self.encounter.pk),Appointment.objects.values().get(pk=self.appointment.pk),Patient.objects.values().get(pk=self.patient.pk))
        self.assertEqual(self.client.get(reverse('lab_order_detail',args=[order.public_id])).status_code,200)
        cancel_order(self.physician,order.public_id,order.version,'Synthetic late cancellation',uuid.uuid4(),True)
        self.assertEqual(before,(Note.objects.values().get(),Encounter.objects.values().get(pk=self.encounter.pk),Appointment.objects.values().get(pk=self.appointment.pk),Patient.objects.values().get(pk=self.patient.pk)))

    def test_owner_roles_and_direct_url_denials(self):
        order=self.draft()
        for role in ['Administrator','Nurse','FrontDesk','Lab Staff']:
            actor=self.staff[role]; self.client.force_login(actor)
            self.assertIn(self.client.get(reverse('lab_order_edit',args=[order.public_id])).status_code,[403,404])
            with self.assertRaises(PermissionDenied): self.submit(order,actor=actor)
            with self.assertRaises(PermissionDenied): cancel_order(actor,order.public_id,1,'bad',uuid.uuid4(),True)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('lab_order_detail',args=[order.public_id])).status_code,404)
        with self.assertRaises(PermissionDenied): self.submit(order,actor=self.other)

    def test_nurse_draft_isolation_and_submitted_read_only(self):
        order=self.draft(); self.client.force_login(self.staff['Nurse'])
        self.assertEqual(self.client.get(reverse('lab_order_detail',args=[order.public_id])).status_code,404)
        self.submit(order)
        response=self.client.get(reverse('lab_order_detail',args=[order.public_id]))
        self.assertContains(response,'Pending')
        self.assertNotContains(response,'Cancel order')

    def test_anonymous_inactive_csrf_escaping_and_no_downstream_routes(self):
        order=self.draft(reason='<script>synthetic</script>')
        self.assertContains(self.client.get(reverse('lab_order_detail',args=[order.public_id])),'&lt;script&gt;')
        secure=Client(enforce_csrf_checks=True); secure.force_login(self.physician)
        self.assertEqual(secure.post(reverse('lab_order_cancel',args=[order.public_id]),{}).status_code,403)
        self.client.logout(); self.assertEqual(self.client.get(reverse('lab_catalog')).status_code,302)
        self.physician.is_active=False; self.physician.save()
        with self.assertRaises(PermissionDenied): self.submit(order)
        self.assertEqual(self.client.get('/app/lab/results/').status_code,302)  # Approved 3B-3 route now exists; anonymous access still requires login.

    def test_context_and_published_content_model_guards(self):
        order=self.draft(); order.patient=self.foreign
        with self.assertRaises(ValidationError): order.full_clean()
        with self.assertRaises(ValidationError): order.save()
        order.refresh_from_db(); self.submit(order); order.refresh_from_db()
        order.reason='Changed'
        with self.assertRaises(ValidationError): order.save()
        specimen=LabSpecimen.objects.get(); specimen.status='collected'
        with self.assertRaises(ValidationError): specimen.save()

    def test_database_uniqueness_and_receipt_immutability(self):
        order=self.draft(); self.submit(order)
        with self.assertRaises(IntegrityError),transaction.atomic(): LabSpecimen.objects.create(order=order,attempt=1,specimen_type='mock_serum',created_by=self.physician)
        event=LabEvent.objects.filter(order=order).first()
        with self.assertRaises(ValidationError): event.save()
        with self.assertRaises(IntegrityError),transaction.atomic():
            LabEvent.objects.create(order=order,audit=AuditEvent.objects.create(actor=self.physician,patient=self.patient),command_actor=event.command_actor,command_key=event.command_key,request_fingerprint=event.request_fingerprint)

    def test_catalog_http_default_schema_and_receipt_replay(self):
        self.client.force_login(self.admin)
        import json
        payload={'code':'SYN-HTTP','revision':1,'display_name':'Synthetic HTTP panel','specimen_type':'mock_serum',
                 'components':json.dumps(DEMO_COMPONENTS),'version':0,'command_key':str(uuid.uuid4()),'synthetic_confirmed':'on'}
        self.assertEqual(self.client.post(reverse('lab_catalog_create'),payload).status_code,302)
        self.assertEqual(self.client.post(reverse('lab_catalog_create'),payload).status_code,302)
        self.assertEqual(LabTestCatalog.objects.filter(code='SYN-HTTP').count(),1)
        duplicate=self.client.post(reverse('lab_catalog_create'),{**payload,'command_key':str(uuid.uuid4())})
        self.assertContains(duplicate,'already exist',status_code=400)
        self.assertNotContains(duplicate,'lab_catalog_revision_unique',status_code=400)
        self.assertNotContains(duplicate,'__all__',status_code=400)
        response=self.client.post(reverse('lab_catalog_create'),{**payload,'command_key':uuid.uuid4(),'components':'{}'})
        self.assertContains(response,'definitions',status_code=400)

    def test_http_draft_replay_with_inactive_catalog_does_not_duplicate(self):
        url=reverse('lab_order_create',args=[self.patient.pk,self.encounter.pk])
        payload={'catalog':self.panel.pk,'reason':'Synthetic','version':0,'command_key':str(uuid.uuid4()),'synthetic_confirmed':'on'}
        self.assertEqual(self.client.post(url,payload).status_code,302)
        set_catalog_active(self.admin,self.panel.pk,self.panel.edit_version,False,uuid.uuid4(),True)
        self.assertEqual(self.client.post(url,payload).status_code,302)
        self.assertEqual(LabOrder.objects.count(),1)
        self.assertEqual(self.client.post(url,{**payload,'command_key':str(uuid.uuid4())}).status_code,400)

    def test_atomic_submission_audit_and_specimen_rollback(self):
        order=self.draft(); count=AuditEvent.objects.count()
        with patch('careflow.labs.services._event',side_effect=RuntimeError('rollback')):
            with self.assertRaises(RuntimeError): self.submit(order)
        order.refresh_from_db(); self.assertEqual((order.status,order.version),('draft',1))
        self.assertFalse(LabSpecimen.objects.exists()); self.assertEqual(AuditEvent.objects.count(),count)
        self.submit(order)

    def test_history_scope_and_navigation(self):
        order=self.draft()
        self.assertContains(self.client.get(reverse('lab_patient_orders',args=[self.patient.pk])),'Demo chemistry')
        self.assertContains(self.client.get(reverse('lab_encounter_orders',args=[self.patient.pk,self.encounter.pk])),'Create lab order')
        self.assertEqual(self.client.get(reverse('lab_encounter_orders',args=[self.foreign.pk,self.encounter.pk])).status_code,404)
        self.assertContains(self.client.get(reverse('patient_chart',args=[self.patient.pk])),'Laboratory orders')
        self.assertContains(self.client.get(reverse('encounter_detail',args=[self.patient.pk,self.encounter.pk])),'Create lab order')


class LaboratoryConcurrencyTests(LabFixture, TransactionTestCase):
    def setUp(self): self.make_fixture()

    def parallel(self, actions):
        barrier=Barrier(len(actions))
        def run(action):
            close_old_connections()
            try:
                actor=get_user_model().objects.get(pk=self.physician.pk)
                barrier.wait(timeout=10)
                try: action(actor); return 'saved'
                except LabConflict: return 'conflict'
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=len(actions)) as pool: return list(pool.map(run,actions))

    def test_competing_submissions_prepare_one_specimen(self):
        order=self.draft(); token=review_token(self.physician,order,1,False,'')
        results=self.parallel([lambda actor: submit_order(actor,order.public_id,1,uuid.uuid4(),True,token=token)]*2)
        self.assertCountEqual(results,['saved','conflict'])
        self.assertEqual(LabSpecimen.objects.count(),1)
        self.assertEqual(LabEvent.objects.filter(audit__action='lab_order_submit').count(),1)

    def test_submission_completion_share_provider_serialization(self):
        order=self.draft(); token=review_token(self.physician,order,1,False,'')
        note=save_note(self.physician,self.encounter.pk,{'subjective':'S','objective':'O','assessment':'A','plan':'P','synthetic_confirmed':True},0)
        sign_note(self.physician,note.pk,1,True)
        from careflow.clinical.services import ClinicalConflict
        def complete(actor):
            try: complete_encounter(actor,self.encounter.pk,1)
            except ClinicalConflict: raise LabConflict('Contention')
        self.parallel([lambda actor: submit_order(actor,order.public_id,1,uuid.uuid4(),True,token=token),complete])
        order.refresh_from_db(); self.encounter.refresh_from_db()
        self.assertIn(order.status,['draft','submitted'])
        if order.status=='draft': self.assertEqual(self.encounter.status,'completed')
        self.assertEqual(LabSpecimen.objects.count(),int(order.status=='submitted'))

    def test_competing_draft_edits_do_not_overwrite(self):
        order=self.draft()
        results=self.parallel([lambda actor: save_draft(actor,self.encounter.pk,self.panel.pk,'Edit A',1,uuid.uuid4(),True,order.public_id),lambda actor: save_draft(actor,self.encounter.pk,self.panel.pk,'Edit B',1,uuid.uuid4(),True,order.public_id)])
        self.assertCountEqual(results,['saved','conflict'])
        order.refresh_from_db(); self.assertEqual(order.version,2)

    def test_competing_submission_and_cancellation_have_no_partial_state(self):
        order=self.draft(); token=review_token(self.physician,order,1,False,'')
        results=self.parallel([lambda actor: submit_order(actor,order.public_id,1,uuid.uuid4(),True,token=token),
                               lambda actor: cancel_order(actor,order.public_id,1,'Synthetic race',uuid.uuid4(),True)])
        self.assertCountEqual(results,['saved','conflict'])
        order.refresh_from_db()
        self.assertEqual(order.version,2)
        self.assertEqual(order.specimens.count(),int(order.status=='submitted'))
