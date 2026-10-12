import unittest
import replay as r

class ReplayTests(unittest.TestCase):
    def test_fee_geometry(self):
        gain=r.TARGET*(1-r.F)-1-r.F
        self.assertAlmostEqual(gain,4*r.LOSS,places=12)
    def test_ambiguous_stop_first(self):
        self.assertEqual(r.barrier(dict(open=100,low=95,high=120,t=0),100,10),(96,'STOP'))
    def test_stop_gap_uncapped(self):
        self.assertEqual(r.barrier(dict(open=90,low=89,high=120,t=0),100,10),(90,'GAP_STOP'))
    def test_target_gap_conservative(self):
        self.assertEqual(r.barrier(dict(open=130,low=125,high=140,t=0),100,10),(100*r.TARGET,'TARGET'))
    def test_timer_open_before_bar(self):
        self.assertEqual(r.barrier(dict(open=100,low=95,high=120,t=10),100,10),(100,'TIMEOUT'))
    def test_causal_signal_prefix(self):
        bars=[dict(t=i*r.HOUR,open=100,high=102,low=98,close=100+(i%19)/10,volume=10+i%7) for i in range(450)]
        a,_=r.ns['build_signals'](bars,'PARENT')
        b,_=r.ns['build_signals'](bars[:430],'PARENT')
        self.assertEqual(a[:430],b)
    def test_shared_account_conservation_and_end(self):
        old=(r.START,r.END)
        try:
            r.START=0;r.END=r.HOUR
            data={s:dict(by_t={0:dict(t=0,open=100,high=101,low=99,close=100),r.HOUR:dict(t=r.HOUR,open=100,high=101,low=99,close=100)},funding={},signals={0:True}) for s in r.SYMBOLS}
            result=r.run(data,.0002,.0025)
            self.assertEqual(result['closed'],2)
            self.assertEqual(result['skipped'],1)
            self.assertTrue(all(x['reason']=='FORCED_END' for x in result['trades']))
            self.assertAlmostEqual(result['net'],sum(x['net'] for x in result['trades']))
        finally:r.START,r.END=old

if __name__=='__main__':unittest.main()
