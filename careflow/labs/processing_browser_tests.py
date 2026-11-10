import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import close_old_connections
from django.utils import timezone
from .test_processing import ProcessingFixture
from .models import LabResult


class ProcessingBrowserTests(ProcessingFixture,StaticLiveServerTestCase):
    def test_collection_receipt_entry_preview_publication_and_access(self):
        from playwright.sync_api import sync_playwright,expect
        self.setup_processing(); password=secrets.token_urlsafe(24)
        for user in self.staff.values(): user.set_password(password); user.save()
        order_id=str(self.order.public_id); accession=str(self.order.specimens.get().accession)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(); page=browser.new_page(viewport={'width':1280,'height':1000})
            def login(role):
                page.goto(self.live_server_url+'/login/'); page.get_by_label('Username').fill(self.staff[role].username); page.get_by_label('Password').fill(password)
                page.get_by_role('button',name='Sign in to workspace').click(); page.wait_for_url('**/app/**')
            def action(name):
                page.get_by_role('link',name=name,exact=True).click()
                page.locator('#id_synthetic_confirmed').check()
            def confirm(): page.get_by_role('button',name='Confirm laboratory action',exact=True).click()
            login('Nurse'); page.goto(self.live_server_url+f'/app/lab/processing/{order_id}/'); action('Collect specimen')
            page.locator('#id_mrn').fill(self.patient.mrn); page.locator('#id_dob').fill(self.patient.dob.isoformat()); page.locator('#id_identity_confirmed').check(); confirm()
            expect(page.locator('main')).to_contain_text('Collected')
            page.get_by_role('button',name='Sign out',exact=True).click(); login('Lab Staff')
            page.get_by_role('link',name='Claim requisition',exact=True).click(); page.locator('#id_reason').fill('Synthetic browser processing'); page.locator('#id_synthetic_confirmed').check(); confirm()
            action('Receive specimen'); page.locator('#id_accession').fill(accession); confirm(); expect(page.locator('main')).to_contain_text('Received')
            action('Start result draft'); confirm(); action('Edit result draft')
            page.locator('#id_components').fill('[{"code":"SYN-A","value_kind":"numeric","value":"3.5","unit":"demo-U"}]')
            page.locator('#id_performed_at').fill(timezone.now().isoformat()); confirm()
            self.assertTrue(page.locator('main').count(),page.locator('body').inner_text()[:12000])
            action('Preview and finalize'); page.get_by_role('button',name='Preview report',exact=True).click()
            expect(page.get_by_role('heading',name='Confirm immutable publication')).to_be_visible()
            page.get_by_role('button',name='Confirm publication',exact=True).click(); expect(page.locator('main')).to_contain_text('Fulfilled')
            for width in [1280,700,390]:
                page.set_viewport_size({'width':width,'height':1000}); expect(page.get_by_role('heading',name='Laboratory processing',exact=True)).to_be_visible()
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width+1)
            page.get_by_role('button',name='Sign out',exact=True).click(); login('FrontDesk')
            response=page.goto(self.live_server_url+f'/app/lab/processing/{order_id}/'); self.assertEqual(response.status,403)
            browser.close()
        self.assertEqual(LabResult.objects.get().status,'final')
