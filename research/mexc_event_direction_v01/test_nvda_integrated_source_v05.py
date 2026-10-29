import unittest,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from nvda_event10m_integrated_v05 import extract_prices
class SourceParserTests(unittest.TestCase):
    def setUp(self):
        self.b=1793288700000
        self.r=self.b+15000
        self.ts=[(self.b-4*60000)//1000,(self.b-60000)//1000]
    def test_two_required_good(self):
        x=extract_prices(self.ts,[100,100.2],self.r,"NVDA","a"*64)
        self.assertEqual(len(x["bars"]),2)
    def test_unrelated_old_zero_does_not_mutate_feature_gate(self):
        x=extract_prices([self.ts[0]-1800]+self.ts,[0,100,100.2],self.r,"NVDA","a"*64)
        self.assertEqual(len(x["bars"]),2)
    def test_required_zero_rejected(self):
        with self.assertRaises(ValueError if False else RuntimeError):
            extract_prices(self.ts,[0,100],self.r,"NVDA","a"*64)
    def test_required_null_rejected(self):
        with self.assertRaises(RuntimeError):
            extract_prices(self.ts,[None,100.2],self.r,"NVDA","a"*64)
    def test_required_missing_rejected(self):
        with self.assertRaises(RuntimeError):
            extract_prices([self.ts[0]],[100],self.r,"NVDA","a"*64)
    def test_required_duplicate_rejected(self):
        with self.assertRaises(RuntimeError):
            extract_prices([self.ts[0],self.ts[0],self.ts[1]],[100,100,100.2],self.r,"NVDA","a"*64)
if __name__=="__main__":unittest.main()
