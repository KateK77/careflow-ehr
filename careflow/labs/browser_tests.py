import os
import secrets
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import close_old_connections
from django.utils import timezone

from careflow.clinical.models import Encounter, Note
from careflow.clinical.services import complete_encounter, save_note, sign_note
from careflow.patients.models import Patient
from careflow.scheduling.models import Appointment
from .models import LabEvent, LabOrder, LabSpecimen, LabTestCatalog


class LaboratoryBrowserTests(StaticLiveServerTestCase):
    def test_catalog_draft_submit_repeat_cancel_and_role_boundaries(self):
        from playwright.sync_api import sync_playwright, expect
        password=secrets.token_urlsafe(24)
        staff={}
        for role in ['Administrator','Physician','Nurse','FrontDesk']:
            actor=get_user_model().objects.create_user(username='lab.browser.'+role,password=password)
            actor.groups.add(Group.objects.get_or_create(name=role)[0]); staff[role]=actor
        patient=Patient.objects.create(mrn='LAB-BROWSER',first_name='Synthetic',last_name='Laboratory',dob=date(1980,1,1),sex='unknown')
        now=timezone.now()
        appointment=Appointment.objects.create(patient=patient,physician=staff['Physician'],start_at=now,end_at=now+timedelta(minutes=30),status='arrived',checked_in_at=now,checked_in_by=staff['FrontDesk'])
        encounter=Encounter.objects.create(patient=patient,physician=staff['Physician'],appointment=appointment)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(); page=browser.new_page(viewport={'width':1440,'height':1000})
            page_errors=[]; page.on('pageerror',lambda e:page_errors.append(str(e)))
            def login(role):
                page.goto(self.live_server_url+'/login/')
                page.get_by_label('Username').fill(staff[role].username); page.get_by_label('Password').fill(password)
                page.get_by_role('button',name='Sign in to workspace').click(); page.wait_for_url('**/app/dashboard/')
            def logout(): page.get_by_role('button',name='Sign out',exact=True).click()
            login('Administrator'); page.goto(self.live_server_url+'/app/lab/catalog/')
            page.get_by_role('link',name='Create catalog revision',exact=True).click()
            page.locator('#id_display_name').fill('Synthetic browser panel')
            page.locator('#id_synthetic_confirmed').check()
            page.get_by_role('button',name='Create catalog revision',exact=True).click()
            row=page.locator('tbody tr').filter(has_text='Synthetic browser panel')
            row.get_by_role('checkbox').check(); row.get_by_role('button',name='Activate',exact=True).click()
            expect(page.locator('tbody')).to_contain_text('Active')
            logout(); login('Physician')
            def new_draft(reason):
                page.goto(self.live_server_url+f'/app/patients/{patient.pk}/encounters/{encounter.pk}/')
                page.get_by_role('link',name='Create lab order',exact=True).click()
                page.locator('#id_catalog').select_option(label='SYN-CHEM-01 r1 · Synthetic browser panel')
                page.locator('#id_reason').fill(reason); page.locator('#id_synthetic_confirmed').check()
                page.get_by_role('button',name='Save draft',exact=True).click()
                expect(page.get_by_role('heading',name='Laboratory order',exact=True)).to_be_visible()
            new_draft('Initial synthetic browser reason')
            first_url=page.url
            page.get_by_role('link',name='Edit draft',exact=True).click()
            page.locator('#id_reason').fill('Edited synthetic browser reason'); page.locator('#id_synthetic_confirmed').check()
            page.get_by_role('button',name='Save draft',exact=True).click()
            page.reload(); expect(page.locator('dl')).to_contain_text('Edited synthetic browser reason')
            page.get_by_role('link',name='Review and submit',exact=True).click()
            page.locator('#id_synthetic_confirmed').check(); page.get_by_role('button',name='Review order',exact=True).click()
            expect(page.get_by_role('heading',name='Confirm laboratory submission')).to_be_visible()
            payload=page.locator('main form').evaluate('f => Object.fromEntries(new FormData(f))')
            submit_url=page.url
            page.get_by_role('button',name='Confirm submission',exact=True).click()
            expect(page.locator('dl')).to_contain_text('Submitted')
            replay=page.request.post(submit_url,data=urlencode({**payload,'action':'confirm'}),headers={'Content-Type':'application/x-www-form-urlencoded','Referer':submit_url},max_redirects=0)
            self.assertEqual(replay.status,302)
            page.reload(); expect(page.locator('main')).to_contain_text('Pending')
            new_draft('Intentional second synthetic draft')
            page.get_by_role('link',name='Review and submit',exact=True).click()
            page.locator('#id_synthetic_confirmed').check(); page.get_by_role('button',name='Review order',exact=True).click()
            expect(page.locator('.form-error-summary')).to_contain_text('repeat testing')
            page.locator('#id_repeat_confirmed').check(); page.locator('#id_repeat_reason').fill('Intentional synthetic repeat')
            page.get_by_role('button',name='Review order',exact=True).click(); page.get_by_role('button',name='Confirm submission',exact=True).click()
            page.get_by_role('link',name='Cancel order',exact=True).click()
            page.locator('#id_reason').fill('Synthetic cancellation after repeat test'); page.locator('#id_synthetic_confirmed').check()
            page.get_by_role('button',name='Confirm cancellation',exact=True).click()
            expect(page.locator('dl')).to_contain_text('Cancelled')
            page.get_by_role('link',name='Patient laboratory orders',exact=True).click()
            for width in [1440,700,390]:
                page.set_viewport_size({'width':width,'height':1000})
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),page.evaluate('innerWidth'))
                expect(page.locator('tbody')).to_contain_text('Synthetic browser panel')
            output=os.environ.get('CAREFLOW_BROWSER_SCREENSHOT_DIR')
            if output:
                Path(output).mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(Path(output)/'lab-history-mobile.png'),full_page=True)
            # Complete via the existing backend services on the isolated test DB, then exercise late browser read.
            def finish():
                close_old_connections()
                try:
                    physician=get_user_model().objects.get(pk=staff['Physician'].pk)
                    note=save_note(physician,encounter.pk,{'subjective':'S','objective':'O','assessment':'A','plan':'P','synthetic_confirmed':True},0)
                    sign_note(physician,note.pk,1,True); complete_encounter(physician,encounter.pk,1)
                    return Note.objects.values().get(pk=note.pk)
                finally:
                    close_old_connections()
            with ThreadPoolExecutor(max_workers=1) as pool:
                signed=pool.submit(finish).result()
            page.goto(first_url); expect(page.locator('main')).to_contain_text('Completed')
            logout(); login('Nurse'); page.goto(first_url)
            expect(page.locator('main')).to_contain_text('Pending')
            expect(page.get_by_role('link',name='Cancel order',exact=True)).to_have_count(0)
            self.assertEqual(page.goto(first_url+'edit/').status,403)
            page.goto(first_url)  # The standard denied page has no staff navigation.
            logout(); login('FrontDesk'); self.assertEqual(page.goto(first_url).status,403)
            self.assertEqual(page_errors,[])
            browser.close()
        self.assertEqual(LabOrder.objects.count(),2)
        self.assertEqual(LabSpecimen.objects.count(),2)
        self.assertEqual(LabEvent.objects.filter(audit__action='lab_order_submit').count(),2)
        self.assertEqual(Note.objects.values().get(pk=signed['id']),signed)
