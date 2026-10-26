import csv, hashlib, importlib.util, tempfile, unittest
from datetime import date,timedelta
from pathlib import Path

MOD=Path(__file__).with_name('audit_economics_v05.py')
spec=importlib.util.spec_from_file_location('econ',MOD)
econ=importlib.util.module_from_spec(spec);spec.loader.exec_module(econ)
FIELDS=('date','avax20','btc20','gross_bps','baseline_trade','fusion_trade','opposite_context_trade')

def fixture(folder):
 p=folder/'sample.csv'
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
  for i in range(730):
   day=date(2022,1,1)+timedelta(days=i)
   a=1 if i%2 else -1; b=a if i%4 else -a
   w.writerow({'date':day.isoformat(),'avax20':a,'btc20':b,'gross_bps':17.0,'baseline_trade':'True','fusion_trade':str(a==b),'opposite_context_trade':str(a==-b)})
 return p

class TestEconomicV05(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.dir=Path(self.tmp.name)
  self.path=fixture(self.dir)
  self.old=econ.EXPECTED_SHA
  econ.EXPECTED_SHA=hashlib.sha256(self.path.read_bytes()).hexdigest()
 def tearDown(self):
  econ.EXPECTED_SHA=self.old;self.tmp.cleanup()
 def test_parse_730(self):
  _,rs=econ.load(self.path)
  self.assertEqual(len(rs),730)
  self.assertEqual(sum(x['fusion'] for x in rs),547)
 def test_cost_sensitivity_is_linear(self):
  _,rs=econ.load(self.path)
  z=econ.stats(rs,'fusion',10)
  q=econ.stats(rs,'fusion',20)
  self.assertAlmostEqual(z['sum_bps']-q['sum_bps'],5470)
 def test_sha_pin(self):
  self.path.write_bytes(self.path.read_bytes()+b'\n')
  with self.assertRaisesRegex(econ.AuditError,'SHA256'):econ.load(self.path)
 def test_masks(self):
  b=self.path.read_text().replace(',True,False,True\n',',True,True,False\n',1)
  self.path.write_text(b)
  econ.EXPECTED_SHA=hashlib.sha256(self.path.read_bytes()).hexdigest()
  with self.assertRaisesRegex(econ.AuditError,'MASK_MISMATCH'):econ.load(self.path)
 def test_clock(self):
  b=self.path.read_text().replace('2022-01-01','2022-01-02',1)
  self.path.write_text(b)
  econ.EXPECTED_SHA=hashlib.sha256(self.path.read_bytes()).hexdigest()
  with self.assertRaisesRegex(econ.AuditError,'CALENDAR_OR_ORDER'):econ.load(self.path)
 def test_nw_constant_is_zero(self):
  self.assertAlmostEqual(econ.nw_long_run_sd([5.]*365,30),0.)

if __name__=='__main__':unittest.main()
