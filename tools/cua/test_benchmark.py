"""Offline contracts for CUA-100; not live Computer Use acceptance."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from benchmark import Driver,Policy,expand,summary,read_only_unchanged
from benchmark_catalog import TASKS
class CatalogTests(unittest.TestCase):
    def test_exactly_100_unique_independent_tasks(self):
        self.assertEqual(len(TASKS),100)
        self.assertEqual(len({t["id"] for t in TASKS}),100)
        self.assertEqual(len({t["title"] for t in TASKS}),100)
    def test_progressive_difficulty_and_writes(self):
        self.assertEqual({t["difficulty"] for t in TASKS},{1,2,3,4,5})
        self.assertEqual(sum(bool(t["steps"]) for t in TASKS),30)
        self.assertTrue(all(t["sql"] for t in TASKS if t["steps"]))
    def test_no_paid_secrets_in_catalog(self):
        import json
        s=json.dumps(TASKS)
        self.assertNotIn("sk-proj-",s)
        self.assertNotIn("pythonanywhere.com",s)
    def test_no_read_task_grants_write_routes(self):
        self.assertTrue(all(not t["post"] for t in TASKS if not t["steps"]))
    def test_definitions_have_unambiguous_status(self):
        self.assertTrue(all(t["status"] in (200,302,403,404) for t in TASKS))
    def test_placeholder_expansion_has_no_mutation(self):
        source={"target":"/x/{patient}/"};self.assertEqual(expand(source,{"patient":1}),{"target":"/x/1/"})
        self.assertEqual(source["target"],"/x/{patient}/")
class PolicyTests(unittest.TestCase):
    def make_driver(self):
        p=Policy(copy.deepcopy(TASKS[0]),{"password":"not-a-real-key"})
        d=Driver.__new__(Driver);d.origin="http://127.0.0.1:19999";d.policy=p
        return d
    def test_external_origins_denied(self):
        d=self.make_driver()
        for url in ("https://example.com/","http://localhost:19999/","http://127.0.0.1:20000/","file:///secret"):
            self.assertFalse(d.allows(url))
    def test_unapproved_route_and_query_denied(self):
        d=self.make_driver()
        self.assertFalse(d.allows(d.origin+"/app/patients/999/"))
        self.assertFalse(d.allows(d.origin+"/?token=anything"))
    def test_local_static_only(self):
        d=self.make_driver()
        self.assertTrue(d.allows(d.origin+"/static/core/v3.css"))
        self.assertFalse(d.allows(d.origin+"/static/core/v3.css?secret=x"))
    def test_auth_phase_does_not_allow_application_writes(self):
        p=self.make_driver().policy
        self.assertTrue(p.allow_post("http://127.0.0.1/login/",""))
        self.assertFalse(p.allow_post("http://127.0.0.1/app/patients/new/",""))
        p.authenticating=False
        self.assertFalse(p.allow_post("http://127.0.0.1/login/",""))
    def test_write_routes_are_exact(self):
        p=Policy(copy.deepcopy(TASKS[70]),{});p.authenticating=False
        self.assertTrue(p.allow_post("http://127.0.0.1/app/patients/new/",""))
        self.assertFalse(p.allow_post("http://127.0.0.1/app/patients/1/edit/",""))
    def test_unexpected_write_status_fails_closed(self):
        with self.assertRaises(RuntimeError):self.make_driver().policy.observe_post(500)
    def test_redirect_navigation_waits_for_authorized_destination(self):
        d=self.make_driver();d.policy.task=copy.deepcopy(TASKS[35]);d.page=Mock();d.page.url=d.origin+"/__benchmark__/"
        action=Mock(button="left",x=50,y=50,keys=[])
        d.click(action)
        d.page.wait_for_url.assert_called_once_with(d.origin+d.policy.task["final"],wait_until="domcontentloaded",timeout=5000)
class EvidenceTests(unittest.TestCase):
    def row(self,status):return {"status":status,"usage":{"estimated_token_cost_usd":0.1}}
    def test_no_attempts_is_not_zero_percent_pass_rate(self):
        self.assertIsNone(summary([])["attempted_pass_rate"])
    def test_blocked_and_not_run_are_visible(self):
        s=summary([self.row("PASS"),self.row("FAIL"),self.row("BLOCKED")])
        self.assertEqual(s["attempted_pass_rate"],50);self.assertEqual(s["overall_pass_fraction"],1);self.assertEqual(s["NOT_RUN"],97)
    def test_append_only_view_audits_are_allowed(self):
        before={"table":"hash","_audit_rows":[(1,1,1,"patient_create")]}
        after={"table":"hash","_audit_rows":[(1,1,1,"patient_create"),(2,1,1,"patient_view")]}
        self.assertTrue(read_only_unchanged(before,after))
    def test_audit_rewrite_is_not_allowed(self):
        before={"table":"hash","_audit_rows":[(1,1,1,"patient_create")]}
        after={"table":"hash","_audit_rows":[(1,1,2,"patient_create")]}
        self.assertFalse(read_only_unchanged(before,after))
    def test_business_write_cannot_hide_as_read_audit(self):
        self.assertFalse(read_only_unchanged({"table":"a","_audit_rows":[]},{"table":"b","_audit_rows":[(1,1,1,"patient_view")]}))
    def test_new_write_audit_is_not_read_only(self):
        self.assertFalse(read_only_unchanged({"_audit_rows":[]},{"_audit_rows":[(1,1,1,"patient_update")]}))
if __name__=="__main__":unittest.main()
