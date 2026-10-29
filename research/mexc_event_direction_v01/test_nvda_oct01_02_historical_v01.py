import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nvda_oct01_02_historical_proxy_v01 import frozen_signal,outcome,aggregate,total
class FreezeParity(unittest.TestCase):
 def test_exact_cash_gap_UP(self):
  side,*_=frozen_signal(100,100.20,100,100.10)
  self.assertEqual(side,"UP")
 def test_exact_cash_gap_DOWN(self):
  side,*_=frozen_signal(100,99.80,100,99.90)
  self.assertEqual(side,"DOWN")
 def test_insufficient_cash_ABSTAIN(self):
  side,*_=frozen_signal(100,100.05,100,100.00)
  self.assertEqual(side,"ABSTAIN")
 def test_lag_has_wrong_sign_ABSTAIN(self):
  side,*_=frozen_signal(100,100.15,100,100.20)
  self.assertEqual(side,"ABSTAIN")
 def test_absolute_thresholds_not_retuned(self):
  side,*_=frozen_signal(100,100.08,100,100.0)
  self.assertEqual(side,"ABSTAIN")
 def test_outcome_direction(self):
  self.assertEqual(outcome("UP",100,101),"WIN")
  self.assertEqual(outcome("DOWN",100,101),"LOSS")
  self.assertEqual(outcome("UP",100,100),"TIE")
 def test_zero_samples_Ev_is_NA(self):
  self.assertIsNone(aggregate([],"signal")["ev_hypothetical_q80"])
if __name__=="__main__":unittest.main()
