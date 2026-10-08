import importlib.util, pathlib, unittest
spec=importlib.util.spec_from_file_location('probe',pathlib.Path(__file__).parents[1]/'probe.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class ScientificInvariants(unittest.TestCase):
 def test_payoff_is_constant_in_all_regions(self):
  for s in (0,50,90,95,100,110,120,1000): self.assertEqual(m.payoff(s,90,110),20)
 def test_fees_notional_cap_and_quantity(self):
  self.assertAlmostEqual(m.fee(100000,1000,.01),.3)
  self.assertAlmostEqual(m.fee(100000,1,.01),.00125)
 def fixture(self):
  legs=[{'instrument_name':str(i),'contract_size':1,'settlement_currency':'USDC','taker_commission':.0003} for i in range(4)]
  g={'k1':90,'k2':110,'dte':60,'quantity':1,'legs':legs}
  prices=[(12,13),(1,2),(1,2),(12,13)]
  books=[{'received_ms':1000,'data':{'instrument_name':str(i),'state':'open','timestamp':1000,'index_price':100,'underlying_price':100,'mark_price':sum(p)/2,'bids':[[p[0],10]],'asks':[[p[1],10]]}} for i,p in enumerate(prices)]
  return g,books
 def test_expensive_box_rejected_before_optional_costs(self):
  g,b=self.fixture(); r=m.assess(g,b)
  self.assertEqual(r['debit_usdc'],24); self.assertAlmostEqual(r['entry_fee_adjusted_upper_bound_usdc'],-4.12)
  self.assertIsNone(r['all_cost_net_usdc']); self.assertFalse(r['atomic_execution_proven'])
 def test_stale_missing_crossed_and_insufficient_never_zero_pnl(self):
  for kind in ('stale','missing','crossed','size','fee'):
   g,b=self.fixture()
   if kind=='stale': b[0]['received_ms']=7000
   if kind=='missing': b[0]['data']['asks']=[]
   if kind=='crossed': b[0]['data']['bids'][0][0]=100
   if kind=='size': b[0]['data']['asks'][0][1]=.01
   if kind=='fee': g['legs'][0]['taker_commission']=0
   r=m.assess(g,b); self.assertEqual(r['source_status'],'INVALID_SOURCE'); self.assertNotIn('entry_fee_adjusted_upper_bound_usdc',r)
 def test_private_and_mutating_endpoints_rejected(self):
  for method in ('auth','buy','create_combo','get_account_summary','../private/buy'):
   with self.assertRaises(ValueError): m.api(method,{},pathlib.Path('.'))
if __name__=='__main__': unittest.main()
