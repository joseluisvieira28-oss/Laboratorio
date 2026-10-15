import unittest
from unittest.mock import patch
from engine.three_convex_v05.signals import Bar, Halt, MS5
from engine.three_convex_v11.experimental import (
    LANES, experimental_signals, experimental_message,
)

class ExperimentalSignalsTests(unittest.TestCase):
    def bars(self, n, end_ms):
        first=end_ms-n*MS5
        return [Bar(first+i*MS5,100.,101.,99.,100.,1000.) for i in range(n)]
    def test_three_allowed(self):
        self.assertEqual(set(LANES),{
            "SOL_CONVEX_4H_EXPERIMENTAL",
            "BNB_CONVEX_30M_EXPERIMENTAL",
            "ETH_CONVEX_1H_EXPERIMENTAL"})
    def test_reject_wrong_symbol(self):
        with self.assertRaises(Halt):
            experimental_signals("XRP_USDT",[],100,0)
    def test_reject_missing_warmup(self):
        with self.assertRaises(Halt):
            experimental_signals("SOL_USDT",self.bars(5,MS5*6),MS5*6+1500,0)
    def test_reject_incomplete_candle(self):
        bars=self.bars(48*260,48*260*MS5)
        with self.assertRaises(Halt):
            experimental_signals("SOL_USDT",bars,48*260*MS5,0)
    def test_reject_gap(self):
        bars=self.bars(48*260,48*260*MS5)
        bars[2]=Bar(bars[2].t+MS5,100,101,99,100,1000)
        with self.assertRaises(Halt):
            experimental_signals("SOL_USDT",bars,48*260*MS5+1500,0)
    def test_reject_wrong_message_identity(self):
        with self.assertRaises(Halt):
            experimental_message({"lane":"SOL_CONVEX_4H_EXPERIMENTAL","symbol":"ETH_USDT"})
    def test_no_past_signal_replay(self):
        bars=self.bars(48*260,48*260*MS5)
        got=experimental_signals("SOL_USDT",bars,48*260*MS5+2000,48*260*MS5+3000)
        self.assertEqual(got,[])
    def test_message_explicitly_experimental(self):
        lane="BNB_CONVEX_30M_EXPERIMENTAL"
        msg=experimental_message({"lane":lane,"symbol":"BNB_USDT","signal_close_ms":MS5*6,"signal_id":f"{lane}:{MS5*6}"})
        self.assertIn("EXPERIMENTAL",msg)
        self.assertIn("NÃO É ORDEM",msg)
        self.assertIn("OOS e rentabilidade não comprovados",msg)

if __name__=="__main__":unittest.main()
