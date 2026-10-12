import math
import unittest
import compare as c

class TrailingMatchedSyntheticTests(unittest.TestCase):
    def test_control_4r_source_is_unmodified(self):
        self.assertEqual(c.baseline.SYMBOLS,['ETHUSDT','SOLUSDT','BNBUSDT'])
        self.assertEqual(c.baseline.F,.0008)
        gain=c.baseline.TARGET*(1-c.baseline.F)-1-c.baseline.F
        self.assertAlmostEqual(gain,4*c.baseline.LOSS,places=11)

    def test_nonlatched_activation_then_deactivation(self):
        self.assertEqual(c.next_active_stop(110,105,100,96),96.8)
        self.assertEqual(c.next_active_stop(110,104,100,96),96)
        self.assertEqual(c.next_active_stop(200,104,100,96),96)
        self.assertEqual(c.next_active_stop(120,106,100,96),105.6)

    def test_same_bar_new_high_cannot_raise_stale_stop(self):
        b=dict(t=2*c.HOUR,open=110,low=101,high=140,close=120)
        self.assertEqual(c.trailing_bar_exit(b,96,0,10*c.HOUR),(None,None,False))
        self.assertGreater(c.next_active_stop(140,120,100,96),101)

    def test_gap_vs_intrabar(self):
        b=dict(t=c.HOUR,open=90,low=89,high=120,close=110)
        self.assertEqual(c.trailing_bar_exit(b,96,0,None),(90,'GAP_STOP',True))
        b=dict(t=c.HOUR,open=100,low=95,high=120,close=110)
        self.assertEqual(c.trailing_bar_exit(b,96,0,None),(96,'STOP',False))

    def test_timer_is_next_bar_open(self):
        b=dict(t=3*c.HOUR,open=108,low=90,high=120,close=110)
        self.assertEqual(c.trailing_bar_exit(b,96,0,3*c.HOUR),(108,'TIMEOUT',True))
        self.assertEqual(c.trailing_bar_exit(b,96,0,None),(96,'STOP',False))

    def test_pine_close_threshold_exact(self):
        self.assertEqual(c.next_active_stop(120,105,100,96),105.6)
        self.assertEqual(c.next_active_stop(120,104.999,100,96),96)

    def test_trail_first_bar_initial_stop(self):
        t0,t1=0,c.HOUR
        old=c.START,c.END
        try:
            c.START,c.END=t0,t1
            data={s:dict(by_t={
                t0:dict(t=t0,open=100,high=101,low=99,close=100),
                t1:dict(t=t1,open=100,high=120,low=95,close=110)
            },funding={},signals={t0:True}) for s in c.SYMBOLS}
            x=c.run_trailing(data,.0002,.0025)
            self.assertEqual(x['closed'],2)
            self.assertEqual(x['skipped'],1)
            self.assertTrue(all(z['reason']=='STOP' for z in x['trades']))
            self.assertTrue(all(abs(z['exit']-96*(1-.0002))<.05 for z in x['trades']))
            self.assertAlmostEqual(x['net'],sum(z['net'] for z in x['trades']),places=8)
        finally:c.START,c.END=old

    def test_next_bar_stop_after_prior_high(self):
        old=c.START,c.END
        try:
            c.START,c.END=0,2*c.HOUR
            data={s:dict(by_t={
               0:dict(t=0,open=100,high=101,low=99,close=100),
               c.HOUR:dict(t=c.HOUR,open=100,high=120,low=98,close=110),
               2*c.HOUR:dict(t=2*c.HOUR,open=110,high=111,low=103,close=104)
            },funding={},signals={0:True}) for s in c.SYMBOLS}
            x=c.run_trailing(data,0.,.0025)
            self.assertEqual(x['closed'],2)
            self.assertEqual(x['skipped'],1)
            self.assertTrue(all(tr['reason']=='STOP' for tr in x['trades']))
            self.assertTrue(all(abs(tr['exit']-105.6)<1e-8 for tr in x['trades']))
        finally:c.START,c.END=old

    def test_funding_conservation_across_same_account(self):
        old=c.START,c.END
        try:
            c.START,c.END=0,2*c.HOUR
            data={s:dict(by_t={
               0:dict(t=0,open=100,high=101,low=99,close=100),
               c.HOUR:dict(t=c.HOUR,open=100,high=102,low=99,close=101),
               2*c.HOUR:dict(t=2*c.HOUR,open=101,high=102,low=100,close=101)
            },funding={2*c.HOUR:{'mark':101,'rate':.001}},signals={0:True}) for s in c.SYMBOLS}
            x=c.run_trailing(data,.0002,.0025)
            self.assertEqual(x['closed'],2)
            self.assertAlmostEqual(x['net'],sum(z['net'] for z in x['trades']),places=8)
            self.assertTrue(all(tr['funding']<0 for tr in x['trades']))
        finally:c.START,c.END=old

if __name__=='__main__':unittest.main()
