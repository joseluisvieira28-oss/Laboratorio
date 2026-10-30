import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from mu_cash_transfer_historical_v01 import predict,classify,summarize
class Guards(unittest.TestCase):
 def test_up(self):self.assertEqual(predict(100,100.2,100,100.1)[0],"UP")
 def test_down(self):self.assertEqual(predict(100,99.8,100,99.9)[0],"DOWN")
 def test_wrong_gap_rejected(self):self.assertEqual(predict(100,100.2,100,100.25)[0],"ABSTAIN")
 def test_low_cash_rejected(self):self.assertEqual(predict(100,100.05,100,100.0)[0],"ABSTAIN")
 def test_loss_and_tie(self):
  self.assertEqual(classify("UP",100,99),"LOSS")
  self.assertEqual(classify("DOWN",100,100),"TIE")
 def test_missing_EV(self):
  self.assertIsNone(summarize([],"signal")["q80_hypothetical_unit_EV"])
if __name__=="__main__":unittest.main()
