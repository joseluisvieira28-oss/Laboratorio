import ast, base64, csv, gzip, io, json, pathlib, unittest
import audit

class AuditTests(unittest.TestCase):
 def test_source_and_metrics_reproduction(self):
  self.assertEqual(audit.compute(),json.loads((audit.ROOT/'descriptive_metrics.json').read_text()))
 def test_original_1h_receipt_reconciliation(self):
  source=next(audit.ROOT.rglob('SEED_TRADE_LEDGER_1H_V0.1.csv.gz.b64'))
  rows=list(csv.DictReader(io.StringIO(gzip.decompress(base64.b64decode(source.read_bytes())).decode())))
  closed=[r for r in rows if r['open']=='False']
  self.assertEqual(len(closed),100)
  self.assertEqual(sum(float(r['pnl'])>0 for r in closed),26)
  self.assertAlmostEqual(sum(float(r['pnl']) for r in closed),37942.76,delta=.05)
  self.assertEqual(len({r['n'] for r in rows}),len(rows))
  for r in closed:
   # TradingView's reported percentage uses entry value INCLUDING entry fee.
   self.assertAlmostEqual(100*float(r['pnl'])/(float(r['value'])*1.001),float(r['ret']),delta=.005)
   self.assertLessEqual(audit.dt(r['entry_dt']),audit.dt(r['exit_dt']))
 def test_open_trade_and_threshold_boundaries(self):
  start=audit.dt('2020-01-01T00:00:00Z'); end=audit.dt('2020-01-02T00:00:00Z')
  rows=[dict(entry=start,exit=end,ret=r,open=False) for r in [-4.19,19.99,20,39.99,40]]
  rows.append(dict(entry=end,exit=None,ret=200,open=True))
  result=audit.summarize(rows)
  self.assertEqual(result['open_excluded'],1)
  self.assertEqual(result['fee_only_target_40_at_1x']['count'],1)
  self.assertEqual(result['fee_only_target_40_at_2x']['count'],3)
 def test_no_network_or_execution_dependencies(self):
  tree=ast.parse((audit.ROOT/'audit.py').read_text())
  imported={alias.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names}
  imported|={n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
  self.assertLessEqual(imported,{'base64','csv','gzip','hashlib','io','json','pathlib','statistics','datetime'})
  self.assertIsNone(audit.compute()['qualified_all_cost_margin_target_count'])
if __name__=='__main__': unittest.main()
