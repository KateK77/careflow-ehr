import secrets
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from django.contrib.auth.models import Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import close_old_connections
from django.urls import reverse
from django.utils import timezone
from .tests import LabFixture
from .models import LabOrder,LabResult,LabResultReview,LabReviewAssignment
from careflow.clinical.models import Note,Encounter
from careflow.scheduling.models import Appointment


class IntegratedLaboratoryBrowserTests(LabFixture,StaticLiveServerTestCase):
    def test_complete_multi_role_late_results_correction_coverage_withdrawal(self):
        from playwright.sync_api import sync_playwright,expect
        self.make_fixture();password=secrets.token_urlsafe(24)
        for actor in [*self.staff.values(),self.other]:actor.set_password(password);actor.save()
        self.admin.user_permissions.add(Permission.objects.get(content_type__app_label='labs',codename='reassign_review_responsibility'))
        def dbwork(fn):
            def run():
                close_old_connections()
                try:return fn()
                finally:close_old_connections()
            with ThreadPoolExecutor(1) as executor:return executor.submit(run).result()
        def clinical_rows():return (list(Note.objects.values()),list(Encounter.objects.values()),list(Appointment.objects.values()))
        with sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            def login(role):
                actor=self.other if role=='Cover' else self.staff[role]
                page.goto(self.live_server_url+'/login/');page.get_by_label('Username').fill(actor.username);page.get_by_label('Password').fill(password);page.get_by_role('button',name='Sign in to workspace').click();page.wait_for_url('**/app/**')
            def logout():page.get_by_role('button',name='Sign out',exact=True).click()
            def action(label):page.get_by_role('link',name=label,exact=True).click();page.locator('#id_synthetic_confirmed').check()
            def command():page.get_by_role('button',name='Confirm laboratory action',exact=True).click()
            login('Physician');page.goto(self.live_server_url+reverse('lab_order_create',args=[self.patient.pk,self.encounter.pk]))
            page.locator('#id_catalog').select_option(str(self.panel.pk));page.locator('#id_reason').fill('Synthetic integrated workflow');page.locator('#id_synthetic_confirmed').check();page.get_by_role('button',name='Save draft',exact=True).click()
            action('Review and submit');page.get_by_role('button',name='Review order',exact=True).click();page.get_by_role('button',name='Confirm submission',exact=True).click()
            order_id=dbwork(lambda:str(LabOrder.objects.get().public_id));accession=dbwork(lambda:str(LabOrder.objects.get().specimens.get().accession))
            # Signing/completion are existing service setup, not claimed as browser SOAP interactions.
            dbwork(self.finish_encounter);protected=dbwork(clinical_rows)
            logout();login('Nurse');page.goto(self.live_server_url+f'/app/lab/processing/{order_id}/');action('Collect specimen');page.locator('#id_mrn').fill(self.patient.mrn);page.locator('#id_dob').fill(self.patient.dob.isoformat());page.locator('#id_identity_confirmed').check();command();expect(page.locator('main')).to_contain_text('Collected')
            logout();login('Lab Staff');page.get_by_role('link',name='Claim requisition',exact=True).click();page.locator('#id_reason').fill('Synthetic lab claim');page.locator('#id_synthetic_confirmed').check();command()
            action('Receive specimen');page.locator('#id_accession').fill(accession);command();action('Start result draft');command()
            def enter_and_publish(value,comment):
                action('Edit result draft');page.locator('#id_components').fill('[{"code":"SYN-A","value_kind":"numeric","value":"'+value+'","unit":"demo-U","comment":"'+comment+'"}]');page.locator('#id_performed_at').fill(timezone.now().isoformat());command()
                action('Preview and finalize');page.get_by_role('button',name='Preview report',exact=True).click();page.get_by_role('button',name='Confirm publication',exact=True).click();expect(page.locator('main')).to_contain_text('Fulfilled')
            enter_and_publish('11.25','ORIGINAL_BROWSER_SECRET')
            logout();login('Physician');page.goto(self.live_server_url+'/app/lab/results/');page.get_by_role('link',name='Review laboratory report',exact=True).click()
            action('Acknowledge current publication');page.locator('#id_comment').fill('PRIOR_ACK_SECRET');page.get_by_role('button',name='Confirm acknowledge',exact=True).click();expect(page.locator('main')).to_contain_text('Current report acknowledged')
            logout();login('Lab Staff');page.goto(self.live_server_url+f'/app/lab/reports/{order_id}/');action('Create correction draft');page.locator('#id_reason').fill('Synthetic correction rationale');page.get_by_role('button',name='Confirm correct',exact=True).click()
            page.get_by_role('link',name='Continue laboratory processing',exact=True).click();enter_and_publish('22.5','CORRECTED_BROWSER_SECRET')
            logout();login('Physician');page.goto(self.live_server_url+f'/app/lab/reports/{order_id}/');expect(page.locator('main')).to_contain_text('Current report review required');action('Acknowledge current publication');page.get_by_role('button',name='Confirm acknowledge',exact=True).click()
            logout()
            def deactivate():
                self.physician.is_active=False;self.physician.save()
            dbwork(deactivate)
            login('Administrator');page.goto(self.live_server_url+f'/app/lab/reports/{order_id}/');expect(page.locator('main')).to_contain_text('Responsibility unresolved');action('Reassign ineligible reviewer');page.locator('#id_physician').select_option(str(self.other.pk));page.locator('#id_reason').fill('Synthetic explicit cover');page.get_by_role('button',name='Preview reassign',exact=True).click();page.get_by_role('button',name='Confirm reassign',exact=True).click()
            logout();login('Cover');page.goto(self.live_server_url+f'/app/lab/reports/{order_id}/');expect(page.locator('main')).to_contain_text('Current report review required');action('Acknowledge current publication');page.get_by_role('button',name='Confirm acknowledge',exact=True).click()
            response=page.request.get(self.live_server_url+reverse('patient_chart',args=[self.patient.pk]));self.assertEqual(response.status,404)
            logout();login('Lab Staff');page.goto(self.live_server_url+f'/app/lab/reports/{order_id}/');action('Withdraw report');page.locator('#id_reason_code').select_option('context_error');page.locator('#id_reason').fill('QUARANTINE_REASON_SECRET');page.get_by_role('button',name='Preview withdraw',exact=True).click();page.get_by_role('button',name='Confirm withdraw',exact=True).click();expect(page.locator('main')).to_contain_text('Report withdrawn')
            logout();login('Cover');page.goto(self.live_server_url+f'/app/lab/reports/{order_id}/');expect(page.locator('main')).to_contain_text('Context-error quarantine')
            for text in ['ORIGINAL_BROWSER_SECRET','CORRECTED_BROWSER_SECRET','PRIOR_ACK_SECRET','QUARANTINE_REASON_SECRET']:expect(page.locator('main')).not_to_contain_text(text)
            action('Acknowledge current publication');self.assertEqual(page.locator('#id_comment').count(),0);page.get_by_role('button',name='Confirm acknowledge',exact=True).click();expect(page.locator('main')).to_contain_text('Withdrawal notice acknowledged')
            for width in [1440,700,390]:
                page.set_viewport_size({'width':width,'height':1000});expect(page.get_by_role('heading',name='Laboratory report history',exact=True)).to_be_visible();self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width+1)
            if os.environ.get('CAREFLOW_BROWSER_SCREENSHOT_DIR'):
                folder=Path(os.environ['CAREFLOW_BROWSER_SCREENSHOT_DIR']);folder.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(folder/'integrated-withdrawal-mobile.png'),full_page=True)
            self.assertEqual(errors,[]);browser.close()
        self.assertEqual(protected,clinical_rows());self.assertEqual(LabResult.objects.count(),3);self.assertEqual(LabResultReview.objects.count(),4);self.assertEqual(LabReviewAssignment.objects.count(),2)
