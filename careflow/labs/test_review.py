import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission,Group
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import close_old_connections
from django.test import TestCase,TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from .test_processing import ProcessingFixture
from .models import LabResult,LabReviewAssignment,LabResultReview,LabEvent,LabOrder
from .review import review_command,review_token,current_reviewed
from .processing import publication_token
from .services import LabConflict


class ReviewFixture(ProcessingFixture):
    def setup_review(self): self.setup_processing(); self.original=self.publish()
    def action(self,action,actor=None,**data):
        self.order.refresh_from_db()
        if action in {'correct','withdraw','acknowledge'}: data.setdefault('publication_id',self.order.current_publication_id)
        if action in {'acknowledge','reassign'}: data.setdefault('assignment_id',self.order.current_review_assignment_id)
        actor=actor or self.lab
        token=review_token(actor,self.order,action,data) if action in {'withdraw','reassign'} else ''
        return review_command(actor,self.order.public_id,self.order.version,uuid.uuid4(),action,data,True,token)
    def acknowledge(self,actor=None): return self.action('acknowledge',actor or self.physician,comment='Synthetic review')
    def correct(self):
        self.action('correct',reason='Synthetic correction'); r=self.order.results.get(status='draft')
        self.command('result_save',result_id=r.pk,result_version=r.edit_version,components=[{'code':'SYN-A','value_kind':'numeric','value':'7.75','unit':'demo-U','comment':'CORRECTED_SECRET'}],performed_at=timezone.now().isoformat())
        r.refresh_from_db(); self.order.refresh_from_db()
        self.command('publish',result_id=r.pk,result_version=r.edit_version,preview_token=publication_token(self.lab,self.order,r))
        return self.order.results.get(status='corrected')
    def grant(self,codename): self.admin.user_permissions.add(Permission.objects.get(content_type__app_label='labs',codename=codename))


class ReviewTests(ReviewFixture,TestCase):
    def setUp(self): self.setup_review()

    def test_initial_assignment_and_version_specific_review(self):
        a=self.order.current_review_assignment; self.assertEqual(a.source,'initial_submission'); self.assertEqual(a.physician,self.physician)
        self.assertFalse(current_reviewed(self.order)); self.acknowledge(); self.order.refresh_from_db(); self.assertTrue(current_reviewed(self.order))
        with self.assertRaises(ValidationError): self.acknowledge()
        review=LabResultReview.objects.get(); self.assertEqual(review.publication,self.original)
        with self.assertRaises(ValidationError): review.save()

    def test_correction_append_only_and_fresh_acknowledgement(self):
        before=copy.deepcopy(self.original.payload); self.acknowledge(); corrected=self.correct()
        self.original.refresh_from_db(); self.assertEqual(self.original.payload,before); self.assertEqual(self.original.status,'final')
        self.assertEqual(corrected.supersedes,self.original); self.assertEqual(corrected.entered_by,self.lab)
        self.order.refresh_from_db(); self.assertFalse(current_reviewed(self.order)); self.acknowledge()
        self.assertEqual(LabResultReview.objects.count(),2); self.assertEqual(self.order.current_publication,corrected)
        with self.assertRaises(ValidationError): corrected.save()

    def test_withdraw_preserves_history_and_requires_notice_review(self):
        self.acknowledge(); corrected=self.correct(); self.acknowledge(); fulfilled=self.order.fulfilled_at
        self.action('withdraw',reason_code='report_error',reason='Synthetic erroneous report')
        self.order.refresh_from_db(); notice=self.order.current_publication
        self.assertEqual(self.order.status,'withdrawn'); self.assertEqual(notice.status,'withdrawn'); self.assertEqual(notice.supersedes,corrected)
        self.assertNotIn('components',notice.payload); self.assertIsNone(notice.performed_at); self.assertEqual(self.order.fulfilled_at,fulfilled)
        self.assertEqual(self.order.results.count(),3); self.assertFalse(current_reviewed(self.order))
        self.action('acknowledge',self.physician,comment=''); self.assertEqual(LabResultReview.objects.last().review_kind,'withdrawal_notice')
        with self.assertRaises(ValidationError): self.action('correct',reason='Forbidden restoration')
        with self.assertRaises(ValidationError): self.action('withdraw',reason_code='report_error',reason='Again')

    def test_correction_draft_blocks_withdrawal_until_abandoned(self):
        self.action('correct',reason='Draft correction')
        with self.assertRaises(ValidationError): self.action('withdraw',reason_code='report_error',reason='Blocked')
        r=self.order.results.get(status='draft'); self.command('abandon',result_id=r.pk,result_version=r.edit_version,reason='Abandon explicitly')
        self.action('withdraw',reason_code='report_error',reason='Withdraw current'); r.refresh_from_db(); self.assertEqual(r.status,'abandoned')

    def test_quarantine_all_clinical_routes_and_old_comments(self):
        self.correct(); self.action('acknowledge',self.physician,comment='ACK_SECRET')
        self.action('withdraw',reason_code='context_error',reason='WITHDRAWAL_SECRET')
        urls=[reverse('lab_report_detail',args=[self.order.public_id]),reverse('lab_processing_detail',args=[self.order.public_id]),reverse('lab_order_detail',args=[self.order.public_id]),reverse('patient_chart',args=[self.patient.pk])]
        for actor in [self.physician,self.nurse,self.admin]:
            self.client.force_login(actor)
            for url in urls:
                response=self.client.get(url,follow=True); self.assertEqual(response.status_code,200)
                for secret in ['CORRECTED_SECRET','ACK_SECRET','WITHDRAWAL_SECRET','7.75']:
                    self.assertNotContains(response,secret)
        self.client.force_login(self.physician)
        response=self.client.get(reverse('lab_review_command',args=[self.order.public_id,'acknowledge']));self.assertNotContains(response,'CORRECTED_SECRET');self.assertNotContains(response,'ACK_SECRET')
        self.client.force_login(self.lab);self.assertContains(self.client.get(urls[0]),'CORRECTED_SECRET')
        self.grant('view_quarantined_report');self.client.force_login(self.admin);self.assertContains(self.client.get(urls[0]),'CORRECTED_SECRET')

    def test_cover_reassignment_needs_explicit_permission_and_ineligibility(self):
        data={'physician_id':self.other.pk,'reason':'Synthetic coverage'}
        with self.assertRaises(PermissionDenied): self.action('reassign',self.admin,**data)
        self.grant('reassign_review_responsibility')
        with self.assertRaises(ValidationError): self.action('reassign',self.admin,**data)
        self.physician.is_active=False; self.physician.save(); self.action('reassign',self.admin,**data)
        self.order.refresh_from_db(); self.assertEqual(self.order.ordering_physician,self.physician);self.assertEqual(self.order.current_review_assignment.physician,self.other)
        self.assertEqual(self.order.review_assignments.count(),2); self.assertFalse(current_reviewed(self.order))
        self.action('acknowledge',self.other,comment='Covered report review')
        self.assertEqual(LabResultReview.objects.get().reviewer,self.other)

    def test_cover_lab_context_does_not_expand_chart_or_soap(self):
        self.grant('reassign_review_responsibility'); self.physician.is_active=False; self.physician.save()
        self.action('reassign',self.admin,physician_id=self.other.pk,reason='Limited coverage')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('lab_report_detail',args=[self.order.public_id])).status_code,200)
        self.assertEqual(self.client.get(reverse('lab_processing_detail',args=[self.order.public_id])).status_code,200)
        self.assertEqual(self.client.get(reverse('patient_chart',args=[self.patient.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('encounter_detail',args=[self.patient.pk,self.encounter.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('lab_order_cancel',args=[self.order.public_id])).status_code,403)
        with self.assertRaises(PermissionDenied): self.action('acknowledge',self.physician,comment='Old responsible physician')

    def test_old_acknowledgements_remain_and_returning_assignee_fresh(self):
        self.acknowledge(); self.grant('reassign_review_responsibility');self.physician.is_active=False;self.physician.save()
        self.action('reassign',self.admin,physician_id=self.other.pk,reason='Cover');self.action('acknowledge',self.other,comment='Cover acknowledgement')
        self.other.is_active=False;self.other.save();self.physician.is_active=True;self.physician.save()
        self.action('reassign',self.admin,physician_id=self.physician.pk,reason='Return responsibility explicitly')
        self.order.refresh_from_db();self.assertFalse(current_reviewed(self.order));self.acknowledge();self.assertEqual(LabResultReview.objects.count(),3)

    def test_wrong_role_targets_and_reassignment_preview(self):
        for actor in [self.admin,self.nurse,self.staff['FrontDesk'],self.other]:
            with self.assertRaises(PermissionDenied): self.action('withdraw',actor,reason_code='report_error',reason='Unauthorized')
        self.grant('reassign_review_responsibility');self.physician.is_active=False;self.physician.save()
        with self.assertRaises(ValidationError): self.action('reassign',self.admin,physician_id=self.nurse.pk,reason='Not physician')
        self.order.refresh_from_db();data={'assignment_id':self.order.current_review_assignment_id,'physician_id':self.other.pk,'reason':'No preview'}
        with self.assertRaises(ValidationError): review_command(self.admin,self.order.public_id,self.order.version,uuid.uuid4(),'reassign',data,True)

    def test_stale_publication_and_assignment_conflicts(self):
        old_id=self.order.current_publication_id; old_assignment=self.order.current_review_assignment_id;self.correct()
        with self.assertRaises(ValidationError): self.action('acknowledge',self.physician,publication_id=old_id,assignment_id=old_assignment)
        with self.assertRaises(ValidationError): self.action('correct',publication_id=old_id,reason='Stale target')

    def test_replay_no_duplicate_review_and_context_error_comment_denied(self):
        self.order.refresh_from_db();version=self.order.version;key=uuid.uuid4();data={'publication_id':self.order.current_publication_id,'assignment_id':self.order.current_review_assignment_id,'comment':'Synthetic'}
        review_command(self.physician,self.order.public_id,version,key,'acknowledge',data,True)
        self.assertTrue(review_command(self.physician,self.order.public_id,version,key,'acknowledge',data,True).replayed);self.assertEqual(LabResultReview.objects.count(),1)
        self.action('withdraw',reason_code='context_error',reason='Synthetic wrong-context suspicion')
        with self.assertRaises(ValidationError):self.action('acknowledge',self.physician,comment='Do not copy sensitive text')

    def test_atomic_review_and_withdrawal_audits(self):
        count=LabResult.objects.count();self.order.refresh_from_db();before=self.order.current_publication_id
        with patch('careflow.labs.services.AuditEvent.objects.create',side_effect=RuntimeError('Injected failure')):
            with self.assertRaises(RuntimeError): self.action('withdraw',reason_code='report_error',reason='Rollback')
        self.order.refresh_from_db();self.assertEqual(self.order.current_publication_id,before);self.assertEqual(LabResult.objects.count(),count)
        with patch('careflow.labs.services.AuditEvent.objects.create',side_effect=RuntimeError('Injected failure')):
            with self.assertRaises(RuntimeError): self.acknowledge()
        self.assertFalse(LabResultReview.objects.exists())

    def test_existing_chart_physician_can_read_published_history_not_private_drafts(self):
        from careflow.scheduling.models import Appointment
        from datetime import timedelta
        now=timezone.now()
        Appointment.objects.create(patient=self.patient,physician=self.other,start_at=now,end_at=now+timedelta(minutes=30))
        self.client.force_login(self.other);self.assertEqual(self.client.get(reverse('lab_report_detail',args=[self.order.public_id])).status_code,200)
        self.assertEqual(self.client.get(reverse('lab_processing_detail',args=[self.order.public_id])).status_code,404)
        self.action('correct',reason='PRIVATE_DRAFT_REASON')
        self.assertNotContains(self.client.get(reverse('lab_report_detail',args=[self.order.public_id])),'PRIVATE_DRAFT_REASON')

    def test_review_urls_csrf_and_no_get_mutation(self):
        from django.test import Client
        self.client.force_login(self.physician);url=reverse('lab_review_command',args=[self.order.public_id,'acknowledge'])
        self.assertEqual(self.client.get(url).status_code,200);self.assertFalse(LabResultReview.objects.exists())
        client=Client(enforce_csrf_checks=True);client.force_login(self.physician);self.assertEqual(client.post(url,{}).status_code,403)
        self.client.force_login(self.staff['FrontDesk']);self.assertEqual(self.client.get(reverse('lab_report_detail',args=[self.order.public_id])).status_code,403)

    def test_immutable_assignments_and_invalid_withdrawal_payload(self):
        a=self.order.current_review_assignment
        with self.assertRaises(ValidationError):a.save()
        self.action('withdraw',reason_code='report_error',reason='Report error');self.order.refresh_from_db();n=self.order.current_publication;n.payload['components']=[]
        with self.assertRaises(ValidationError):n.clean()

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_form_input(self):
        from .forms import StrictJSONField
        field=StrictJSONField()
        for payload in ['{"value":"1","value":"2"}','[{"code":"SYN-A","value":NaN}]']:
            with self.assertRaises(ValidationError):field.clean(payload)

    def test_superuser_without_explicit_grant_cannot_reassign(self):
        self.admin.is_superuser=True;self.admin.save();self.physician.is_active=False;self.physician.save()
        with self.assertRaises(PermissionDenied):self.action('reassign',self.admin,physician_id=self.other.pk,reason='Explicit grant required')

    def test_context_error_reviewer_can_ack_notice_after_reassignment(self):
        self.action('withdraw',reason_code='context_error',reason='Context suspicion')
        self.grant('reassign_review_responsibility');self.physician.is_active=False;self.physician.save()
        self.action('reassign',self.admin,physician_id=self.other.pk,reason='Review withdrawal notice')
        self.action('acknowledge',self.other,comment='');self.order.refresh_from_db();self.assertTrue(current_reviewed(self.order))
        self.assertEqual(LabResultReview.objects.get().review_kind,'withdrawal_notice')

    def test_history_cannot_be_deleted_via_instance(self):
        self.acknowledge()
        for obj in [self.original,self.order.current_review_assignment,LabResultReview.objects.get(),LabEvent.objects.first()]:
            with self.assertRaises(ValidationError):obj.delete()

    def test_foreign_assignment_and_publication_review_denied(self):
        with self.assertRaises(ValidationError):self.action('acknowledge',self.physician,publication_id=99999)
        with self.assertRaises(ValidationError):self.action('acknowledge',self.physician,assignment_id=99999)

    def test_saved_draft_values_are_withheld_from_non_lab_audit_routes(self):
        # A submitted order without a publication must not leak a mutable draft through raw event snapshots.
        new=self.submit(self.draft(),repeat_confirmed=True,repeat_reason='Independent synthetic panel').record
        self.order=new;r=self.result_draft();self.client.force_login(self.nurse)
        response=self.client.get(reverse('lab_order_detail',args=[new.public_id]));self.assertNotContains(response,'result_snapshot')
        response=self.client.get(reverse('lab_processing_detail',args=[new.public_id]));self.assertNotContains(response,'2.25')



class ReviewConcurrencyTests(ReviewFixture,TransactionTestCase):
    def test_acknowledgement_and_withdrawal_one_version_wins(self):
        self.setup_review();self.order.refresh_from_db();version=self.order.version;publication=self.order.current_publication_id;assignment=self.order.current_review_assignment_id;barrier=Barrier(2)
        def race(action):
            close_old_connections();actor=get_user_model().objects.get(pk=self.physician.pk if action=='acknowledge' else self.lab.pk)
            data={'publication_id':publication,'assignment_id':assignment,'comment':''} if action=='acknowledge' else {'publication_id':publication,'reason_code':'report_error','reason':'Race withdrawal'}
            token=review_token(actor,self.order,action,data) if action=='withdraw' else '';barrier.wait()
            try:review_command(actor,self.order.public_id,version,uuid.uuid4(),action,data,True,token);return 'ok'
            except ValidationError:return 'conflict'
            finally:close_old_connections()
        with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(race,['acknowledge','withdraw']))
        self.assertEqual(outcomes.count('ok'),1)
        self.order.refresh_from_db()
        if self.order.status=='withdrawn':self.assertFalse(current_reviewed(self.order))

    def test_two_reassignments_one_epoch(self):
        self.setup_review();self.grant('reassign_review_responsibility');self.physician.is_active=False;self.physician.save();self.order.refresh_from_db();version=self.order.version;barrier=Barrier(2)
        data={'assignment_id':self.order.current_review_assignment_id,'physician_id':self.other.pk,'reason':'Concurrent coverage'}
        def race(_):
            close_old_connections();actor=get_user_model().objects.get(pk=self.admin.pk);token=review_token(actor,self.order,'reassign',data);barrier.wait()
            try:review_command(actor,self.order.public_id,version,uuid.uuid4(),'reassign',data,True,token);return 'ok'
            except ValidationError:return 'conflict'
            finally:close_old_connections()
        with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(race,[1,2]))
        self.assertEqual(outcomes.count('ok'),1);self.assertEqual(self.order.review_assignments.count(),2)

    def test_two_withdrawals_publish_one_notice(self):
        self.setup_review();self.order.refresh_from_db();version=self.order.version;barrier=Barrier(2)
        data={'publication_id':self.order.current_publication_id,'reason_code':'report_error','reason':'Concurrent notices'}
        def race(_):
            close_old_connections();actor=get_user_model().objects.get(pk=self.lab.pk);token=review_token(actor,self.order,'withdraw',data);barrier.wait()
            try:review_command(actor,self.order.public_id,version,uuid.uuid4(),'withdraw',data,True,token);return 'ok'
            except ValidationError:return 'conflict'
            finally:close_old_connections()
        with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(race,[1,2]))
        self.assertEqual(outcomes.count('ok'),1);self.assertEqual(LabResult.objects.filter(status='withdrawn').count(),1)

    def test_correction_draft_and_withdrawal_one_winner(self):
        self.setup_review();self.order.refresh_from_db();version=self.order.version;barrier=Barrier(2)
        def race(action):
            close_old_connections();actor=get_user_model().objects.get(pk=self.lab.pk)
            data={'publication_id':self.order.current_publication_id,'reason':'Concurrent mutation'}
            if action=='withdraw':data['reason_code']='report_error'
            token=review_token(actor,self.order,action,data) if action=='withdraw' else '';barrier.wait()
            try:review_command(actor,self.order.public_id,version,uuid.uuid4(),action,data,True,token);return 'ok'
            except ValidationError:return 'conflict'
            finally:close_old_connections()
        with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(race,['correct','withdraw']))
        self.assertEqual(outcomes.count('ok'),1);self.assertFalse(LabResult.objects.filter(status='draft').exists() and LabResult.objects.filter(status='withdrawn').exists())
