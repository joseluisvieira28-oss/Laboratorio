import importlib.util
import unittest
from datetime import date
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('v3', HERE/'ced_1d_v3_boundary_readjudication_v01.py')
v3=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(v3)

def load_frozen():
    root=Path(__import__('os').environ['CED1D_FROZEN_CLOSEOUT_ROOT'])
    spec=importlib.util.spec_from_file_location('frozen', root/'src'/'closeout.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return root,mod

class BoundaryAuthorityPureTests(unittest.TestCase):
    def test_first_partial_week_excluded(self):
        self.assertFalse(v3.signal_week_eligible(date(2021,1,1)))
        self.assertFalse(v3.signal_week_eligible(date(2021,1,3)))
        self.assertTrue(v3.signal_week_eligible(date(2021,1,4)))

    def test_last_complete_signal_week_and_entry_boundary(self):
        self.assertTrue(v3.signal_week_eligible(date(2024,12,29)))
        self.assertFalse(v3.signal_week_eligible(date(2024,12,30)))
        self.assertFalse(v3.signal_week_eligible(date(2024,12,31)))

    def test_filter_uses_signal_not_entry(self):
        e={'signal_day':date(2024,12,29),'day':date(2024,12,30),'gross':5.0}
        ok,bad=v3.filtered_events([e])
        self.assertEqual(ok,[e]); self.assertEqual(bad,[])

    def test_profit_factor_formula(self):
        pf,status=v3.profit_factor([10,-5,20,-5])
        self.assertEqual(status,'FINITE'); self.assertEqual(pf,3.0)

    def test_drawdown_formula(self):
        self.assertEqual(v3.max_drawdown([10,-4,-9,20,-3]),13.0)

class FrozenEngineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root,cls.frozen=load_frozen()

    def test_sample_week_clusters_use_signal_week(self):
        es=[
            {'signal_day':date(2024,12,28),'day':date(2024,12,29),'gross':5.0},
            {'signal_day':date(2024,12,29),'day':date(2024,12,30),'gross':5.0},
        ]
        rules={'min_events':1,'min_active_days':1,'min_active_week_clusters':1,'min_active_months':1,'min_months_per_calendar_year':0}
        g=v3.sample_gate_signal_week(self.frozen,es,rules)
        self.assertEqual(g['active_week_clusters'],1)
        self.assertEqual(g['active_days'],2)

    def test_bootstrap_reuses_frozen_arithmetic_with_signal_anchor(self):
        es=[]
        for d,g in [(date(2021,1,4),20.0),(date(2021,1,5),-5.0),(date(2021,1,11),15.0),(date(2021,1,12),8.0)]:
            es.append({'signal_day':d,'day':d,'gross':g})
        p=self.frozen.WeekPlan(99,20260908)
        a=self.frozen.bootstrap(es,10,p)
        b=v3.bootstrap_signal_week(self.frozen,es,10,p)
        for k in ('status','p_raw','ci_low','ci_high','invalid_fraction'):
            self.assertEqual(a[k],b[k])

    def test_bootstrap_accepts_entry_in_partial_week_when_signal_week_complete(self):
        es=[{'signal_day':date(2024,12,29),'day':date(2024,12,30),'gross':30.0}]
        p=self.frozen.WeekPlan(19,20260908)
        b=v3.bootstrap_signal_week(self.frozen,es,10,p)
        self.assertNotEqual(b['status'],'INFERENCE_BLOCKED_INCOMPLETE_BOUNDARY_WEEK')
        self.assertEqual(b['boundary_week_events'],0)

    def test_dependency_scope_frozen(self):
        raw=Path(__import__('os').environ['CED1D_RAW_DIR'])
        cells={r['test_id']:__import__('json').loads(r['config_json']) for r in self.frozen.parse_csv((raw/'results_raw.csv').read_bytes())}
        deps=v3.dependency_scope(self.frozen,cells)
        self.assertEqual(set(deps),{'CED1D-0031','CED1D-0033','CED1D-0041','CED1D-0241','CED1D-0243','CED1D-0251','CED1D-0253','CED1D-0261'})

if __name__=='__main__':
    unittest.main()
