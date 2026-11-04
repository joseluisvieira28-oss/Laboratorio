import json, unittest
from shadow import Replay, sweep, economic_gate

class Adversarial(unittest.TestCase):
    def row(self, r, venue, payload, now=1000000):
        r.feed({'seq':r.last+1,'utc_ms':now,'venue':venue,'kind':'frame','raw':json.dumps(payload)})
    def depth(self, now=1000000,version=1):
        return {'channel':'push.depth.full','ts':now,'data':{'timestamp':now,'version':version,'bids':[[100-i,100000,1] for i in range(5)],'asks':[[101+i,100000,1] for i in range(5)]}}
    def test_sweep_uses_contract_units_and_haircut(self):
        self.assertAlmostEqual(sweep([[100,10],[110,10]],.15,.1), 103.33333333333333)
    def test_no_unfilled_depth(self):
        with self.assertRaises(ValueError): sweep([[100,1]],1,.1)
    def test_nan_rejected(self):
        with self.assertRaises(ValueError): sweep([[float('nan'),10]],1,1)
    def test_stale_quarantines(self):
        r=Replay(1); self.row(r,'mexc',self.depth()); self.row(r,'mexc',self.depth(),1002000)
        self.assertIsNone(r.mexc); self.assertTrue(r.errors)
    def test_crossed(self):
        r=Replay(1); d=self.depth(); d['data']['asks'][0][0]=99
        self.row(r,'mexc',d); self.assertIsNone(r.mexc)
    def test_version_regression(self):
        r=Replay(1); self.row(r,'mexc',self.depth()); self.row(r,'mexc',self.depth())
        self.assertTrue(r.errors)
    def test_delta_not_snapshot(self):
        r=Replay(1); self.row(r,'bybit',{'topic':'orderbook.1.BTCUSDT','type':'delta','ts':1000000,'data':{'b':[[100,1]],'a':[[101,1]]}})
        self.assertIsNone(r.book)
    def test_duplicate_liquidation_not_new_event(self):
        r=Replay(1); d={'topic':'allLiquidation.BTCUSDT','data':[{'T':1000000,'S':'Buy','v':'1','p':'100000'}]}
        self.row(r,'bybit',d); self.row(r,'bybit',d)
        self.assertEqual(r.count['bybit:liquidations'],1)
    def test_future_trade_rejected(self):
        r=Replay(1); self.row(r,'bybit',{'topic':'publicTrade.BTCUSDT','data':[{'T':1001000,'i':'x','S':'Buy','p':100,'v':1}]})
        self.assertTrue(r.errors); self.assertEqual(r.trades,[])
    def test_no_entry_before_delay(self):
        r=Replay(1); p={'status':'PENDING_ENTRY','due':1001000,'side':'Buy','qty_btc':1}; r.pending=p
        r.execute(1000000,self.depth()['data']); self.assertNotIn('entry',p)
    def test_entry_timeout(self):
        r=Replay(1); p={'status':'PENDING_ENTRY','due':1000000}; r.pending=p
        r.execute(1002001,{}); self.assertEqual(p['status'],'FAILED_ENTRY')
    def test_missing_exit_unresolved(self):
        r=Replay(1); p={'status':'OPEN'}; r.pending=p; r.decisions=[p]
        self.assertEqual(r.finish()['decisions'][0]['status'],'UNRESOLVED')
    def test_losing_round_trip_and_stress(self):
        r=Replay(1); p={'status':'PENDING_ENTRY','due':1000000,'side':'Buy','qty_btc':1}; r.pending=p; r.decisions=[p]
        d=self.depth()['data']; r.execute(1000000,d); r.execute(1060000,d)
        self.assertEqual(p['status'],'COMPLETE'); self.assertLess(p['base_bps'],0); self.assertLess(p['stress_bps'],p['base_bps'])
    def test_source_failure_not_no_edge(self):
        self.assertEqual(Replay().finish()['verdict'],'SOURCE_BLOCKED')
    def test_receive_reversal(self):
        r=Replay(1)
        for _ in range(2): r.feed({'seq':1,'utc_ms':1000000,'venue':'mexc','kind':'subscription','raw':''})
        self.assertIn('RECEIVE_SEQUENCE',r.errors)
    def test_causal_signal_requires_past_flow(self):
        r=Replay(.0001); r.book=1000000; r.mexc=(1000000,self.depth()['data'])
        r.liq=[(999999,'Buy',60000),(1000000,'Buy',60000)]; r.detect(1000000)
        self.assertFalse(r.decisions)
        r.trades=[(1000000,'Buy',10000)]; r.detect(1000000)
        self.assertEqual(len(r.decisions),1); self.assertEqual(r.decisions[0]['due'],1001000)
    def test_economic_insufficient_is_not_no_edge(self):
        self.assertEqual(economic_gate([])['verdict'],'ECONOMIC_INSUFFICIENT_SAMPLE')
    def test_clock_reversal_blocks(self):
        r=Replay(1)
        for seq,now in [(1,100),(2,99)]: r.feed({'seq':seq,'utc_ms':now,'venue':'mexc','kind':'subscription','raw':''})
        self.assertIn('CLOCK_REVERSAL',r.errors)
    def test_transport_gap_never_drops_exposure(self):
        r=Replay(1); p={'status':'OPEN'}; r.pending=p; r.decisions=[p]
        r.reset('disconnect'); self.assertEqual(p['status'],'UNRESOLVED'); self.assertIsNone(r.pending)
    def test_unknown_units_block(self):
        r=Replay(); r.book=1000000; r.mexc=(1000000,self.depth()['data'])
        r.liq=[(999999,'Buy',60000),(1000000,'Buy',60000)]; r.trades=[(1000000,'Buy',10000)]; r.detect(1000000)
        self.assertFalse(r.decisions)

if __name__=='__main__': unittest.main()

